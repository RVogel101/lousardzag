#!/usr/bin/env python3
"""
Integration tests for the phrase-chunking progression pipeline and the
OCR-to-vocabulary bridge.

Covers:
  - Tag helper functions (level_tag, batch_tag, grammar_tag, syllable_tag)
  - Level-band rules (max_syllables_for_level, max_vocab_words_per_phrase)
  - ProgressionPlan: sorting, syllable gating, batch/level assignment
  - ProgressionPlan.coverage_report
  - assign_due_positions: monotonic ordering, vocab-before-phrase
  - score_western_armenian: base score, WA marker, EA marker
  - extract_armenian_words: tokenisation, deduplication, OCR correction
  - ocr_text_to_word_entries: end-to-end bridge, threshold rejection,
    min_syllables filtering, translation_map lookup

Run with:  python test_progression.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from armenian_anki.morphology.core import ARM
from armenian_anki.progression import (
    BATCHES_PER_LEVEL,
    VOCAB_BATCH_SIZE,
    PhraseBatch,
    ProgressionPlan,
    VocabBatch,
    WordEntry,
    assign_due_positions,
    batch_tag,
    grammar_tag,
    level_tag,
    max_syllables_for_level,
    max_vocab_words_per_phrase,
    syllable_tag,
)
from armenian_anki.ocr_bridge import (
    WESTERN_ARMENIAN_THRESHOLD,
    OcrVocabResult,
    _EA_PROGRESSIVE,
    _PREVERB_PARTICLE,
    extract_armenian_words,
    ocr_text_to_word_entries,
    score_western_armenian,
)


# ─── Word-building helpers ────────────────────────────────────────────

# Consonants that do not create extra syllables when appended to a vowel
_CONS = [
    ARM[c] for c in [
        "k", "t", "n", "s", "l", "m", "r", "h",
        "v", "b", "d", "g", "p", "kh", "gh", "sh",
        "ts", "dz", "j", "ch", "rr", "z", "zh", "f",
    ]
]

# Vowels
_VOWELS = [ARM[v] for v in ["a", "i", "e", "ye", "vo"]]


def _1syl(rank: int, pos: str = "noun") -> WordEntry:
    """Return a unique 1-syllable test WordEntry.

    Word shape: vowel + consonant  (one vowel → one syllable).
    Uniqueness is guaranteed for rank in [0, len(_CONS) * len(_VOWELS)).
    """
    c = _CONS[rank % len(_CONS)]
    v = _VOWELS[(rank // len(_CONS)) % len(_VOWELS)]
    word = v + c
    return WordEntry(word=word, translation=f"w{rank}", pos=pos, frequency_rank=rank + 1)


def _2syl(rank: int, pos: str = "noun") -> WordEntry:
    """Return a unique 2-syllable test WordEntry.

    Word shape: consonant + vowel1 + consonant + vowel2  (two vowels → two syllables).
    """
    c1 = _CONS[rank % len(_CONS)]
    c2 = _CONS[(rank + 1) % len(_CONS)]
    v1 = _VOWELS[rank % len(_VOWELS)]
    v2 = _VOWELS[(rank + 1) % len(_VOWELS)]
    word = c1 + v1 + c2 + v2
    return WordEntry(word=word, translation=f"w2_{rank}", pos=pos, frequency_rank=rank + 1)


def _3syl(rank: int, pos: str = "noun") -> WordEntry:
    """Return a unique 3-syllable test WordEntry."""
    c1 = _CONS[rank % len(_CONS)]
    c2 = _CONS[(rank + 1) % len(_CONS)]
    c3 = _CONS[(rank + 2) % len(_CONS)]
    v1 = _VOWELS[rank % len(_VOWELS)]
    v2 = _VOWELS[(rank + 1) % len(_VOWELS)]
    v3 = _VOWELS[(rank + 2) % len(_VOWELS)]
    word = c1 + v1 + c2 + v2 + c3 + v3
    return WordEntry(word=word, translation=f"w3_{rank}", pos=pos, frequency_rank=rank + 1)


def _words_1syl(count: int, start_rank: int = 0) -> list[WordEntry]:
    return [_1syl(start_rank + i) for i in range(count)]


# ─── Tests: tag helpers ───────────────────────────────────────────────

class TestTagHelpers(unittest.TestCase):
    """Unit tests for the Anki tag formatting functions."""

    def test_level_tag_single_digit(self):
        self.assertEqual(level_tag(1), "level::01")

    def test_level_tag_double_digit(self):
        self.assertEqual(level_tag(15), "level::15")

    def test_level_tag_large(self):
        self.assertEqual(level_tag(99), "level::99")

    def test_batch_tag_leading_zeros(self):
        self.assertEqual(batch_tag(0), "batch::000")

    def test_batch_tag_mid(self):
        self.assertEqual(batch_tag(7), "batch::007")

    def test_batch_tag_large(self):
        self.assertEqual(batch_tag(100), "batch::100")

    def test_grammar_tag(self):
        self.assertEqual(grammar_tag("nominative_subject"), "grammar::nominative_subject")

    def test_grammar_tag_simple(self):
        self.assertEqual(grammar_tag("plural"), "grammar::plural")

    def test_syllable_tag(self):
        self.assertEqual(syllable_tag(1), "syl::1")
        self.assertEqual(syllable_tag(3), "syl::3")


# ─── Tests: level-band rules ──────────────────────────────────────────

class TestLevelBandRules(unittest.TestCase):

    def test_max_syllables_level_1(self):
        self.assertEqual(max_syllables_for_level(1), 1)

    def test_max_syllables_level_5(self):
        self.assertEqual(max_syllables_for_level(5), 1)

    def test_max_syllables_level_6(self):
        self.assertEqual(max_syllables_for_level(6), 2)

    def test_max_syllables_level_10(self):
        self.assertEqual(max_syllables_for_level(10), 2)

    def test_max_syllables_level_11(self):
        self.assertEqual(max_syllables_for_level(11), 3)

    def test_max_syllables_level_15(self):
        self.assertEqual(max_syllables_for_level(15), 3)

    def test_max_syllables_level_16_no_limit(self):
        self.assertGreater(max_syllables_for_level(16), 10)

    def test_max_vocab_per_phrase_level_1(self):
        self.assertEqual(max_vocab_words_per_phrase(1), 1)

    def test_max_vocab_per_phrase_level_5(self):
        self.assertEqual(max_vocab_words_per_phrase(5), 1)

    def test_max_vocab_per_phrase_level_6(self):
        self.assertEqual(max_vocab_words_per_phrase(6), 3)

    def test_max_vocab_per_phrase_level_10(self):
        self.assertEqual(max_vocab_words_per_phrase(10), 3)

    def test_max_vocab_per_phrase_level_11(self):
        self.assertEqual(max_vocab_words_per_phrase(11), 4)

    def test_max_vocab_per_phrase_level_20(self):
        self.assertEqual(max_vocab_words_per_phrase(20), 5)

    def test_max_vocab_per_phrase_level_21(self):
        self.assertEqual(max_vocab_words_per_phrase(21), 6)


# ─── Tests: ProgressionPlan ───────────────────────────────────────────

class TestProgressionPlanEmpty(unittest.TestCase):

    def setUp(self):
        self.plan = ProgressionPlan([])

    def test_no_vocab_batches(self):
        self.assertEqual(self.plan.vocab_batches, [])

    def test_no_phrase_batches(self):
        self.assertEqual(self.plan.phrase_batches, [])

    def test_ordered_segments_empty(self):
        self.assertEqual(list(self.plan.ordered_segments()), [])

    def test_coverage_report_zero(self):
        report = self.plan.coverage_report()
        self.assertEqual(report["total_vocab"], 0)
        self.assertEqual(report["covered_in_phrases"], 0)
        self.assertEqual(report["coverage_pct"], 0.0)


class TestProgressionPlanSingleBatch(unittest.TestCase):
    """20 one-syllable words → exactly one VocabBatch + one PhraseBatch."""

    def setUp(self):
        self.words = _words_1syl(VOCAB_BATCH_SIZE)
        self.plan = ProgressionPlan(self.words)

    def test_one_vocab_batch(self):
        self.assertEqual(len(self.plan.vocab_batches), 1)

    def test_one_phrase_batch(self):
        self.assertEqual(len(self.plan.phrase_batches), 1)

    def test_batch_level_is_1(self):
        self.assertEqual(self.plan.vocab_batches[0].level, 1)

    def test_batch_index_is_0(self):
        self.assertEqual(self.plan.vocab_batches[0].batch_index, 0)

    def test_all_words_in_batch(self):
        self.assertEqual(len(self.plan.vocab_batches[0].words), VOCAB_BATCH_SIZE)

    def test_sorted_by_frequency(self):
        batch_words = self.plan.vocab_batches[0].words
        ranks = [w.frequency_rank for w in batch_words]
        self.assertEqual(ranks, sorted(ranks))

    def test_phrase_batch_covers_all_words(self):
        covered = {p.target_word for p in self.plan.phrase_batches[0].phrases}
        batch_words = {w.word for w in self.plan.vocab_batches[0].words}
        self.assertEqual(covered, batch_words)

    def test_ordered_segments_yields_vocab_then_phrase(self):
        segments = list(self.plan.ordered_segments())
        self.assertIsInstance(segments[0], VocabBatch)
        self.assertIsInstance(segments[1], PhraseBatch)


class TestProgressionPlanSyllableGating(unittest.TestCase):
    """Syllable gating ensures 2-syl words follow all 1-syl words in the sequence.

    Level assignment is purely positional (level = batch_index // BATCHES_PER_LEVEL + 1).
    For a 2-syl word to land in level 6+, at least 5 full levels (500 words) of
    1-syl words must precede it.  The tests below use 20 one-syl words to check
    ordering, and the VOCAB_BATCH_SIZE boundary to verify inter-batch deferral.
    """

    def setUp(self):
        # 20 one-syllable words (ranks 1-20) + 1 two-syllable word (rank 3)
        self.words_1syl = _words_1syl(20)
        self.word_2syl = _2syl(0)
        self.word_2syl.frequency_rank = 3  # high frequency, but 2 syllables
        self.plan = ProgressionPlan(self.words_1syl + [self.word_2syl])

    def _batch_of(self, word_str: str) -> int:
        """Return the batch_index of the batch containing *word_str*."""
        for vb in self.plan.vocab_batches:
            for w in vb.words:
                if w.word == word_str:
                    return vb.batch_index
        raise AssertionError(f"{word_str!r} not found in any batch")

    def test_2syl_word_deferred_to_later_batch(self):
        """The 2-syl word must appear in a later batch than all 1-syl words."""
        two_syl_batch = self._batch_of(self.word_2syl.word)
        for w in self.words_1syl:
            one_syl_batch = self._batch_of(w.word)
            self.assertLess(one_syl_batch, two_syl_batch,
                            msg=f"1-syl word {w.word!r} should precede 2-syl batch")

    def test_1syl_words_all_in_first_batch(self):
        """All 20 one-syl words fill batch 0; the 2-syl word spills into batch 1."""
        first_batch_words = {w.word for w in self.plan.vocab_batches[0].words}
        for w in self.words_1syl:
            self.assertIn(w.word, first_batch_words)

    def test_2syl_word_in_second_batch(self):
        """With exactly 20 one-syl words before it, the 2-syl word is in batch 1."""
        self.assertEqual(self._batch_of(self.word_2syl.word), 1)


class TestProgressionPlanOneLevelBoundary(unittest.TestCase):
    """Exactly 100 words fills one complete level (5 batches × 20 words)."""

    def setUp(self):
        self.words = _words_1syl(VOCAB_BATCH_SIZE * BATCHES_PER_LEVEL)
        self.plan = ProgressionPlan(self.words)

    def test_five_vocab_batches(self):
        self.assertEqual(len(self.plan.vocab_batches), BATCHES_PER_LEVEL)

    def test_all_batches_level_1(self):
        for vb in self.plan.vocab_batches:
            self.assertEqual(vb.level, 1)

    def test_full_phrase_coverage(self):
        report = self.plan.coverage_report()
        self.assertEqual(report["coverage_pct"], 100.0)
        self.assertEqual(report["uncovered"], [])


class TestProgressionPlanMultiLevel(unittest.TestCase):
    """101 one-syllable words → 6 batches spanning 2 levels."""

    def setUp(self):
        count = VOCAB_BATCH_SIZE * BATCHES_PER_LEVEL + 1  # 101
        self.plan = ProgressionPlan(_words_1syl(count))

    def test_six_vocab_batches(self):
        self.assertEqual(len(self.plan.vocab_batches), BATCHES_PER_LEVEL + 1)

    def test_first_five_batches_level_1(self):
        for vb in self.plan.vocab_batches[:BATCHES_PER_LEVEL]:
            self.assertEqual(vb.level, 1)

    def test_sixth_batch_level_2(self):
        self.assertEqual(self.plan.vocab_batches[BATCHES_PER_LEVEL].level, 2)


class TestProgressionPlanCoverageReport(unittest.TestCase):

    def test_all_words_covered(self):
        plan = ProgressionPlan(_words_1syl(10))
        report = plan.coverage_report()
        self.assertEqual(report["total_vocab"], 10)
        self.assertEqual(report["covered_in_phrases"], 10)
        self.assertEqual(report["coverage_pct"], 100.0)
        self.assertEqual(report["uncovered"], [])

    def test_total_vocab_matches_input(self):
        words = _words_1syl(25)
        plan = ProgressionPlan(words)
        report = plan.coverage_report()
        self.assertEqual(report["total_vocab"], 25)


class TestProgressionPlanSummary(unittest.TestCase):

    def test_summary_is_string(self):
        plan = ProgressionPlan(_words_1syl(5))
        summary = plan.summary()
        self.assertIsInstance(summary, str)
        self.assertIn("Level", summary)

    def test_summary_contains_word_count(self):
        plan = ProgressionPlan(_words_1syl(5))
        self.assertIn("5", plan.summary())


# ─── Tests: assign_due_positions ──────────────────────────────────────

class TestAssignDuePositions(unittest.TestCase):

    def setUp(self):
        self.words = _words_1syl(VOCAB_BATCH_SIZE)
        self.plan = ProgressionPlan(self.words)
        self.positions = assign_due_positions(self.plan)

    def test_all_words_have_positions(self):
        for w in self.words:
            self.assertIn(w.word, self.positions)

    def test_all_phrase_keys_present(self):
        for pb in self.plan.phrase_batches:
            for phrase in pb.phrases:
                key = f"phrase::{phrase.target_word}"
                self.assertIn(key, self.positions)

    def test_vocab_positions_before_phrase_positions_in_batch_0(self):
        vb = self.plan.vocab_batches[0]
        pb = self.plan.phrase_batches[0]

        max_vocab_pos = max(self.positions[w.word] for w in vb.words)
        min_phrase_pos = min(
            self.positions[f"phrase::{p.target_word}"]
            for p in pb.phrases
        )
        self.assertLess(max_vocab_pos, min_phrase_pos)

    def test_vocab_positions_are_positive(self):
        for w in self.words:
            self.assertGreater(self.positions[w.word], 0)

    def test_phrase_positions_are_positive(self):
        for pb in self.plan.phrase_batches:
            for phrase in pb.phrases:
                key = f"phrase::{phrase.target_word}"
                self.assertGreater(self.positions[key], 0)

    def test_empty_plan_returns_empty_dict(self):
        empty_plan = ProgressionPlan([])
        self.assertEqual(assign_due_positions(empty_plan), {})


# ─── Tests: Western Armenian scoring ─────────────────────────────────

class TestScoreWesternArmenian(unittest.TestCase):

    def test_empty_string_returns_zero(self):
        self.assertEqual(score_western_armenian(""), 0.0)

    def test_latin_only_returns_zero(self):
        self.assertEqual(score_western_armenian("hello world"), 0.0)

    def test_digits_only_returns_zero(self):
        self.assertEqual(score_western_armenian("12345"), 0.0)

    def test_armenian_base_score(self):
        # Single Armenian word, no special markers → base 0.40
        arm_word = ARM["k"] + ARM["a"]  # "ka"
        score = score_western_armenian(arm_word)
        self.assertAlmostEqual(score, 0.40)

    def test_wa_preverbal_particle_increases_score(self):
        # Text containing WA preverbal "կը" → score should exceed base
        wa_text = _PREVERB_PARTICLE + " " + ARM["k"] + ARM["a"]
        score = score_western_armenian(wa_text)
        self.assertGreater(score, 0.40)
        self.assertAlmostEqual(score, 0.65)

    def test_ea_progressive_decreases_score(self):
        # Text containing EA "գոր" → score should drop below base
        ea_text = ARM["k"] + ARM["a"] + " " + _EA_PROGRESSIVE
        score = score_western_armenian(ea_text)
        self.assertLess(score, 0.40)
        self.assertAlmostEqual(score, 0.05)

    def test_score_clamped_to_0_1(self):
        # Multiple WA markers — score must not exceed 1.0
        wa_text = (_PREVERB_PARTICLE + " ") * 10 + ARM["k"] + ARM["a"]
        score = score_western_armenian(wa_text)
        self.assertLessEqual(score, 1.0)

    def test_score_never_negative(self):
        # Multiple EA markers — score must not go below 0.0
        ea_text = (_EA_PROGRESSIVE + " ") * 10
        score = score_western_armenian(ea_text)
        self.assertGreaterEqual(score, 0.0)

    def test_base_score_above_threshold(self):
        # A plain Armenian word should pass the default threshold
        arm_word = ARM["t"] + ARM["a"]
        self.assertGreaterEqual(score_western_armenian(arm_word),
                                WESTERN_ARMENIAN_THRESHOLD)

    def test_ea_text_below_threshold(self):
        # EA-marked text should fall below threshold
        ea_text = ARM["k"] + ARM["a"] + " " + _EA_PROGRESSIVE
        self.assertLess(score_western_armenian(ea_text),
                        WESTERN_ARMENIAN_THRESHOLD)


# ─── Tests: extract_armenian_words ───────────────────────────────────

class TestExtractArmenianWords(unittest.TestCase):

    def test_empty_input(self):
        self.assertEqual(extract_armenian_words(""), [])

    def test_latin_only_input(self):
        self.assertEqual(extract_armenian_words("hello world"), [])

    def test_single_armenian_word(self):
        word = ARM["k"] + ARM["a"]
        result = extract_armenian_words(word)
        self.assertEqual(result, [word])

    def test_multiple_words(self):
        w1 = ARM["k"] + ARM["a"]
        w2 = ARM["t"] + ARM["a"]
        text = w1 + " " + w2
        result = extract_armenian_words(text)
        self.assertEqual(result, [w1, w2])

    def test_deduplication(self):
        word = ARM["k"] + ARM["a"]
        text = word + " " + word + " " + word
        result = extract_armenian_words(text)
        self.assertEqual(result, [word])

    def test_mixed_latin_armenian(self):
        w = ARM["k"] + ARM["a"]
        text = "This is " + w + " and some text"
        result = extract_armenian_words(text)
        self.assertEqual(result, [w])

    def test_ocr_correction_applied(self):
        # U+0578 U+0582 U+057E (ouv misread) → U+0578 U+057E (ov)
        misread = "\u0578\u0582\u057E"
        corrected = "\u0578\u057E"
        result = extract_armenian_words(misread)
        # After correction, the token should be the corrected form
        self.assertIn(corrected, result)
        self.assertNotIn(misread, result)

    def test_preserves_first_occurrence_order(self):
        w1 = ARM["k"] + ARM["a"]
        w2 = ARM["t"] + ARM["i"]
        w3 = ARM["n"] + ARM["a"]
        text = w1 + " " + w2 + " " + w3
        result = extract_armenian_words(text)
        self.assertEqual(result, [w1, w2, w3])

    def test_punctuation_stripped(self):
        word = ARM["k"] + ARM["a"]
        text = word + "." + " " + word + ","
        result = extract_armenian_words(text)
        self.assertEqual(result, [word])


# ─── Tests: ocr_text_to_word_entries ────────────────────────────────

class TestOcrBridge(unittest.TestCase):

    def _wa_sentence(self) -> str:
        """Build a minimal WA sentence with the preverbal particle."""
        return _PREVERB_PARTICLE + " " + ARM["k"] + ARM["a"]

    def test_returns_ocr_vocab_result(self):
        result = ocr_text_to_word_entries(self._wa_sentence())
        self.assertIsInstance(result, OcrVocabResult)

    def test_wa_text_produces_entries(self):
        result = ocr_text_to_word_entries(self._wa_sentence())
        self.assertGreater(len(result.word_entries), 0)

    def test_all_entries_are_word_entry(self):
        result = ocr_text_to_word_entries(self._wa_sentence())
        for entry in result.word_entries:
            self.assertIsInstance(entry, WordEntry)

    def test_wa_score_stored_in_result(self):
        result = ocr_text_to_word_entries(self._wa_sentence())
        self.assertAlmostEqual(result.wa_score, 0.65)

    def test_raw_words_populated(self):
        result = ocr_text_to_word_entries(self._wa_sentence())
        self.assertIsInstance(result.raw_words, list)
        self.assertGreater(len(result.raw_words), 0)

    def test_empty_text_returns_empty_result(self):
        result = ocr_text_to_word_entries("")
        self.assertEqual(result.word_entries, [])
        self.assertEqual(result.wa_score, 0.0)

    def test_ea_text_below_threshold_returns_empty(self):
        # EA "gor" drops score below threshold
        ea_text = ARM["k"] + ARM["a"] + " " + _EA_PROGRESSIVE
        result = ocr_text_to_word_entries(ea_text)
        self.assertEqual(result.word_entries, [])
        self.assertEqual(len(result.raw_words), 2)  # words found but rejected

    def test_latin_only_returns_empty(self):
        result = ocr_text_to_word_entries("hello world")
        self.assertEqual(result.word_entries, [])
        self.assertEqual(result.wa_score, 0.0)

    def test_custom_threshold_zero_accepts_everything(self):
        # threshold=0.0 → even EA text is accepted
        ea_text = ARM["k"] + ARM["a"] + " " + _EA_PROGRESSIVE
        result = ocr_text_to_word_entries(ea_text, threshold=0.0)
        self.assertGreater(len(result.word_entries), 0)

    def test_custom_threshold_one_rejects_everything(self):
        wa_text = self._wa_sentence()
        result = ocr_text_to_word_entries(wa_text, threshold=1.0)
        self.assertEqual(result.word_entries, [])

    def test_frequency_rank_starts_at_base(self):
        wa_text = self._wa_sentence()
        result = ocr_text_to_word_entries(wa_text, base_frequency_rank=42)
        ranks = [e.frequency_rank for e in result.word_entries]
        self.assertGreaterEqual(min(ranks), 42)

    def test_pos_propagated_to_entries(self):
        wa_text = self._wa_sentence()
        result = ocr_text_to_word_entries(wa_text, pos="verb")
        for entry in result.word_entries:
            self.assertEqual(entry.pos, "verb")

    def test_translation_map_applied(self):
        word = ARM["k"] + ARM["a"]
        wa_text = _PREVERB_PARTICLE + " " + word
        result = ocr_text_to_word_entries(
            wa_text, translation_map={word: "some translation"}
        )
        translations = {e.word: e.translation for e in result.word_entries}
        self.assertEqual(translations.get(word), "some translation")

    def test_min_syllables_filters_short_words(self):
        # Build text with a 1-syllable and a 2-syllable word, plus preverbal
        w1 = ARM["k"] + ARM["a"]                            # 1 syllable
        w2 = ARM["kh"] + ARM["vo"] + ARM["s"] + ARM["ye"] + ARM["l"]  # 2 syllables
        wa_text = _PREVERB_PARTICLE + " " + w1 + " " + w2
        result = ocr_text_to_word_entries(wa_text, min_syllables=2)
        result_words = {e.word for e in result.word_entries}
        self.assertNotIn(w1, result_words)
        self.assertIn(w2, result_words)

    def test_filtered_count_reflects_excluded_words(self):
        w1 = ARM["k"] + ARM["a"]  # 1 syllable → filtered
        wa_text = _PREVERB_PARTICLE + " " + w1
        result = ocr_text_to_word_entries(wa_text, min_syllables=2)
        # The preverbal "կը" is 1-syllable and "w1" is 1-syllable → both filtered
        self.assertGreaterEqual(result.filtered_count, 1)


# ─── Integration: OCR bridge feeding ProgressionPlan ─────────────────

class TestOcrToProgressionIntegration(unittest.TestCase):
    """End-to-end: OCR text → word entries → ProgressionPlan."""

    def _build_wa_text_with_words(self, n: int) -> tuple[str, list[str]]:
        """Build a WA text block containing n distinct 1-syllable Armenian words."""
        words = []
        for i in range(n):
            c = _CONS[i % len(_CONS)]
            v = _VOWELS[(i // len(_CONS)) % len(_VOWELS)]
            words.append(v + c)
        text = _PREVERB_PARTICLE + " " + " ".join(words)
        return text, words

    def test_bridge_then_plan_has_correct_batch_count(self):
        text, expected_words = self._build_wa_text_with_words(VOCAB_BATCH_SIZE)
        bridge_result = ocr_text_to_word_entries(text)
        # The preverbal particle itself is also an Armenian token; filter to
        # only the words we deliberately constructed
        extracted = {e.word for e in bridge_result.word_entries}
        plan_words = [e for e in bridge_result.word_entries
                      if e.word in set(expected_words)]
        plan = ProgressionPlan(plan_words)
        self.assertGreaterEqual(len(plan.vocab_batches), 1)

    def test_bridge_produces_valid_word_entries_for_plan(self):
        text, _ = self._build_wa_text_with_words(10)
        bridge_result = ocr_text_to_word_entries(text)
        plan = ProgressionPlan(bridge_result.word_entries)
        report = plan.coverage_report()
        self.assertEqual(report["total_vocab"], len(bridge_result.word_entries))
        self.assertEqual(report["coverage_pct"], 100.0)

    def test_ea_text_produces_empty_plan(self):
        # EA "gor" makes the block score below threshold → no entries → empty plan
        ea_text = ARM["k"] + ARM["a"] + " " + _EA_PROGRESSIVE
        bridge_result = ocr_text_to_word_entries(ea_text)
        plan = ProgressionPlan(bridge_result.word_entries)
        self.assertEqual(plan.vocab_batches, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
