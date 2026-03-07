"""Compatibility shim for future armenian-linguistics-core package.

Import from this module in migration-safe call sites.
It prefers the external package when available, and falls back to local
lousardzag implementations today.
"""

from __future__ import annotations

import os


def _env_true(name: str) -> bool:
    return os.getenv(name, "0").strip().lower() in {"1", "true", "yes", "on"}


if _env_true("LOUSARDZAG_USE_EXTERNAL_CORES"):
    try:
        # Future canonical package (not yet installed in this repo).
        from armenian_linguistics_core import (  # type: ignore
            ARMENIAN_DIGRAPHS,
            ARMENIAN_PHONEMES,
            LETTER_NAME_IPA,
            LETTER_SOUND_IPA,
            calculate_phonetic_difficulty,
            get_phonetic_transcription,
            get_pronunciation_guide,
        )
    except ImportError:
        # Current local fallback.
        from lousardzag.phonetics import (
            ARMENIAN_DIGRAPHS,
            ARMENIAN_PHONEMES,
            LETTER_NAME_IPA,
            LETTER_SOUND_IPA,
            calculate_phonetic_difficulty,
            get_phonetic_transcription,
            get_pronunciation_guide,
        )
else:
    from lousardzag.phonetics import (
        ARMENIAN_DIGRAPHS,
        ARMENIAN_PHONEMES,
        LETTER_NAME_IPA,
        LETTER_SOUND_IPA,
        calculate_phonetic_difficulty,
        get_phonetic_transcription,
        get_pronunciation_guide,
    )

__all__ = [
    "ARMENIAN_DIGRAPHS",
    "ARMENIAN_PHONEMES",
    "LETTER_NAME_IPA",
    "LETTER_SOUND_IPA",
    "get_phonetic_transcription",
    "calculate_phonetic_difficulty",
    "get_pronunciation_guide",
]
