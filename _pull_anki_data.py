#!/usr/bin/env python3
"""
Pull Anki note data and filter for Western Armenian content.

Connects to AnkiConnect, reads notes from a source deck, scores each
note's Armenian text fields using the Western Armenian scoring algorithm,
and exports the filtered and tagged results to JSON / CSV.

The Western Armenian filter ensures that only WA content is retained,
preventing Eastern Armenian (EA) or Classical Armenian (Grabar/Krapar)
data from contaminating the Anki generation pipeline.

Usage examples
──────────────
Pull all notes from the default source deck:
    python _pull_anki_data.py

Pull from a specific deck with a lower WA threshold:
    python _pull_anki_data.py --deck "My Armenian Deck" --threshold 0.4

Process a previously exported JSON file (no Anki connection needed):
    python _pull_anki_data.py --input notes.json

Save results to a custom path:
    python _pull_anki_data.py --output filtered_notes.json

Dry-run: print statistics without writing any files:
    python _pull_anki_data.py --dry-run

Verbose mode:
    python _pull_anki_data.py -v
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from pathlib import Path
from typing import Any

from armenian_anki.anki_connect import AnkiConnect, AnkiConnectError
from armenian_anki.config import SOURCE_DECK, SOURCE_FIELDS
from armenian_anki.western_armenian_scorer import (
    WA_THRESHOLD,
    MIN_ARMENIAN_CHARS,
    score_text,
    ScoreResult,
)

logger = logging.getLogger(__name__)

# ── Default output paths ───────────────────────────────────────────────────────
DEFAULT_OUTPUT_JSON = Path("pulled_anki_data.json")
DEFAULT_OUTPUT_CSV = Path("pulled_anki_data.csv")

# ── Fields to inspect for Armenian text during scoring ────────────────────────
# The scorer concatenates the values of these fields before analysis.
SCORE_FIELDS = ("word", "translation")


# ── Note processing ────────────────────────────────────────────────────────────

def _extract_fields(note: dict) -> dict[str, str]:
    """Return a flat {key: value} dict from an AnkiConnect note object."""
    raw_fields: dict[str, dict] = note.get("fields", {})
    return {k: v.get("value", "") for k, v in raw_fields.items()}


def process_notes(
    notes: list[dict],
    threshold: float = WA_THRESHOLD,
    min_chars: int = MIN_ARMENIAN_CHARS,
) -> tuple[list[dict], dict[str, int]]:
    """Score and filter a list of raw AnkiConnect note objects.

    Args:
        notes:     Raw note objects as returned by AnkiConnect.
        threshold: WA score threshold; notes below this are excluded.
        min_chars: Minimum Armenian character count for a note to be scored.

    Returns:
        A ``(filtered_notes, stats)`` tuple where *filtered_notes* is the
        list of notes that passed the WA filter (each enriched with a
        ``wa_score`` and ``wa_matched`` key), and *stats* is a summary dict.
    """
    stats: dict[str, int] = {
        "total": len(notes),
        "passed_wa_filter": 0,
        "rejected_not_wa": 0,
        "rejected_insufficient_text": 0,
    }

    filtered: list[dict] = []

    for note in notes:
        fields = _extract_fields(note)

        # Build the text block to score: combine all field values.
        text_parts = [v for v in fields.values() if v]
        combined_text = " ".join(text_parts)

        result = score_text(combined_text, threshold, min_chars)

        if result.total_armenian_chars < min_chars:
            logger.debug(
                "Note %s skipped: only %d Armenian chars",
                note.get("noteId", "?"),
                result.total_armenian_chars,
            )
            stats["rejected_insufficient_text"] += 1
            continue

        if not result.is_western_armenian:
            logger.debug(
                "Note %s rejected (score=%.3f): %s",
                note.get("noteId", "?"),
                result.score,
                combined_text[:60],
            )
            stats["rejected_not_wa"] += 1
            continue

        # Enrich the note with scoring metadata before keeping it.
        enriched = dict(note)
        enriched["wa_score"] = result.score
        enriched["wa_raw_score"] = result.raw_score
        enriched["wa_matched"] = [
            {"pattern": desc, "contribution": contrib}
            for desc, contrib in result.matched_patterns
        ]
        filtered.append(enriched)
        stats["passed_wa_filter"] += 1

        logger.debug(
            "Note %s accepted (score=%.3f): %s",
            note.get("noteId", "?"),
            result.score,
            combined_text[:60],
        )

    return filtered, stats


# ── Anki data pull ─────────────────────────────────────────────────────────────

def pull_from_anki(deck: str) -> list[dict]:
    """Connect to AnkiConnect and pull all notes from *deck*.

    Returns a list of raw AnkiConnect note objects.

    Raises:
        AnkiConnectError: If Anki is not running or the deck cannot be found.
        SystemExit:       If AnkiConnect is not reachable.
    """
    anki = AnkiConnect()
    if not anki.ping():
        logger.error(
            "Cannot reach AnkiConnect.  Is Anki running with the "
            "AnkiConnect plugin installed?  "
            "(Tools → Add-ons → Get Add-ons → Code: 2055492159)"
        )
        sys.exit(1)

    logger.info("Pulling notes from deck: %s", deck)
    notes = anki.get_deck_notes(deck)
    logger.info("Pulled %d notes from '%s'", len(notes), deck)
    return notes


# ── I/O helpers ───────────────────────────────────────────────────────────────

def load_notes_from_file(path: Path) -> list[dict]:
    """Load notes from a previously exported JSON file."""
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, list):
        return data
    # Support {notes: [...]} wrapper format
    return data.get("notes", [])


def save_json(notes: list[dict], path: Path, stats: dict[str, int]) -> None:
    """Save filtered notes and stats to *path* as JSON."""
    output = {"stats": stats, "notes": notes}
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Saved %d notes to %s", len(notes), path)


def save_csv(notes: list[dict], path: Path) -> None:
    """Save filtered notes to *path* as CSV.

    Only the fields mapped via SOURCE_FIELDS plus the wa_score column are
    written; the full morphology blob and wa_matched list are omitted to
    keep the CSV human-readable.
    """
    if not notes:
        logger.warning("No notes to save to CSV")
        return

    # Determine CSV columns: SOURCE_FIELDS keys + wa_score
    csv_keys = list(SOURCE_FIELDS.keys()) + ["wa_score", "noteId"]

    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=csv_keys, extrasaction="ignore")
        writer.writeheader()
        for note in notes:
            raw_fields = _extract_fields(note)
            row: dict[str, Any] = {
                "noteId": note.get("noteId", ""),
                "wa_score": note.get("wa_score", ""),
            }
            # Map Anki field names → pipeline keys via SOURCE_FIELDS
            for pipeline_key, anki_field_name in SOURCE_FIELDS.items():
                row[pipeline_key] = raw_fields.get(anki_field_name, "")
            writer.writerow(row)

    logger.info("Saved CSV to %s", path)


# ── CLI ────────────────────────────────────────────────────────────────────────

def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )


def _print_stats(stats: dict[str, int], threshold: float) -> None:
    print("\n" + "=" * 60)
    print("  Pull Anki Data — Western Armenian Filter Summary")
    print("=" * 60)
    print(f"  WA score threshold:       {threshold:.2f}")
    print(f"  Total notes examined:     {stats['total']}")
    print(f"  Passed WA filter:         {stats['passed_wa_filter']}")
    print(f"  Rejected (not WA):        {stats['rejected_not_wa']}")
    print(f"  Rejected (no ARM text):   {stats['rejected_insufficient_text']}")
    pct = (
        100 * stats["passed_wa_filter"] / stats["total"]
        if stats["total"] > 0
        else 0.0
    )
    print(f"  Pass rate:                {pct:.1f}%")
    print("=" * 60)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Pull Anki notes and filter for Western Armenian content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--deck",
        default=SOURCE_DECK,
        help=f"Source Anki deck name (default: {SOURCE_DECK!r})",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=WA_THRESHOLD,
        help=f"WA score threshold, 0–1 (default: {WA_THRESHOLD})",
    )
    parser.add_argument(
        "--min-chars",
        type=int,
        default=MIN_ARMENIAN_CHARS,
        help=f"Minimum Armenian character count (default: {MIN_ARMENIAN_CHARS})",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Process a previously exported JSON file instead of pulling from Anki",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_JSON,
        help=f"Output JSON path (default: {DEFAULT_OUTPUT_JSON})",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_OUTPUT_CSV,
        help=f"Output CSV path (default: {DEFAULT_OUTPUT_CSV})",
    )
    parser.add_argument(
        "--no-csv",
        action="store_true",
        help="Skip CSV output",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print statistics without writing any output files",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args(argv)
    _setup_logging(args.verbose)

    # ── 1. Load notes ─────────────────────────────────────────────────
    if args.input:
        logger.info("Loading notes from file: %s", args.input)
        notes = load_notes_from_file(args.input)
    else:
        notes = pull_from_anki(args.deck)

    if not notes:
        print("No notes found.  Nothing to process.")
        sys.exit(0)

    # ── 2. Score and filter ───────────────────────────────────────────
    filtered, stats = process_notes(notes, args.threshold, args.min_chars)
    _print_stats(stats, args.threshold)

    if args.dry_run:
        print("\n[dry-run] No output files written.")
        return

    # ── 3. Save results ───────────────────────────────────────────────
    save_json(filtered, args.output, stats)

    if not args.no_csv:
        save_csv(filtered, args.csv)


if __name__ == "__main__":
    main()
