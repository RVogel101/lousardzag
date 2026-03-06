"""Unit tests for rule-based dialect classifier.

All Armenian strings used below come from internal project documentation/code
(e.g., CLASSICAL_ORTHOGRAPHY_GUIDE.md and morphology modules).
"""

from lousardzag.dialect_classifier import (
    classify_text_dialect,
    classify_vocab_and_sentences,
)


def test_classical_iywn_is_western_signal():
    result = classify_text_dialect("գիւղ")
    assert result.label == "likely_western"
    assert result.western_score > result.eastern_score


def test_reformed_spelling_is_eastern_signal():
    result = classify_text_dialect("գյուղ")
    assert result.label == "likely_eastern"
    assert result.eastern_score > result.western_score


def test_western_indefinite_article_marker():
    result = classify_text_dialect("տուն մը")
    assert result.label == "likely_western"
    assert any(hit.rule_id == "WA_INDEF_ARTICLE_MEH" for hit in result.evidence)


def test_western_future_particle_marker():
    result = classify_text_dialect("պիտի")
    assert result.label == "likely_western"
    assert any(hit.rule_id == "WA_FUTURE_PARTICLE_BIDI" for hit in result.evidence)


def test_unknown_text_stays_inconclusive():
    result = classify_text_dialect("unknown-token")
    assert result.label == "inconclusive"
    assert result.western_score == 0
    assert result.eastern_score == 0


def test_batch_summary_counts():
    payload = classify_vocab_and_sentences(
        vocab=["գիւղ", "գյուղ"],
        sentences=["պիտի", "unknown-token"],
    )

    counts = payload["summary"]["counts"]
    assert counts["likely_western"] >= 2
    assert counts["likely_eastern"] >= 1
    assert counts["inconclusive"] >= 1
