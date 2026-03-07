# Multi-Project Integration Strategy
**Date**: March 6, 2026  
**Scenario**: Combining lousardzag with another similar Armenian language project  
**Goal**: Unified data/package extraction with deduplication and harmonization

---

## Critical Questions First

Before proceeding, we need to understand what you're combining:

### About the Other Project
1. **What type of project is it?**
   - [ ] Another Armenian learning platform?
   - [ ] Corpus/text collection?
   - [ ] Dictionary/lexicon tool?
   - [ ] Linguistic analysis toolkit?
   - [ ] TTS/speech system?

2. **What data/components overlap with lousardzag?**
   - [ ] Vocabulary database (cards, words, translations)?
   - [ ] Corpus data (frequency rankings, text samples)?
   - [ ] Phonetics mappings (IPA, pronunciation)?
   - [ ] Morphology rules (verb conjugations, noun declensions)?
   - [ ] Audio files (TTS, recordings)?
   - [ ] Scrapers (same sources: IA, newspapers)?

3. **What's unique in each project?**
   - Lousardzag has: [fill in]
   - Other project has: [fill in]

4. **Quality comparison**
   - Which has more accurate phonetics? ___________
   - Which has larger corpus? ___________
   - Which has better test coverage? ___________
   - Which has cleaner code structure? ___________

5. **Target architecture**
   - [ ] Merge everything into ONE unified package
   - [ ] Keep separate packages, share common data layer
   - [ ] Extract best-of-both into new canonical packages
   - [ ] Keep both, create integration/bridge layer

---

## How This Changes the Extraction Plan

### Original Plan (Single Project)
```
lousardzag → split into 3 packages:
  1. wa-corpus (data sourcing)
  2. armenian-linguistics (linguistic tools)
  3. lousardzag (learning platform)
```

### New Plan (Multi-Project Integration)

#### Option A: Unified Extraction (Recommended if projects are similar)
```
Project A (lousardzag) ─┐
                        ├─→ Merge & Dedupe ─→ 3 unified packages:
Project B (other)      ─┘                      1. armenian-corpus (best data)
                                               2. armenian-linguistics (best tools)
                                               3. armenian-learning (best platform)
```

#### Option B: Parallel Packages with Shared Base
```
Project A ──→ lousardzag-corpus ───┐
                                    ├──→ armenian-data-unified (shared)
Project B ──→ projectb-corpus ─────┘

Project A ──→ lousardzag-linguistics ──┐
                                        ├──→ armenian-linguistics-unified
Project B ──→ projectb-linguistics ────┘

Each keeps separate learning platform (lousardzag, projectb-app)
```

#### Option C: Bridge Layer (If projects stay separate)
```
lousardzag (3 packages) ────────┐
                                │
armenian-integration (bridge) ──┤  ← New integration package
                                │
other-project (N packages) ─────┘
```

---

## Phase 0: Pre-Extraction Analysis & Harmonization (NEW)
**Time**: 3-5 hours  
**Do this BEFORE starting Phase 1**

### Step 0a: Data Inventory (1 hour)

**Create comparison spreadsheet:**

| Data Type | Lousardzag | Other Project | Overlap | Unique to A | Unique to B | Winner/Merge Strategy |
|-----------|------------|---------------|---------|-------------|-------------|----------------------|
| **Databases** |  |  |  |  |  |  |
| Vocabulary entries | 8,395 cards | ??? | ??? | ??? | ??? | ??? |
| Frequency ranks | Yes (wa_corpus) | ??? | ??? | ??? | ??? | ??? |
| Audio files | 81 letter MP3s | ??? | ??? | ??? | ??? | ??? |
| **Corpus Data** |  |  |  |  |  |  |
| Internet Archive texts | 9,763 files, 15GB | ??? | ??? | ??? | ??? | ??? |
| Newspaper articles | 995 scraped | ??? | ??? | ??? | ??? | ??? |
| Wikipedia | ??? | ??? | ??? | ??? | ??? | ??? |
| **Linguistic Tools** |  |  |  |  |  |  |
| Phonetics (IPA) | 38 phonemes, WA-specific | ??? | ??? | ??? | ??? | ??? |
| Morphology (verbs) | ~15 irregular verbs | ??? | ??? | ??? | ??? | ??? |
| POS tagging | Rule-based inference | ??? | ??? | ??? | ??? | ??? |
| **Code Quality** |  |  |  |  |  |  |
| Test coverage | 377 tests, ~85%? | ??? | ??? | ??? | ??? | ??? |
| Documentation | Extensive | ??? | ??? | ??? | ??? | ??? |

**Action**: Fill this table by analyzing both projects

---

### Step 0b: Database Schema Comparison (1 hour)

**Compare card/vocabulary schemas:**

```python
# Example: lousardzag schema
# 08-data/armenian_cards.db
CREATE TABLE cards (
    id INTEGER PRIMARY KEY,
    word TEXT NOT NULL,
    translation TEXT,
    pos TEXT,
    frequency_rank INTEGER,
    syllable_count INTEGER,
    morphology_json TEXT,
    metadata_json TEXT,
    custom_level INTEGER,
    ...
)

# Other project schema:
# ???.db
CREATE TABLE ??? (
    ???
)
```

**Questions:**
- Do column names match? (word vs armenian_word vs term?)
- Do data types match? (INTEGER vs TEXT for frequency_rank?)
- Which has more enrichment fields?
- Can schemas be unified or need migration?

**Action**: Document schema differences, plan unified schema

---

### Step 0c: Phonetics/Morphology Validation (1.5 hours)

**Critical**: Western Armenian phonetics MUST be accurate!

**Test both projects:**

```python
# Test case: պետք should be "bedk" (b-e-d-k)
# If either project returns "petik" → Eastern Armenian, WRONG

test_words = [
    ("պետք", "bedk"),      # պ=b, տ=d (reversed voicing)
    ("ժամ", "zham"),       # ժ=zh
    ("ջուր", "choor"),     # ջ=ch  
    ("ոչ", "voch"),        # ո=vo before consonant
    ("իւր", "yur"),        # իւ=yoo diphthong
]

# Run against both projects:
for word, expected in test_words:
    result_a = lousardzag.phonetics.get_phonetic_transcription(word)
    result_b = other_project.phonetics.get_phonetic_transcription(word)
    
    if result_a != expected:
        print(f"⚠️ Lousardzag WRONG: {word} → {result_a} (expected {expected})")
    if result_b != expected:
        print(f"⚠️ Other project WRONG: {word} → {result_b} (expected {expected})")
```

**If other project uses Eastern Armenian phonetics:**
- ❌ **Cannot merge phonetics modules directly**
- ✅ **Use lousardzag phonetics as canonical**
- 📝 **Document other project as "Eastern Armenian variant" (separate package)**

**If both use Western Armenian correctly:**
- ✅ **Can merge phonetics modules**
- 🔍 **Compare accuracy on edge cases (diphthongs, context-dependent letters)**
- 🏆 **Choose most comprehensive or merge best features**

---

### Step 0d: Corpus Deduplication Strategy (1.5 hours)

**If other project has corpus data:**

```python
# Example deduplication pseudocode
from collections import Counter

# Load both corpora
corpus_a = load_corpus("lousardzag/wa_corpus/data/")  # 15GB
corpus_b = load_corpus("other_project/corpus/")       # ???GB

# Find overlaps
texts_a = set(corpus_a.get_all_texts())
texts_b = set(corpus_b.get_all_texts())

overlap = texts_a & texts_b
unique_a = texts_a - texts_b
unique_b = texts_b - texts_a

print(f"Overlap: {len(overlap)} texts")
print(f"Unique to A: {len(unique_a)} texts")
print(f"Unique to B: {len(unique_b)} texts")

# Frequency ranking comparison
freq_a = corpus_a.get_frequency_ranks()
freq_b = corpus_b.get_frequency_ranks()

# Example word: "տուն" (house)
word = "տուն"
rank_a = freq_a.get(word, None)  # e.g., rank 150
rank_b = freq_b.get(word, None)  # e.g., rank 180

# Decision: How to combine?
# Option 1: Take average
combined_rank = (rank_a + rank_b) / 2

# Option 2: Weighted by corpus size
combined_rank = (rank_a * size_a + rank_b * size_b) / (size_a + size_b)

# Option 3: Prefer one source (e.g., larger corpus)
combined_rank = rank_a if size_a > size_b else rank_b
```

**Decision Matrix:**

| Scenario | Strategy |
|----------|----------|
| Other project has SAME sources (IA, newspapers) | Deduplicate, keep latest scrape |
| Other project has DIFFERENT sources | Combine all sources, aggregate frequencies |
| Other project has SMALLER corpus | Import into lousardzag, use as supplement |
| Other project has LARGER corpus | Use as primary, import lousardzag as supplement |
| Frequency rankings differ significantly | Investigate quality, choose more reliable source |

---

## Modified Extraction Timeline

### NEW Phase 0: Pre-Extraction (3-5 hours) — **DO THIS FIRST**
- [ ] Step 0a: Data inventory comparison (1h)
- [ ] Step 0b: Database schema comparison (1h)
- [ ] Step 0c: Phonetics/morphology validation (1.5h)
- [ ] Step 0d: Corpus deduplication strategy (1.5h)
- [ ] **Decision point**: Option A, B, or C architecture?

### Phase 1: Extract & Merge Corpus Data (6-8 hours, was 4-6h)
**Additional work:**
- [ ] Step 1a-g: Original wa-corpus extraction (4-6h)
- [ ] **Step 1h: Import other project corpus** (1h)
  - Copy corpus data from other project
  - Run deduplication script
  - Combine frequency rankings
- [ ] **Step 1i: Unified corpus validation** (1h)
  - Verify frequency ranks are sensible
  - Check for data corruption
  - Generate combined statistics report

### Phase 2: Extract & Merge Linguistic Tools (5-7 hours, was 3-5h)
**Additional work:**
- [ ] Step 2a-j: Original armenian-linguistics extraction (3-5h)
- [ ] **Step 2k: Compare phonetics implementations** (1h)
  - Run test suite against both
  - Identify discrepancies
  - Choose canonical implementation or merge
- [ ] **Step 2l: Compare morphology implementations** (1h)
  - Compare verb conjugation accuracy
  - Check irregular verb tables
  - Merge unique verbs from both projects

### Phase 3: Refactor & Integrate Platforms (7-10 hours, was 5-7h)
**Additional work:**
- [ ] Step 3a-i: Original lousardzag refactor (5-7h)
- [ ] **Step 3j: Import other project features** (1-2h)
  - Identify unique features in other project
  - Port to lousardzag or keep separate
  - Update dependencies
- [ ] **Step 3k: Unified testing** (1h)
  - Run both test suites
  - Create integration tests
  - Verify data flows correctly

**New Total Effort: 18-25 hours** (was 12-18 hours)

---

## Integration Patterns

### Pattern 1: Database Merge (if both have vocabulary DBs)

```python
# merge_databases.py
import sqlite3

def merge_vocabulary_databases(db_a_path, db_b_path, output_path):
    """Merge two vocabulary databases with deduplication."""
    
    conn_a = sqlite3.connect(db_a_path)
    conn_b = sqlite3.connect(db_b_path)
    conn_out = sqlite3.connect(output_path)
    
    # Strategy 1: Union (keep all, prefer A on conflicts)
    # Strategy 2: Intersection (only keep words in both)
    # Strategy 3: Best-of-both (richer metadata wins)
    
    # Example: Best-of-both
    cursor_a = conn_a.execute("SELECT * FROM cards")
    cursor_b = conn_b.execute("SELECT * FROM vocabulary")  # Different table name
    
    words_a = {row[1]: row for row in cursor_a}  # {word: row_data}
    words_b = {row[0]: row for row in cursor_b}  # Different schema!
    
    # Merge logic
    merged = {}
    for word in set(words_a.keys()) | set(words_b.keys()):
        row_a = words_a.get(word)
        row_b = words_b.get(word)
        
        if row_a and row_b:
            # Both have this word: merge metadata
            merged[word] = merge_metadata(row_a, row_b)
        else:
            # Only one has it: use that one
            merged[word] = row_a or row_b
    
    # Write to output
    for word, data in merged.items():
        conn_out.execute("INSERT INTO unified_cards VALUES (...)", data)
    
    conn_out.commit()
    print(f"Merged {len(merged)} unique words")
    print(f"  From A: {len(words_a)} words")
    print(f"  From B: {len(words_b)} words")
    print(f"  Overlap: {len(words_a.keys() & words_b.keys())} words")
```

---

### Pattern 2: Corpus Aggregation (if both have frequency data)

```python
# aggregate_frequencies.py
from collections import Counter

def aggregate_frequency_rankings(corpus_a_data, corpus_b_data):
    """Combine frequency rankings from two corpora."""
    
    # Load frequency counts (not ranks)
    freq_a = load_word_frequencies(corpus_a_data)  # {word: count}
    freq_b = load_word_frequencies(corpus_b_data)
    
    # Get corpus sizes
    total_a = sum(freq_a.values())
    total_b = sum(freq_b.values())
    
    print(f"Corpus A: {total_a:,} total words")
    print(f"Corpus B: {total_b:,} total words")
    
    # Combine (weighted by corpus size)
    combined = Counter()
    for word, count in freq_a.items():
        combined[word] += count
    for word, count in freq_b.items():
        combined[word] += count
    
    # Convert to ranks
    sorted_words = [word for word, count in combined.most_common()]
    freq_ranks = {word: rank+1 for rank, word in enumerate(sorted_words)}
    
    # Save
    save_frequency_ranks(freq_ranks, "unified_corpus/frequency_ranks.json")
    
    print(f"Combined vocabulary: {len(freq_ranks):,} unique words")
    
    # Show top 20
    for rank, (word, count) in enumerate(combined.most_common(20), 1):
        rank_a = get_rank(freq_a, word) if word in freq_a else "N/A"
        rank_b = get_rank(freq_b, word) if word in freq_b else "N/A"
        print(f"{rank:3}. {word:15} (A:{rank_a:>5}, B:{rank_b:>5}, total:{count:>8})")
```

---

### Pattern 3: Phonetics Validation & Merge

```python
# validate_phonetics.py
def compare_phonetic_implementations(project_a, project_b):
    """Test both phonetics modules for accuracy."""
    
    # Test cases (from ARMENIAN_QUICK_REFERENCE.md)
    test_cases = [
        ("պետք", {"ipa": "pʰɛtkʰ", "english": "bedk"}),
        ("ժամ", {"ipa": "ʒɑm", "english": "zham"}),
        ("ջուր", {"ipa": "tʃur", "english": "choor"}),
        ("ոչ", {"ipa": "votʃʰ", "english": "voch"}),
        ("իւր", {"ipa": "jur", "english": "yur"}),
    ]
    
    results_a = []
    results_b = []
    
    for word, expected in test_cases:
        result_a = project_a.phonetics.get_phonetic_transcription(word)
        result_b = project_b.phonetics.get_phonetic_transcription(word)
        
        match_a = result_a["ipa"] == expected["ipa"]
        match_b = result_b["ipa"] == expected["ipa"]
        
        results_a.append(match_a)
        results_b.append(match_b)
        
        if not match_a:
            print(f"❌ Project A: {word} → {result_a['ipa']} (expected {expected['ipa']})")
        if not match_b:
            print(f"❌ Project B: {word} → {result_b['ipa']} (expected {expected['ipa']})")
    
    accuracy_a = sum(results_a) / len(results_a) * 100
    accuracy_b = sum(results_b) / len(results_b) * 100
    
    print(f"\nAccuracy:")
    print(f"  Project A: {accuracy_a:.0f}%")
    print(f"  Project B: {accuracy_b:.0f}%")
    
    # Decision
    if accuracy_a >= accuracy_b:
        print(f"\n✅ Recommendation: Use Project A phonetics as canonical")
        return "use_a"
    else:
        print(f"\n✅ Recommendation: Use Project B phonetics as canonical")
        return "use_b"
```

---

## Decision Framework

Use this to decide on architecture:

### Choose Option A (Unified Packages) if:
- ✅ Projects have 60%+ overlap in data
- ✅ Code quality is comparable
- ✅ Same linguistic focus (both Western Armenian)
- ✅ You want single source of truth
- ✅ You're the sole maintainer

**Result**: 3 unified packages (armenian-corpus, armenian-linguistics, armenian-learning)

### Choose Option B (Parallel + Shared Base) if:
- ⚠️ Projects have 30-60% overlap
- ⚠️ Different data quality levels
- ⚠️ Different linguistic focuses (WA vs EA, or different domains)
- ⚠️ Want to preserve both implementations
- ⚠️ Multiple maintainers with different preferences

**Result**: 5 packages (lousardzag-corpus, other-corpus, shared-base, lousardzag-app, other-app)

### Choose Option C (Bridge Layer) if:
- ❌ Projects have <30% overlap
- ❌ Very different architectures
- ❌ Can't refactor both projects
- ❌ Need gradual migration path
- ❌ Projects serve different use cases

**Result**: Original packages + 1 integration bridge

---

## Recommended Action Plan

### Week 1: Analysis
- [ ] Complete Phase 0 (pre-extraction analysis)
- [ ] Fill comparison spreadsheet
- [ ] Run phonetics validation
- [ ] Decide on Option A, B, or C

### Week 2: Data Integration
- [ ] Run database merge script
- [ ] Run corpus deduplication
- [ ] Validate combined data quality
- [ ] Generate comparison report

### Week 3: Package Extraction
- [ ] Start Phase 1 (corpus extraction with merged data)
- [ ] Continue Phase 2 (linguistics extraction with merged tools)

### Week 4: Platform Integration
- [ ] Complete Phase 3 (platform refactor)
- [ ] Integration testing
- [ ] Documentation
- [ ] Release v1.0.0

---

## Key Risks & Mitigation

| Risk | Mitigation |
|------|------------|
| **Data loss during merge** | Backup both projects before starting; use git branches |
| **Incompatible schemas** | Create migration scripts; test on sample data first |
| **Conflicting phonetics** | Run validation suite; choose most accurate; document differences |
| **Corpus duplication** | Use content hashing to detect duplicates; log all decisions |
| **Integration bugs** | Comprehensive test suite; gradual rollout; keep rollback option |
| **Time overrun** | Start with Option C (bridge), migrate to Option A later if needed |

---

## Next Steps

**Before I can help further, I need answers to:**

1. **What is the other project?**
   - Name/link: ___________
   - Purpose: ___________
   - Size: ___________

2. **What data overlaps?**
   - Vocabulary: Yes/No
   - Corpus: Yes/No
   - Phonetics: Yes/No
   - Morphology: Yes/No

3. **What's your preferred architecture?**
   - [ ] Option A: Unified packages (merge everything)
   - [ ] Option B: Parallel packages with shared base
   - [ ] Option C: Bridge layer (keep separate)

4. **Timeline?**
   - Deadline: ___________
   - Hours/week available: ___________

Once you provide these details, I can create a **specific, customized integration plan** for your exact scenario.
