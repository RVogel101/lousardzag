# CHANGELOG

All notable changes to this project are documented here. This follows the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format.

## [0.4.0] - 2026-03-03 (Letter Cards & TTS Audio)

### ✨ Added

- **Armenian Letter Card System**
  - `letter_data.py` — Comprehensive data for all 38 Armenian letters (phonetics, examples, difficulty)
  - `letter_practice.py` — Interactive letter practice and quiz modules
  - `letter_progression.py` — Difficulty-aware letter learning progression
  - `letter_audio.py` — Letter audio generation and management
  - Anki card templates: `letter_cards/`, `letter_visual/` (front/back HTML + CSS)

- **Western Armenian TTS Audio Generation**
  - `07-tools/generate_vocab_audio_mms.py` — Production audio script using Meta MMS
  - Model: `facebook/mms-tts-hyw` (Western Armenian specific, VITS architecture)
  - **3-pass denoising**: Generate audio 3 times, pad to equal length, average — reduces synthesis artifacts
  - Speed tuning: 0.90x via librosa `time_stretch()` for natural pacing
  - Post-processing: `minimal_declick()` — 50Hz high-pass + 3-tap median filter
  - Generated production audio for 10 vocabulary words (16kHz WAV)

- **Interactive Audio Comparison Tool**
  - `03-cli/letter_cards_viewer.py` — Flask web viewer (localhost:5001)
  - `/vocab` page for vocabulary audio triage
  - `/compare` page for A/B testing TTS variants (espeak-ng vs MMS vs neural)
  - Comparison groups: espeak-ng, MMS natural/slow, 3-pass/5-pass denoised, enhanced variants

- **Anki Card Templates**
  - `noun_declension/` — Noun declension card template (front/back)
  - `verb_conjugation/` — Verb conjugation card template (front/back)
  - `vocab_sentences/` — Vocabulary sentences card template (front/back)

### 🔧 Changed

- Updated `.gitignore` to exclude audio data directories (`audio_comparison/`, `letter_audio/`, `vocab_audio/`, `letter_audio_ipa_test/`)
- Consolidated TTS scripts — removed obsolete generation experiments (`07-tools/generation/`)
- Updated `phonetics.py` with minor improvements

### 🧪 TTS Evaluation Summary

| Engine | Result |
|--------|--------|
| espeak-ng | Correct pronunciation, robotic quality |
| Bark (suno/bark) | Gibberish — no Armenian training data |
| Coqui XTTS v2 | Gibberish — no Armenian training data |
| Google Cloud TTS | Armenian not in 63 supported languages |
| Meta MMS (hyw) | ✅ Natural, intelligible Western Armenian |

---

## [0.3.0] - 2026-03-02 (Lousardzag Rebrand)

### ✨ Changed (Major)

- **Project Renamed**: "Armenian Anki Note Generation Pipelines" → "**Lousardzag**" (Լուսարձակ)
  - New package name: `lousardzag` (formerly `armenian_anki`)
  - New CLI scripts: `lousardzag-*` (formerly `anki-*`)
  - Better reflects expanded scope as a comprehensive Western Armenian learning platform
  - Meaning: "Light-spreading" or "Dawn-bringer" in Western Armenian

### 📝 Documentation

- **New**: [REBRANDING.md](01-docs/REBRANDING.md) — Technical implementation details of rebrand
- **New**: [NAME-HISTORY.md](01-docs/NAME-HISTORY.md) — Decision process, name research, and historical context
- **New**: [SESSION-SUMMARY.md](01-docs/SESSION-SUMMARY.md) — Complete work log for March 2, 2026 session
- **Updated**: [README.md](README.md) — Comprehensive rewrite with new name and unified feature list
- **Updated**: [.github/copilot-instructions.md](.github/copilot-instructions.md) — Project name and references

### 🔄 Migration Guide

**For users with existing installations:**

```bash
# Update imports
from armenian_anki.morphology import ...   # OLD
from lousardzag.morphology import ...      # NEW

# Update CLI commands
anki-generate-cards ...      # OLD
lousardzag-generate-cards ... # NEW

anki-preview-server          # OLD
lousardzag-preview-server    # NEW
```

**For GitHub users:**

When the repository is renamed to `lousardzag`, update your clone:
```bash
git remote set-url origin https://github.com/yourusername/lousardzag.git
```

### 🎯 No Functionality Changes

- All 323 tests passing
- No breaking changes in library API
- Only package name, imports, and documentation affected
- Completely backward-compatible after import updates

---

## [0.2.0] - 2026-02-18 (Project Restructuring)

### ✨ Added

- **Directory Structure**: 8-part organization system (01-docs through 08-data)
  - `01-docs/` — Documentation and references
  - `02-src/` — Source packages (armenian_anki, wa_corpus)
  - `03-cli/` — Command-line interfaces
  - `04-tests/` — Test suite
  - Configuration moved to `02-src/lousardzag/` (consolidated)
  - `06-notebooks/` — Jupyter notebooks
  - `07-tools/` — Utility scripts
  - `08-data/` — Data outputs

- **Build System**: Modern pyproject.toml with setuptools configuration
  - Package discovery
  - Dependency management
  - Tool configurations (pytest, black, isort, mypy)

- **Documentation**: PROJECT-RESTRUCTURING.md explaining new layout

### 🔧 Changed

- All path references updated across 7+ configuration files
- CLI scripts updated to use new directory structure
- Test configuration updated to reflect new locations

### ✅ Validated

- All tests passing (323 total) with new structure
- CLI scripts working correctly with new paths
- Complete git history preserved

---

## [0.1.0] - 2025-12-01 (Initial Release)

### ✨ Features

- **Morphological Analysis**
  - Noun declension (8 cases)
  - Verb conjugation (15 tenses)
  - Irregular verb handling
  - Schwa epenthesis detection
  - Syllable counting

- **Progression System**
  - Vocabulary batching (20 words/batch)
  - Level-based difficulty (20 levels)
  - Syllable constraints by level
  - Prerequisite tracking
  - Bootstrap vocabulary (36 core words)

- **Corpus Tools**
  - Newspaper scraper (Asbarez, Aztag, Nor Gyank)
  - Internet Archive scraper (PDF → text extraction)
  - Nayiri dictionary scraper (polite rate limiting)
  - Frequency analysis and tokenization

- **Flashcard Generation**
  - Context-aware sentence generation
  - Vocabulary dependency management
  - Ordered card progression
  - HTML preview generation
  - Multiple export formats

- **Anki Integration**
  - AnkiConnect API support
  - Read-only card import
  - Deck management
  - Profile support

- **Testing**
  - 323 comprehensive tests
  - Unit and integration test coverage
  - Pytest with conftest configuration

### 📚 Documentation

- README.md with usage instructions
- Inline code documentation
- corpus-sources.md documenting translation sources
- Configuration examples

---

## Documentation

- See individual `.md` files in `01-docs/` for detailed documentation
- Latest session work: [SESSION-SUMMARY.md](01-docs/SESSION-SUMMARY.md)
- Rebranding details: [REBRANDING.md](01-docs/REBRANDING.md)
- Name decision process: [NAME-HISTORY.md](01-docs/NAME-HISTORY.md)

---

## Support

For issues, questions, or contributions related to this project, see the documentation in `01-docs/`.

---

**Current Version**: 0.3.0 (Lousardzag Rebrand)  
**Last Updated**: March 2, 2026  
**Package Name**: `lousardzag`  
**Python**: 3.10+  
**License**: MIT
