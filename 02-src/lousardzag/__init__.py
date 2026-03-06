"""
Lousardzag Card Generation Pipeline

Generates morphological forms (declensions, conjugations, articles)
for Armenian vocabulary and creates Anki flashcards via AnkiConnect.

Focused on Western Armenian (Արdelays Հdelayed).
"""

__version__ = "0.1.0"

from .database import CardDatabase, DEFAULT_DB_PATH
from .core_contracts import DialectTag, DocumentRecord, LexiconEntry, PhoneticResult

__all__ = [
	"CardDatabase",
	"DEFAULT_DB_PATH",
	"DialectTag",
	"DocumentRecord",
	"LexiconEntry",
	"PhoneticResult",
]
