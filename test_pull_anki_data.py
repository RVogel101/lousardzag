#!/usr/bin/env python3
"""
Tests for _pull_anki_data and armenian_anki.dialect_scorer.

Run with:  python test_pull_anki_data.py
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(__file__))

from armenian_anki.dialect_scorer import (
    DialectScore,
    WA_THRESHOLD,
    EA_THRESHOLD,
    classify_text,
    filter_western,
    score_text,
)
from _pull_anki_data import (
    extract_audio_filenames,
    extract_image_filenames,
    extract_media_from_note,
    pull_deck,
    save_csv,
    save_json,
    score_note,
    _flatten_note,
)


# ─── dialect_scorer tests ─────────────────────────────────────────────────────

class TestDialectScorer(unittest.TestCase):

    # ── score_text: empty / trivial inputs ──────────────────────────────────

    def test_empty_string_is_ambiguous(self):
        ds = score_text("")
        self.assertEqual(ds.label, "ambiguous")
        self.assertEqual(ds.normalised_score, 0.0)
        self.assertEqual(ds.matched_markers, [])

    def test_whitespace_only_is_ambiguous(self):
        ds = score_text("   \t\n  ")
        self.assertEqual(ds.label, "ambiguous")

    def test_no_markers_is_ambiguous(self):
        ds = score_text("hello world this has no armenian markers")
        self.assertEqual(ds.label, "ambiguous")

    # ── score_text: Western Armenian markers ──────────────────────────────────

    def test_kuh_particle_straight_apostrophe_is_western(self):
        # կ' (kuh) particle with straight apostrophe — strong WA marker
        ds = score_text("կ'utem indz")
        self.assertEqual(ds.label, "western")
        self.assertGreater(ds.normalised_score, 0.0)

    def test_kuh_particle_curly_apostrophe_is_western(self):
        # κ' with U+2019 right single quotation mark
        ds = score_text("կ\u2019eri anor")
        self.assertEqual(ds.label, "western")

    def test_wa_ull_construction_is_western(self):
        # կ'ulla — WA "will become"
        ds = score_text("կ\u2019ullam yes")
        self.assertEqual(ds.label, "western")

    def test_wa_negation_particle_is_western(self):
        # չ' — WA contracted negation
        ds = score_text("չ\u2019eni")
        self.assertGreater(ds.normalised_score, 0.0)

    # ── score_text: Eastern Armenian markers ─────────────────────────────────

    def test_oom_em_construction_is_eastern(self):
        # "-oom em" = EA present progressive
        ds = score_text("kardom em")
        self.assertEqual(ds.label, "eastern")
        self.assertLess(ds.normalised_score, 0.0)

    def test_ea_perfect_el_em_is_eastern(self):
        # «... el em» = EA perfect
        ds = score_text("groum el em anor")
        self.assertLess(ds.normalised_score, 0.0)

    def test_ea_eka_word_is_eastern(self):
        ds = score_text("yes eka tun")
        self.assertLess(ds.normalised_score, 0.0)

    # ── DialectScore properties ───────────────────────────────────────────────

    def test_is_western_property(self):
        ds = score_text("կ'eri")
        self.assertTrue(ds.is_western)
        self.assertFalse(ds.is_eastern)
        self.assertFalse(ds.is_ambiguous)

    def test_is_eastern_property(self):
        ds = score_text("kardom em")
        self.assertTrue(ds.is_eastern)
        self.assertFalse(ds.is_western)

    def test_token_count_populated(self):
        ds = score_text("one two three four")
        self.assertEqual(ds.token_count, 4)

    def test_matched_markers_not_empty_when_match(self):
        ds = score_text("կ'eri")
        self.assertGreater(len(ds.matched_markers), 0)

    def test_normalised_score_clamped_positive(self):
        # Many WA markers should clamp at +1.0
        many_wa = " ".join(["կ'eri"] * 50)
        ds = score_text(many_wa)
        self.assertLessEqual(ds.normalised_score, 1.0)
        self.assertGreaterEqual(ds.normalised_score, -1.0)

    def test_normalised_score_clamped_negative(self):
        many_ea = " ".join(["kardom em"] * 50)
        ds = score_text(many_ea)
        self.assertLessEqual(ds.normalised_score, 1.0)
        self.assertGreaterEqual(ds.normalised_score, -1.0)

    # ── classify_text ─────────────────────────────────────────────────────────

    def test_classify_text_returns_string(self):
        label = classify_text("կ'eri")
        self.assertIn(label, ("western", "eastern", "ambiguous"))

    def test_classify_text_western(self):
        self.assertEqual(classify_text("կ'eri"), "western")

    def test_classify_text_eastern(self):
        self.assertEqual(classify_text("kardom em"), "eastern")

    def test_classify_text_ambiguous(self):
        self.assertEqual(classify_text("just some latin text"), "ambiguous")

    # ── filter_western ────────────────────────────────────────────────────────

    def test_filter_western_keeps_wa(self):
        texts = ["կ'eri", "kardom em", "just ambiguous"]
        kept = filter_western(texts, include_ambiguous=False)
        labels = [ds.label for _, _, ds in kept]
        self.assertNotIn("eastern", labels)
        self.assertNotIn("ambiguous", labels)

    def test_filter_western_include_ambiguous(self):
        texts = ["կ'eri", "kardom em", "just ambiguous"]
        kept = filter_western(texts, include_ambiguous=True)
        labels = {ds.label for _, _, ds in kept}
        self.assertNotIn("eastern", labels)

    def test_filter_western_preserves_original_index(self):
        texts = ["kardom em", "կ'eri", "kardom em"]
        kept = filter_western(texts)
        indices = [idx for idx, _, _ in kept]
        self.assertIn(1, indices)   # index 1 is the WA text
        self.assertNotIn(0, indices)
        self.assertNotIn(2, indices)

    def test_filter_western_empty_input(self):
        self.assertEqual(filter_western([]), [])

    def test_filter_western_returns_score_objects(self):
        texts = ["կ'eri"]
        result = filter_western(texts)
        self.assertIsInstance(result[0][2], DialectScore)


# ─── Media parsing tests ──────────────────────────────────────────────────────

class TestMediaParsing(unittest.TestCase):

    def test_extract_audio_single(self):
        self.assertEqual(
            extract_audio_filenames("[sound:pronunciation.mp3]"),
            ["pronunciation.mp3"],
        )

    def test_extract_audio_multiple(self):
        val = "[sound:a.mp3] some text [sound:b.ogg]"
        self.assertEqual(extract_audio_filenames(val), ["a.mp3", "b.ogg"])

    def test_extract_audio_none(self):
        self.assertEqual(extract_audio_filenames("no audio here"), [])

    def test_extract_image_single(self):
        self.assertEqual(
            extract_image_filenames('<img src="photo.jpg">'),
            ["photo.jpg"],
        )

    def test_extract_image_single_quotes(self):
        self.assertEqual(
            extract_image_filenames("<img src='photo.png'>"),
            ["photo.png"],
        )

    def test_extract_image_with_extra_attrs(self):
        val = '<img class="card-img" src="word.gif" alt="word">'
        self.assertEqual(extract_image_filenames(val), ["word.gif"])

    def test_extract_image_none(self):
        self.assertEqual(extract_image_filenames("no images"), [])

    def test_extract_media_from_note(self):
        note = {
            "fields": {
                "Word": {"value": "[sound:word.mp3]"},
                "Image": {"value": '<img src="picture.jpg">'},
                "Sentence": {"value": "some text"},
            }
        }
        media = extract_media_from_note(note)
        self.assertIn("word.mp3", media["audio"])
        self.assertIn("picture.jpg", media["images"])

    def test_extract_media_deduplicates(self):
        note = {
            "fields": {
                "F1": {"value": "[sound:same.mp3]"},
                "F2": {"value": "[sound:same.mp3]"},
            }
        }
        media = extract_media_from_note(note)
        self.assertEqual(media["audio"].count("same.mp3"), 1)

    def test_extract_media_empty_note(self):
        media = extract_media_from_note({})
        self.assertEqual(media["audio"], [])
        self.assertEqual(media["images"], [])


# ─── score_note tests ─────────────────────────────────────────────────────────

class TestScoreNote(unittest.TestCase):

    def test_score_note_returns_dialect_score(self):
        note = {"fields": {"Word": {"value": "կ'eri"}}}
        ds = score_note(note)
        self.assertIsInstance(ds, DialectScore)

    def test_score_note_strips_html(self):
        # HTML tags should not confuse the scorer
        note = {"fields": {"Word": {"value": "<b>կ'eri</b>"}}}
        ds = score_note(note)
        self.assertEqual(ds.label, "western")

    def test_score_note_strips_anki_audio_tags(self):
        note = {"fields": {"Audio": {"value": "[sound:word.mp3]"}}}
        # "[sound:...]" should not produce false positive markers
        ds = score_note(note)
        self.assertIsInstance(ds, DialectScore)

    def test_score_note_empty_fields(self):
        note = {"fields": {}}
        ds = score_note(note)
        self.assertEqual(ds.label, "ambiguous")


# ─── pull_deck tests (with mocked AnkiConnect) ───────────────────────────────

def _make_mock_note(note_id: int, word: str, audio: str = "", image: str = "") -> dict:
    """Build a minimal fake AnkiConnect notesInfo dict."""
    word_value = word
    if audio:
        word_value += f" [sound:{audio}]"
    img_value = f'<img src="{image}">' if image else ""
    return {
        "noteId": note_id,
        "modelName": "TestModel",
        "tags": ["test"],
        "fields": {
            "Word": {"value": word_value, "order": 0},
            "Image": {"value": img_value, "order": 1},
        },
    }


class TestPullDeck(unittest.TestCase):

    def _make_anki(self, notes: list[dict]) -> MagicMock:
        anki = MagicMock()
        anki.find_notes.return_value = [n["noteId"] for n in notes]
        anki.notes_info.return_value = notes
        return anki

    def test_pull_deck_returns_enriched_notes(self):
        notes = [_make_mock_note(1, "test word")]
        anki = self._make_anki(notes)
        result = pull_deck("Test Deck", anki)
        self.assertEqual(len(result), 1)
        self.assertIn("media", result[0])
        self.assertIn("dialect", result[0])

    def test_pull_deck_empty_deck(self):
        anki = MagicMock()
        anki.find_notes.return_value = []
        result = pull_deck("Empty Deck", anki)
        self.assertEqual(result, [])

    def test_pull_deck_includes_audio_in_media(self):
        notes = [_make_mock_note(1, "hello", audio="word.mp3")]
        anki = self._make_anki(notes)
        result = pull_deck("Test Deck", anki)
        self.assertIn("word.mp3", result[0]["media"]["audio"])

    def test_pull_deck_includes_image_in_media(self):
        notes = [_make_mock_note(1, "hello", image="pic.jpg")]
        anki = self._make_anki(notes)
        result = pull_deck("Test Deck", anki)
        self.assertIn("pic.jpg", result[0]["media"]["images"])

    def test_pull_deck_filter_western_drops_eastern(self):
        wa_note = _make_mock_note(1, "կ'eri")
        ea_note = _make_mock_note(2, "kardom em")
        notes = [wa_note, ea_note]
        anki = self._make_anki(notes)
        result = pull_deck("Test Deck", anki, filter_western=True)
        note_ids = [n["noteId"] for n in result]
        self.assertIn(1, note_ids)
        self.assertNotIn(2, note_ids)

    def test_pull_deck_filter_western_include_ambiguous(self):
        wa_note = _make_mock_note(1, "կ'eri")
        ambiguous_note = _make_mock_note(2, "just some text")
        ea_note = _make_mock_note(3, "kardom em")
        notes = [wa_note, ambiguous_note, ea_note]
        anki = self._make_anki(notes)

        result_without = pull_deck("T", anki, filter_western=True, include_ambiguous=False)
        result_with = pull_deck("T", anki, filter_western=True, include_ambiguous=True)

        ids_without = {n["noteId"] for n in result_without}
        ids_with = {n["noteId"] for n in result_with}

        self.assertNotIn(3, ids_without)   # EA always excluded
        self.assertNotIn(3, ids_with)      # EA always excluded
        self.assertIn(2, ids_with)         # ambiguous kept when requested
        self.assertNotIn(2, ids_without)   # ambiguous excluded by default

    def test_pull_deck_dialect_field_present(self):
        notes = [_make_mock_note(1, "test")]
        anki = self._make_anki(notes)
        result = pull_deck("Test", anki)
        dialect = result[0]["dialect"]
        self.assertIn("label", dialect)
        self.assertIn("score", dialect)
        self.assertIn("matched_markers", dialect)

    def test_pull_deck_downloads_media_when_dir_given(self):
        notes = [_make_mock_note(1, "hello", audio="word.mp3")]
        anki = self._make_anki(notes)
        anki.retrieve_media_file.return_value = b"fake audio data"

        with tempfile.TemporaryDirectory() as tmpdir:
            media_dir = Path(tmpdir) / "media"
            pull_deck("Test", anki, media_dir=media_dir)
            saved = media_dir / "word.mp3"
            self.assertTrue(saved.exists())
            self.assertEqual(saved.read_bytes(), b"fake audio data")

    def test_pull_deck_handles_missing_media_gracefully(self):
        notes = [_make_mock_note(1, "hello", audio="missing.mp3")]
        anki = self._make_anki(notes)
        anki.retrieve_media_file.return_value = None  # file not found in Anki

        with tempfile.TemporaryDirectory() as tmpdir:
            media_dir = Path(tmpdir) / "media"
            # Should not raise
            result = pull_deck("Test", anki, media_dir=media_dir)
            self.assertEqual(len(result), 1)


# ─── Export tests ─────────────────────────────────────────────────────────────

class TestExport(unittest.TestCase):

    def _sample_notes(self) -> list[dict]:
        return [
            {
                "noteId": 1,
                "modelName": "TestModel",
                "tags": ["tag1"],
                "fields": {"Word": {"value": "test", "order": 0}},
                "media": {"audio": ["a.mp3"], "images": []},
                "dialect": {"label": "ambiguous", "score": 0.0, "matched_markers": []},
            }
        ]

    def test_save_json_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "out.json"
            save_json(self._sample_notes(), out)
            self.assertTrue(out.exists())
            loaded = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0]["noteId"], 1)

    def test_save_csv_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "out.csv"
            save_csv(self._sample_notes(), out)
            self.assertTrue(out.exists())
            content = out.read_text(encoding="utf-8")
            self.assertIn("note_id", content)
            self.assertIn("1", content)

    def test_flatten_note_has_field_prefix(self):
        note = {
            "noteId": 5,
            "modelName": "M",
            "tags": [],
            "fields": {"Word": {"value": "hello"}, "Trans": {"value": "world"}},
            "media": {"audio": [], "images": []},
            "dialect": {"label": "ambiguous", "score": 0.0, "matched_markers": []},
        }
        flat = _flatten_note(note)
        self.assertIn("field_Word", flat)
        self.assertIn("field_Trans", flat)
        self.assertEqual(flat["field_Word"], "hello")

    def test_flatten_note_joins_tags(self):
        note = {
            "noteId": 5, "modelName": "M",
            "tags": ["a", "b", "c"],
            "fields": {},
            "media": {"audio": [], "images": []},
            "dialect": {"label": "ambiguous", "score": 0.0, "matched_markers": []},
        }
        flat = _flatten_note(note)
        self.assertEqual(flat["tags"], "a b c")

    def test_flatten_note_joins_media_with_pipe(self):
        note = {
            "noteId": 5, "modelName": "M", "tags": [],
            "fields": {},
            "media": {"audio": ["a.mp3", "b.mp3"], "images": ["x.jpg"]},
            "dialect": {"label": "ambiguous", "score": 0.0, "matched_markers": []},
        }
        flat = _flatten_note(note)
        self.assertEqual(flat["media_audio"], "a.mp3|b.mp3")
        self.assertEqual(flat["media_images"], "x.jpg")

    def test_save_json_empty_notes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "empty.json"
            save_json([], out)
            self.assertTrue(out.exists())
            loaded = json.loads(out.read_text())
            self.assertEqual(loaded, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
