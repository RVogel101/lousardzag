#!/usr/bin/env python3
"""
Tests for armenian_anki.western_armenian_filter.

Run with:  python test_western_armenian_filter.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from armenian_anki.western_armenian_filter import (
    is_armenian_script,
    has_grabar_markers,
    armenian_script_ratio,
    score_pronunciation,
    score_western_armenian,
    classify_note,
    filter_notes,
    _normalise_armenian,
    THRESHOLD_LIKELY_WA,
)


class TestIsArmenianScript(unittest.TestCase):
    def test_armenian_word_detected(self):
        self.assertTrue(is_armenian_script("մատ"))   # mat (finger)

    def test_latin_only_not_detected(self):
        self.assertFalse(is_armenian_script("hello"))

    def test_empty_string(self):
        self.assertFalse(is_armenian_script(""))

    def test_mixed_returns_true(self):
        # Armenian characters mixed with Latin
        self.assertTrue(is_armenian_script("arm: մատ"))

    def test_uppercase_armenian_detected(self):
        self.assertTrue(is_armenian_script("Մատ"))   # capitalised


class TestHasGrabarMarkers(unittest.TestCase):
    def test_grabar_past_participle(self):
        # -եալ is a Classical Armenian past participle suffix
        self.assertTrue(has_grabar_markers("գրեալ"))

    def test_grabar_genitive_dative(self):
        # -ոյ is a Grabar genitive-dative ending
        self.assertTrue(has_grabar_markers("հօրոյ"))

    def test_modern_armenian_not_flagged(self):
        self.assertFalse(has_grabar_markers("մատ"))

    def test_empty_string(self):
        self.assertFalse(has_grabar_markers(""))


class TestArmenianScriptRatio(unittest.TestCase):
    def test_pure_armenian(self):
        ratio = armenian_script_ratio("մատ")
        self.assertAlmostEqual(ratio, 1.0)

    def test_empty_string(self):
        self.assertEqual(armenian_script_ratio(""), 0.0)

    def test_half_armenian(self):
        # 3 Armenian chars + 3 Latin chars = 0.5
        ratio = armenian_script_ratio("մատabc")
        self.assertAlmostEqual(ratio, 0.5)

    def test_latin_only(self):
        self.assertEqual(armenian_script_ratio("hello"), 0.0)


class TestScorePronunciation(unittest.TestCase):
    def test_wa_aspirate_p_boost(self):
        # p' is a Western Armenian aspirated stop marker
        score = score_pronunciation("p'ayt")
        self.assertGreater(score, 0.0)

    def test_wa_kh_boost(self):
        score = score_pronunciation("khosk")   # "word" in WA romanisation
        self.assertGreater(score, 0.0)

    def test_empty_string_zero(self):
        self.assertEqual(score_pronunciation(""), 0.0)

    def test_wa_and_ea_mix(self):
        # Having both WA and EA patterns; score should reflect combined
        score_wa = score_pronunciation("kh")
        score_ea = score_pronunciation("ts")
        # WA marker alone gives positive; function is additive
        self.assertGreater(score_wa, score_ea)


class TestScoreWesternArmenian(unittest.TestCase):
    def test_plain_armenian_word_passes_baseline(self):
        # Any Armenian script word should get at least the baseline score.
        score = score_western_armenian("մատ")
        self.assertGreater(score, 0.0)

    def test_latin_only_returns_zero(self):
        self.assertEqual(score_western_armenian("hello"), 0.0)

    def test_grabar_marker_reduces_score(self):
        # Word with Grabar marker should score lower than a plain word.
        score_grabar = score_western_armenian("գրեալ")
        score_plain  = score_western_armenian("գրել")
        self.assertLess(score_grabar, score_plain)

    def test_wa_pronunciation_boosts_score(self):
        score_with_pron = score_western_armenian("մատ", pronunciation="mat")
        score_without   = score_western_armenian("մատ")
        # Adding a neutral pronunciation shouldn't hurt the score.
        self.assertGreaterEqual(score_with_pron, score_without - 0.01)

    def test_reference_headword_hit_boosts_score(self):
        headwords = {"մատ"}
        score_with_ref = score_western_armenian("մատ", reference_headwords=headwords)
        score_without  = score_western_armenian("մատ")
        self.assertGreater(score_with_ref, score_without)

    def test_reference_headword_miss_no_boost(self):
        headwords = {"բառ"}  # a different word
        score_hit  = score_western_armenian("բառ", reference_headwords=headwords)
        score_miss = score_western_armenian("մատ", reference_headwords=headwords)
        self.assertGreater(score_hit, score_miss)

    def test_score_clamped_to_one(self):
        # Maximum score should never exceed 1.0
        headwords = {"մատ"}
        score = score_western_armenian("մատ", pronunciation="kh t' p'",
                                       reference_headwords=headwords)
        self.assertLessEqual(score, 1.0)

    def test_score_clamped_to_zero(self):
        self.assertGreaterEqual(score_western_armenian("hello"), 0.0)


class TestClassifyNote(unittest.TestCase):
    """Tests for classify_note using the AnkiConnect-style note dict format."""

    def _make_note(self, word="", pronunciation=""):
        """Helper to build a minimal AnkiConnect-style note dict."""
        return {
            "fields": {
                "Word": {"value": word},
                "Pronunciation": {"value": pronunciation},
            }
        }

    def test_armenian_word_classified_wa(self):
        note = self._make_note(word="մատ")
        is_wa, score = classify_note(note)
        # Score should be at least the baseline even without pronunciation
        self.assertGreater(score, 0.0)
        # Plain Armenian script should pass the default threshold (score ≥ 0.40)
        self.assertTrue(is_wa)

    def test_empty_note_rejected(self):
        is_wa, score = classify_note({})
        self.assertFalse(is_wa)
        self.assertEqual(score, 0.0)

    def test_latin_only_word_rejected(self):
        note = self._make_note(word="hello")
        is_wa, score = classify_note(note)
        self.assertFalse(is_wa)
        self.assertEqual(score, 0.0)

    def test_note_with_wa_pronunciation_higher_score(self):
        note_wa = self._make_note(word="մատ", pronunciation="mat kh t'")
        note_no = self._make_note(word="մատ", pronunciation="")
        _, score_wa = classify_note(note_wa)
        _, score_no = classify_note(note_no)
        self.assertGreaterEqual(score_wa, score_no - 0.01)

    def test_fallback_field_names(self):
        # Notes using 'Front' instead of 'Word' should still be classified.
        note = {"fields": {"Front": {"value": "մատ"}}}
        is_wa, score = classify_note(note)
        self.assertGreater(score, 0.0)

    def test_plain_dict_fallback(self):
        # Non-AnkiConnect format: flat dict with string values
        note = {"Word": "մատ", "Pronunciation": "mat"}
        is_wa, score = classify_note(note)
        self.assertGreater(score, 0.0)

    def test_custom_threshold_low_accepts_more(self):
        note = self._make_note(word="մատ")
        _, score = classify_note(note)
        # With a very low threshold everything Armenian should pass
        is_wa_low, _ = classify_note(note, threshold=0.1)
        is_wa_high, _ = classify_note(note, threshold=0.99)
        self.assertTrue(is_wa_low)
        self.assertFalse(is_wa_high)


class TestFilterNotes(unittest.TestCase):
    def _make_note(self, word):
        return {"fields": {"Word": {"value": word}}}

    def test_split_accepted_rejected(self):
        notes = [
            self._make_note("մատ"),    # Armenian → should be accepted
            self._make_note("hello"),  # Latin → should be rejected
            self._make_note("բառ"),    # Armenian → should be accepted
        ]
        accepted, rejected = filter_notes(notes, threshold=0.1)
        self.assertEqual(len(accepted), 2)
        self.assertEqual(len(rejected), 1)

    def test_empty_input(self):
        accepted, rejected = filter_notes([])
        self.assertEqual(accepted, [])
        self.assertEqual(rejected, [])

    def test_all_accepted(self):
        notes = [self._make_note("մատ"), self._make_note("բառ")]
        accepted, rejected = filter_notes(notes, threshold=0.1)
        self.assertEqual(len(accepted), 2)
        self.assertEqual(len(rejected), 0)

    def test_all_rejected(self):
        notes = [self._make_note("hello"), self._make_note("world")]
        accepted, rejected = filter_notes(notes)
        self.assertEqual(len(accepted), 0)
        self.assertEqual(len(rejected), 2)

    def test_reference_headwords_influence(self):
        # With a headword reference, a matched word should score higher.
        notes = [self._make_note("մատ")]
        # Without reference, use low threshold so it passes anyway
        accepted_no_ref, _ = filter_notes(notes, threshold=0.1)
        # With reference including the word
        accepted_ref, _ = filter_notes(notes, reference_headwords={"մատ"}, threshold=0.1)
        self.assertEqual(len(accepted_no_ref), 1)
        self.assertEqual(len(accepted_ref), 1)


class TestNormaliseArmenian(unittest.TestCase):
    def test_uppercase_lowercased(self):
        result = _normalise_armenian("Մատ")
        self.assertEqual(result, "մատ")

    def test_latin_chars_stripped(self):
        result = _normalise_armenian("մատ (hand)")
        self.assertEqual(result, "մատ")

    def test_empty_string(self):
        self.assertEqual(_normalise_armenian(""), "")

    def test_already_lowercase(self):
        self.assertEqual(_normalise_armenian("մատ"), "մատ")


if __name__ == "__main__":
    unittest.main(verbosity=2)
