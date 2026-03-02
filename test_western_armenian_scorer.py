#!/usr/bin/env python3
"""
Tests for armenian_anki.western_armenian_scorer.

Run with:  python test_western_armenian_scorer.py

The tests validate the core scoring algorithm against known Western Armenian
and Eastern Armenian text patterns, using the Armenian character codes
defined in armenian_anki.morphology.core.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from armenian_anki.morphology.core import ARM
from armenian_anki.western_armenian_scorer import (
    WA_THRESHOLD,
    MIN_ARMENIAN_CHARS,
    ScoreResult,
    filter_western_armenian,
    is_western_armenian,
    score_text,
)

# ── Character shortcuts ────────────────────────────────────────────────────────
_a     = ARM["a"]       # ա
_g     = ARM["g"]       # կ  (WA: g / preverbal particle)
_ye    = ARM["ye"]      # ե
_i     = ARM["i"]       # ի
_vo    = ARM["vo"]      # ո
_yiwn  = ARM["yiwn"]    # ւ
_m     = ARM["m"]       # մ
_n     = ARM["n"]       # ն
_y     = ARM["y"]       # յ
_schwa = ARM["y_schwa"] # ը
_t_asp = ARM["t_asp"]   # թ
_c_asp = ARM["c_asp"]   # ց
_s     = ARM["s"]       # ս
_k_asp = ARM["k_asp"]   # ք

# Frequent digraphs
_aw = _a + _yiwn                  # աւ  — WA old-orthography /o/
_um = _vo + _yiwn + _m            # UM — EA present-participle suffix
_wa_particle = _g + _schwa        # կ+ը  — WA preverbal particle with schwa

# ── Helpers ────────────────────────────────────────────────────────────────────

def _arm_word(*keys: str) -> str:
    """Build an Armenian word from ARM key names."""
    return "".join(ARM[k] for k in keys)


class TestScoreTextReturnType(unittest.TestCase):
    """score_text must always return a well-formed ScoreResult."""

    def test_returns_score_result(self):
        result = score_text("hello")
        self.assertIsInstance(result, ScoreResult)

    def test_score_in_range(self):
        for text in ["", "hello", "abc " * 10, _aw * 5]:
            result = score_text(text)
            self.assertGreaterEqual(result.score, 0.0)
            self.assertLessEqual(result.score, 1.0)

    def test_empty_string(self):
        result = score_text("")
        self.assertEqual(result.score, 0.0)
        self.assertFalse(result.is_western_armenian)
        self.assertEqual(result.total_armenian_chars, 0)

    def test_non_armenian_text(self):
        result = score_text("This is English only text.")
        self.assertEqual(result.score, 0.0)
        self.assertFalse(result.is_western_armenian)

    def test_insufficient_armenian_chars(self):
        # Only 4 Armenian chars — below MIN_ARMENIAN_CHARS=5
        short = _a + _a + _a + _a
        result = score_text(short)
        self.assertEqual(result.score, 0.0)
        self.assertFalse(result.is_western_armenian)

    def test_matched_patterns_is_list(self):
        result = score_text(_aw * 3 + _a * 5)
        self.assertIsInstance(result.matched_patterns, list)

    def test_raw_score_field(self):
        result = score_text(_um * 3 + _a * 5)
        self.assertIsInstance(result.raw_score, float)


class TestWAPositivePatterns(unittest.TestCase):
    """Texts with WA-only markers must score > WA_THRESHOLD."""

    def _assert_wa(self, text: str, msg: str = ""):
        result = score_text(text)
        self.assertGreater(
            result.score,
            WA_THRESHOLD,
            msg=f"Expected WA score > {WA_THRESHOLD} for: {text!r}  {msg}",
        )
        self.assertTrue(result.is_western_armenian, msg=f"Expected is_WA=True for: {text!r}  {msg}")

    def test_wa_particle_apostrophe(self):
        # կ' (verb particle + apostrophe) — strong WA marker
        text = _g + "'" + _a * 5  # build a minimal context
        self._assert_wa(text, "WA particle with apostrophe")

    def test_wa_particle_apostrophe_typographic(self):
        # Same with typographic right single quotation mark U+2019
        text = _g + "\u2019" + _a * 5
        self._assert_wa(text, "WA particle with typographic apostrophe")

    def test_wa_particle_schwa(self):
        # կ+ը as used by the sentence generator
        text = _wa_particle + " " + _a * 8
        self._assert_wa(text, "WA particle with schwa")

    def test_aw_digraph(self):
        # Multiple աւ occurrences (e.g. in verb endings)
        text = _a * 3 + _aw + _a * 3 + _aw + _a * 3
        self._assert_wa(text, "WA aw-digraph")

    def test_imperfect_3sg_ending(self):
        # -եաւ ending (ye + a + yiwn)
        ending = _ye + _a + _yiwn
        text = _a * 5 + ending
        self._assert_wa(text, "WA imperfect 3sg -eaw ending")

    def test_past_aorist_3sg_ending(self):
        # -ցaW ending (c_asp + a + yiwn)
        ending = _c_asp + _a + _yiwn
        text = _a * 5 + ending
        self._assert_wa(text, "WA past-aorist 3sg ending")

    def test_genitive_oy(self):
        # -oy (vo + y) old genitive
        genitive = _vo + _y
        text = _a * 5 + genitive
        self._assert_wa(text, "WA genitive -oy")

    def test_multiple_wa_markers_combined(self):
        # Text with several WA markers → strong positive score
        text = _g + "'" + _a * 3 + _aw + _a * 3 + _ye + _a + _yiwn
        self._assert_wa(text, "multiple WA markers combined")


class TestEANegativePatterns(unittest.TestCase):
    """Texts with EA-only markers must score ≤ WA_THRESHOLD."""

    def _assert_not_wa(self, text: str, msg: str = ""):
        result = score_text(text)
        self.assertFalse(
            result.is_western_armenian,
            msg=f"Expected is_WA=False for: {text!r}  {msg}",
        )

    def test_ea_present_participle_um(self):
        # -UM suffix (ո+ւ+մ) — quintessential EA marker
        text = _a * 5 + _um
        self._assert_not_wa(text, "EA -UM suffix")

    def test_ea_inchoative_anum(self):
        # -anum (ա+ն+UM) — EA inchoative verb form
        text = _a * 3 + _n + _um
        self._assert_not_wa(text, "EA inchoative -anum")

    def test_multiple_um_suffixes(self):
        # Repeated EA marker → strongly not WA
        text = _a * 3 + _um + _a * 3 + _um
        self._assert_not_wa(text, "multiple EA -UM suffixes")


class TestMixedAndNeutralText(unittest.TestCase):
    """Edge cases: neutral text and mixed WA+EA content."""

    def test_neutral_armenian_text(self):
        # Armenian text with no distinctive WA or EA markers — neutral (≈0.5)
        neutral = _a + _n + _a + _n + _a + _n + _a + _n + _a + _n
        result = score_text(neutral)
        # Should not be classified as WA (no evidence)
        self.assertFalse(result.is_western_armenian)

    def test_wa_wins_over_single_ea_marker(self):
        # Strong WA signal overrides a single EA marker
        strong_wa = _g + "'" + _a * 3 + _aw * 3
        weak_ea = _um
        text = strong_wa + weak_ea
        result = score_text(text)
        self.assertGreater(result.score, WA_THRESHOLD)

    def test_ea_wins_over_single_wa_marker(self):
        # Strong EA signal overrides a single WA marker
        strong_ea = _um * 3 + _a * 5
        weak_wa = _aw
        text = strong_ea + weak_wa
        result = score_text(text)
        self.assertFalse(result.is_western_armenian)

    def test_custom_threshold_lower(self):
        # Lowering the threshold makes borderline text pass as WA
        text = _aw + _a * 8  # single aw-digraph
        low_threshold = 0.3
        result_low = score_text(text, threshold=low_threshold)
        result_default = score_text(text, threshold=WA_THRESHOLD)
        # With a lower threshold, the text that was borderline may be WA
        # At minimum, score should be the same either way
        self.assertEqual(result_low.score, result_default.score)
        if result_low.score > low_threshold:
            self.assertTrue(result_low.is_western_armenian)

    def test_min_chars_parameter(self):
        # Text with exactly 6 Armenian chars should pass with min_chars=5
        text = _a * 6
        result = score_text(text, min_chars=5)
        # Score of neutral text should be returned (no markers)
        self.assertEqual(result.total_armenian_chars, 6)

    def test_min_chars_blocks_short_text(self):
        text = _a * 4  # 4 chars < default min_chars=5
        result = score_text(text, min_chars=5)
        self.assertEqual(result.score, 0.0)
        self.assertFalse(result.is_western_armenian)


class TestIsWesternArmenian(unittest.TestCase):
    """is_western_armenian convenience wrapper."""

    def test_wa_text_returns_true(self):
        text = _g + "'" + _a * 3 + _aw * 2
        self.assertTrue(is_western_armenian(text))

    def test_ea_text_returns_false(self):
        text = _a * 5 + _um * 2
        self.assertFalse(is_western_armenian(text))

    def test_empty_returns_false(self):
        self.assertFalse(is_western_armenian(""))

    def test_custom_threshold(self):
        # Neutral text (score ≈ 0.5) should pass with threshold=0.4
        text = _aw * 2 + _a * 8  # mild WA signal
        result = score_text(text)
        expected = result.score > 0.4
        self.assertEqual(is_western_armenian(text, threshold=0.4), expected)


class TestFilterWesternArmenian(unittest.TestCase):
    """filter_western_armenian batch helper."""

    def test_empty_list(self):
        self.assertEqual(filter_western_armenian([]), [])

    def test_all_wa(self):
        wa_text = _g + "'" + _a * 3 + _aw * 2
        texts = [wa_text, wa_text]
        results = filter_western_armenian(texts)
        self.assertEqual(len(results), 2)
        for idx, text, result in results:
            self.assertTrue(result.is_western_armenian)

    def test_all_ea(self):
        ea_text = _a * 5 + _um * 2
        texts = [ea_text, ea_text]
        results = filter_western_armenian(texts)
        self.assertEqual(results, [])

    def test_mixed_list(self):
        wa_text = _g + "'" + _a * 3 + _aw * 2
        ea_text = _a * 5 + _um * 2
        texts = [wa_text, ea_text, wa_text]
        results = filter_western_armenian(texts)
        # Only the two WA texts should pass
        self.assertEqual(len(results), 2)
        # Original indices should be preserved
        indices = [r[0] for r in results]
        self.assertIn(0, indices)
        self.assertIn(2, indices)
        self.assertNotIn(1, indices)

    def test_original_index_preserved(self):
        texts = ["no armenian", _a * 5 + _um, _g + "'" + _a * 3 + _aw]
        results = filter_western_armenian(texts)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], 2)  # original index 2

    def test_text_preserved_in_result(self):
        wa_text = _g + "'" + _a * 3 + _aw * 2
        results = filter_western_armenian([wa_text])
        self.assertEqual(results[0][1], wa_text)


class TestScoreConsistency(unittest.TestCase):
    """Score must be deterministic and consistent."""

    def test_deterministic(self):
        text = _g + "'" + _a * 3 + _aw
        result1 = score_text(text)
        result2 = score_text(text)
        self.assertEqual(result1.score, result2.score)

    def test_more_wa_markers_higher_score(self):
        few = _g + "'" + _a * 5
        many = (_g + "'" + _a * 3) * 4
        result_few = score_text(few)
        result_many = score_text(many)
        self.assertGreater(result_many.score, result_few.score)

    def test_more_ea_markers_lower_score(self):
        few_ea = _a * 5 + _um
        many_ea = _a * 5 + _um * 4
        result_few = score_text(few_ea)
        result_many = score_text(many_ea)
        self.assertLess(result_many.score, result_few.score)

    def test_score_clamped_to_unit_interval(self):
        # Extreme WA text should not exceed 1.0
        extreme = (_g + "'" + _a * 2 + _aw + _ye + _a + _yiwn) * 20
        result = score_text(extreme)
        self.assertLessEqual(result.score, 1.0)
        self.assertGreaterEqual(result.score, 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
