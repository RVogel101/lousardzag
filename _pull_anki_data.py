#!/usr/bin/env python3
"""
Pull Anki deck data — including audio and image media — via AnkiConnect.

Optionally scores each note for Western Armenian dialect content using the
built-in dialect scorer and filters out Eastern Armenian notes.

Prerequisites
-------------
  1. Anki desktop running with AnkiConnect plugin (code: 2055492159).
  2. The deck to pull from must exist in Anki.

Usage
-----
  # Pull all notes and save to JSON:
  python _pull_anki_data.py

  # Pull from a specific deck:
  python _pull_anki_data.py --deck "Armenian Vocabulary"

  # Pull, score for dialect, keep only Western Armenian notes:
  python _pull_anki_data.py --filter-western

  # Include ambiguous-dialect notes when filtering:
  python _pull_anki_data.py --filter-western --include-ambiguous

  # Save media (audio + images) to a directory:
  python _pull_anki_data.py --media-dir ./pulled_media

  # Export as CSV instead of JSON:
  python _pull_anki_data.py --format csv --output pulled_notes.csv

  # Dry-run: print a summary without writing any files:
  python _pull_anki_data.py --dry-run
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Optional

# Allow running from the repo root without installing the package.
sys.path.insert(0, str(Path(__file__).parent))

from armenian_anki.anki_connect import AnkiConnect, AnkiConnectError
from armenian_anki.config import SOURCE_DECK
from armenian_anki.dialect_scorer import DialectScore, score_text

logger = logging.getLogger(__name__)

# ─── Media parsing helpers ───────────────────────────────────────────────────

# Matches Anki audio tags, e.g. [sound:pronunciation.mp3]
_AUDIO_PATTERN = re.compile(r"\[sound:([^\]]+)\]")

# Matches HTML image tags, e.g. <img src="image.jpg"> or <img src='image.png'>
_IMAGE_PATTERN = re.compile(r'<img\s[^>]*src=["\']([^"\']+)["\'][^>]*>', re.IGNORECASE)


def extract_audio_filenames(field_value: str) -> list[str]:
    """Return all audio filenames referenced in an Anki field value."""
    return _AUDIO_PATTERN.findall(field_value)


def extract_image_filenames(field_value: str) -> list[str]:
    """Return all image filenames referenced in an Anki field value."""
    return _IMAGE_PATTERN.findall(field_value)


def extract_media_from_note(note: dict) -> dict[str, list[str]]:
    """Collect all audio and image filenames referenced in a note's fields.

    Args:
        note: A note dict as returned by AnkiConnect ``notesInfo``.

    Returns:
        Dict with keys ``"audio"`` and ``"images"``, each a list of filenames.
    """
    audio: list[str] = []
    images: list[str] = []
    for field_name, field_data in note.get("fields", {}).items():
        value = field_data.get("value", "") if isinstance(field_data, dict) else str(field_data)
        audio.extend(extract_audio_filenames(value))
        images.extend(extract_image_filenames(value))
    return {"audio": list(dict.fromkeys(audio)), "images": list(dict.fromkeys(images))}


# ─── Note scoring ────────────────────────────────────────────────────────────

def _note_text(note: dict) -> str:
    """Concatenate all field values of a note into a single string for scoring."""
    parts: list[str] = []
    for field_data in note.get("fields", {}).values():
        value = field_data.get("value", "") if isinstance(field_data, dict) else str(field_data)
        # Strip HTML tags for cleaner scoring
        plain = re.sub(r"<[^>]+>", " ", value)
        # Remove Anki media tags
        plain = _AUDIO_PATTERN.sub(" ", plain)
        parts.append(plain)
    return " ".join(parts)


def score_note(note: dict) -> DialectScore:
    """Return a :class:`~armenian_anki.dialect_scorer.DialectScore` for a note."""
    return score_text(_note_text(note))


# ─── Media download ──────────────────────────────────────────────────────────

def download_media(
    anki: AnkiConnect,
    filenames: list[str],
    dest_dir: Path,
) -> dict[str, Optional[Path]]:
    """Download media files from Anki and save them to *dest_dir*.

    Args:
        anki:      Initialised :class:`~armenian_anki.anki_connect.AnkiConnect` client.
        filenames: List of filenames to retrieve from Anki's media folder.
        dest_dir:  Directory to write the files into (created if absent).

    Returns:
        Mapping of ``filename → saved_path`` (``None`` if download failed).
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    saved: dict[str, Optional[Path]] = {}
    for filename in filenames:
        data = anki.retrieve_media_file(filename)
        if data is None:
            logger.warning("Media file not found in Anki: %s", filename)
            saved[filename] = None
            continue
        dest = dest_dir / filename
        dest.write_bytes(data)
        logger.debug("Saved media file: %s (%d bytes)", dest, len(data))
        saved[filename] = dest
    return saved


# ─── Core pull logic ─────────────────────────────────────────────────────────

def pull_deck(
    deck: str,
    anki: AnkiConnect,
    filter_western: bool = False,
    include_ambiguous: bool = False,
    media_dir: Optional[Path] = None,
) -> list[dict]:
    """Pull notes from an Anki deck and optionally filter by dialect.

    Args:
        deck:             Name of the Anki deck to pull from.
        anki:             Initialised AnkiConnect client.
        filter_western:   If True, discard notes that score as Eastern Armenian.
        include_ambiguous:If True, keep ambiguous-dialect notes when filtering.
        media_dir:        If provided, download audio and image media to this dir.

    Returns:
        List of enriched note dicts, each containing:
          - all original AnkiConnect ``notesInfo`` fields
          - ``"media"``:  {``"audio"``: [...], ``"images"``: [...]}
          - ``"dialect"``: {``"label"``, ``"score"``, ``"matched_markers"``}
    """
    logger.info("Fetching note IDs from deck '%s'…", deck)
    note_ids = anki.find_notes(f'"deck:{deck}"')
    if not note_ids:
        logger.warning("No notes found in deck '%s'", deck)
        return []

    logger.info("Fetching info for %d notes…", len(note_ids))
    raw_notes = anki.notes_info(note_ids)

    results: list[dict] = []
    skipped_ea = 0
    all_audio: list[str] = []
    all_images: list[str] = []

    for note in raw_notes:
        media = extract_media_from_note(note)
        dialect_score = score_note(note)

        # Dialect filtering
        if filter_western:
            if dialect_score.is_eastern:
                skipped_ea += 1
                logger.debug(
                    "Skipping Eastern Armenian note (id=%s, score=%.3f)",
                    note.get("noteId"),
                    dialect_score.normalised_score,
                )
                continue
            if not include_ambiguous and dialect_score.is_ambiguous:
                continue

        all_audio.extend(media["audio"])
        all_images.extend(media["images"])

        enriched = dict(note)
        enriched["media"] = media
        enriched["dialect"] = {
            "label": dialect_score.label,
            "score": round(dialect_score.normalised_score, 4),
            "matched_markers": [pat for pat, _ in dialect_score.matched_markers],
        }
        results.append(enriched)

    if filter_western:
        logger.info(
            "Dialect filter: kept %d notes, skipped %d Eastern Armenian notes",
            len(results),
            skipped_ea,
        )

    # Download media if requested
    if media_dir is not None:
        unique_audio = list(dict.fromkeys(all_audio))
        unique_images = list(dict.fromkeys(all_images))
        all_media = unique_audio + unique_images
        if all_media:
            logger.info(
                "Downloading %d media files (%d audio, %d images) to '%s'…",
                len(all_media),
                len(unique_audio),
                len(unique_images),
                media_dir,
            )
            download_media(anki, all_media, media_dir)
        else:
            logger.info("No media files referenced in the pulled notes.")

    return results


# ─── Export helpers ──────────────────────────────────────────────────────────

def _flatten_note(note: dict) -> dict:
    """Flatten a note dict into a one-level dict suitable for CSV export."""
    flat: dict = {
        "note_id": note.get("noteId", ""),
        "model_name": note.get("modelName", ""),
        "tags": " ".join(note.get("tags", [])),
        "dialect_label": note.get("dialect", {}).get("label", ""),
        "dialect_score": note.get("dialect", {}).get("score", ""),
        "media_audio": "|".join(note.get("media", {}).get("audio", [])),
        "media_images": "|".join(note.get("media", {}).get("images", [])),
    }
    for field_name, field_data in note.get("fields", {}).items():
        value = field_data.get("value", "") if isinstance(field_data, dict) else str(field_data)
        flat[f"field_{field_name}"] = value
    return flat


def save_json(notes: list[dict], output_path: Path) -> None:
    """Write notes to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(notes, fh, ensure_ascii=False, indent=2)
    logger.info("Saved %d notes to '%s'", len(notes), output_path)


def save_csv(notes: list[dict], output_path: Path) -> None:
    """Write notes to a CSV file."""
    if not notes:
        logger.warning("No notes to write.")
        return
    flat_notes = [_flatten_note(n) for n in notes]
    fieldnames = list(flat_notes[0].keys())
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flat_notes)
    logger.info("Saved %d notes to '%s'", len(notes), output_path)


# ─── CLI ─────────────────────────────────────────────────────────────────────

def _setup_logging(verbose: bool = False) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )


def _print_summary(notes: list[dict]) -> None:
    """Print a summary of pulled notes to stdout."""
    print(f"\n{'=' * 60}")
    print(f"  Pull summary: {len(notes)} notes")
    print(f"{'=' * 60}")
    labels = {"western": 0, "eastern": 0, "ambiguous": 0}
    audio_total = 0
    image_total = 0
    for note in notes:
        label = note.get("dialect", {}).get("label", "ambiguous")
        labels[label] = labels.get(label, 0) + 1
        audio_total += len(note.get("media", {}).get("audio", []))
        image_total += len(note.get("media", {}).get("images", []))
    print(f"  Western Armenian:  {labels['western']}")
    print(f"  Eastern Armenian:  {labels['eastern']}")
    print(f"  Ambiguous dialect: {labels['ambiguous']}")
    print(f"  Audio files:       {audio_total}")
    print(f"  Image files:       {image_total}")
    print(f"{'=' * 60}\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Pull Anki deck data (including media) via AnkiConnect",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--deck", default=SOURCE_DECK,
        help=f"Deck to pull from (default: {SOURCE_DECK!r})",
    )
    parser.add_argument(
        "--filter-western", action="store_true",
        help="Keep only notes that score as Western Armenian",
    )
    parser.add_argument(
        "--include-ambiguous", action="store_true",
        help="With --filter-western: also keep ambiguous-dialect notes",
    )
    parser.add_argument(
        "--media-dir", type=Path, default=None, metavar="DIR",
        help="Download referenced audio/image files to this directory",
    )
    parser.add_argument(
        "--format", choices=["json", "csv"], default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--output", "-o", type=Path, default=None, metavar="FILE",
        help="Output file path (default: pulled_notes.json or pulled_notes.csv)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print a summary without writing any files",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args(argv)
    _setup_logging(args.verbose)

    try:
        anki = AnkiConnect()
        if not anki.ping():
            print(
                "✗ Cannot connect to AnkiConnect.  "
                "Is Anki running with the AnkiConnect plugin installed?\n"
                "  Install AnkiConnect: Tools → Add-ons → Get Add-ons → Code: 2055492159",
                file=sys.stderr,
            )
            return 1

        notes = pull_deck(
            deck=args.deck,
            anki=anki,
            filter_western=args.filter_western,
            include_ambiguous=args.include_ambiguous,
            media_dir=args.media_dir,
        )

        _print_summary(notes)

        if args.dry_run:
            print("[dry-run] No files written.")
            return 0

        output = args.output or Path(f"pulled_notes.{args.format}")
        if args.format == "csv":
            save_csv(notes, output)
        else:
            save_json(notes, output)

        return 0

    except AnkiConnectError as exc:
        print(f"✗ AnkiConnect error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
