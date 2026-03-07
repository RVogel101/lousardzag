# Remaining Work — Lousardzag Project
**Last Updated**: March 5, 2026  
**Status**: 4 critical issues verified FIXED ✅ | Non-critical work documented for future sprints

---

## 🎯 Critical Issues Status (All FIXED ✅)

| Issue | Status | Notes |
|-------|--------|-------|
| Import Errors | ✅ FIXED | Package installed with `pip install -e .` |
| Type Errors | ✅ VERIFIED | No active errors in reporting.py, audio_utils.py |
| Missing Letter Audio | ✅ EXISTS | 81 MP3 files in 08-data/letter_audio/ with full manifest |
| Broken Corpus Builder | ✅ WORKING | Newspaper scraper actively scraping Aztag Daily |

---

## 📋 Short-Term Work (2-3 hours each)

### 3. Expand Irregular Verbs (Priority: HIGH)
**Goal**: Boost sentence generation variety for learners  
**Current State**: ~15 irregular verbs in morphology system  
**Work Required**:
- [ ] Add 15-20 more irregular verbs to `02-src/lousardzag/morphology/irregular_verbs.py`
- [ ] Expand test coverage for all tense/person combinations
- [ ] Validate against corpus examples
- [ ] Test in sentence_progression module

**Files**: 
- `02-src/lousardzag/morphology/irregular_verbs.py`
- `04-tests/unit/test_detect_irregular.py` (currently ~15 test cases)

**Est. Time**: 2-3 hours  
**Dependents**: Sentence generation, vocabulary enrichment pipelines

---

### 4. Vocabulary Coverage Gap Analysis (Level 3-5 Advanced Words)
**Goal**: Identify and close gaps for intermediate-to-advanced learners  
**Current State**:
- Level 1-2: 88-97% corpus coverage ✓
- Level 3-5: 51-60% corpus coverage ⚠️

**Work Required**:
- [ ] Run corpus aggregation: `python -m wa_corpus.build_corpus --aggregate`
- [ ] Analyze unmatched_rank_report.json to identify missing vocabulary
- [ ] Decision point: Expand corpus OR update Anki deck with better sources
- [ ] If expanding: Identify source texts to add (news archives, literature, specialized domains)
- [ ] If updating: Curate additional vocabulary cards from highest-frequency gaps

**Files**:
- `08-data/unmatched_rank_report.json` (analysis input)
- `02-src/wa_corpus/frequency_aggregator.py` (aggregation tool)
- Corpus data: `02-src/wa_corpus/data/` (newspapers, IA, wiki)

**Est. Time**: 2-3 hours (analysis) + 1-2 hours (remediation)  
**Impacts**: Learner progression satisfaction, vocabulary breadth

---

## 🔧 Medium-Term Work (Feature Enhancement)

### 5. Card Enrichment Pipeline — Phase 2 (Priority: HIGH)
**Goal**: Auto-populate remaining database metadata columns  
**Current Status**: Phase 1 ✅ COMPLETE (March 5, 2026)

**Phase 1 Completed** (from CLEANUP_ENRICHMENT_FINAL_REPORT.md):
- ✅ Database cleanup: 179 duplicates removed (8,574 → 8,395 cards)
- ✅ Schema upgrade: Added frequency_rank, syllable_count, morphology_json, custom_level
- ✅ Syllable Counter: 8,395/8,395 populated (100%)
- ✅ POS Tag Inference: 8,395/8,395 populated (100%)
- ✅ Phonetics Enrichment: All cards have IPA, pronunciation, phonetic_difficulty (100%)

**Phase 2 Remaining**:
- `frequency_rank`: 0% populated — needs frequency corpus mapping
- `custom_level`: 0% populated — needs difficulty assignment (1-7 scale)
- `morphology_json`: Partial — has phonetics; needs declensions/conjugations

#### 5a. Frequency Mapper (Est: 1-2 hours)
**Goal**: Link vocabulary words to corpus frequency ranks  
**Work Required**:
- [ ] Create `07-tools/enrich_card_frequency.py`
- [ ] Load aggregated corpus frequency data
- [ ] Match card lemmas to corpus vocabulary
- [ ] Update `cards.frequency_rank` for each card
- [ ] Log match statistics (% matched, gaps)

**Files**:
- New: `07-tools/enrich_card_frequency.py`
- Input: Aggregated corpus frequency (from wa_corpus)
- Target: `08-data/armenian_cards.db`, `frequency_rank` column

**Dependencies**: Corpus builder (item 2) — currently ✅ working

---

#### 5b. Level Assignment Engine (Est: 1-2 hours)
**Goal**: Auto-assign progression level (1-7) based on frequency + complexity  
**Work Required**:
- [ ] Create `07-tools/enrich_card_levels.py`
- [ ] Implement multi-factor difficulty: frequency_rank + syllable_count
- [ ] Define banding rules: Level 1 = most common 1-2 syllables; Level 7 = rare 4+ syllables
- [ ] Update `cards.custom_level` for all 8,395 cards
- [ ] Validate distribution: ensure all levels are represented

**Files**:
- New: `07-tools/enrich_card_levels.py`
- Target: `08-data/armenian_cards.db`, `custom_level` column

**Dependencies**: Frequency Mapper (5a) — provides frequency_rank

---

#### 5c. Morphology Expansion (Est: 2-3 hours)
**Goal**: Add declensions/conjugations to morphology_json  
**Work Required**:
- [ ] Extend current morphology_json structure to include:
  - Full nominal declensions (all 6 cases, singular + plural)
  - Full verb conjugations (present, aorist, perfect, subjunctive, conditional)
  - Links to related cards (e.g., word→genitive form, verb→past participle)
- [ ] Use existing `lousardzag.morphology` routines for generation
- [ ] Update all card morphology_json fields
- [ ] Create validation tests (ensure no null/invalid forms)

**Files**:
- Extend: `07-tools/enrich_anki_database.py` or create `enrich_card_morphology.py`
- Core logic: `02-src/lousardzag/morphology/` (noun_forms.py, verb_forms.py)
- Target: `08-data/armenian_cards.db`, `morphology_json` column

**Dependencies**: Irregular verbs expansion (item 3) — needed for complete conjugation tables

---

### 6. Context-Aware Phoneme Implementation (Est: 2-3 hours)
**Goal**: Accurate pronunciation rules based on word position  
**Current Implementation**: Static phoneme mapping  
**Improvements Needed**:
- [ ] Vowel pronunciation rules:
  - **ե**: /je/ (yeh) at word start; /ɛ/ (eh) in middle/end
  - **ո**: /vo/ before consonants (ոչ=voch, որ=vor); /o/ (oh) as vowel
  - **ե vs է**: Both /ɛ/ but different letters; validate distinction
- [ ] Diphthong context handling: ու (oo) and իւ (yoo) in all positions
- [ ] Consonant cluster rules for epenthesis: շ+բ/գ/կ/պ/տ/ք trigger schwa insertion
- [ ] Implement context-aware predicates in phonetics module

**Files**:
- `02-src/lousardzag/phonetics.py` (add context functions)
- `04-tests/unit/test_phonetics.py` (add context test cases)
- Reference: `/memories/western-armenian-requirement.md`

**Est. Time**: 2-3 hours  
**Validation**: Test against 100 corpus examples with known pronunciations

---

### 7. Anki Integration Bridge (Est: 3-4 hours)
**Goal**: Connect generated vocabulary cards → active Anki deck  
**Current State**: AnkiConnect wrapper exists and works (read-only by default)

**Work Required**:
- [ ] Enhance `03-cli/generate_cards.py` with Anki sync options
- [ ] Implement card push to Anki profile (`armenians_global`)
- [ ] Add FSRS spaced repetition scheduling
- [ ] Create card update/merge logic (avoid duplicates)
- [ ] Add progress tracking and sync logs

**Files**:
- Core: `02-src/lousardzag/anki_connect.py` (wrapper, already working)
- CLI: `03-cli/generate_cards.py` (enhance with Anki options)
- New: `03-cli/sync_to_anki.py` (optional standalone sync tool)

**Est. Time**: 3-4 hours  
**⚠️ Important**: Requires explicit user permission before modifying Anki data

---

### 8. Syllable Counting Logic Validation (Est: 2-3 hours)
**Goal**: Audit and enhance syllable counting for all 8,395+ cards  
**Current Implementation**: `count_vowels()` in `02-src/lousardzag/morphology/core.py`
- Uses vowel count as syllable proxy
- Handles digraph ու correctly as single vowel
- Returns minimum of 1 syllable

**Work Required**:
- [ ] Test current logic against corpus vocabulary samples
- [ ] Document edge cases:
  - Consonant clusters (e.g., վր, ստ, ցր)
  - Final consonants (do they extend syllables?)
  - Weak vowels: How do ե, ի behave in unstressed positions?
  - Diphthongs: Does ու count as 1 or 2 syllables?
- [ ] Validate syllable counts for all 8,395+ database cards
- [ ] Add unit tests for Western Armenian syllabification rules
- [ ] Question: Are Armenian semi-vowels (յ, ւ) handled correctly in all contexts?

**Files**:
- `02-src/lousardzag/morphology/core.py` (current implementation)
- `04-tests/unit/test_morphology.py` (add tests)

**Est. Time**: 2-3 hours  
**Impact**: Foundation for phonetic difficulty scoring, learning progression, rhythm-aware TTS

---

### 9. Armenian-to-IPA Text Converter (Est: 2-3 hours)
**Goal**: Convert full Armenian text (sentences/paragraphs) to IPA, not just words  
**Current State**: `get_phonetic_transcription(word)` converts word-by-word

**Work Required**:
- [ ] Create `02-src/lousardzag/converters.py` with `armenian_text_to_ipa(text)` function
- [ ] Process multi-word text, handle word boundaries and spacing
- [ ] Respect phoneme context rules (vowel position, consonant clusters)
- [ ] Generate formatted IPA output (with syllable markers, stress marks)
- [ ] Add sentence-level tests with corpus examples
- [ ] Integrate into web UI or preview server for live IPA display

**Files**:
- New: `02-src/lousardzag/converters.py`
- Extend: `02-src/lousardzag/phonetics.py` (add context-aware rules from item 6)
- UI integration: `03-cli/preview_server.py` or `03-cli/letter_cards_viewer.py`

**Est. Time**: 2-3 hours  
**Impact**: Pronunciation guides for sentences, speech synthesis, linguistics education

---

### 10. Armenian-to-English Transliteration Converter (Est: 2-3 hours)
**Goal**: Convert full Armenian text to standard Latin transliteration (not just single words)  
**Current State**: `romanize(word)` in `02-src/lousardzag/morphology/core.py` converts word-level script

**Work Required**:
- [ ] Create `02-src/lousardzag/converters.py` with `armenian_text_to_transliteration(text, style='ISO9985')`
- [ ] Define standard mapping table (ISO 9985 or ALA-LC standard)
- [ ] Process full text, preserve formatting/punctuation
- [ ] Compare with existing `romanize()` and consolidate if appropriate
- [ ] Add tests against transliteration standards and corpus examples
- [ ] Integrate into vocabulary export (CSV, flashcard formats)

**Files**:
- New/extend: `02-src/lousardzag/converters.py`
- Reference: `02-src/lousardzag/morphology/core.py` (existing `romanize()`)

**Est. Time**: 2-3 hours  
**Impact**: Education/publishing (transliterated learning materials), data export, non-Unicode accessibility

---

## 📊 Work Summary

| Category | Item | Est. Time | Urgency | Status |
|----------|------|-----------|---------|--------|
| **Short-Term** | 3. Irregular Verbs | 2-3h | HIGH | Not Started |
| | 4. Vocabulary Gaps | 2-3h + remediation | MEDIUM | Not Started |
| **Medium-Term** | 5a. Frequency Mapper | 1-2h | HIGH | Not Started |
| | 5b. Level Assignment | 1-2h | HIGH | Depends on 5a |
| | 5c. Morphology Expansion | 2-3h | MEDIUM | Depends on 3 |
| | 6. Context-Aware Phonemes | 2-3h | MEDIUM | Not Started |
| | 7. Anki Bridge | 3-4h | MEDIUM | Not Started |
| | 8. Syllable Validation | 2-3h | LOW | Not Started |
| | 9. Text-to-IPA Converter | 2-3h | LOW | Not Started |
| | 10. Transliteration Converter | 2-3h | LOW | Not Started |

**Total Estimated Effort**: 20-28 hours of focused development

---

## 🔗 Dependencies & Sequencing

For efficient scheduling, work items have dependencies:

```
Item 5a (Frequency Mapper)
  ├─ depends on: Corpus builder (✅ working)
  └─ enables: 5b (Level Assignment)

Item 5b (Level Assignment)
  ├─ depends on: 5a
  └─ enables: Learning progression features

Item 5c (Morphology Expansion)
  ├─ depends on: 3 (Irregular Verbs)
  └─ enables: Advanced sentence generation

Item 6 (Context-Aware Phonemes)
  └─ enables: Accurate pronunciation (9, TTS improvements)

Item 9 (Text-to-IPA)
  ├─ depends on: 6 (Context rules)
  └─ enables: UI pronunciation guides

Items 7, 8, 10: Independent (can start anytime)
```

---

## 📝 Notes

- **Phase 1 Enrichment Check**: See `CLEANUP_ENRICHMENT_FINAL_REPORT.md` for Phase 1 completion details
- **Corpus Status**: Newspapers scraper ✅ working; verify IA scraper frequency data available
- **Western Armenian Phonetics**: All phoneme references validated against `/memories/western-armenian-requirement.md`
- **Testing Infrastructure**: All items include test file references; ensure pytest coverage ≥85%
