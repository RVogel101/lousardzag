"""Migration compatibility shim namespace."""

from .corpus_core import (
    DialectTag,
    DocumentRecord,
    LexiconEntry,
    normalize_text_for_hash,
    sha256_normalized,
)
from .linguistics_core import (
    ARMENIAN_DIGRAPHS,
    ARMENIAN_PHONEMES,
    LETTER_NAME_IPA,
    LETTER_SOUND_IPA,
    calculate_phonetic_difficulty,
    get_phonetic_transcription,
    get_pronunciation_guide,
)
from .mappers import (
    anki_card_row_to_lexicon_entry,
    sentence_row_to_document_record,
    wa_fingerprint_row_to_document_record,
)

__all__ = [
    "DialectTag",
    "DocumentRecord",
    "LexiconEntry",
    "normalize_text_for_hash",
    "sha256_normalized",
    "ARMENIAN_DIGRAPHS",
    "ARMENIAN_PHONEMES",
    "LETTER_NAME_IPA",
    "LETTER_SOUND_IPA",
    "get_phonetic_transcription",
    "calculate_phonetic_difficulty",
    "get_pronunciation_guide",
    "anki_card_row_to_lexicon_entry",
    "sentence_row_to_document_record",
    "wa_fingerprint_row_to_document_record",
]
