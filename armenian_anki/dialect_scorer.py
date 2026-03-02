"""
Western Armenian dialect scorer.

Scores Armenian text to estimate whether it is Western Armenian (WA) or
Eastern Armenian (EA) based on orthographic and lexical markers.

Background
----------
Western and Eastern Armenian diverged as literary standards in the 19th–20th
century and have several systematic differences:

  Phonology (consonant shift — WA vs EA):
    բ = /p/ in WA, /b/ in EA
    պ = /b/ in WA, /p'/ in EA
    գ = /k/ in WA, /g/ in EA
    կ = /g/ in WA, /k/ in EA

  Verb system:
    WA present tense uses the "կ'" (kuh) particle prefixed to the verb stem,
    e.g. «կ'utem» (I eat), «կ'eri» (I go).
    EA present uses the «-(o)um em» (oom em) periphrastic construction,
    e.g. «kardom em» (I am reading).

  Vocabulary:
    Several common words differ between the dialects, e.g.
    WA «chgayr» (there isn't) / EA «chka», WA «կ'eni» / EA «eka», etc.

  Orthography:
    WA traditionally uses Classical Armenian spelling (Mashtotsian).
    EA uses reformed Soviet-era spelling for many words.

Scoring
-------
``score_text`` returns a float in [-1.0, +1.0]:
  +1.0  → strongly Western Armenian
  -1.0  → strongly Eastern Armenian
   0.0  → neutral / ambiguous

``classify_text`` maps the score to a label:
  "western"   (score > WA_THRESHOLD)
  "eastern"   (score < EA_THRESHOLD)
  "ambiguous" (between the two thresholds)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence

# ─── Thresholds ──────────────────────────────────────────────────────────────

# A text must score above this to be labelled "western"
WA_THRESHOLD: float = 0.15

# A text must score below this to be labelled "eastern"
EA_THRESHOLD: float = -0.15


# ─── Marker definitions ───────────────────────────────────────────────────────

# Each tuple is (pattern, weight) where weight > 0 is WA and weight < 0 is EA.
# Patterns are matched case-insensitively against the full text.

_RAW_MARKERS: list[tuple[str, float]] = [
    # ── Western Armenian markers ─────────────────────────────────────────
    # The "կ'" (kuh) verbal particle — the most reliable WA marker.
    # WA present tense: կ'utem, կ'eri, կ'eni, կ'im…
    (r"կ[\u2018\u2019']", 1.0),   # կ' with curly or straight apostrophe

    # WA future / prospective marker "pidid" (պիtid)
    # In WA, pidid is a standalone word preceding the infinitive.
    (r"\bpitid\b", 0.6),           # romanised variant
    (r"\bpidid\b", 0.6),

    # Classical/WA spelling: "ow" digraph (ու) retained where EA reforms it
    # "oulleS" – WA for "I was"        (EA: «kur»)
    # Classic WA words containing the "-ow-" particle:
    (r"oul", 0.3),                  # found in classical WA spellings

    # WA definite article suffix "-N" on vowel-final words,
    # e.g. «aXe-N», «toune-N» (EA places the article differently)
    (r"ն\b", 0.2),                  # common in WA definite forms (low weight – also EA)

    # WA negation particle "չ'" contracted form
    (r"չ[\u2018\u2019']", 0.5),

    # WA words: "կ\u2019ulla" / "կ'ulla" (will become / will be)
    (r"կ[\u2018\u2019']ull", 0.8),  # կ'ull...
    (r"կ[\u2018\u2019']im\b", 0.8), # կ'im (I go — WA)
    (r"կ[\u2018\u2019']es\b", 0.8), # կ'es (you go — WA)
    (r"կ[\u2018\u2019']e\b",  0.8), # կ'e  (he/she goes — WA)

    # WA word "amo" (there) — unique WA vocabulary
    (r"\bamo\b", 0.5),

    # WA orthography: classical "-awn" ending (retained in WA, dropped in EA)
    (r"awn\b", 0.4),

    # ── Eastern Armenian markers ─────────────────────────────────────────
    # EA present participle suffix "-oom" / "-um" / "-om" + copula.
    # «kardom em» (I am reading), «grooum em» (I am writing).
    # The present progressive construction is unique to Eastern Armenian.
    (r"oom\s+(?:em|es|e|enk|ek|en)\b", -1.0),  # -oom + to-be verb (full form)
    (r"um\s+(?:em|es|e|enk|ek|en)\b",   -0.8), # -um + to-be verb (common EA spelling)
    (r"om\s+(?:em|es|e|enk|ek|en)\b",   -0.7), # -om + to-be verb (shortened EA form)
    (r"um\s+(?:եm|ел|е|ens)\b", -0.8),          # Armenian script variant

    # EA present suffix written directly: «-oomem» contracted
    (r"oomer\b", -0.7),
    (r"umer\b",  -0.7),

    # EA past "gr-el-a" / "grela" perfect construction (not in WA)
    (r"el\s+em\b", -0.6),   # «... el em» perfect (EA)
    (r"el\s+es\b", -0.6),
    (r"el\s+e\b",  -0.6),

    # EA reformed spelling: dropping of "h" in some words
    # EA «zma» (of him) vs WA «anor» — hard to capture without wordlist,
    # but the "zm" cluster is distinctively EA.
    (r"\bzm[aeiou]", -0.5),    # EA pronominal forms

    # EA-specific words (romanised & Unicode)
    (r"\beka\b",  -0.8),       # EA «eka» (I came) — WA uses «yeka»
    (r"\bchka\b", -0.6),       # EA «chka» (there isn't) — WA «chgayr»
    (r"\bchkas\b",-0.6),       # EA «chkas» (you don't have) — WA «chgayr»
    (r"\bvor\b",  -0.3),       # «vor» (which/that) — used in both but more frequent in EA prose
]


# Pre-compile all patterns for efficiency
_MARKERS: list[tuple[re.Pattern, float]] = [
    (re.compile(pat, re.IGNORECASE), weight)
    for pat, weight in _RAW_MARKERS
]


# ─── Public API ───────────────────────────────────────────────────────────────

@dataclass
class DialectScore:
    """Result of dialect scoring for a piece of text."""

    raw_score: float
    """Unnormalised sum of matched marker weights."""

    normalised_score: float
    """Score clamped to [-1.0, +1.0]."""

    label: str
    """'western' | 'eastern' | 'ambiguous'."""

    matched_markers: list[tuple[str, float]]
    """List of (pattern, weight) pairs that were found in the text."""

    token_count: int
    """Approximate number of whitespace tokens in the input (for context)."""

    @property
    def is_western(self) -> bool:
        return self.label == "western"

    @property
    def is_eastern(self) -> bool:
        return self.label == "eastern"

    @property
    def is_ambiguous(self) -> bool:
        return self.label == "ambiguous"

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"DialectScore(label={self.label!r}, "
            f"normalised={self.normalised_score:+.3f}, "
            f"matches={len(self.matched_markers)})"
        )


def score_text(text: str) -> DialectScore:
    """Score *text* for Western / Eastern Armenian dialect content.

    Args:
        text: Raw Armenian text (Unicode).  May contain romanised Armenian,
              AnkiConnect HTML markup, or plain Unicode Armenian script.

    Returns:
        A :class:`DialectScore` describing the result.
    """
    if not text or not text.strip():
        return DialectScore(
            raw_score=0.0,
            normalised_score=0.0,
            label="ambiguous",
            matched_markers=[],
            token_count=0,
        )

    token_count = len(text.split())
    raw_score = 0.0
    matched: list[tuple[str, float]] = []

    for pattern, weight in _MARKERS:
        if pattern.search(text):
            raw_score += weight
            matched.append((pattern.pattern, weight))

    # Normalise: scale by number of unique markers fired; clamp to [-1, +1].
    # A single strong marker should be enough to classify; multiple markers
    # compound up to the ceiling.
    n = max(len(matched), 1)
    normalised = max(-1.0, min(1.0, raw_score / n))

    # Determine label
    if normalised > WA_THRESHOLD:
        label = "western"
    elif normalised < EA_THRESHOLD:
        label = "eastern"
    else:
        label = "ambiguous"

    return DialectScore(
        raw_score=raw_score,
        normalised_score=normalised,
        label=label,
        matched_markers=matched,
        token_count=token_count,
    )


def classify_text(text: str) -> str:
    """Return 'western', 'eastern', or 'ambiguous' for the given text."""
    return score_text(text).label


def filter_western(
    texts: Sequence[str],
    include_ambiguous: bool = False,
) -> list[tuple[int, str, DialectScore]]:
    """Filter a sequence of texts, returning only Western Armenian ones.

    Args:
        texts:             Sequence of text strings to evaluate.
        include_ambiguous: If True, also include texts labelled 'ambiguous'.

    Returns:
        List of ``(original_index, text, score)`` tuples for retained items.
    """
    results: list[tuple[int, str, DialectScore]] = []
    for idx, text in enumerate(texts):
        ds = score_text(text)
        if ds.is_western or (include_ambiguous and ds.is_ambiguous):
            results.append((idx, text, ds))
    return results
