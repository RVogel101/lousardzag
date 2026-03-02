#!/usr/bin/env python3
"""
Pull and validate Armenian vocabulary data from Anki.

This script connects to a running Anki instance via AnkiConnect, reads notes
from one or more decks, and validates that each note represents Western
Armenian (as opposed to Eastern Armenian or Classical Armenian / Grabar).

It is strictly READ-ONLY — no Anki data is created, modified, or deleted.

Optionally, it can first run the Nayiri headword scraper to build a reference
word list that is used as an additional cross-validation signal.

Usage
-----
Run from the repository root::

    python _pull_anki_data.py [--deck "My Deck"] [--nayiri] [--output results.json]

Flags
-----
  --deck DECK_NAME    Anki deck to pull from (default: "Armenian Vocabulary")
  --nayiri            Scrape Nayiri.com headwords before validating notes
  --max-nayiri N      Max pages of Nayiri headwords to scrape (default: 5)
  --threshold FLOAT   Minimum WA confidence score, 0–1 (default: 0.55)
  --output FILE       Write full results to a JSON file (optional)
  --verbose           Show per-note classification details
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

# ── Package path ─────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

from armenian_anki.anki_connect import AnkiConnect, AnkiConnectError
from armenian_anki.western_armenian_filter import (
    filter_notes,
    classify_note,
    THRESHOLD_LIKELY_WA,
    is_armenian_script,
)

logger = logging.getLogger(__name__)

# ─── Nayiri headword scraper ──────────────────────────────────────────────────

_NAYIRI_BASE = "https://www.nayiri.com"
# Nayiri browse-by-letter URL template (Western Armenian dictionary).
# Each letter page lists headwords alphabetically.
_NAYIRI_BROWSE_URL = _NAYIRI_BASE + "/search?dictionaryId=6&dt=HY_EN&query={letter}"

# Armenian lowercase letters in alphabetical order (used to iterate pages).
_ARM_LETTERS = [
    "ա", "բ", "գ", "դ", "ե", "զ", "է", "ը", "թ", "ժ",
    "ի", "լ", "խ", "ծ", "կ", "հ", "ձ", "ղ", "ճ", "մ",
    "յ", "ն", "շ", "ո", "չ", "պ", "ջ", "ռ", "ս", "վ",
    "տ", "ր", "ց", "ւ", "փ", "ք", "օ", "ֆ",
]

# Regex-free extraction: headwords appear as <a href="/...?...&query=WORD">
_HEADWORD_HREF_MARKER = 'href="/search?'


def scrape_nayiri_headwords(
    max_pages: int = 5,
    delay_seconds: float = 1.5,
) -> set[str]:
    """Scrape Western Armenian headwords from Nayiri.com.

    Iterates over Armenian letter pages on Nayiri (Western Armenian ↔ English
    dictionary, dictionaryId=6) and collects headwords.

    Args:
        max_pages:     Maximum number of letter pages to fetch.  Each letter
                       covers words starting with that character.  Set to a
                       small value for quick cross-validation; use 38 (full
                       alphabet) for a comprehensive word list.
        delay_seconds: Polite delay between HTTP requests.

    Returns:
        A set of lowercase Armenian headword strings.
    """
    headwords: set[str] = set()
    letters_to_fetch = _ARM_LETTERS[:max_pages]

    logger.info("Nayiri scraper: fetching %d letter page(s)…", len(letters_to_fetch))

    for letter in letters_to_fetch:
        url = _NAYIRI_BROWSE_URL.format(
            letter=urllib.parse.quote(letter, safe="")
        )
        try:
            words = _fetch_nayiri_page(url)
            headwords.update(words)
            logger.info("  %s → %d headword(s) (running total: %d)",
                        letter, len(words), len(headwords))
        except Exception as exc:
            logger.warning("  %s → failed to fetch: %s", letter, exc)
        time.sleep(delay_seconds)

    logger.info("Nayiri scraper: collected %d unique headwords total.", len(headwords))
    return headwords


def _fetch_nayiri_page(url: str) -> set[str]:
    """Fetch one Nayiri page and extract headword strings from the HTML."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (compatible; Armenian-Anki-Pipeline/1.0; "
                "+https://github.com/RVogel101/anki-note-generation-pipeline)"
            ),
            "Accept-Language": "hy,en;q=0.9",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8", errors="replace")

    return _parse_nayiri_headwords(html)


def _parse_nayiri_headwords(html: str) -> set[str]:
    """Extract headwords from raw Nayiri HTML (no external parser needed).

    Looks for anchor tags whose href points to a Nayiri search result,
    then extracts the ``query`` parameter value which is the headword.
    """
    words: set[str] = set()
    for segment in html.split(_HEADWORD_HREF_MARKER)[1:]:
        # Grab everything up to the closing quote of the href attribute value.
        href_fragment = segment.split('"')[0]  # e.g. "dictionaryId=6&...&query=WORD"
        # Parse query parameters from the fragment.
        params = dict(
            part.split("=", 1) for part in href_fragment.split("&")
            if "=" in part
        )
        raw_query = params.get("query", "")
        word = urllib.parse.unquote(raw_query).strip()
        if word and is_armenian_script(word):
            words.add(word.lower())
    return words


# ─── Anki data puller ─────────────────────────────────────────────────────────

def pull_and_validate(
    deck: str,
    anki: Optional[AnkiConnect] = None,
    reference_headwords: Optional[set[str]] = None,
    threshold: float = THRESHOLD_LIKELY_WA,
    verbose: bool = False,
) -> dict:
    """Pull notes from *deck* and classify each one as Western Armenian or not.

    This function is strictly read-only: it calls only ``findNotes`` and
    ``notesInfo`` on the AnkiConnect API.

    Args:
        deck:               Name of the Anki deck to query.
        anki:               AnkiConnect client (created automatically if None).
        reference_headwords: Optional set of known WA headwords from Nayiri.
        threshold:          Minimum WA confidence to classify a note as WA.
        verbose:            If True, log per-note classification details.

    Returns:
        A result dict with keys:
            deck, total, accepted, rejected, acceptance_rate,
            accepted_notes, rejected_notes
    """
    client = anki or AnkiConnect()

    logger.info("Connecting to AnkiConnect…")
    if not client.ping():
        raise AnkiConnectError(
            "Cannot reach AnkiConnect.  "
            "Make sure Anki is running with the AnkiConnect plugin installed."
        )

    logger.info("Pulling notes from deck: %s", deck)
    note_ids = client.find_notes(f'"deck:{deck}"')
    if not note_ids:
        logger.warning("No notes found in deck '%s'.", deck)
        return {
            "deck": deck,
            "total": 0,
            "accepted": 0,
            "rejected": 0,
            "acceptance_rate": 0.0,
            "accepted_notes": [],
            "rejected_notes": [],
        }

    logger.info("Found %d note(s) — fetching details…", len(note_ids))
    notes = client.notes_info(note_ids)

    # Annotate each note with its WA score before splitting.
    for note in notes:
        is_wa, score = classify_note(note, reference_headwords, threshold)
        note["_wa_score"] = round(score, 3)
        note["_is_western_armenian"] = is_wa
        if verbose:
            fields = {k: v.get("value", "") if isinstance(v, dict) else v
                      for k, v in note.get("fields", {}).items()}
            word = (fields.get("Word") or fields.get("Front")
                    or fields.get("Infinitive") or "(unknown)")
            logger.info("  Note %-20s  score=%.2f  wa=%s",
                        word[:20], score, is_wa)

    accepted, rejected = filter_notes(notes, reference_headwords, threshold)

    total = len(notes)
    n_accepted = len(accepted)
    acceptance_rate = round(n_accepted / total * 100, 1) if total else 0.0

    result = {
        "deck": deck,
        "total": total,
        "accepted": n_accepted,
        "rejected": len(rejected),
        "acceptance_rate": acceptance_rate,
        "accepted_notes": accepted,
        "rejected_notes": rejected,
    }

    logger.info(
        "Results for '%s': %d total, %d WA (%.1f%%), %d rejected",
        deck, total, n_accepted, acceptance_rate, len(rejected),
    )
    return result


# ─── CLI ──────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="_pull_anki_data",
        description=(
            "Pull Armenian vocabulary from Anki and validate for Western Armenian "
            "(read-only — no Anki data is modified)."
        ),
    )
    parser.add_argument(
        "--deck",
        default="Armenian Vocabulary",
        help="Anki deck name to pull from (default: 'Armenian Vocabulary')",
    )
    parser.add_argument(
        "--nayiri",
        action="store_true",
        help="Scrape Nayiri.com headwords before validating notes",
    )
    parser.add_argument(
        "--max-nayiri",
        type=int,
        default=5,
        metavar="N",
        help="Number of Nayiri letter pages to scrape (default: 5)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=THRESHOLD_LIKELY_WA,
        metavar="SCORE",
        help=f"Minimum WA confidence score 0–1 (default: {THRESHOLD_LIKELY_WA})",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        help="Write full JSON results to this file",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Log per-note classification details",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s  %(message)s",
        datefmt="%H:%M:%S",
    )

    args = _build_parser().parse_args(argv)

    # ── Optional Nayiri cross-validation ──────────────────────────────
    reference_headwords: Optional[set[str]] = None
    if args.nayiri:
        logger.info("Running Nayiri scraper (max_pages=%d)…", args.max_nayiri)
        try:
            reference_headwords = scrape_nayiri_headwords(
                max_pages=args.max_nayiri
            )
        except Exception as exc:
            logger.error("Nayiri scraper failed: %s — continuing without it.", exc)

    # ── Pull and validate Anki data ────────────────────────────────────
    try:
        results = pull_and_validate(
            deck=args.deck,
            reference_headwords=reference_headwords,
            threshold=args.threshold,
            verbose=args.verbose,
        )
    except AnkiConnectError as exc:
        logger.error("AnkiConnect error: %s", exc)
        return 1

    # ── Print summary ──────────────────────────────────────────────────
    print("\n" + "═" * 60)
    print("  Anki Western Armenian Validation Report")
    print("═" * 60)
    print(f"  Deck:              {results['deck']}")
    print(f"  Total notes:       {results['total']}")
    print(f"  Western Armenian:  {results['accepted']}  "
          f"({results['acceptance_rate']}%)")
    print(f"  Rejected:          {results['rejected']}")
    if reference_headwords is not None:
        print(f"  Nayiri headwords:  {len(reference_headwords)}")
    print("═" * 60 + "\n")

    if results["rejected"] and args.verbose:
        print("Rejected notes:")
        for note in results["rejected_notes"]:
            fields = {k: v.get("value", "") if isinstance(v, dict) else v
                      for k, v in note.get("fields", {}).items()}
            word = (fields.get("Word") or fields.get("Front")
                    or fields.get("Infinitive") or "(unknown)")
            print(f"  {word:<30}  score={note.get('_wa_score', '?')}")

    # ── Optional JSON output ───────────────────────────────────────────
    if args.output:
        out_path = Path(args.output)
        # Strip the note lists for the JSON summary to keep the file lightweight.
        summary = {k: v for k, v in results.items()
                   if k not in ("accepted_notes", "rejected_notes")}
        summary["rejected_words"] = [
            _note_word(n) for n in results["rejected_notes"]
        ]
        out_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        logger.info("Results written to %s", out_path)

    return 0


def _note_word(note: dict) -> str:
    """Extract the primary word field from a note dict."""
    fields = {k: v.get("value", "") if isinstance(v, dict) else v
              for k, v in note.get("fields", {}).items()}
    return (fields.get("Word") or fields.get("Front")
            or fields.get("Infinitive") or "(unknown)")


if __name__ == "__main__":
    sys.exit(main())
