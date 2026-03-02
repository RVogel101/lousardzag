"""
OCR-to-vocabulary bridge for the Armenian Anki pipeline.

Converts raw OCR text (from CWAS flash-card images or other sources)
into :class:`~armenian_anki.progression.WordEntry` objects ready for use
in the :class:`~armenian_anki.progression.ProgressionPlan` engine.

Western Armenian authenticity scoring
======================================
Each block of OCR text is scored on a 0.0–1.0 scale based on
orthographic and grammatical markers specific to Western Armenian.
Blocks scoring below :data:`WESTERN_ARMENIAN_THRESHOLD` are rejected so
that Eastern Armenian or non-Armenian text is not fed into the pipeline.

Scoring heuristics
------------------
+0.40  base: text contains Armenian Unicode characters
+0.25  WA preverbal particle ``կը`` (gə) found — exclusive to
        Western Armenian present-tense constructions
-0.35  EA progressive auxiliary ``գոր`` (gor) found — used only in
        Eastern Armenian; never appears in Western Armenian

The result is clamped to [0.0, 1.0].  For single-word input the base
score of 0.40 is returned unless EA markers are present.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from .morphology.core import ARM, count_syllables, is_armenian
from .progression import WordEntry

logger = logging.getLogger(__name__)

# ─── Thresholds ───────────────────────────────────────────────────────

WESTERN_ARMENIAN_THRESHOLD: float = 0.35
"""Minimum score to accept a text block as Western Armenian."""

# ─── Orthographic markers ─────────────────────────────────────────────

# WA present-tense preverbal particle "կը" (gə)
# ARM["g"] = chr(0x056F) = կ  (WA: g sound)
# ARM["y_schwa"] = chr(0x0568) = ը
_PREVERB_PARTICLE: str = ARM["g"] + ARM["y_schwa"]

# EA progressive auxiliary "գոր" (gor) — exclusive to Eastern Armenian
# ARM["k"] = chr(0x0563) = գ  (WA pronunciation: k; EA pronunciation: g)
# ARM["vo"] = chr(0x0578) = ո
# ARM["r"] = chr(0x0580) = ր
_EA_PROGRESSIVE: str = ARM["k"] + ARM["vo"] + ARM["r"]

# Contiguous runs of Armenian Unicode letters (one word at a time)
_ARM_WORD_RE = re.compile(r"[\u0531-\u0556\u0561-\u0586]+")


# ─── Public result type ───────────────────────────────────────────────

@dataclass
class OcrVocabResult:
    """Result returned by :func:`ocr_text_to_word_entries`."""

    word_entries: list[WordEntry]
    """Vocabulary words extracted and wrapped as WordEntry objects."""

    wa_score: float
    """Western Armenian authenticity score for the source text (0.0–1.0)."""

    raw_words: list[str]
    """All Armenian word tokens found before length/syllable filtering."""

    filtered_count: int
    """Number of tokens rejected during post-processing (e.g. too short)."""


# ─── Public functions ─────────────────────────────────────────────────

def score_western_armenian(text: str) -> float:
    """Return a confidence score (0.0–1.0) that *text* is Western Armenian.

    Args:
        text: Raw text to analyse (may be a single word or a full sentence).

    Returns:
        Float in [0.0, 1.0].  Values below :data:`WESTERN_ARMENIAN_THRESHOLD`
        indicate the text is likely not Western Armenian.
    """
    if not text:
        return 0.0
    if not any(is_armenian(c) for c in text):
        return 0.0

    score = 0.40  # base: has Armenian characters

    # Western Armenian exclusive marker (additive)
    if _PREVERB_PARTICLE in text:
        score += 0.25

    # Eastern Armenian exclusive marker (subtractive)
    if _EA_PROGRESSIVE in text:
        score -= 0.35

    return max(0.0, min(1.0, score))


def extract_armenian_words(text: str) -> list[str]:
    """Extract deduplicated Armenian word tokens from *text*.

    Applies the standard OCR correction for the ouv → ov misread before
    tokenising, then returns unique tokens in first-occurrence order.

    Args:
        text: Raw text from OCR or another source.

    Returns:
        List of Armenian-script tokens (punctuation and Latin stripped).
    """
    text = _correct_ocr(text)
    tokens = _ARM_WORD_RE.findall(text)
    seen: set[str] = set()
    unique: list[str] = []
    for tok in tokens:
        if tok not in seen:
            seen.add(tok)
            unique.append(tok)
    return unique


def ocr_text_to_word_entries(
    text: str,
    pos: str = "noun",
    base_frequency_rank: int = 1,
    threshold: float = WESTERN_ARMENIAN_THRESHOLD,
    min_syllables: int = 1,
    translation_map: dict[str, str] | None = None,
) -> OcrVocabResult:
    """Convert a block of OCR text into :class:`WordEntry` objects.

    The full text block is scored for Western Armenian authenticity first.
    If the score is below *threshold*, an empty result is returned so that
    Eastern Armenian or irrelevant text is never fed into the progression
    pipeline.

    Args:
        text:                Raw OCR output (may contain noise/Latin chars).
        pos:                 Default part-of-speech to assign to each entry.
        base_frequency_rank: Starting frequency rank; incremented per word.
        threshold:           Minimum WA score required to accept the block.
        min_syllables:       Words with fewer syllables than this are skipped.
        translation_map:     Optional mapping of Armenian word → English
                             translation used to populate
                             :attr:`WordEntry.translation`.

    Returns:
        :class:`OcrVocabResult` with extracted entries and diagnostic info.
    """
    wa_score = score_western_armenian(text)
    raw_words = extract_armenian_words(text)
    translation_map = translation_map or {}

    if wa_score < threshold:
        logger.debug(
            "Rejected OCR block: wa_score=%.2f < threshold=%.2f — %.60r",
            wa_score, threshold, text,
        )
        return OcrVocabResult(
            word_entries=[],
            wa_score=wa_score,
            raw_words=raw_words,
            filtered_count=len(raw_words),
        )

    entries: list[WordEntry] = []
    filtered = 0

    for rank_offset, word in enumerate(raw_words):
        if count_syllables(word) < min_syllables:
            filtered += 1
            continue

        entries.append(WordEntry(
            word=word,
            translation=translation_map.get(word, ""),
            pos=pos,
            frequency_rank=base_frequency_rank + rank_offset,
        ))

    logger.debug(
        "OCR bridge: wa_score=%.2f, %d entries, %d filtered from %d tokens",
        wa_score, len(entries), filtered, len(raw_words),
    )
    return OcrVocabResult(
        word_entries=entries,
        wa_score=wa_score,
        raw_words=raw_words,
        filtered_count=filtered,
    )


# ─── Internal helpers ─────────────────────────────────────────────────

def _correct_ocr(text: str) -> str:
    """Apply known Tesseract OCR misread corrections for Armenian text.

    Corrects the documented mis-segmentation of ov (ո + վ, U+0578 U+057E)
    into ouv (ո + ւ + վ, U+0578 U+0582 U+057E) caused by the ու digraph
    recogniser misfiring on the letter վ.
    """
    # ouv → ov  (U+0578 U+0582 U+057E → U+0578 U+057E)
    return text.replace("\u0578\u0582\u057E", "\u0578\u057E")
