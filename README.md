# CWAS Facebook Image Scraping & OCR Pipeline

A pipeline for scraping images from the [Centre for Western Armenian Studies](https://www.facebook.com/) Facebook page, extracting Armenian and English text via OCR, and preparing the data for Anki flashcard generation.

## Overview

The project has three main stages:

1. **Scrape** — Download full-resolution images from the CWAS Facebook photos page using Selenium.
2. **Extract** — Run Tesseract OCR on each image to extract Armenian and English text.
3. **Explore** — Categorise and clean the extracted text in a Jupyter notebook for Anki import.

## Project Structure

| File | Description |
|---|---|
| `scrape_fb_images.py` | Facebook image scraper (Selenium + Chrome). Scrolls the photo grid, visits each photo page, and downloads full-resolution images via parallel workers. |
| `extract_image_text_simple.py` | Tesseract OCR extraction with multiple preprocessing variants, PSM modes, and Armenian-specific post-processing corrections. |
| `main_coordinator.py` | Orchestrates the full pipeline — scraping → OCR extraction → CSV/pickle export. |
| `exloration.ipynb` | Jupyter notebook for exploring, cleaning, and categorising extracted text (Etymology, Word Breakdown, Example, Declension, etc.). |
| `logging_config.py` | Shared logging configuration with session-based log files. |
| `test_ocr_setup.py` | Verifies Tesseract installation and language pack availability. |
| `test_date_extraction.py` | Tests date extraction from Facebook photo pages. |
| `_pull_anki_data.py` | Pull notes (including audio / image media) from an Anki deck via AnkiConnect; optionally filter by Western Armenian dialect score. |
| `generate_anki_cards.py` | Generate Armenian morphology cards (declensions, conjugations, sentences) and push them to Anki. |
| `armenian_anki/dialect_scorer.py` | Western Armenian dialect scorer — scores text on a [-1, +1] scale (positive = Western Armenian, negative = Eastern Armenian). |

### Directories

| Directory | Contents |
|---|---|
| `FB-UK-CWAS-Content/` | Downloaded images (CWAS_{number}_{date}.jpg) |
| `extracted_text_simple/` | OCR output (CSV, JSON, pickle) |
| `logs/` | Session and debug log files |

## Requirements

- **Python 3.10+**
- **Google Chrome** + matching ChromeDriver
- **Tesseract OCR** with Armenian (`hye`) and English (`eng`) language packs
  - Windows: install from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki)

### Python Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements_ocr.txt
```

Key packages: `selenium`, `pytesseract`, `opencv-python`, `pillow`, `pandas`, `psutil`

## Usage

### 1. Scrape Images

```bash
python scrape_fb_images.py
```

Launches Chrome, logs in to Facebook (uses an existing session cookie), scrolls through the CWAS photos page, and downloads full-resolution images to `FB-UK-CWAS-Content/`.

### 2. Extract Text (OCR)

```bash
python extract_image_text_simple.py
```

Processes all images with Tesseract OCR using `eng+hye` language mode, multiple preprocessing variants (grayscale, denoised, binary, adaptive, morphological, contrast-enhanced, sharpened), and multiple PSM modes. Results are saved as CSV, JSON, and pickle.

### 3. Explore & Categorise

Open `exloration.ipynb` in Jupyter/VS Code and run the cells to:

- Load and clean the extracted text (remove copyright notices, headers)
- Categorise entries: Etymology, Word Breakdown, Phrasal Breakdown, Example, Declension, Conjugation, Conjunction, etc.
- Split combined Declension-Example cards into separate rows

### Full Pipeline

```bash
python main_coordinator.py
```

Runs scraping and extraction end-to-end.

## Card Categories

The CWAS "Word of the Day" images fall into these categories:

| Category | Description |
|---|---|
| Etymology | Word origin and history |
| Word Breakdown | Morphological analysis of a single word |
| Phrasal Breakdown | Analysis of a phrase or expression |
| Example | Usage example with Armenian sentence + English translation |
| Declension | Noun/adjective declension table (singular & plural) |
| Conjugation | Verb conjugation table |
| Conjunction | Conjunction usage patterns |

## Pulling Anki Data

`_pull_anki_data.py` reads notes from an existing Anki deck via
[AnkiConnect](https://foosoft.net/projects/anki-connect/) and exports them
with media references and optional Western Armenian dialect scoring.

### Prerequisites

- Anki desktop running with the AnkiConnect plugin (code **2055492159**).
- A source deck configured in `armenian_anki/config.py` (default: `"Armenian Vocabulary"`).

### Usage

```bash
# Pull all notes from the default source deck and save to pulled_notes.json:
python _pull_anki_data.py

# Pull from a specific deck:
python _pull_anki_data.py --deck "My Armenian Deck"

# Keep only Western Armenian notes:
python _pull_anki_data.py --filter-western

# Keep Western Armenian + ambiguous-dialect notes:
python _pull_anki_data.py --filter-western --include-ambiguous

# Download audio and image media to a local directory:
python _pull_anki_data.py --media-dir ./pulled_media

# Export as CSV:
python _pull_anki_data.py --format csv --output notes.csv

# Dry-run (print summary only, write nothing):
python _pull_anki_data.py --dry-run
```

Each exported note includes:
- All original Anki fields
- `"media"` — lists of audio (`[sound:…]`) and image (`<img …>`) filenames
- `"dialect"` — dialect label (`"western"` / `"eastern"` / `"ambiguous"`),
  numeric score, and the marker patterns that fired

### Western Armenian Dialect Scorer

`armenian_anki/dialect_scorer.py` provides programmatic access to the
dialect scoring logic:

```python
from armenian_anki.dialect_scorer import score_text, classify_text, filter_western

# Score a single string
result = score_text("կ\u2019eri anor")
print(result.label)            # "western"
print(result.normalised_score) # float in [-1.0, +1.0]
print(result.matched_markers)  # patterns that matched

# Quick label only
print(classify_text("kardom em"))  # "eastern"

# Filter a list of strings, keeping only Western Armenian ones
texts = ["կ\u2019eri", "kardom em", "just some text"]
wa_texts = filter_western(texts, include_ambiguous=False)
# Returns: [(index, text, DialectScore), ...]
```

Scores are in the range [-1.0, +1.0]:
- **> 0.15** → labelled `"western"`
- **< -0.15** → labelled `"eastern"`
- **in between** → labelled `"ambiguous"`

---

## Notes

- The scraper uses a temporary Chrome profile copy to avoid locking your main profile.
- Facebook login is handled via existing session cookies — no credentials are stored.
- OCR includes Armenian-specific corrections (e.g. fixing `ուdelays` → ` delays oundsv` misreads).
- Images are deduplicated by URL hash during scraping.
