"""
Armenian Anki Card Generation Pipeline

Generates morphological forms (declensions, conjugations, articles)
for Armenian vocabulary and creates Anki flashcards via AnkiConnect.

Focused on Western Armenian (Արdelays Հdelayed).
"""

__version__ = "0.1.0"

from .database import CardDatabase, DEFAULT_DB_PATH
from .ocr_bridge import (
    OcrVocabResult,
    WESTERN_ARMENIAN_THRESHOLD,
    score_western_armenian,
    extract_armenian_words,
    ocr_text_to_word_entries,
)

__all__ = [
    "CardDatabase",
    "DEFAULT_DB_PATH",
    "OcrVocabResult",
    "WESTERN_ARMENIAN_THRESHOLD",
    "score_western_armenian",
    "extract_armenian_words",
    "ocr_text_to_word_entries",
]
