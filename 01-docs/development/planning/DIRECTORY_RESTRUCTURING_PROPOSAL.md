# Directory Restructuring for Data & Linguistic Tools Extraction
**Date**: March 6, 2026  
**Goal**: Isolate scraping, data processing, and linguistic tools for migration to standalone packages

---

## Current Structure Analysis

### Root Level Files
- **Outdated**: `analyze_anki_database.py`, Docker installer, test logs at root
- **Should be**: In `07-tools/analysis/` or `scripts/`

### Package Structure
```
02-src/
├── lousardzag/          ← Main learning platform (app logic + dependent tools mix)
│   ├── morphology/      ← Linguistic tools (should be separately packaged)
│   ├── anki_connect.py  ← Anki integration (app-specific)
│   ├── phonetics.py     ← Linguistic tools (reusable, should extract)
│   ├── card_generator.py← App-specific
│   └── sentence_progression.py ← App-specific (but uses linguistic tools)
└── wa_corpus/           ← Data/scraping (perfect for standalone extraction)
    ├── data/            ← HUGE: 15GB+ of corpus data
    ├── ia_scraper.py
    ├── newspaper_scraper.py
    ├── nayiri_scraper.py
    ├── wiki_processor.py
    ├── frequency_aggregator.py
    └── tokenizer.py

07-tools/               ← Mixed: Some app-specific, some reusable
├── generation/         ← Audio generation (could be standalone)
├── scraping/          ← Additional scrapers (belongs in wa_corpus)
├── analysis/          ← Analysis tools (belongs in linguistic tools)
└── ... 13 other subdirs of varying purpose
```

---

## Proposed 3-Package Architecture

### Package 1: `wa-corpus` (Standalone Data & Scraping)
**Purpose**: Source and aggregate Western Armenian corpus data  
**Status**: Mostly ready for extraction (only needs data cleanup)  
**Size**: ~15GB (in `wa_corpus/data/`)

**Structure**:
```
wa-corpus/
├── README.md                       # How to build corpus
├── pyproject.toml                  # Separate package config
├── src/wa_corpus/
│   ├── __init__.py
│   ├── __main__.py                # CLI entry point
│   ├── build_corpus.py            # Main orchestrator
│   ├── config.py                  # Corpus sources, paths
│   ├── tokenizer.py               # Text tokenization
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── ia_scraper.py          # Internet Archive
│   │   ├── newspaper_scraper.py   # Aztag, Horizon, etc.
│   │   ├── nayiri_scraper.py      # Dictionary
│   │   └── wiki_processor.py      # Wikipedia dumps
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── text_cleaner.py        # Deduplicate, normalize
│   │   ├── frequency_aggregator.py# Combine all sources
│   │   └── classifier.py          # WA/EA dialect classification
│   ├── data/                      # Corpus storage
│   │   ├── ia/                    # Internet Archive texts
│   │   ├── newspapers/            # Article collections
│   │   ├── wiki/                  # Wikipedia dumps
│   │   ├── nayiri/                # Dictionary entries
│   │   └── aggregated/            # Final frequency rankings
│   └── utils/
│       ├── logging.py
│       ├── network.py             # Retry logic, rate limiting
│       └── cache.py               # Local caching
├── tests/
│   ├── test_scrapers.py
│   ├── test_processors.py
│   └── fixtures/
└── docs/
    ├── SOURCES.md                 # Data source documentation
    ├── BUILDING.md                # How to run corpus builder
    └── DATA_QUALITY.md            # Statistics & validation
```

**Key Files to Move** (from current locations):
- `02-src/wa_corpus/*` → `src/wa_corpus/`
- `02-src/wa_corpus/data/` → `data/` (keep separate, gitignore)
- `07-tools/scraping/*` → `src/wa_corpus/scrapers/`

**To Extract**:
- `tokenizer.py` → Keep (tokenization is corpus-specific)
- `frequency_aggregator.py` → Keep (corpus aggregation)
- `wa_classifier.py` → Move to `processors/classifier.py`

**NOT for this package**:
- `dialect_classifier.py` (only classify, don't depend on wa_corpus) → Move to `armenian-linguistics`
- `anki_connect.py` → App-specific, stays in main package

---

### Package 2: `armenian-linguistics` (Standalone Linguistic Tools)
**Purpose**: Reusable Western Armenian morphology, phonetics, analysis  
**Status**: Ready to extract (clean, well-tested)  
**Size**: ~5MB

**Structure**:
```
armenian-linguistics/
├── README.md                       # Quick start & API
├── pyproject.toml                  # Dependencies (minimal, no external data)
├── src/armenian_linguistics/
│   ├── __init__.py
│   ├── phonetics/
│   │   ├── __init__.py
│   │   ├── core.py                # Phoneme definitions, IPA mapping
│   │   ├── transcription.py       # Word→IPA, Text→IPA
│   │   ├── difficulty.py          # Phonetic difficulty scoring
│   │   └── data.py                # ARMENIAN_PHONEMES, DIGRAPHS dicts
│   ├── morphology/
│   │   ├── __init__.py
│   │   ├── core.py                # Stemming, syllable counting, romanization
│   │   ├── nouns.py               # Noun declensions
│   │   ├── verbs.py               # Verb conjugations, irregular tables
│   │   ├── adjectives.py          # Adjective forms
│   │   ├── difficulty.py          # Morphological complexity scoring
│   │   └── data/
│   │       ├── irregular_verbs.py
│   │       └── phoneme_difficulty.json
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── pos_tagger.py          # POS inference (noun, verb, adj, etc.)
│   │   ├── stemmer.py             # Lemmatization
│   │   ├── text_cleaner.py        # Remove diacritics, normalize
│   │   └── validators.py          # Is valid Armenian?, etc.
│   ├── converters/
│   │   ├── __init__.py
│   │   ├── ipa_converter.py       # Armenian→IPA (word & text level)
│   │   ├── transliterator.py      # Armenian→Latin (ISO 9985)
│   │   ├── romanizer.py           # Current romanize() function
│   │   └── csv_exporter.py        # Export with linguistic data
│   └── utils/
│       ├── validators.py
│       └── constants.py            # Letter data, phoneme constants
├── tests/
│   ├── test_phonetics.py
│   ├── test_morphology.py
│   ├── test_analysis.py
│   └── fixtures/
│       ├── armenian_words.txt
│       └── test_sentences.txt
├── docs/
│   ├── API.md                      # Full API reference
│   ├── PHONETICS.md                # Phonetic rules & IPA mapping
│   ├── MORPHOLOGY.md               # Grammar rules & verb tables
│   └── EXAMPLES.md                 # Usage examples
└── references/
    └── western-armenian-requirement.md  # Phonetic authority
```

**Key Files to Move** (from current locations):
- `02-src/lousardzag/phonetics.py` → `src/armenian_linguistics/phonetics/core.py`
- `02-src/lousardzag/morphology/*` → `src/armenian_linguistics/morphology/`
- `02-src/lousardzag/analysis_utils.py` → `src/armenian_linguistics/analysis/`
- `02-src/lousardzag/stemmer.py` → `src/armenian_linguistics/analysis/stemmer.py`
- `02-src/lousardzag/dialect_classifier.py` → `src/armenian_linguistics/analysis/dialect_classifier.py`
- `02-src/lousardzag/letter_data.py` → `src/armenian_linguistics/utils/letter_data.py`

**NOT for this package**:
- `card_generator.py` (app-specific) → Stays in main package
- `sentence_progression.py` (app-specific) → Stays in main package
- `anki_connect.py` (Anki integration) → Stays in main package
- TTS/audio generation → Separate `armenian-audio` package (optional)

---

### Package 3: `lousardzag` (Main Learning Platform)
**Purpose**: Anki-integrated vocabulary progression & learning  
**Refactored**: Depends on `armenian-linguistics` and optionally `wa-corpus`

**Structure** (simplified from current):
```
lousardzag/
├── README.md
├── pyproject.toml                  # Now declares array_linguistics as dependency
├── src/lousardzag/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── card_generator.py       # Generate Anki cards (uses linguistic tools)
│   │   ├── sentence_generator.py   # Generate sentences (uses morphology)
│   │   ├── sentence_progression.py # Difficulty-aware coaching
│   │   └── progression.py          # Learning level assignment
│   ├── anki/
│   │   ├── __init__.py
│   │   ├── connect.py              # AnkiConnect wrapper (was anki_connect.py)
│   │   ├── sync.py                 # Sync logic
│   │   └── models.py               # Anki note type definitions
│   ├── enrichment/
│   │   ├── __init__.py
│   │   ├── frequency_mapper.py     # Link to corpus frequency ranks
│   │   ├── level_assigner.py       # Assign 1-7 levels
│   │   ├── morphology_enricher.py  # Add declensions/conjugations
│   │   └── phonetics_enricher.py   # Add IPA/pronunciation
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py               # SQLite card schema
│   │   ├── operations.py           # CRUD operations
│   │   ├── migrations.py           # Schema versions
│   │   └── carddb.py               # CardDatabase class
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── web_server.py           # Flask/FastAPI server
│   │   ├── letter_viewer.py        # Letter cards viewer
│   │   ├── vocab_viewer.py         # Vocabulary triage UI
│   │   └── preview_server.py       # Integration preview
│   ├── templates/                  # HTML/Anki card templates
│   │   ├── flashcard/
│   │   ├── models/
│   │   │   ├── letter_cards/
│   │   │   ├── vocab_sentences/
│   │   │   ├── noun_declension/
│   │   │   └── verb_conjugation/
│   │   └── styles/
│   ├── config.py
│   ├── logging_config.py
│   └── cli.py                      # CLI entry point
├── 03-cli/                         # CLI scripts (can move into src/)
│   ├── generate_cards.py
│   ├── preview_server.py
│   ├── pull_anki_data.py
│   └── start_server.py
├── tests/
│   ├── test_card_generator.py
│   ├── test_sentence_progression.py
│   ├── test_integration.py
│   └── ...
├── 08-data/                        # Runtime data (gitignored)
│   ├── armenian_cards.db           # Local Anki sync cache
│   ├── letter_audio/               # 81 MP3 files
│   ├── vocab_*.csv                 # Generated vocabulary lists
│   └── reports/                    # Analysis reports
└── docs/
    ├── GETTING_STARTED.md
    ├── ARCHITECTURE.md
    └── CONTRIBUTING.md
```

---

## Migration Steps & Timeline

### Phase 1: Extract `wa-corpus` (week 1-2, 4-6 hours)
1. **Create new repo**: `wa-corpus` with standalone structure
2. **Move code**:
   - `02-src/wa_corpus/*` → new package `src/wa_corpus/`
   - `07-tools/scraping/*` → new package `src/wa_corpus/scrapers/`
3. **Handle data**:
   - Create `.gitignore` for `data/` (.gitignore: `data/**/*.txt`, `data/**/*.json` but keep directory structure)
   - Extract data structure to separate location (if migrating to new machine)
4. **Create pyproject.toml** with:
   - Core deps: `requests`, `beautifulsoup4`, `selenium` (for scrapers)
   - Tokenization: `tokenize>=3.0` if needed
5. **Update imports** in main `lousardzag` package (remove wa_corpus dependency initially)
6. **Tests**: Move `04-tests/` relevant tests to new package

**Outcomes**:
- ✅ `wa-corpus` pip-installable: `pip install wa-corpus` or `pip install git+https://github.com/.../wa-corpus`
- ✅ Data stays in local working directory (gitignore'd)
- ✅ Main `lousardzag` can work WITHOUT corpus (optional integration)

---

### Phase 2: Extract `armenian-linguistics` (week 2-3, 3-5 hours)
1. **Create new repo**: `armenian-linguistics` with standalone structure
2. **Move code**:
   - `02-src/lousardzag/phonetics.py` → new package
   - `02-src/lousardzag/morphology/` → new package
   - `02-src/lousardzag/analysis_utils.py` → new package
   - `02-src/lousardzag/stemmer.py` → new package
   - `02-src/lousardzag/letter_data.py` → new package
   - `02-src/lousardzag/dialect_classifier.py` → new package
3. **Create pyproject.toml** with NO external data dependencies (phoneme maps are in-code)
4. **Update imports** in main `lousardzag` package:
   ```python
   # Before:
   from lousardzag.phonetics import get_phonetic_transcription
   
   # After:
   from armenian_linguistics.phonetics import get_phonetic_transcription
   ```
5. **Tests**: Move or duplicate phonetics/morphology tests to new package

**Outcomes**:
- ✅ `armenian-linguistics` pip-installable (pure Python, no data files)
- ✅ Can be used standalone by linguists, educators, tool developers
- ✅ Decoupled from Anki integration, learning progression, corpus

---

### Phase 3: Refactor `lousardzag` (week 3-4, 5-7 hours)
1. **Update dependencies** in `pyproject.toml`:
   ```toml
   dependencies = [
       "armenian-linguistics>=0.1.0",
       "pandas>=1.3.0",
       "requests>=2.25.0",
       "fastapi>=0.112.0",
       "uvicorn>=0.30.0",
   ]
   
   optional-dependencies.corpus = ["wa-corpus>=0.1.0"]
   ```
2. **Reorganize source** into `src/lousardzag/` subdirectories (as shown above)
3. **Move CLI scripts** from `03-cli/` into `src/lousardzag/cli.py` or keep separate
4. **Update all imports** to point to new locations
5. **Clean up 07-tools/**:
   - Move reusable generation tools → optional `armenian-audio` package
   - Keep app-specific tools in `07-tools/` for now
6. **Consolidate 08-data/** structure

**Outcomes**:
- ✅ `lousardzag` has clean, modular structure
- ✅ Easy to see what's app-specific vs reusable
- ✅ Works with or without `wa-corpus` (graceful degradation)

---

## File Movement Summary Table

| Current Location | New Location (Package) | Reason |
|---|---|---|
| `02-src/wa_corpus/*` | `wa-corpus/src/wa_corpus/` | Core data/scraping functionality |
| `07-tools/scraping/*` | `wa-corpus/src/wa_corpus/scrapers/` | Additional scrapers specific to corpus |
| `02-src/lousardzag/phonetics.py` | `armenian-linguistics/src/armenian_linguistics/phonetics/` | Reusable linguistic tool |
| `02-src/lousardzag/morphology/` | `armenian-linguistics/src/armenian_linguistics/morphology/` | Reusable linguistic tool |
| `02-src/lousardzag/letter_data.py` | `armenian-linguistics/src/armenian_linguistics/utils/` | Reference data for linguistics |
| `02-src/lousardzag/stemmer.py` | `armenian-linguistics/src/armenian_linguistics/analysis/` | Analysis tool |
| `02-src/lousardzag/analysis_utils.py` | `armenian-linguistics/src/armenian_linguistics/analysis/` | Analysis tool |
| `02-src/lousardzag/dialect_classifier.py` | `armenian-linguistics/src/armenian_linguistics/analysis/` | Analysis tool |
| `02-src/lousardzag/card_generator.py` | `lousardzag/src/lousardzag/core/` | App-specific |
| `02-src/lousardzag/sentence_progression.py` | `lousardzag/src/lousardzag/core/` | App-specific |
| `02-src/lousardzag/anki_connect.py` | `lousardzag/src/lousardzag/anki/` | App-specific |
| `02-src/lousardzag/database.py` | `lousardzag/src/lousardzag/database/` | App-specific |
| `03-cli/*` | `lousardzag/src/lousardzag/cli.py` (consolidated) | App CLI |
| `07-tools/generation/*` | Optional `armenian-audio/` package OR keep in `lousardzag/` | TTS generation (reusable but heavy deps) |
| `07-tools/analysis/*` | Keep in main for now; could move to `armenian-linguistics/` later | Various analysis utilities |
| `07-tools/cleanup/*` | Keep in main for now | Anki maintenance scripts |
| `01-docs/` | Distribute to each package: core docs, linguistic docs, data docs | Documentation |

---

## Dependency Graph After Restructuring

```
User Applications
    ↓
lousardzag (learning platform)
    ├── depends on: armenian-linguistics
    ├── optionally depends on: wa-corpus
    └── depends on: pandas, fastapi, requests
    
armenian-linguistics (reusable tools)
    ├── NO external data dependencies (all in-code)
    └── depends on: (minimal stdlib only, optionally scipy for some phonetics)

wa-corpus (data sourcing)
    ├── depends on: requests, beautifulsoup4, selenium
    └── generates: frequency_rank.json, aggregated_corpus.json
    
Third-party packages (optional add-ons)
    ├── armenian-audio (TTS generation)
    │   └── depends on: armenian-linguistics, torch/fairseq or gcloud-tts
    └── armenian-nayiri (lexicon sourcing)
        └── depends on: wa-corpus
```

---

## Key Benefits After Reorganization

### 1. **Modularity**
- ✅ Can use `armenian-linguistics` in any project (web scrapers, translators, etc.)
- ✅ Can source corpus data independently of learning platform
- ✅ Easy to swap in new TTS engine without touching core platform

### 2. **Maintainability**
- ✅ Scraper bugs don't break learning platform
- ✅ Phonetics updates propagate to all users of `armenian-linguistics`
- ✅ Each package has its own test suite, CI/CD

### 3. **Deployment Flexibility**
- ✅ Run corpus builder on separate machine (no need for Anki/FastAPI)
- ✅ Update linguistic rules without restarting learning app
- ✅ Share corpus data via PyPI or cloud CDN

### 4. **Contribution Barriers**
- ✅ Linguists can contribute to phonetics/morphology without understanding Anki
- ✅ Web devs can improve UI without touching corpus scrapers
- ✅ Data engineers can optimize frequency aggregation independently

### 5. **Reusability**
- ✅ Other Armenian language projects can depend on `armenian-linguistics`
- ✅ `wa-corpus` data can serve as reference for academic research
- ✅ No Anki lock-in: pure linguistic data tools

---

## Quick-Start After Migration

**For a new developer:**
```bash
# Install learning platform with all components
pip install lousardzag[corpus]

# OR minimal install (just learning, no corpus building)
pip install lousardzag

# OR use linguistic tools independently
pip install armenian-linguistics
from armenian_linguistics.phonetics import get_phonetic_transcription

# OR rebuild corpus from scratch
pip install wa-corpus
python -m wa_corpus --all --output-dir ~/wa-corpus-build
```

---

## Implementation Checklist

### Before Starting
- [ ] Set up 3 new GitHub repos (wa-corpus, armenian-linguistics, lousardzag-refactored)
- [ ] Decide on PyPI organization or GitHub Packages hosting
- [ ] Create shared GitHub organization if needed

### Phase 1: wa-corpus
- [ ] Create repo structure with `src/wa_corpus/` layout
- [ ] Move scraper files with imports updated
- [ ] Create pyproject.toml with dependencies
- [ ] Create build_corpus.py that orchestrates all scrapers
- [ ] Add tests for each scraper
- [ ] Create docs/SOURCES.md and docs/BUILDING.md
- [ ] Create GitHub Actions CI/CD for testing scrapers
- [ ] First release: v0.1.0 to PyPI

### Phase 2: armenian-linguistics
- [ ] Create repo structure with modular phonetics/morphology/analysis
- [ ] Move files with imports updated (remove Anki references)
- [ ] Create pyproject.toml with minimal dependencies
- [ ] Move all phonetics tests, add morphology tests, add analysis tests
- [ ] Create docs/API.md, docs/PHONETICS.md, docs/MORPHOLOGY.md
- [ ] Create GitHub Actions CI/CD
- [ ] First release: v0.1.0 to PyPI

### Phase 3: lousardzag refactor
- [ ] Reorganize into src/lousardzag/ subdirectories
- [ ] Update all imports to use `armenian-linguistics`
- [ ] Update pyproject.toml with new dependencies
- [ ] Move/consolidate 03-cli into src/lousardzag/cli.py
- [ ] Test with `pip install -e .`
- [ ] Run full test suite
- [ ] Release as v1.0.0 (major version bump for backward compat)

### After Releases
- [ ] Archive old GitHub repo or mark it as migrated
- [ ] Update README to point to new repos
- [ ] Create MIGRATION.md guide for users of old package
- [ ] Plan next steps: ci-cd, documentation site, automatic releases

---

## Notes & Gotchas

1. **Data migration**: `wa_corpus/data/` is ~15GB. Plan for:
   - Whether to keep in git (no, gitignore it)
   - How to transfer to new machines (rsync, S3, BitTorrent, etc.)
   - Whether to version data files (probably not; version scrapers instead)

2. **Import paths change**:
   - All existing imports from `lousardzag.phonetics` → `armenian_linguistics.phonetics`
   - Update across 04-tests/, 07-tools/, 03-cli/
   - Create alias imports in old locations for 1-2 releases for backward compat

3. **Circular deps**: Be careful that:
   - `armenian-linguistics` doesn't import from `wa-corpus`
   - `wa-corpus` doesn't import from `lousardzag` (it can import from `armenian-linguistics`)

4. **Testing strategy**:
   - Each package should have 100% testable functionality (no Anki, no real network calls)
   - Use fixtures/mocks for scrapers (use cassettes or sample data)
   - Integration tests stay in `lousardzag` that combine all packages

5. **Documentation**:
   - Each package gets its own docs (GitHub Pages, Sphinx)
   - Top-level lousardzag.com might list all three packages
   - Cross-link from README files
