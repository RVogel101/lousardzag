# Project Assessment - March 6, 2026 (Updated)

## Executive Summary

**Lousardzag** is a Western Armenian learning platform in active development. The core infrastructure is **operational**, with 323+ tests passing and multiple functional systems. Card enrichment Phase 1 is **complete** (8,395 cards with syllable counts, POS tags, and phonetics). A 3-phase package extraction plan exists. The project is ready for **Phase 2 enrichment and modular architecture work**.

---

## Current State Overview

### ✅ What's Working

#### Core Systems (Production-Ready)
1. **Morphological Analysis** (Complete)
   - Noun declension (8 cases)
   - Verb conjugation (15 tenses)
   - Irregular verb handling
   - Syllable counting

2. **Vocabulary Ordering System** (Complete)
   - 5 ordering modes: frequency, pos_frequency, band_pos_frequency, difficulty, difficulty_band
   - 3 batch strategies: fixed, growth, banded
   - 4 presets: l1-core, l2-expand, l3-bridge, n-standard
   - Output: CSV + HTML with phonetic columns
   - N1-N7 proficiency labeling (7 contiguous blocks)
   - Works: Generates vocab_n_standard.csv (140 words) with phonetic data

3. **Western Armenian Phonetics Module** (Complete)
   - ARMENIAN_PHONEMES dict (38 letters)
   - IPA transcription + English approximations
   - Phonetic difficulty scoring (1-5 scale)
   - Context-aware letters documented
   - **Critical**: Voicing reversal pattern correctly implemented for Western Armenian

4. **Flashcard Generation** (Functional)
   - generate_ordered_cards.py: 40-word card generation with syllable controls
   - Sentence progression framework with difficulty tracking
   - Prerequisite validation

5. **Database & Corpus Integration**
   - 8,395 unique vocabulary entries (deduplicated from 8,574)
   - Frequency mapping to 1.47M corpus entries
   - Sentence/phrase filtering (26 cards removed)
   - Multiple corpus scrapers (newspapers, Internet Archive, wiki)

6. **Card Enrichment Phase 1** (Complete as of March 5)
   - Syllable counting: 100% of 8,395 cards enriched
   - POS tag inference: 100% of 8,395 cards tagged
   - Phonetics enrichment: 100% of 8,395 cards have IPA, pronunciation, difficulty
   - Database schema upgraded with frequency_rank, syllable_count, morphology_json, custom_level columns

7. **Dialect Classifier** (New, March 6)
   - Rule-based Western/Eastern Armenian classifier in `dialect_classifier.py`
   - CLI wrapper: `07-tools/analysis/classify_dialect.py`
   - Conservative `inconclusive` default when evidence is insufficient
   - Source-traceable evidence for each classification decision

8. **Package Extraction Plan** (New, March 6)
   - 3-phase plan documented in IMPLEMENTATION_ACTION_PLAN.md
   - Phase 1: Extract `wa-corpus` (corpus tools)
   - Phase 2: Extract `armenian-linguistics` (phonetics, morphology, analysis)
   - Phase 3: Refactor `lousardzag` (learning platform consuming the above)

#### Testing Infrastructure
- 323 tests across unit and integration suites
- Test categories:
  - Card generation tests: 9 passing
  - Transliteration tests: 60+ passing
  - Difficulty scoring tests: 28+ passing
  - Verb expansion tests: 11+ passing
  - FSRS (spaced repetition): 17+ passing
  - Progression tests: 35+ passing
  - Phrase wiring tests: 38+ passing
  - Database tests: 28+ passing
  - Corpus tests: 40+ passing

#### Data Outputs
Generated vocabulary files:
- vocab_n_standard.csv (140 words, phonetically annotated)
- vocab_l1_core.csv
- vocab_preset_l1.csv, l2.csv, l3.csv
- vocab_ordered_custom.csv

---

### ❌ What's Missing or Incomplete

#### Documentation
The following guide documents now exist (created March 3-5):
- [x] WESTERN_ARMENIAN_PHONETICS_GUIDE.md — `01-docs/references/`
- [x] VOCABULARY_ORDERING_GUIDE.md — `01-docs/guides/`
- [x] NEXT_SESSION_INSTRUCTIONS.md — `01-docs/development/`
- [x] ARMENIAN_QUICK_REFERENCE.md — `01-docs/references/`
- [x] INDEX.md (navigation guide) — `01-docs/`

**Still needed:**
- [ ] Environment setup guide for speech tooling (espeak-ng, MMS, conda environments)
- [ ] Confidence interpretation docs for dialect classifier
- [ ] ARCHITECTURE.md for 3-package design (post-extraction)

#### Feature Incompleteness

0. **Card Enrichment Phase 2** (Columns exist, data empty)
   - `frequency_rank`: 0% — needs corpus frequency mapping (depends on corpus builder fix)
   - `custom_level`: 0% — needs difficulty/progression assignment (depends on frequency mapper)
   - `morphology_json` (full): Currently has phonetics only; needs declensions/conjugations

1. **Context-Aware Phonemes** (Documented but not fully implemented)
   - ո: Position-dependent (v before consonants, ɔ elsewhere)
   - ե: Position-dependent (ye at word start, e elsewhere)
   - յ: Position-dependent (h at start, j elsewhere)
   - ւ: Position-dependent (v between vowels, u in diphthongs)
   - **Status**: get_phonetic_transcription() needs word-position parsing

2. **Diphthongs** (Partially implemented)
   - Currently: 3 entries (ու, իւ) 
   - Status: Placeholder structure, incomplete list

3. **Digraphs** (Not implemented)
   - Framework exists but empty implementation

#### Nayiri Dictionary Integration

**Status**: BROKEN (documented in /memories/nayiri-implementation-note.md)
- Current approach: Search-based with 2-letter prefixes (returns "word not found")
- Only returns 148 entries instead of thousands
- **Solution needed**: Switch to page-based browsing with imagepage.php
- **Priority**: LOW (deferred in favor of other features)

#### Known Limitations

1. Stress/accent marking not implemented
2. Historical/etymology notes not included
3. Regional dialect variations not handled
4. Spaced repetition integration incomplete
5. Interactive pronunciation guide generation not done

---

## Branch Status

**Current Branch**: pr/copilot-swe-agent/2

**Last Commits**:
```
2d8d9a3 docs: Comprehensive documentation update with phonetics, v...
          (README.md, .github/copilot-instructions.md updated)

760ac8f chore: Add corpus analysis and vocabulary mapping utilities
97d2e54 refactor: Enhance core modules with vocabulary ordering and phonetics
4205c61 feat: Add sentence progression framework
61c2c64 feat: Add configurable vocabulary ordering and proficiency system
760ac8f feat: Add Western Armenian phonetic transcription module
```

**Pending**: Uncommitted changes from March 6 session (dialect classifier, session docs, future ideas).

---

## Test Coverage

| Category | Count | Status |
|----------|-------|--------|
| Card Generation | 9 | ✅ Pass |
| Integration Overall | 175+ | ✅ Pass |
| Unit Tests | 140+ | ✅ Pass |
| Dialect Classifier | New | ✅ Pass |
| **TOTAL** | **323+** | ✅ **ALL PASS** |

No failing tests reported.

---

## Next Session Recommendations (Updated March 6)

### Tier 1: IMMEDIATE (Critical Path)

**1. Generate Letter Audio** (1-2 hours)
- Create audio for all 38 Armenian letters using IPA-direct synthesis (espeak-ng) or MMS
- Unblocks letter card viewer pronunciation feature
- **Files**: Create `07-tools/generate_letter_audio_ipa_espeak.py`

**2. Fix Corpus Builder** (1-2 hours)
- Debug newspaper scraper network/parsing issues
- Test each source individually
- Add retry with backoff and continue-on-error mode
- **Why**: Blocks frequency mapping (Phase 2 enrichment)

**3. Frequency Mapper** (1-2 hours)
- Link 8,395 vocabulary cards to corpus frequency ranks
- Update `cards.frequency_rank` in SQLite database
- **Depends on**: Corpus builder fix (#2)
- **File**: `07-tools/enrich_card_frequency.py` (new)

### Tier 2: HIGH PRIORITY (Feature Advancement)

**4. Level Assignment** (1-2 hours)
- Assign N1-N7 style progression levels based on frequency + syllables
- Update `cards.custom_level` in database
- **Depends on**: Frequency mapper (#3)

**5. Implement Context-Aware Phoneme Logic** (2-3 hours)
- Enhance get_phonetic_transcription() to detect word position
- Apply context rules for ո, ե, յ, ւ
- Add comprehensive tests
- **Files**: 02-src/lousardzag/phonetics.py

**6. Expand Dialect Classifier** (1-2 hours)
- Add mixed-signal tests (texts with both Eastern and Western markers)
- Add punctuation/boundary edge-case tests
- Add CSV/JSONL output mode for analysis pipelines
- Wire into vocab generation as optional `--dialect-gate`

### Tier 3: MEDIUM PRIORITY (Quality & Architecture)

**7. Package Extraction Phase 1: wa-corpus** (4-6 hours)
- Follow IMPLEMENTATION_ACTION_PLAN.md Phase 1
- Extract corpus tools to standalone package
- Create pyproject.toml, tests, documentation

**8. Build Armenian-to-IPA Text Converter** (2-3 hours)
- Sentence/text-level IPA converter (beyond single-word)
- **File**: `02-src/lousardzag/converters.py`

**9. Fix Nayiri Dictionary Scraper** (2-3 hours)
- Rewrite to use page-based browsing (requires IP whitelist from Serouj)
- **Files**: wa_corpus/nayiri_scraper.py

**7. Enhance Vocabulary Filtering** (1.5 hours)
- Refine sentence/phrase detection heuristics
- Add POS-based filtering options
- Improve example validation
- **Files**: 07-tools/gen_vocab_simple.py
- **Why**: Currently removes 26 sentence cards; could be smarter

**8. Add Stress/Accent Marking** (2 hours)
- Research Western Armenian stress patterns
- Implement stress marking in transcription
- Add to phonetic difficulty calculation
- **Files**: 02-src/lousardzag/phonetics.py
- **Why**: Improves pronunciation accuracy

### Tier 4: LOW PRIORITY (Nice-to-Have)

- Regional dialect support
- Etymology integration
- Interactive pronunciation interface
- Performance optimization for large corpus

---

## Project Metrics

| Metric | Value |
|--------|-------|
| Total Tests | 323 |
| Pass Rate | 100% |
| Documentation Files | 5+ (existing) |
| Vocabulary Entries (DB) | 3,242 |
| Frequency Entries Matched | ~3,084 (95%) |
| Corpus Entries Available | 1.47M |
| Current Vocabulary Output | 140-280 words (configurable) |
| Supported Proficiency Levels | 7 (N1-N7) |

---

## Code Quality Assessment

### Strengths
- ✅ Comprehensive test coverage (323 tests)
- ✅ Clear module separation (morphology, phonetics, corpus, progression)
- ✅ Working vocabulary ordering system with multiple presets
- ✅ Proper git commit history with descriptive messages
- ✅ Configuration-driven tools (gen_vocab_simple.py)

### Areas for Improvement
- ⚠️ Documentation fragmented (no single comprehensive guide)
- ⚠️ Some context-aware logic documented but not implemented
- ⚠️ Nayiri scraper broken (design issue with search approach)
- ⚠️ Some placeholders in digraph/context handling
- ⚠️ Limited inline code comments in complex modules

---

## Timeline Estimate for Recommended Work

| Task | Estimate | Effort |
|------|----------|--------|
| Documentation files | 30-45 min | LOW |
| Context-aware phonemes | 2-3 hours | MEDIUM |
| Diphthong expansion | 45 min | LOW |
| Pronunciation guides | 2 hours | MEDIUM |
| Anki integration | 3-4 hours | HIGH |
| Nayiri scraper fix | 2-3 hours | MEDIUM |
| **TOTAL (All Tiers)** | **13-16 hours** | - |

**Recommended Session Work**: Tier 1 (3-3.5 hours) fully implements critical path

---

## Decision Points for Next Session

**Decision 1**: Start with documentation (recommended) or jump into feature work?
- **Argument for docs first**: Prevents recurring errors, enables confident future work
- **Argument for features first**: Visible progress immediately, documentation can follow

**Decision 2**: Focus on phonetics improvements or Anki integration?
- **Phonetics**: Addresses technical debt, completes documented but unimplemented features
- **Anki**: Delivers end-to-end learning workflow, higher user impact

**Decision 3**: Fix Nayiri scraper or defer?
- **Fix now**: Adds significant data (50K+ entries)
- **Defer**: Acknowledge limitation, prioritize working features

---

## Files to Know (Quick Reference)

| File | Purpose | Status |
|------|---------|--------|
| 02-src/lousardzag/phonetics.py | Armenian phonetics module | ✅ Complete, partially implemented context logic |
| 07-tools/gen_vocab_simple.py | Vocabulary ordering orchestration | ✅ Complete, 4 presets working |
| 02-src/lousardzag/progression.py | Sentence difficulty framework | ✅ Complete, active |
| 02-src/lousardzag/database.py | Vocabulary metadata cache | ✅ Complete, 3,242 entries |
| 04-tests/ | Test suite | ✅ 323 tests passing |
| 08-data/vocab_n_standard.csv | Latest vocabulary output | ✅ 140 words, phonetic data |
| .github/copilot-instructions.md | Session guidelines | ✅ Updated, comprehensive |

---

## Critical Knowledge to Remember

1. **Western Armenian Voicing is Reversed** FROM LETTER APPEARANCE
   - բ (looks voiced) = [p] (unvoiced)
   - պ (looks unvoiced) = [b] (voiced)
   - Same pattern repeats: դ/տ, կ/գ
   - Test word: պետք = "bedk" NOT "petik"

2. **Documentation is Incomplete** — Must be created before major phonetic work

3. **Tests Are Passing** — Infrastructure is stable; safe to refactor

4. **Vocabulary System is Working** — Can generate phonetically-annotated word lists immediately

---

## Conclusion

**Lousardzag is a mature, working platform ready for targeted feature advancement.** 

The core infrastructure (morphology, vocabulary ordering, phonetics) is operational with comprehensive test coverage. Missing critical documentation and some partially-implemented features represent **improvement opportunities, not blockers**.

**Recommended Starting Point**: Complete documentation files (Tier 1), then implement pending context-aware phoneme logic (Tier 2). This positions the project for robust, maintainable growth.

---

**Assessment Date**: March 3, 2026  
**Branch**: pr/copilot-swe-agent/2  
**Assessment Confidence**: HIGH (based on 323 passing tests, working output files, git history)
