"""Core domain contracts for migration-safe integration.

Temporary location in lousardzag. Intended to move to a standalone core package.
"""

from .hashing import normalize_text_for_hash, sha256_normalized
from .types import DialectTag, DocumentRecord, LexiconEntry, PhoneticResult

__all__ = [
    "DialectTag",
    "DocumentRecord",
    "LexiconEntry",
    "PhoneticResult",
    "normalize_text_for_hash",
    "sha256_normalized",
]
