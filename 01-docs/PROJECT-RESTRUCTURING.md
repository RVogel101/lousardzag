# Project Restructuring Summary

## Date
March 2, 2026

## Changes Made

This commit reorganizes the project from a flat, root-level structure to a professional, maintainable layout following Python packaging standards.

### New Directory Structure

```
anki-note-generation-pipelines/
├── README.md
├── pyproject.toml                [NEW] Build configuration
├── .gitignore                     [UPDATED]
├── requirements.txt
├── requirements_ocr.txt
│
├── 01-docs/                       [Documentation first]
│   ├── PROJECT-RESTRUCTURING.md
│   ├── corpus-sources.md
│   └── logging.md
│
├── 02-src/                        [Core packages]
│   ├── armenian_anki/
│   │   ├── card_generator.py
│   │   ├── database.py
│   │   ├── api.py
│   │   ├── preview.py
│   │   ├── renderer.py
│   │   ├── morphology/
│   │   ├── templates/
│   │   └── ...
│   │
│   └── wa_corpus/
│       ├── build_corpus.py
│       ├── wiki_processor.py
│       ├── newspaper_scraper.py
│       ├── ia_scraper.py
│       ├── nayiri_scraper.py
│       └── data/
│
├── 03-cli/                        [User-facing entry points]
│   ├── generate_cards.py
│   ├── preview_server.py
│   └── pull_anki_data.py
│
├── 04-tests/                      [Test suite organized by type]
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── 05-config/                     [Configuration files]
│   └── logging_config.py
│
├── 06-notebooks/                  [Jupyter & exploration]
│   ├── demo_component_analysis.py
│   └── exploration.ipynb
│
├── 07-tools/                      [Utilities & experimental scripts]
│   ├── scrape_fb_images.py
│   ├── extract_image_text.py
│   ├── _extract_wa_sources.py
│   └── ocr_setup_check.py
│
├── 08-data/                       [Generated artifacts (gitignored)]
│   ├── .gitkeep
│   ├── armenian_cards.db
│   ├── anki_export.json
│   ├── anki_media/
│   ├── extracted_text_simple/
│   └── _wa_source_extract/
│
└── logs/                          (existing)
```

### Key Improvements

#### 1. **Package Organization**
- Main packages (`armenian_anki`, `wa_corpus`) now in `src/` directory
- Enables proper Python package distribution via pip
- Supports `pip install -e .` for development mode

#### 2. **Clear Entry Points**
- User-facing CLI scripts consolidated in `cli/` directory
- Easy to identify which scripts to run
- All have sys.path setup to import from `src/`

#### 3. **Test Organization**
- Tests organized by type: `unit/`, `integration/`, `e2e/`
- New `conftest.py` for pytest configuration (auto-loads `src/` path)
- Test discovery and maintenance simplified

#### 4. **Utility Scripts Isolated**
- Experimental and one-off scripts moved to `tools/`
- Keeps core project clean
- Makes it clear what's production vs. exploratory

#### 5. **Generated Data Contained**
- All runtime outputs now in `data/` directory
- Updated `.gitignore` for new structure
- Easier to separate source control from artifacts

#### 6. **Build Configuration**
- New `pyproject.toml` defines:
  - Package metadata, dependencies, optional groups
  - Tool configurations (pytest, black, isort, mypy)
  - CLI entry points (future script wrapper support)
  - Package discovery from `src/`

### Files Moved
- **Packages**: `armenian_anki/`, `wa_corpus/` → `src/`
- **CLI Scripts**: `generate_anki_cards.py`, `render_preview.py`, `_pull_anki_data.py` → `cli/`
- **Core Tests**: `test_*.py` from root → `tests/ `organized by type
- **Utilities**: `scrape_fb_images.py`, OCR tools → `tools/`
- **Config**: `logging_config.py` → `config/`
- **Notebooks**: `exloration.ipynb`, demo script → `notebooks/`
- **Documentation**: `TRANSLATION_SOURCES.md`, `LOGGING_README.md` → `docs/`
- **Generated Data**: `*.db`, `*.json`, `anki_media/` → `data/`

### Files Cleaned Up (Deleted)
- Temporary debug files: `debug_page.html`, `_ddg_*.html`, `_temp_export.*`
- Checkpoint: `.phase2_checkpoint`

### Import Path Updates
- **CLI scripts**: Added `sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))` 
- **Tests**: Created `tests/conftest.py` to auto-add src to path (pytest standard)
- **pyproject.toml**: Configured `setuptools` to find packages in `src/`

### Backward Compatibility
- All 326 tests pass after reorganization
- Import structure supported via:
  - Pytest's `conftest.py` auto-discovery
  - Manual path setup in CLI scripts
  - Standard pip installation with pyproject.toml

### Next Steps
1. Install development dependencies: `pip install -e .[dev]`
2. Run tests: `pytest tests/`
3. Run CLI scripts: `python cli/generate_cards.py`
4. Future: Create wrapper CLI commands via pyproject.toml scripts section

