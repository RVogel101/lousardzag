# Lousardzag (Լուսարձակ)

**Western Armenian Language Learning Platform**

Lousardzag ("Light-spreading" or "Dawn-bringer") is a comprehensive platform for Western Armenian language learning, featuring morphological analysis, vocabulary progression, and intelligent flashcard generation.

## Overview

Lousardzag combines computational linguistics with pedagogical progression to create an effective Western Armenian learning experience:

- **Morphological Analysis** — Advanced noun declension, verb conjugation, and irregular verb handling
- **Intelligent Progression** — Syllable-based difficulty progression with prerequisite tracking
- **Corpus Building** — Automated scraping from newspapers, Internet Archive, and dictionaries
- **Flashcard Generation** — Context-aware sentence generation with vocabulary dependency management

## Project Structure

```
lousardzag/
├── 01-docs/          Documentation and references
├── 02-src/           Source code
│   ├── lousardzag/   Core learning platform (morphology, progression, card generation)
│   └── wa_corpus/    Western Armenian corpus tools (scrapers, tokenization, frequency analysis)
├── 03-cli/           Command-line interfaces
├── 04-tests/         Test suite
├── 05-config/        Configuration files
├── 06-notebooks/     Jupyter notebooks for analysis
├── 07-tools/         Utility scripts
└── 08-data/          Data outputs (gitignored)
```

## Requirements

- **Python 3.10+**
- **Conda environment** (Python 3.12.3 recommended)
- **Anki desktop** with AnkiConnect add-on (for Anki integration)

### Installation

```bash
pip install -r requirements.txt
```

## Usage

### Generate Flashcards

```bash
python 07-tools/generate_ordered_cards.py --max-cards 50 --english-mode off
```

Options:
- `--max-cards`: Number of cards to generate
- `--english-mode`: Control English translations (off/always/fallback)
- `--max-syllables-level-1`: Syllable limit for level 1 (default: 2)

### Build Western Armenian Corpus

**Newspapers** (Asbarez, Aztag, Nor Gyank):
```bash
python -m wa_corpus.build_corpus --newspapers
```

**Internet Archive** (historical documents):
```bash
python -m wa_corpus.build_corpus --ia
```

**Nayiri Dictionary** (polite scraping):
```bash
python -m wa_corpus.nayiri_scraper --delay-min 3.0 --delay-max 6.0
```

### Development Server

```bash
python 03-cli/preview_server.py
```

Launches FastAPI server at http://127.0.0.1:8000 for flashcard preview.

## Key Features

### Morphological Analysis
- Noun declension (8 cases: nominative, accusative, genitive, dative, ablative, instrumental, locative)
- Verb conjugation (15 tenses, 6 persons, irregular verb support)
- Schwa epenthesis detection
- Syllable counting and phonological difficulty assessment

### Progression System
- Level-based vocabulary introduction (20 words per batch, 5 batches per level)
- Syllable constraints by level (Level 1-5: 1-2 syllables, Level 6-10: 2 syllables, etc.)
- Prerequisite tracking (vocabulary used in sentences must be taught first)
- Bootstrap vocabulary (36 common grammatical words)

### Corpus Tools
- Multi-source newspaper scraping with deduplication
- Internet Archive catalog management and PDF text extraction
- Nayiri dictionary scraping with rate limiting and cooldown periods
- Western Armenian tokenization and frequency analysis

## Testing

```bash
python -m pytest
```

Current test coverage: 323 tests passing

## Project Name

**Lousardzag** (Լուսարձակ) — Western Armenian transliteration of "light-spreading" or "dawn-bringer", reflecting the project's mission to illuminate and spread Western Armenian language knowledge.

## License

MIT

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

## Notes

- The scraper uses a temporary Chrome profile copy to avoid locking your main profile.
- Facebook login is handled via existing session cookies — no credentials are stored.
- OCR includes Armenian-specific corrections (e.g. fixing `ուdelays` → ` delays oundsv` misreads).
- Images are deduplicated by URL hash during scraping.
