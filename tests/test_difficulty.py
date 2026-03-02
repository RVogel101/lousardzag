"""
Tests for morphological and phonological difficulty analysis.
"""

import unittest

from armenian_anki.morphology.core import ARM
from armenian_anki.morphology.difficulty import (
    count_syllables_with_context,
    score_noun_difficulty,
    score_verb_difficulty,
    score_word_difficulty,
    analyze_word,
    _score_rare_phonemes,
    _score_consonant_clusters,
)


class TestHiddenVowelCounting(unittest.TestCase):
    """Test syllable counting with grammatical vowels."""

    def test_basic_syllable_count(self):
        """Basic counting without grammatical vowels."""
        # Single syllable
        self.assertEqual(count_syllables_with_context(ARM["a"], with_grammatical_vowels=False), 1)
        # Two syllables
        mama = ARM["m"] + ARM["a"] + ARM["m"] + ARM["a"]
        self.assertEqual(count_syllables_with_context(mama, with_grammatical_vowels=False), 2)

    def test_with_hidden_vowels(self):
        """Test that hidden vowels (ը) count in grammatical contexts."""
        # Word ending in stem + schwa + suffix pattern
        # ե.ր+ք (երք) = "day" + suffix, has hidden vowel context
        word_with_schwa = ARM["ye"] + ARM["r"] + ARM["y_schwa"] + ARM["k"]
        count_base = count_syllables_with_context(word_with_schwa, with_grammatical_vowels=False)
        count_with_grammar = count_syllables_with_context(word_with_schwa, with_grammatical_vowels=True)
        # Should count higher with grammatical vowels
        self.assertGreaterEqual(count_with_grammar, count_base)


class TestPhonologicalScoring(unittest.TestCase):
    """Test phoneme rarity scoring."""

    def test_rare_fricatives(self):
        """Fricatives like ժ (zh) increase difficulty."""
        # ժամ (jam) — "hour"
        jam = ARM["zh"] + ARM["a"] + ARM["m"]
        score = _score_rare_phonemes(jam)
        self.assertGreater(score, 0.0)

    def test_affricates(self):
        """Affricates like ծ (ts) increase difficulty."""
        # ծանուցել — note the ts sound
        word = ARM["ts"] + ARM["a"] + ARM["n"]
        score = _score_rare_phonemes(word)
        self.assertGreater(score, 0.0)

    def test_common_consonants(self):
        """Words with common sounds have low phonological score."""
        # մեր (mer) — "our"
        mer = ARM["m"] + ARM["ye"] + ARM["r"]
        score = _score_rare_phonemes(mer)
        self.assertEqual(score, 0.0)  # No rare phonemes


class TestConsonantClusters(unittest.TestCase):
    """Test consonant cluster complexity scoring."""

    def test_simple_cv(self):
        """Simple CV syllables have no cluster penalty."""
        # մա (ma)
        ma = ARM["m"] + ARM["a"]
        score = _score_consonant_clusters(ma)
        self.assertEqual(score, 0.0)

    def test_double_consonants(self):
        """Double consonants should increase score."""
        # Word with consonant cluster
        word = ARM["m"] + ARM["n"] + ARM["a"]  # mna (consonant cluster)
        score = _score_consonant_clusters(word)
        self.assertGreater(score, 0.0)


class TestNounDifficulty(unittest.TestCase):
    """Test noun difficulty scoring."""

    def test_regular_noun_i_class(self):
        """Regular i-class nouns have lower difficulty."""
        # մեղ (megh) — "sin"
        megh = ARM["m"] + ARM["ye"] + ARM["gh"]
        score = score_noun_difficulty(megh, declension_class="i_class")
        self.assertLess(score, 3.0)  # Should be relatively easy

    def test_irregular_noun_o_class(self):
        """Irregular o-class nouns have higher difficulty."""
        word = ARM["h"] + ARM["a"] + ARM["y"] + ARM["r"]
        score_regular = score_noun_difficulty(word, declension_class="i_class")
        score_irregular = score_noun_difficulty(word, declension_class="o_class")
        self.assertGreater(score_irregular, score_regular)

    def test_multisyllabic_noun(self):
        """Longer words have higher difficulty."""
        # Single syllable
        short = ARM["m"] + ARM["a"]
        score_short = score_noun_difficulty(short, declension_class="i_class")
        # Three syllables
        long = ARM["m"] + ARM["a"] + ARM["m"] + ARM["a"] + ARM["n"] + ARM["a"] + ARM["n"]
        score_long = score_noun_difficulty(long, declension_class="i_class")
        self.assertGreater(score_long, score_short)


class TestVerbDifficulty(unittest.TestCase):
    """Test verb difficulty scoring."""

    def test_weak_verb(self):
        """Weak verbs have low difficulty."""
        word = ARM["g"] + ARM["a"] + ARM["l"]
        score = score_verb_difficulty(word, verb_class="weak")
        # Should be relatively low but > 0
        self.assertGreater(score, 0.0)
        self.assertLess(score, 5.0)

    def test_irregular_verb(self):
        """Irregular verbs have high difficulty."""
        word = ARM["g"] + ARM["a"] + ARM["l"]
        score_weak = score_verb_difficulty(word, verb_class="weak")
        score_irregular = score_verb_difficulty(word, verb_class="irregular")
        self.assertGreater(score_irregular, score_weak)


class TestCompositeScoring(unittest.TestCase):
    """Test overall word difficulty scoring."""

    def test_generic_noun(self):
        """Score generic words by POS."""
        # Simple noun
        word = ARM["m"] + ARM["a"]
        score = score_word_difficulty(word, pos="noun")
        self.assertGreater(score, 0.0)
        self.assertLess(score, 10.0)

    def test_noun_with_class(self):
        """Noun with declension class info."""
        word = ARM["m"] + ARM["a"]
        score = score_word_difficulty(word, pos="noun", declension_class="i_class")
        self.assertGreater(score, 0.0)

    def test_verb_with_class(self):
        """Verb with conjugation class info."""
        word = ARM["g"] + ARM["a"] + ARM["l"]
        score = score_word_difficulty(word, pos="verb", verb_class="weak")
        self.assertGreater(score, 0.0)


class TestWordAnalysis(unittest.TestCase):
    """Test complete word analysis."""

    def test_analysis_creates_record(self):
        """analyze_word() creates a complete analysis record."""
        word = ARM["m"] + ARM["a"]
        analysis = analyze_word(word, pos="noun", declension_class="i_class")

        self.assertEqual(analysis.word, word)
        self.assertEqual(analysis.pos, "noun")
        self.assertGreater(analysis.syllables_base, 0)
        self.assertGreater(analysis.overall_difficulty, 0.0)
        self.assertLessEqual(analysis.overall_difficulty, 10.0)

    def test_analysis_summary(self):
        """analyze_word() produces a readable summary."""
        word = ARM["m"] + ARM["a"]
        analysis = analyze_word(word, pos="noun", declension_class="i_class")
        summary = analysis.summary()
        # Should contain word, POS, and scores
        self.assertIn("noun", summary)
        self.assertIn("difficulty", summary)


if __name__ == "__main__":
    unittest.main()
