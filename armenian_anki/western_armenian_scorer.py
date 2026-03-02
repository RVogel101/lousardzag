"""
Western Armenian text scorer and filter.

Scores Armenian text for the likelihood it is Western Armenian (WA),
as opposed to Eastern Armenian (EA) or Classical Armenian (Grabar/Krapar).

The algorithm detects morphological and orthographic markers that are
distinctive to each dialect/register and combines them into a normalised
score in [0.0, 1.0]:

    score > WA_THRESHOLD  →  likely Western Armenian
    score ≤ WA_THRESHOLD  →  likely Eastern Armenian, Grabar,
                              or insufficient evidence

Western Armenian–specific features exploited
─────────────────────────────────────────────
• Verbal particle ``կ`` (ken, /g/ in WA) used as a pre-verbal clitic,
  optionally followed by the schwa ``ը`` or an apostrophe before a
  vowel-initial stem:  կ'ուտ…  /  կ+ը +(verb)
• Old orthography ``աւ`` digraph (a + yiwn = /aw/) representing the /o/
  sound in verb endings: imperfect 3 sg -եաւ, aorist 3 sg -աւ.
• Old genitive article ``ոյ`` (-oy) in noun forms.
• Verb ending ``-ցաւ`` (3 sg past aorist) unique to WA.

Eastern Armenian–specific features (reduce WA score)
─────────────────────────────────────────────────────
• Present-tense verbal noun / progressive suffix ``-UM`` (ո+ւ+մ).
  This suffix is extremely common in EA and essentially absent in WA.
• Inchoative verbal suffix ``-aNUM`` (անում) dominant in EA.

Grabar (Classical Armenian) indicators (reduce WA score)
─────────────────────────────────────────────────────────
• Classical genitive suffix ``-ոյ`` used *before* other cases (Grabar
  uses it in nominal compounds differently from WA).  Given overlap with
  WA genitive we treat this pattern conservatively.
• Classical verbal suffix ``-եSan`` (3 pl past) in texts containing
  Classical vocabulary markers.

Note on character encoding
──────────────────────────
All patterns are built from the ``ARM`` mapping in
``armenian_anki.morphology.core`` so that the correct Unicode code
points are always used regardless of keyboard layout or copy-paste
artefacts.
"""

from __future__ import annotations

import re
from typing import NamedTuple

from .morphology.core import ARM

# ── Decision threshold ─────────────────────────────────────────────────────────
WA_THRESHOLD: float = 0.5


# ── Regex for counting Armenian letters ───────────────────────────────────────
_ARMENIAN_RE = re.compile(r"[\u0531-\u0556\u0561-\u0586]")

# Minimum number of Armenian characters required before emitting a score;
# texts shorter than this are treated as having insufficient evidence.
MIN_ARMENIAN_CHARS: int = 5


# ── Build pattern helper ───────────────────────────────────────────────────────

def _c(*keys: str) -> str:
    """Return the concatenated ARM characters for the given key sequence."""
    return "".join(ARM[k] for k in keys)


# ── Pattern tables ─────────────────────────────────────────────────────────────
# Each entry: (regex_pattern, weight, human_description)
# Positive weight  →  evidence for WA
# Negative weight  →  evidence against WA (EA or Grabar)

# ── WA-positive patterns ───────────────────────────────────────────────────────
_WA_PATTERNS: list[tuple[str, float, str]] = [
    # Verb particle: կ' (apostrophe elision before vowel-initial stem).
    # The apostrophe can be ASCII U+0027, typographic U+2019, or modifier
    # letter apostrophe U+02BC — match all three.
    (
        _c("g") + r"['\u2019\u02bc]",
        5.0,
        "WA verb particle կ' (elision before vowel-initial stem)",
    ),
    # Verb particle: կ+ը (with schwa, as generated in this codebase)
    (
        _c("g", "y_schwa"),
        4.0,
        "WA verb particle կ+ը (preverbal clitic with schwa)",
    ),
    # Old orthography aw-digraph աւ — WA /o/ in verb and word endings.
    # This digraph (a + yiwn) is largely absent from standard EA text.
    (
        _c("a", "yiwn"),
        4.0,
        "WA old orthography aw-digraph աւ (represents /o/)",
    ),
    # Imperfect 3 sg ending: -եաւ  (ye + a + yiwn)
    (
        _c("ye", "a", "yiwn"),
        5.0,
        "WA imperfect 3sg verb ending -եaW",
    ),
    # Past-aorist 3 sg ending: -ցaW  (ts_asp + a + yiwn)
    # e.g.  գnac-աw  (gə-nats-aw = he/she went)
    (
        _c("c_asp", "a", "yiwn"),
        5.0,
        "WA past-aorist 3sg ending -ցaW",
    ),
    # Old genitive article -oy: ոյ  (vo + y)
    # WA preserves this Classical genitive ending in many fossilised forms.
    (
        _c("vo", "y"),
        3.0,
        "WA/old genitive ending -oy (ոյ)",
    ),
]

# ── EA-negative patterns ───────────────────────────────────────────────────────
_EA_PATTERNS: list[tuple[str, float, str]] = [
    # EA present participle suffix -UM (ո+ւ+մ).
    # This is the most reliable single-marker distinguishing EA from WA.
    (
        _c("vo", "yiwn", "m"),
        -5.0,
        "EA present participle suffix -UM (ում)",
    ),
    # EA inchoative -anum (ա+ն+ո+ւ+մ): not present in WA.
    (
        _c("a", "n", "vo", "yiwn", "m"),
        -4.0,
        "EA inchoative verb suffix -anum (անUM)",
    ),
    # EA 3sg present marker -um e + present form (iterative pattern check)
    # e.g., «կ-ա-nt-UM» (reads/reads)
    (
        _c("a", "vo", "yiwn", "m"),
        -3.0,
        "EA verb form -a-UM (present stem)",
    ),
]

# ── Grabar-negative patterns ───────────────────────────────────────────────────
_GRABAR_PATTERNS: list[tuple[str, float, str]] = [
    # Classical 3 pl past: -եՍan / -eSan — unique to Grabar in medial stem forms.
    # Pattern: ye + s + a + n  (visible in Classical verb endings like -եsAN)
    (
        _c("ye", "s", "a", "n"),
        -3.0,
        "Grabar 3pl past ending -eSaN",
    ),
    # Classical suffix -ութiWN: noun suffix found in both WA and Grabar but
    # *combined* with other Classical endings indicates Grabar register.
    # We only penalise when it appears right before a Classical case suffix.
    # Grabar genitive: -ութiWN + -oy: -ութean (yiwn + yo)
    (
        _c("t_asp", "yiwn", "n") + _c("vo", "y"),
        -2.0,
        "Grabar nominal -t'iwn + genitive-oy compound",
    ),
]

_ALL_PATTERN_LISTS = (_WA_PATTERNS, _EA_PATTERNS, _GRABAR_PATTERNS)


# ── Result type ────────────────────────────────────────────────────────────────

class ScoreResult(NamedTuple):
    """Result of scoring a piece of Armenian text.

    Attributes:
        score:               Normalised WA likelihood in [0.0, 1.0].
        is_western_armenian: True when score > threshold and enough text.
        total_armenian_chars: Number of Armenian characters found in text.
        matched_patterns:    List of (description, contribution) pairs for
                             every pattern that fired.
        raw_score:           Unnormalised weighted sum before clamping.
    """
    score: float
    is_western_armenian: bool
    total_armenian_chars: int
    matched_patterns: list[tuple[str, float]]
    raw_score: float


# ── Core scoring function ──────────────────────────────────────────────────────

def score_text(
    text: str,
    threshold: float = WA_THRESHOLD,
    min_chars: int = MIN_ARMENIAN_CHARS,
) -> ScoreResult:
    """Score *text* for Western Armenian content.

    Args:
        text:      The Armenian (or mixed) text to analyse.
        threshold: Decision boundary; ``score > threshold`` is considered WA.
        min_chars: Minimum Armenian character count to emit a non-zero score.
                   Texts with fewer Armenian characters are returned with
                   ``score=0.0`` and ``is_western_armenian=False``.

    Returns:
        A :class:`ScoreResult` named tuple.
    """
    if not text:
        return ScoreResult(0.0, False, 0, [], 0.0)

    arm_chars = len(_ARMENIAN_RE.findall(text))
    if arm_chars < min_chars:
        return ScoreResult(0.0, False, arm_chars, [], 0.0)

    raw = 0.0
    matched: list[tuple[str, float]] = []

    for pattern_list in _ALL_PATTERN_LISTS:
        for pat, weight, desc in pattern_list:
            hits = re.findall(pat, text)
            if hits:
                contribution = weight * len(hits)
                raw += contribution
                matched.append((desc, contribution))

    # Normalise raw score to [0.0, 1.0] using a linear clamp over [-20, +20].
    # This range comfortably covers typical sentence-length texts.
    clamped = max(-20.0, min(20.0, raw))
    normalised = round((clamped + 20.0) / 40.0, 4)

    is_wa = normalised > threshold
    return ScoreResult(normalised, is_wa, arm_chars, matched, raw)


# ── Convenience wrapper ────────────────────────────────────────────────────────

def is_western_armenian(text: str, threshold: float = WA_THRESHOLD) -> bool:
    """Return ``True`` if *text* is likely Western Armenian.

    Shorthand for ``score_text(text, threshold).is_western_armenian``.
    """
    return score_text(text, threshold).is_western_armenian


# ── Batch helper ───────────────────────────────────────────────────────────────

def filter_western_armenian(
    texts: list[str],
    threshold: float = WA_THRESHOLD,
    min_chars: int = MIN_ARMENIAN_CHARS,
) -> list[tuple[int, str, ScoreResult]]:
    """Filter a list of texts, returning only those likely to be WA.

    Args:
        texts:     List of strings to evaluate.
        threshold: WA decision boundary.
        min_chars: Minimum Armenian chars required to make a determination.

    Returns:
        List of ``(original_index, text, score_result)`` for texts that
        pass the WA filter.
    """
    results = []
    for idx, text in enumerate(texts):
        result = score_text(text, threshold, min_chars)
        if result.is_western_armenian:
            results.append((idx, text, result))
    return results
