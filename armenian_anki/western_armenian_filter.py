"""
Western Armenian (Արեւմտահայ) validation and filtering utilities.

Provides functions to determine whether Armenian text or Anki note data
represents Western Armenian as opposed to Eastern Armenian or Classical
Armenian (Grabar).

Detection strategy (in order of reliability):
  1. Armenian script presence — text must contain at least one Armenian
     Unicode character (U+0531–U+0587).  Without this the note cannot be
     Armenian at all.
  2. Pronunciation / transliteration scoring — if a romanisation field is
     available it is tested against known Western Armenian consonant-shift
     patterns.  WA underwent a voicing shift relative to Eastern Armenian:
       բ = /p/ (EA: /b/),  պ = /b/ (EA: /p/)
       դ = /t/ (EA: /d/),  տ = /d/ (EA: /t/)
       գ = /k/ (EA: /g/),  կ = /g/ (EA: /k/)
  3. Grabar (Classical Armenian) detection — a set of archaic morphological
     markers is used to flag probable Classical text, which is not Western
     or Eastern colloquial Armenian.
  4. Optional cross-validation against a WA reference headword set —
     when a set of known WA vocabulary is supplied, coverage is used to
     boost or reduce the confidence score.

Returned scores are floats in [0.0, 1.0]:
  ≥ THRESHOLD_LIKELY_WA   → almost certainly Western Armenian
  < THRESHOLD_LIKELY_WA   → uncertain or likely not Western Armenian
"""

from __future__ import annotations

import re
import unicodedata
from typing import Collection, Optional

# ─── Unicode ranges ────────────────────────────────────────────────────────────
_ARM_UPPERCASE_START = 0x0531  # Ա
_ARM_UPPERCASE_END   = 0x0556  # Փ
_ARM_LOWERCASE_START = 0x0561  # ա
_ARM_LOWERCASE_END   = 0x0587  # ﬖ (includes ligature ﬕ)

# ─── Score thresholds ──────────────────────────────────────────────────────────
THRESHOLD_LIKELY_WA: float = 0.40


# ─── Grabar (Classical Armenian) markers ─────────────────────────────────────
# Verb endings and case suffixes that are characteristic of written Classical
# Armenian and rarely appear in modern colloquial Western Armenian.
_GRABAR_VERB_ENDINGS = (
    "եալ",   # past participle suffix -eal
    "ութիւն",  # abstract noun suffix -ut'iwn (archaic spelling with ւ)
    "ութեան",  # gen-dat of above
    "ացիք",  # 2pl aorist ending
    "ցաք",   # 1pl aorist ending (Grabar form)
)

_GRABAR_CASE_ENDINGS = (
    "ոյ",    # gen-dat -oy (Grabar)
    "ոք",    # locative particle
    "իւ",    # instrumental -iw (Grabar)
)

# Compile a single regex for Grabar markers to avoid repeated compilation.
_GRABAR_PATTERN = re.compile(
    "|".join(re.escape(m) for m in _GRABAR_VERB_ENDINGS + _GRABAR_CASE_ENDINGS)
)

# ─── Western Armenian pronunciation patterns ─────────────────────────────────
# These are romanisation sub-strings that are phonologically distinctive of
# Western Armenian.  Pronunciation fields are expected to use Roman letters.

# Patterns strongly associated with WA romanisation:
_WA_PRONUNC_PATTERNS: list[tuple[str, float]] = [
    # WA voiced stops represented as unaspirated voiceless in romanisation.
    # "kh", "gh", "dz" are WA retentions vs EA shifts.
    (r"\bkh",   0.15),   # WA /kh/ (խ)
    (r"\bgh",   0.15),   # WA /gh/ (ղ)
    (r"\bdz",   0.10),   # WA /dz/ vs EA /ts/
    # WA aspirated stops typically written with apostrophe or h-digraph:
    (r"p'",     0.10),
    (r"t'",     0.10),
    (r"k'",     0.10),
    (r"ch'",    0.10),
    (r"ts'",    0.05),
    # WA consonant clusters distinctive from EA:
    (r"\bmb",   0.05),   # WA onset cluster (e.g. "mbr")
    (r"\bnd",   0.05),   # WA onset cluster
]

# Patterns more typical of Eastern Armenian romanisation (penalise):
_EA_PRONUNC_PATTERNS: list[tuple[str, float]] = [
    (r"\bby",  -0.10),   # EA voiced bilabial clusters
    (r"\bgy",  -0.10),
    (r"\bdy",  -0.10),
    (r"ts\b",  -0.05),   # EA word-final /ts/
]

# Pre-compile all pronunciation patterns.
_WA_COMPILED = [(re.compile(p, re.IGNORECASE), w) for p, w in _WA_PRONUNC_PATTERNS]
_EA_COMPILED = [(re.compile(p, re.IGNORECASE), w) for p, w in _EA_PRONUNC_PATTERNS]


# ─── Public helpers ───────────────────────────────────────────────────────────

def is_armenian_script(text: str) -> bool:
    """Return True if *text* contains at least one Armenian Unicode character."""
    for ch in text:
        cp = ord(ch)
        if (_ARM_UPPERCASE_START <= cp <= _ARM_UPPERCASE_END
                or _ARM_LOWERCASE_START <= cp <= _ARM_LOWERCASE_END):
            return True
    return False


def has_grabar_markers(text: str) -> bool:
    """Return True if *text* contains Classical Armenian (Grabar) markers."""
    return bool(_GRABAR_PATTERN.search(text))


def armenian_script_ratio(text: str) -> float:
    """Return the fraction of characters in *text* that are Armenian script.

    Returns 0.0 if *text* is empty.
    """
    if not text:
        return 0.0
    arm_count = sum(
        1 for ch in text
        if (_ARM_UPPERCASE_START <= ord(ch) <= _ARM_UPPERCASE_END
            or _ARM_LOWERCASE_START <= ord(ch) <= _ARM_LOWERCASE_END)
    )
    return arm_count / len(text)


def score_pronunciation(pronunciation: str) -> float:
    """Score a romanised pronunciation string for WA consonant patterns.

    Returns a signed float.  Positive values suggest WA; negative suggest EA.
    Values are not calibrated probabilities — use them relative to each other.
    """
    if not pronunciation:
        return 0.0
    score = 0.0
    for pattern, weight in _WA_COMPILED:
        if pattern.search(pronunciation):
            score += weight
    for pattern, weight in _EA_COMPILED:
        if pattern.search(pronunciation):
            score += weight  # weight is already negative
    return score


def score_western_armenian(
    word: str,
    pronunciation: str = "",
    reference_headwords: Optional[Collection[str]] = None,
) -> float:
    """Return a WA confidence score in [0.0, 1.0] for a single vocabulary item.

    Args:
        word:               The Armenian-script word (required).
        pronunciation:      Optional Roman transliteration / pronunciation string.
        reference_headwords: Optional collection of known WA headwords for
                             cross-validation (e.g. from the Nayiri scraper).

    Returns:
        A float in [0.0, 1.0] where 1.0 is high confidence WA.
    """
    # ── Must contain Armenian script ──────────────────────────────────
    if not is_armenian_script(word):
        return 0.0

    score = 0.3  # baseline: Armenian script is present

    # ── Penalise Grabar markers ────────────────────────────────────────
    if has_grabar_markers(word):
        score -= 0.25

    # ── Pronunciation field scoring ────────────────────────────────────
    if pronunciation:
        pron_score = score_pronunciation(pronunciation)
        # Map pron_score (roughly −0.3 … +0.8) into a [−0.2, +0.4] adjustment
        score += max(-0.20, min(0.40, pron_score))

    # ── Armenian script ratio (how "pure" the word field is) ──────────
    ratio = armenian_script_ratio(word)
    if ratio >= 0.85:
        score += 0.15
    elif ratio >= 0.50:
        score += 0.05

    # ── Nayiri cross-validation ────────────────────────────────────────
    if reference_headwords:
        # Normalise for lookup (lowercase, strip non-Armenian punctuation)
        normalised = _normalise_armenian(word)
        if normalised in reference_headwords:
            score += 0.20

    return max(0.0, min(1.0, score))


def classify_note(
    note: dict,
    reference_headwords: Optional[Collection[str]] = None,
    threshold: float = THRESHOLD_LIKELY_WA,
) -> tuple[bool, float]:
    """Classify an Anki note dict as Western Armenian or not.

    Looks for the word in common field names (``Word``, ``Front``,
    ``Armenian``) and optionally a pronunciation field.

    Args:
        note:               An Anki note dict (as returned by
                            ``AnkiConnect.notes_info()``).  Expected to have
                            a ``fields`` sub-dict keyed by field name.
        reference_headwords: Optional set of known WA headwords.
        threshold:          Minimum score to consider the note WA.

    Returns:
        ``(is_western_armenian, confidence_score)``
    """
    fields: dict = {}
    if "fields" in note:
        # AnkiConnect format: {"fields": {"Word": {"value": "..."}, ...}}
        fields = {k: v.get("value", "") if isinstance(v, dict) else v
                  for k, v in note["fields"].items()}
    else:
        fields = note  # plain dict fallback

    word = (
        fields.get("Word")
        or fields.get("Front")
        or fields.get("Armenian")
        or fields.get("Infinitive")
        or ""
    )
    pronunciation = (
        fields.get("Pronunciation")
        or fields.get("Transliteration")
        or fields.get("Romanization")
        or ""
    )

    if not word:
        return False, 0.0

    score = score_western_armenian(word, pronunciation, reference_headwords)
    return score >= threshold, score


def filter_notes(
    notes: list[dict],
    reference_headwords: Optional[Collection[str]] = None,
    threshold: float = THRESHOLD_LIKELY_WA,
) -> tuple[list[dict], list[dict]]:
    """Split *notes* into (western_armenian, rejected) lists.

    Args:
        notes:               List of Anki note dicts.
        reference_headwords: Optional WA reference headword set.
        threshold:           Minimum WA confidence score to pass.

    Returns:
        ``(accepted, rejected)`` — two disjoint lists summing to *notes*.
    """
    accepted: list[dict] = []
    rejected: list[dict] = []
    for note in notes:
        is_wa, _score = classify_note(note, reference_headwords, threshold)
        if is_wa:
            accepted.append(note)
        else:
            rejected.append(note)
    return accepted, rejected


# ─── Internal helpers ──────────────────────────────────────────────────────────

def _normalise_armenian(text: str) -> str:
    """Lowercase and strip non-Armenian characters for dictionary lookup."""
    result = []
    for ch in text:
        cp = ord(ch)
        if _ARM_UPPERCASE_START <= cp <= _ARM_UPPERCASE_END:
            result.append(chr(cp + 0x30))  # to lowercase
        elif _ARM_LOWERCASE_START <= cp <= _ARM_LOWERCASE_END:
            result.append(ch)
        # skip punctuation, spaces, etc.
    return "".join(result)
