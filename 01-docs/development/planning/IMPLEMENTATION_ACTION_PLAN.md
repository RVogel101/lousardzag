# Implementation Action Plan: Package Extraction
**Date**: March 6, 2026  
**Effort**: 3 phases, 12-18 hours total  
**Target Completion**: ~3 weeks with 1-2 hours/day

---

## Conversation-Derived Backlog (Mar 3-6, 2026)

This section captures concrete learnings and action items extracted from recent terminal work + planning chats, so they are tracked in the implementation plan.

### Key Learnings

- **Audio training scope reality**: Existing Anki audio inventory is useful for validation but not enough for full TTS fine-tuning. Strategy should prioritize adaptation/fine-tuning over from-scratch model training.
- **Operational pain point**: `03-cli/letter_cards_viewer.py` repeatedly exits with code `1` and currently lacks enough startup diagnostics for fast failure triage.
- **Pipeline fragility**: Audio generation/testing scripts show intermittent failures (`generate_letter_audio_enhanced.py`, `test_mms_tts.py`) and need consistent error reporting.
- **Corpus build consistency gap**: `python -m wa_corpus.build_corpus --newspapers 1` succeeded, while at least one multi-source run with `--newspapers 2` failed. This indicates source-specific robustness issues.
- **Environment dependency**: Conda base activation remains a hard prerequisite in this workspace; missed activation can produce misleading failures.

### Prioritized Sprint Checklist (P0/P1/P2)

#### P0 - Stabilize Core Workflows (Total: 8-12h)
- [ ] `letter_cards_viewer` startup diagnostics and explicit fatal errors (2-3h)
- [ ] `--debug` mode for `03-cli/letter_cards_viewer.py` and `07-tools/test_mms_tts.py` (1-2h)
- [ ] CLI smoke tests for high-use entry points (2-3h)
  - [ ] `03-cli/letter_cards_viewer.py --help`
  - [ ] `03-cli/preview_server.py --pretty`
  - [ ] `python -m wa_corpus.build_corpus --newspapers 1`
- [ ] Normalize failure logs under `logs/` with timestamp + failure-type summary (1-2h)
- [ ] Harden newspaper build for partial failures (retry + continue-on-error + end-of-run status) (2h)

#### P1 - Operational Safety and Guardrails (Total: 5-8h)
- [ ] Add Nayiri `--preflight` mode (delay bounds, readiness checklist, whitelist reminder) (2-3h)
- [ ] Add VPN/public-IP guardrail check before Nayiri runs (1-2h)
- [ ] Add required first-run bounded command (`--max-pages 3`) to tool help/runbooks (0.5h)
- [ ] Add regression tests for default scraper mode and cooldown windows (1.5-2.5h)

#### P2 - Developer Experience and Reporting (Total: 6-10h)
- [ ] Add `lousardzag doctor` diagnostics command (ports, env, dependencies, file/model presence) (3-4h)
- [ ] Add Audio Pipeline Health Report command (2-3h)
- [ ] Add TTS Data Readiness Score utility (1-2h)
- [ ] Add unified config file for audio generation scripts (YAML/JSON) (1h)

### Suggested Sprint Sequence

1. Sprint A (P0): stabilize and unmask failures.
2. Sprint B (P1): add safe defaults and preflight checks.
3. Sprint C (P2): improve developer velocity and observability.

---

## Phase 1: Extract `wa-corpus` (4-6 hours, Days 1-2)

### Step 1a: Create New Repository Structure (30 mins)
```bash
# Locally (before pushing to GitHub):
mkdir wa-corpus
cd wa-corpus

# Create directory structure
mkdir -p src/wa_corpus/{scrapers,processors,data,utils}
mkdir -p tests/fixtures
mkdir -p docs
```

**Files to create:**
- [ ] `src/wa_corpus/__init__.py` — Package init
- [ ] `src/wa_corpus/__main__.py` — CLI entry point (copy from current `build_corpus.py` main)
- [ ] `src/wa_corpus/build_corpus.py` — Orchestrator (rename current Build_corpus.py)
- [ ] `src/wa_corpus/config.py` — Source definitions (extract from current build_corpus.py)
- [ ] `src/wa_corpus/tokenizer.py` — Move from 02-src/
- [ ] `pyproject.toml` — Package config
- [ ] `README.md` — Quick start guide
- [ ] `.gitignore` — Ignore data/*.txt, data/**/*.json (keep structure)
- [ ] `MANIFEST.in` — Include docs, exclude large data

### Step 1b: Move Scraper Files (1 hour)
```bash
# From lousardzag project:
cp 02-src/wa_corpus/ia_scraper.py → src/wa_corpus/scrapers/
cp 02-src/wa_corpus/newspaper_scraper.py → src/wa_corpus/scrapers/
cp 02-src/wa_corpus/nayiri_scraper.py → src/wa_corpus/scrapers/
cp 02-src/wa_corpus/wiki_processor.py → src/wa_corpus/scrapers/
cp 07-tools/scraping/*.py → src/wa_corpus/scrapers/
cp 02-src/wa_corpus/frequency_aggregator.py → src/wa_corpus/processors/
cp 02-src/wa_corpus/wa_classifier.py → src/wa_corpus/processors/
```

**Create new __init__ files:**
- [ ] `src/wa_corpus/scrapers/__init__.py` — import all scrapers
- [ ] `src/wa_corpus/processors/__init__.py` — import all processors

### Step 1c: Update Imports in Moved Files (45 mins)
**Files to update** (in new wa-corpus package):
- [ ] `scrapers/ia_scraper.py`: 
  ```python
  # Old: from wa_corpus.tokenizer import ...
  # New: from wa_corpus.tokenizer import ...  (stays same)
  ```
- [ ] `scrapers/newspaper_scraper.py`: Update any wa_corpus imports
- [ ] `processors/frequency_aggregator.py`: Remove any lousardzag imports
- [ ] `processors/wa_classifier.py`: Change `from lousardzag.dialect_classifier` → local import

### Step 1d: Create pyproject.toml (30 mins)
**Example content:**
```toml
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "wa-corpus"
version = "0.1.0"
description = "Western Armenian corpus sourcing and frequency aggregation"
readme = "README.md"
requires-python = ">=3.10"
license = { text = "MIT" }

dependencies = [
    "requests>=2.25.0",
    "beautifulsoup4>=4.9.0",
    "selenium>=4.0.0",
]

[project.optional-dependencies]
dev = ["pytest>=7.0.0", "pytest-cov>=4.0.0"]

[project.scripts]
wa-corpus-build = "wa_corpus.build_corpus:main"

[tool.setuptools]
packages = ["wa_corpus"]
package-dir = { "" = "src" }

[tool.setuptools.package-data]
wa_corpus = ["data/.gitkeep"]
```

**Create .gitignore** (prevent 15GB data from being committed):
```
data/**/*.txt
data/**/*.json
data/**/*.html
data/**/*.pdf
!data/.gitkeep
```

### Step 1e: Move Tests (45 mins)
- [ ] Create `tests/test_ia_scraper.py` (if exists in old location)
- [ ] Create `tests/test_newspaper_scraper.py`
- [ ] Create `tests/fixtures/` directory with sample data
- [ ] Create `conftest.py` for test setup

### Step 1f: Create Documentation (1 hour)
**docs/SOURCES.md** —List all corpus sources:
```markdown
# Corpus Sources

## Internet Archive
- URL: archive.org
- Search query: Western Armenian texts
- Coverage: ~200 items, 500M+ words

## Newspapers
- Aztag Daily (aztagdaily.com)
- Horizon Weekly (horizonweekly.ca)

## Wikipedia
- Armenian Wikipedia (hy.wikipedia.org) filtered for Western Armenian

## Nayiri Dictionary
- Dictionary: nayiri.com
```

**docs/BUILDING.md** — How to run corpus builder:
```markdown
# Building the Corpus

## Quick Start
pip install wa-corpus
python -m wa_corpus --all --output-dir ~/wa-data

## Individual Sources
python -m wa_corpus --newspapers
python -m wa_corpus --ia --max-items 100
python -m wa_corpus --wiki
python -m wa_corpus --nayiri
python -m wa_corpus --aggregate

## Output
- ~15GB total data
- Frequency rankings in: aggregated/frequency_rank.json
```

**Create docs/DATA_QUALITY.md** — Statistics:
```markdown
# Data Quality Report (as of March 6, 2026)

## Coverage
- Internet Archive: ~9763 files, 15GB text
- Newspapers: 995 articles scraped
- Wikipedia: [size TBD]
- Dictionary: [size TBD]

## Tokenization Coverage
- Words with frequency rank: 8,395 (100% of Anki deck)
- Level 1-2 coverage: 88-97%
- Level 3-5 coverage: 51-60%
```

### Step 1g: Verify Package Works (1 hour)
```bash
cd wa-corpus
pip install -e ".[dev]"
pytest  # Run all tests
python -m wa_corpus --help  # Check CLI works
```

### ✅ Phase 1 Complete Checklist
- [ ] New `wa-corpus` repo created with proper structure
- [ ] All scraper files moved with imports updated
- [ ] pyproject.toml created and verified
- [ ] .gitignore prevents data leak
- [ ] Tests run successfully
- [ ] Documentation (SOURCES.md, BUILDING.md, DATA_QUALITY.md) created
- [ ] `pip install -e .` works locally
- [ ] Ready to push to GitHub

---

## Phase 2: Extract `armenian-linguistics` (3-5 hours, Days 3-5)

### Step 2a: Create New Repository Structure (30 mins)
```bash
mkdir armenian-linguistics
cd armenian-linguistics

mkdir -p src/armenian_linguistics/{phonetics,morphology,analysis,converters,utils}
mkdir -p tests
mkdir -p docs/{references}
```

**Files to create:**
- [ ] `src/armenian_linguistics/__init__.py`
- [ ] `src/armenian_linguistics/phonetics/__init__.py` + modules
- [ ] `src/armenian_linguistics/morphology/__init__.py` + modules
- [ ] `src/armenian_linguistics/analysis/__init__.py` + modules
- [ ] `src/armenian_linguistics/converters/__init__.py` + modules
- [ ] `src/armenian_linguistics/utils/__init__.py`
- [ ] `pyproject.toml`
- [ ] `README.md`
- [ ] `docs/API.md` — Full API reference
- [ ] `docs/PHONETICS.md` — Rules & mapping
- [ ] `docs/MORPHOLOGY.md` — Grammar & verb tables
- [ ] `docs/EXAMPLES.md` — Usage examples

### Step 2b: Move Phonetics Files (45 mins)
```bash
# From old lousardzag:
cp 02-src/lousardzag/phonetics.py → src/armenian_linguistics/phonetics/core.py
cp 02-src/lousardzag/letter_data.py → src/armenian_linguistics/utils/letter_data.py

# Create additional files:
# src/armenian_linguistics/phonetics/
#   ├── __init__.py (export public API)
#   ├── core.py (existing phonetics.py)
#   ├── transcription.py (word→IPA, text→IPA)
#   ├── difficulty.py (phonetic difficulty scoring)
#   └── data.py (ARMENIAN_PHONEMES, DIGRAPHS constants)
```

**Update imports in phonetics/core.py:**
- Remove any deps on `lousardzag.letter_data`
- Update to `from armenian_linguistics.utils.letter_data import ...`

### Step 2c: Move Morphology Files (1 hour)
```bash
# Copy entire directory:
cp -r 02-src/lousardzag/morphology/ → src/armenian_linguistics/morphology/

# Reorganize (optional, can do in Phase 2b refactoring):
# src/armenian_linguistics/morphology/
#   ├── __init__.py
#   ├── core.py (existing core.py)
#   ├── nouns.py (extract from core.py or existing)
#   ├── verbs.py (verb_forms.py, irregular_verbs.py)
#   ├── adjectives.py (new, if needed)
#   ├── difficulty.py (morphological complexity scoring)
#   └── data/
#       ├── irregular_verbs.py
#       └── phoneme_difficulty.json
```

**Update all imports within morphology/**:
- Change internal imports to use relative paths
- Remove any `lousardzag` imports

### Step 2d: Move Analysis Files (45 mins)
```bash
cp 02-src/lousardzag/analysis_utils.py → src/armenian_linguistics/analysis/analysis_utils.py
cp 02-src/lousardzag/stemmer.py → src/armenian_linguistics/analysis/stemmer.py
cp 02-src/lousardzag/dialect_classifier.py → src/armenian_linguistics/analysis/dialect_classifier.py

# Create:
# src/armenian_linguistics/analysis/
#   ├── __init__.py
#   ├── analysis_utils.py
#   ├── pos_tagger.py (rename from analysis_utils.py's POS funcs)
#   ├── stemmer.py
#   ├── dialect_classifier.py
#   ├── validators.py (Armenian validation)
#   └── text_cleaner.py (diacritic removal, normalization)
```

### Step 2e: Create Converter Modules (1 hour)
**New files to create:**
- [ ] `src/armenian_linguistics/converters/ipa_converter.py` — Word and text-level Armenian→IPA
- [ ] `src/armenian_linguistics/converters/transliterator.py` — Armenian→Latin (ISO 9985)
- [ ] `src/armenian_linguistics/converters/romanizer.py` — Wrapper around existing `romanize()`
- [ ] `src/armenian_linguistics/converters/csv_exporter.py` — Export vocabulary with linguistic data

### Step 2f: Create __init__.py Files & Public API (45 mins)
**`src/armenian_linguistics/__init__.py`** — Main export:
```python
"""
Armenian Linguistics Toolkit
Western Armenian phonetics, morphology, and analysis tools
"""

from .phonetics import (
    get_phonetic_transcription,
    calculate_phonetic_difficulty,
    get_pronunciation_guide,
    ARMENIAN_PHONEMES,
    ARMENIAN_DIGRAPHS,
)

from .morphology import (
    get_noun_forms,
    get_verb_conjugation,
    romanize,
    count_syllables,
)

from .analysis import (
    infer_pos_tag,
    stem_word,
    classify_dialect,
)

from .converters import (
    armenian_text_to_ipa,
    armenian_text_to_transliteration,
    export_vocabulary_csv,
)

__version__ = "0.1.0"
__all__ = [
    # Phonetics
    "get_phonetic_transcription",
    "calculate_phonetic_difficulty",
    "get_pronunciation_guide",
    "ARMENIAN_PHONEMES",
    "ARMENIAN_DIGRAPHS",
    # Morphology
    "get_noun_forms",
    "get_verb_conjugation",
    "romanize",
    "count_syllables",
    # Analysis
    "infer_pos_tag",
    "stem_word",
    "classify_dialect",
    # Converters
    "armenian_text_to_ipa",
    "armenian_text_to_transliteration",
    "export_vocabulary_csv",
]
```

### Step 2g: Move & Update Tests (1 hour)
- [ ] `tests/test_phonetics.py` — Copy from 04-tests/unit/test_phonetics.py
- [ ] `tests/test_morphology.py` — Copy from 04-tests/unit/test_morphology.py
- [ ] `tests/test_analysis.py` — New or copy from existing
- [ ] `tests/conftest.py` — Test fixtures
- [ ] Update all imports to use new `armenian_linguistics` package

### Step 2h: Create Documentation (1.5 hours)
**docs/API.md** — Full API reference:
```markdown
# Armenian Linguistics API

## Phonetics Module

### get_phonetic_transcription(word: str) -> Dict
Transcribe Armenian word to IPA with difficulty score.
...

### ARMENIAN_PHONEMES: Dict[str, Dict]
All 38 western Armenian phonemes with mappings.
...

## Morphology Module
...

## Analysis Module
...

## Converters Module
...
```

**docs/PHONETICS.md** — Rules (copy from memory file + source code):
**docs/MORPHOLOGY.md** — Grammar (copy from docs + source code)
**docs/EXAMPLES.md** — Usage examples

### Step 2i: Create pyproject.toml (30 mins)
```toml
[project]
name = "armenian-linguistics"
version = "0.1.0"
description = "Western Armenian phonetics, morphology, and linguistic analysis tools"
readme = "README.md"
requires-python = ">=3.10"

dependencies = []  # Pure Python, no external data deps!

[project.optional-dependencies]
dev = ["pytest>=7.0.0", "pytest-cov>=4.0.0"]

[tool.setuptools]
packages = ["armenian_linguistics"]
package-dir = { "" = "src" }
```

### Step 2j: Verify Package Works (1 hour)
```bash
cd armenian-linguistics
pip install -e ".[dev]"
pytest  # 100% coverage of phonetics, morphology, analysis
python -c "from armenian_linguistics import *; print(ARMENIAN_PHONEMES.keys())"
```

### ✅ Phase 2 Complete Checklist
- [ ] New `armenian-linguistics` repo created with modular structure
- [ ] All phonetics, morphology, analysis files moved
- [ ] Converters created (IPA, transliteration, CSV export)
- [ ] Public API defined in `__init__.py` files
- [ ] All imports updated (no external lousardzag references)
- [ ] Tests updated and passing (100% coverage target)
- [ ] Documentation complete (API.md, PHONETICS.md, MORPHOLOGY.md, EXAMPLES.md)
- [ ] pyproject.toml has ZERO external dependencies (pure Python, reusable)
- [ ] `pip install -e .` works locally
- [ ] Ready to push to GitHub

---

## Phase 3: Refactor `lousardzag` (5-7 hours, Days 6-10)

### Step 3a: Update pyproject.toml (30 mins)
**Add new dependencies:**
```toml
dependencies = [
    "armenian-linguistics>=0.1.0",  # NEW!
    "pandas>=1.3.0",
    "requests>=2.25.0",
    "fastapi>=0.112.0",
    "uvicorn>=0.30.0",
]

[project.optional-dependencies]
corpus = ["wa-corpus>=0.1.0"]  # NEW!
dev = [...]
```

### Step 3b: Create src/lousardzag/ Directory Structure (30 mins)
```bash
mkdir -p src/lousardzag/{core,anki,enrichment,database,ui}
# OR reorganize existing 02-src/lousardzag/
```

**Plan:**
- [ ] `src/lousardzag/core/` — Card generation, sentence progression, card learning logic
- [ ] `src/lousardzag/anki/` — Anki integration (was anki_connect.py)
- [ ] `src/lousardzag/enrichment/` — Database enrichment (frequency, levels, morphology)
- [ ] `src/lousardzag/database/` — SQLite operations, models, migrations
- [ ] `src/lousardzag/ui/` — Web server, viewer UIs
- [ ] `src/lousardzag/templates/` — Keep as-is

### Step 3c: Delete/Refactor Linguistic Files (1 hour)
**Delete (now in armenian-linguistics):**
- [ ] `02-src/lousardzag/phonetics.py` — DELETE
- [ ] `02-src/lousardzag/morphology/` — DELETE
- [ ] `02-src/lousardzag/stemmer.py` — DELETE
- [ ] `02-src/lousardzag/analysis_utils.py` — DELETE
- [ ] `02-src/lousardzag/letter_data.py` — DELETE
- [ ] `02-src/lousardzag/dialect_classifier.py` — DELETE

**Create aliases (for backward compat, Phase 3 final iteration):**
```python
# 02-src/lousardzag/phonetics.py (backward compat shim)
"""DEPRECATED: Import from armenian_linguistics instead."""
import warnings
from armenian_linguistics.phonetics import *

warnings.warn(
    "Importing from lousardzag.phonetics is deprecated. "
    "Use armenian_linguistics.phonetics instead.",
    DeprecationWarning,
    stacklevel=2,
)
```

### Step 3d: Update All Imports in Core Files (2 hours)
**Files to update:**
- [ ] `02-src/lousardzag/card_generator.py` — Change imports to use `armenian_linguistics`
- [ ] `02-src/lousardzag/sentence_generator.py` — Change imports
- [ ] `02-src/lousardzag/sentence_progression.py` — Change imports
- [ ] `02-src/lousardzag/anki_connect.py` → `core/anki_connect.py` + rename to `anki/connect.py`

---

## Conversation Addendum - March 6, 2026 (Execution Learnings)

### Completed During Conversation
- Implemented and validated a rule-based dialect classifier with evidence tracing.
- Added classifier CLI and unit tests.
- Repaired API/CLI integration test drift and reran passing suites.
- Updated quick reference diphthong table with missing entries (`եա`, `ոյ`, `այ`).

### Actionable Follow-Up
- [ ] Add mixed-marker classifier test fixtures (Western + Eastern in one input).
- [ ] Add boundary-focused regex regression tests.
- [ ] Add optional dialect quality-gate integration in vocab/corpus pipelines.
- [ ] Add compact confidence-guidance doc for consumers of classifier output.

### Planning Note
These follow-ups are implementation-level and can be scheduled independently from the package extraction phases above.
- [ ] `02-src/lousardzag/database.py` → `database/` subdirectory
- [ ] `02-src/lousardzag/letter_audio.py` — Update imports

**Example transformation:**
```python
# OLD:
from lousardzag.phonetics import get_phonetic_transcription
from lousardzag.morphology import get_noun_forms
from lousardzag.stemmer import stem_word

# NEW:
from armenian_linguistics import (
    get_phonetic_transcription,
    get_noun_forms,
    stem_word,
)
```

### Step 3e: Organize 03-cli/ Files (45 mins)
**Option A: Consolidate into src/lousardzag/cli.py**
```bash
# Create:
src/lousardzag/cli.py  # Main CLI dispatcher

# Import functions from:
- src/lousardzag/core/card_generator.py → generate_cards()
- src/lousardzag/database/operations.py → pull_anki_data()
- src/lousardzag/ui/preview_server.py → preview_server()
```

**Option B: Keep 03-cli/ separate**
- [ ] Update all imports in `03-cli/*.py` to use new package structure
- [ ] Keep as-is for backward compat

### Step 3f: Update Tests (1.5 hours)
**Files to update:**
- [ ] `04-tests/unit/test_*.py` — Change imports from `lousardzag.*` to `armenian_linguistics.*`
- [ ] `04-tests/integration/test_*.py` — Update imports
- [ ] `04-tests/e2e/test_*.py` — Update imports
- [ ] Add new tests for enrichment features (frequency mapper, level assigner)

**Run tests:**
```bash
pytest 04-tests/ --cov=src/lousardzag --cov-report=term-missing
```

### Step 3g: Update Documentation (1 hour)
- [ ] Update `README.md` to show new package structure
- [ ] Create `ARCHITECTURE.md` explaining 3-package design
- [ ] Create `MIGRATION.md` guide for users of old package
- [ ] Update `01-docs/INDEX.md` to link to new packages
- [ ] Add install instructions:
  ```bash
  # Full install with corpus building
  pip install lousardzag[corpus]
  
  # Just learning platform
  pip install lousardzag
  
  # Just linguistic tools
  pip install armenian-linguistics
  ```

### Step 3h: Test Complete Integration (1 hour)
```bash
# Fresh environment
python -m venv test_env
source test_env/bin/activate  # or: test_env\Scripts\activate on Windows

# Install all three packages
pip install -e ../wa-corpus
pip install -e ../armenian-linguistics
pip install -e .

# Test imports
python -c "from armenian_linguistics import *; print('✓ Linguistics')"
python -c "from wa_corpus import *; print('✓ Corpus')"
python -c "from lousardzag import *; print('✓ Lousardzag')"

# Run full test suite
pytest 04-tests/

# Test CLI
python -m lousardzag.cli --help
```

### Step 3i: Create deployment docs (30 mins)
- [ ] `DEPLOYMENT.md` — How to deploy with new structure
- [ ] GitHub Actions CI/CD config — Test with all 3 packages
- [ ] GitHub Actions CD — Auto-publish to PyPI

### ✅ Phase 3 Complete Checklist
- [ ] Updated `pyproject.toml` with new dependencies
- [ ] Deleted linguistic tool files (now in armenian-linguistics)
- [ ] Created backward compat shims if needed
- [ ] Updated ALL imports across codebase
- [ ] Reorganized directory structure (optional, can refactor incrementally)
- [ ] Tests pass with 90%+ coverage
- [ ] Documentation updated (README, ARCHITECTURE, MIGRATION guides)
- [ ] Full integration test: import all 3 packages, run tests
- [ ] Deployment docs created
- [ ] Ready to release as v1.0.0

---

## Post-Phase-3: Publishing & Roadmap

### Publishing (1-2 hours)
```bash
# Make sure you're on GitHub
git remote add origin https://github.com/yourusername/lousardzag
git push -u origin main

# Ensure PyPI setup (if desired)
pip install build twine

# Build distributions
python -m build

# Upload to PyPI
python -m twine upload dist/*
```

### Next Steps After Restructuring
- [ ] Set up GitHub Pages for documentation
- [ ] Create ci-cd workflow for automatic testing on PRs
- [ ] Create CONTRIBUTING.md
- [ ] Set up Discord/community discussion channel
- [ ] Plan v1.1 features (optional: `armenian-audio` package for TTS)

---

## Rollback Plan (If Needed)

If you need to back out during restructuring:

**Worst case**: Keep all files in place, just do logical separation:
- Don't extract to separate repos
- Create 3 subdirectory namespaces: `lousardzag/corpus/`, `lousardzag/linguistics/`, `lousardzag/learning/`
- Same dependencies, but less modular
- Can always extract to separate repos later

**During Phase 1**: If wa-corpus extraction fails, keep scrapers in main repo
**During Phase 2**: If linguistics extraction fails, keep tools in main repo
**During Phase 3**: If lousardzag refactor breaks, use git revert

---

## Effort Tracking

Track your time for each phase:

```markdown
# Time Log

## Phase 1: wa-corpus
- Step 1a: 0h30m
- Step 1b: 1h00m
- Step 1c: 0h45m
- Step 1d: 0h30m
- Step 1e: 0h45m
- Step 1f: 1h00m
- Step 1g: 1h00m
**Phase 1 Total: 5h30m** (target: 4-6h)

## Phase 2: armenian-linguistics
...

## Phase 3: lousardzag refactor
...
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Circular imports | Use TYPE_CHECKING, defer imports, or restructure modules |
| Data files missing | Create `.gitkeep` files in empty directories; document data setup |
| Tests fail after refactor | Update fixtures, check import paths, ensure test DB isolation |
| Old imports break | Create shim files with deprecation warnings; update docs |
| Package install fails | Check pyproject.toml syntax, ensure package-dir correct |
