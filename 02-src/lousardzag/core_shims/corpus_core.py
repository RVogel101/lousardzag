"""Compatibility shim for future armenian-corpus-core package.

Current implementation exports lousardzag-local contracts so call sites can
stabilize imports before externalizing code.
"""

from __future__ import annotations

import os


def _env_true(name: str) -> bool:
    return os.getenv(name, "0").strip().lower() in {"1", "true", "yes", "on"}


if _env_true("LOUSARDZAG_USE_EXTERNAL_CORES"):
    try:
        # Future canonical package (not yet installed in this repo).
        from armenian_corpus_core import (  # type: ignore
            DialectTag,
            DocumentRecord,
            LexiconEntry,
            normalize_text_for_hash,
            sha256_normalized,
        )
    except ImportError:
        from lousardzag.core_contracts import (
            DialectTag,
            DocumentRecord,
            LexiconEntry,
            normalize_text_for_hash,
            sha256_normalized,
        )
else:
    from lousardzag.core_contracts import (
        DialectTag,
        DocumentRecord,
        LexiconEntry,
        normalize_text_for_hash,
        sha256_normalized,
    )

__all__ = [
    "DialectTag",
    "DocumentRecord",
    "LexiconEntry",
    "normalize_text_for_hash",
    "sha256_normalized",
]
