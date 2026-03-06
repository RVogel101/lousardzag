#!/usr/bin/env python3
"""Classify text as likely Western or Eastern Armenian using internal project rules.

Rules are sourced from internal documentation and code only.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

# Ensure local package import works when run as script.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "02-src"))

from lousardzag.dialect_classifier import classify_vocab_and_sentences


def _load_lines(file_path: str) -> list[str]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    return [line for line in lines if line]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Classify vocab/sentences as likely Western or Eastern Armenian.",
    )
    parser.add_argument(
        "--vocab",
        action="append",
        default=[],
        help="Vocabulary item (can be provided multiple times).",
    )
    parser.add_argument(
        "--sentence",
        action="append",
        default=[],
        help="Sentence/phrase item (can be provided multiple times).",
    )
    parser.add_argument(
        "--vocab-file",
        help="UTF-8 text file with one vocab item per line.",
    )
    parser.add_argument(
        "--sentence-file",
        help="UTF-8 text file with one sentence/phrase per line.",
    )
    parser.add_argument(
        "--output",
        help="Output JSON file path. If omitted, prints JSON to stdout.",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    vocab = list(args.vocab)
    sentences = list(args.sentence)

    if args.vocab_file:
        vocab.extend(_load_lines(args.vocab_file))
    if args.sentence_file:
        sentences.extend(_load_lines(args.sentence_file))

    result = classify_vocab_and_sentences(vocab=vocab, sentences=sentences)

    serialized = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(serialized, encoding="utf-8")
        print(f"Wrote classification results to: {args.output}")
    else:
        print(serialized)


if __name__ == "__main__":
    main()
