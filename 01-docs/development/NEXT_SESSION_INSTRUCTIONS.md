# Next Session Instructions

**Start here** when resuming work on Lousardzag. This document contains mandatory checklists and common workflows.

## Before You Do ANYTHING Phonetic-Related

**MANDATORY 10-MINUTE CHECKLIST:**

- [ ] Read ARMENIAN_QUICK_REFERENCE.md (2 minutes)
- [ ] Note the voicing reversal pattern (բ=p, պ=b, etc.)
- [ ] Test your understanding with 5 words: պետք, ժամ, ջուր, ոչ, իւր
- [ ] Bookmark /memories/western-armenian-requirement.md (persistent reminder)
- [ ] Check 02-src/lousardzag/phonetics.py line 1 (Western Armenian declaration)

**If you skip this, you will default to Eastern Armenian. This happened repeatedly in the previous session.**

---

## Project State Summary

**What's Working** ✅
- Vocabulary ordering system (5 modes, 3 strategies, 4 presets)
- Western Armenian phonetics module (38-letter map with difficulty scoring)
- Flashcard generation with syllable/sentence controls
- 323+ passing tests across unit and integration suites
- Morphological analysis and verb conjugation
- Card enrichment Phase 1: 8,395 cards with syllable counts, POS tags, and phonetics (100%)
- Dialect classifier (rule-based, source-traceable, conservative defaults)

**What's Incomplete** ⚠️
- Card enrichment Phase 2: frequency_rank (0%), custom_level (0%), full morphology_json
- Context-aware phoneme implementation (documented but not fully functional)
- Diphthong coverage (partial, needs expansion)
- Nayiri dictionary scraper (broken, requires IP whitelist)
- Letter audio generation (IPA-direct approach pending, MMS available as fallback)
- Corpus builder newspaper scraping (intermittent failures)

**What's Planned** 📋
- Package extraction: wa-corpus → armenian-linguistics → lousardzag refactor (see IMPLEMENTATION_ACTION_PLAN.md)
- Custom Western Armenian TTS model (see 01-docs/development/planning/FUTURE_IDEAS.md § Audio Training Models)
- Card template redesign (see 01-docs/CARD-REDESIGN-SPEC.md)

**Critical Constraint** 🔴
- Western Armenian has BACKWARDS voicing (letter appearance ≠ pronunciation)
- This is unique to Western dialect and NOT true of Eastern Armenian
- Defaulting to Eastern voicing will silently corrupt phonetic data

---

## Common Commands

### Generate Vocabulary

```bash
# Standard: JLPT-style 7 levels (N1-N7)
python 07-tools/gen_vocab_simple.py --preset n-standard --max-words 140 \
  --csv-output 08-data/vocab_n_standard.csv

# Custom: Difficulty-focused with growth batches
python 07-tools/gen_vocab_simple.py \
  --ordering-mode difficulty_band \
  --batch-strategy growth --batch-base 20 --batch-step 5 --batch-max 30 \
  --max-words 100 \
  --csv-output 08-data/vocab_difficulty.csv
```

### Run Tests

```bash
# Full test suite
python -m pytest 04-tests/ -q

# Specific test category
python -m pytest 04-tests/unit/test_difficulty.py -v

# With coverage
python -m pytest 04-tests/ --cov=lousardzag
```

### Preview Vocabulary

```bash
# Generate with HTML preview
python 07-tools/gen_vocab_simple.py --preset n-standard --max-words 140 \
  --html-output 08-data/vocabulary_preview.html
```

### Check Phonetics

```bash
# Test phonetic module directly
python 02-src/lousardzag/phonetics.py

# Or interactively
python
>>> from lousardzag.phonetics import get_phonetic_transcription
>>> get_phonetic_transcription('պետdelays')
```

### Classify Dialect

```bash
# Classify a text sample
python 07-tools/analysis/classify_dialect.py --text "sample Armenian text"

# Classify from file
python 07-tools/analysis/classify_dialect.py --file path/to/text.txt
```

### Audio Generation

```bash
# Generate vocabulary audio (MMS, production quality)
python 07-tools/generate_vocab_audio_mms.py

# Letter card viewer with audio comparison
python 03-cli/letter_cards_viewer.py
# Then open: http://localhost:5001 (letters), :5001/vocab (vocab), :5001/compare (A/B test)
```

### Espeak-ng (IPA Path) Verification

```powershell
# System binary path check
where.exe espeak-ng

# Conda env checks
conda run -n base espeak-ng --version
conda run -n wa-llm espeak-ng --version
```

Expected installed path on this machine:
- `C:\Program Files\eSpeak NG\espeak-ng.exe`

If missing in `wa-llm`:

```powershell
conda install -n wa-llm -c conda-forge espeak-ng -y
conda run -n wa-llm espeak-ng --version
```

### Card Enrichment

```bash
# Enrich database with syllable counts, POS tags, phonetics (Phase 1 - already done)
python 07-tools/enrich_anki_database.py

# Future Phase 2: frequency mapping (depends on corpus builder)
# python 07-tools/enrich_card_frequency.py
# python 07-tools/enrich_card_levels.py
```

---

## P0 Sprint: Stabilize Core Workflows (Est. 8-12 hours)

**Purpose**: Fix high-friction entry points and unmask silent failures.  
**Target**: Make all 5 primary CLIs pass smoke tests with clear error messages.

### Daily Tasks (Pick 1-2 per session)

#### Task 1: Fix `letter_cards_viewer.py` Startup (2-3h) 
**Status**: [ ] Not started

**Steps**:
1. [ ] Run: `python 03-cli/letter_cards_viewer.py` 
2. [ ] Capture **exact** failure mode (exits with code 1 — where does it fail?)
3. [ ] Add diagnostic output at entry: 
   - Log port availability check
   - Log template/static file existence
   - Log environment variables (PYTHONPATH, etc.)
4. [ ] Test with `--debug` flag: `python 03-cli/letter_cards_viewer.py --debug`
5. [ ] Commit with message: `fix(cli): add startup diagnostics to letter_cards_viewer`

**Expected outcome**: Clear "Why did I exit?" message instead of silent code 1.

---

#### Task 2: Add `--debug` Mode to CLI Tools (1-2h)
**Status**: [ ] Not started

**Affected tools**:
- `03-cli/letter_cards_viewer.py`
- `07-tools/test_mms_tts.py`

**Steps**:
1. [ ] Add argument parser: `parser.add_argument('--debug', action='store_true')`
2. [ ] Enable verbose logging when `--debug` set
3. [ ] Test: `python 03-cli/letter_cards_viewer.py --debug` → should see detailed logs
4. [ ] Commit: `feat(cli): add --debug mode for verbose logging`

**Expected outcome**: Users can run `--debug` to see internal state without code changes.

---

#### Task 3: CLI Smoke Tests (2-3h)
**Status**: [ ] Not started

**Create file**: `04-tests/smoke/test_cli_entry_points.py`

**Tests to add**:
```bash
# Test 1: letter_cards_viewer help
python 03-cli/letter_cards_viewer.py --help
# Expected: exits 0, shows usage

# Test 2: preview_server help
python 03-cli/preview_server.py --help
# Expected: exits 0, shows usage

# Test 3: corpus build single source
python -m wa_corpus.build_corpus --newspapers 1
# Expected: exits 0, creates/updates corpus

# Test 4: vocabulary generation
python 07-tools/gen_vocab_simple.py --preset n-standard --max-words 10
# Expected: exits 0, creates CSV
```

**Steps**:
1. [ ] Create `04-tests/smoke/test_cli_entry_points.py` and `04-tests/smoke/__init__.py`
2. [ ] Implement subprocess calls with timeout (e.g., 60 seconds max)
3. [ ] Assert exit code 0 and expected output patterns
4. [ ] Run: `python -m pytest 04-tests/smoke/ -v`
5. [ ] Commit: `test(smoke): add CLI entry-point smoke tests`

**Expected outcome**: `pytest 04-tests/smoke/ -v` passes; CI can auto-detect CLI breakage.

---

#### Task 4: Normalize Failure Logs (1-2h)
**Status**: [ ] Not started

**Current state**: `logs/` has many .log files with inconsistent naming and format.

**Steps**:
1. [ ] Review logs structure: `ls -la logs/`
2. [ ] Define standard log naming: `{YYYYMMDD}_{HHMM}_{tool}_{result}.log`
   - Example: `20260306_0945_newspaper_scrape_FAILED.log`
3. [ ] Every failed tool run appends (not overwrites) to timestamped log
4. [ ] Update scraper/tool entry points to use this pattern
5. [ ] Commit: `refactor(logging): standardize log naming and retention`

**Expected outcome**: `logs/` directory is organized and searchable.

---

#### Task 5: Harden Newspaper Build for Partial Failures (2h)
**Status**: [ ] Not started

**Current symptom**: `python -m wa_corpus.build_corpus --newspapers 2` exits on first source error (should continue and report).

**Steps**:
1. [ ] Review `wa_corpus/build_corpus.py` newspaper scraping logic
2. [ ] Add try-catch around each newspaper source:
   ```python
   try:
       scrape_newspaper(source)
   except Exception as e:
       logger.error(f"Failed to scrape {source}: {e}")
       failed_sources.append(source)
       continue  # Don't exit—process next source
   ```
3. [ ] At end, print summary: `Scraped 5/6 sources. Failed: source_X (reason)`
4. [ ] Test: `python -m wa_corpus.build_corpus --newspapers 3` → should continue after failures
5. [ ] Commit: `fix(corpus): add retry and partial-failure recovery to newspaper builder`

**Expected outcome**: Newspaper scraping resilient to individual source failures.

---

### Quick Test All P0 Items

```bash
# After completing each task, run this to verify nothing broke
python -m pytest 04-tests/ -q

# Then spot-check the CLI tools
python 03-cli/letter_cards_viewer.py --help
python 03-cli/preview_server.py --help
python -m wa_corpus.build_corpus --help
```

### Tracking P0 Completion

Use IMPLEMENTATION_ACTION_PLAN.md § "Prioritized Sprint Checklist (P0/P1/P2)" to mark items complete:
```markdown
#### P0 - Stabilize Core Workflows (Total: 8-12h)
- [x] `letter_cards_viewer` startup diagnostics and explicit fatal errors (2-3h)
- [x] `--debug` mode for CLI tools (1-2h)
- [x] CLI smoke tests (2-3h)
- [ ] Normalize failure logs...
```

---

## Workflow: Adding a Phonetic Feature

**Scenario**: You need to add/modify Armenian phonetic mappings

### Step 1: Verify Western Armenian (5 min)
```bash
# Read reference materials
cat ARMENIAN_QUICK_REFERENCE.md        # Quick lookup
cat WESTERN_ARMENIAN_PHONETICS_GUIDE.md # Complete phoneme map
```

### Step 2: Find the Letter (2 min)
```python
# 02-src/lousardzag/phonetics.py
ARMENIAN_PHONEMES = {
    'բ': {'ipa': 'p', 'english': 'p', 'difficulty': 1, ...},  # ← Edit here
    'պ': {'ipa': 'b', 'english': 'b', 'difficulty': 1, ...},
    ...
}
```

### Step 3: Update Both IPA and English Fields
```python
# CORRECT - both fields updated
'բ': {'ipa': 'p', 'english': 'p', 'difficulty': 1, 'word': 'pat'},

# WRONG - only partial update
'բ': {'ipa': 'p', 'english': 'b', ...},  # Mismatched!
```

### Step 4: Test with Sample Words (5 min)
```bash
# Test your change
python -c "from lousardzag.phonetics import ARMENIAN_PHONEMES; \
  print(ARMENIAN_PHONEMES['բ']['ipa'])"
# Should print: p (not b)

# Test with full transcription
python -c "from lousardzag.phonetics import get_phonetic_transcription; \
  print(get_phonetic_transcription('պետք'))"
# Should have 'b' sound, not 'p'
```

### Step 5: Regenerate Vocabulary (5 min)
```bash
python 07-tools/gen_vocab_simple.py --preset n-standard --max-words 140 \
  --csv-output 08-data/vocab_n_standard.csv
```

### Step 6: Verify Output (2 min)
```bash
# Check IPA column populated
python -c "import pandas as pd; df = pd.read_csv('08-data/vocab_n_standard.csv'); \
  print('IPA blanks:', df['IPA'].isna().sum())"
# Should print: 0
```

### Step 7: Commit
```bash
git add 02-src/lousardzag/phonetics.py 08-data/vocab_n_standard.csv
git commit -m "fix(phonetics): correct Western Armenian [letter] IPA mapping

- Updated [letter] from [old] to [new]
- Regenerated vocabulary with new mapping
- Verified with test words: պետք, ժամ, ջուր
- All 140 words have phonetic data"
```

---

## Workflow: Implementing Context-Aware Phonemes

**Scenario**: Making ո, ե, յ, or ւ work based on word position

### Background
Four letters change pronunciation by position:
- **ո**: [v] before consonants → [ɔ] as vowel
- **ե**: [jɛ] at word start → [ɛ] in middle
- **յ**: [h] at word start → [j] in middle
- **ւ**: [u] in diphthongs → [v] between vowels

Currently documented but not implemented in get_phonetic_transcription().

### Implementation Steps

1. **Enhance get_phonetic_transcription()**
   - Add word-position detection
   - Apply context rules per letter
   - Return appropriate IPA for position

2. **Add Tests**
   ```python
   test_cases = {
       'եղջ': 'yeghch', # ե at start = ye
       'բե': 'pe',      # ե in middle = e
       'ոչ': 'voch',   # ո + consonant = vo
       'որ': 'vor',    # ո + consonant = vo (before ր)
   }
   ```

3. **Regenerate Vocabulary**
   ```bash
   python 07-tools/gen_vocab_simple.py --preset n-standard --max-words 140
   ```

4. **Verify IPA Quality Improves**
   ```bash
   # Check if phonetic difficulty scores changed appropriately
   python -c "import pandas as pd; df = pd.read_csv('08-data/vocab_n_standard.csv'); \
     print(df[['Word', 'IPA', 'Phonetic_Difficulty']].head(20))"
   ```

---

## Common Mistakes & How to Fix Them

### Mistake 1: Eastern Armenian Voicing

**Symptom**: Phonetic output has wrong voicing (բ=b, պ=p)

**Fix**:
1. Read ARMENIAN_QUICK_REFERENCE.md § "The Wrong Way"
2. Check phonetics.py — you've reversed the mappings
3. Swap all voicing-reversed pairs
4. Regenerate vocabulary
5. Test: պետք should give "bedk" not "petik"

**Prevention**: Always start with voicing checklist before phonetic work

### Mistake 2: Incomplete Context Handling

**Symptom**: ո and ե always pronounced the same regardless of position

**Fix**:
1. Check if get_phonetic_transcription() has position detection
2. If not documented, add docstring explaining context rules
3. Implement position-aware logic
4. Add test cases for each context

**Prevention**: document expected behavior before implementing

### Mistake 3: Missing IPA Updates

**Symptom**: English approximations updated but IPA not updated (or vice versa)

**Fix**:
1. Regenerate vocabulary: `gen_vocab_simple.py ...`
2. Inspect CSV — IPA column should match English sounds
3. If mismatch, update both fields in ARMENIAN_PHONEMES
4. Regenerate again

**Prevention**: Always update IPA and english fields together; use pre-commit hooks if available

### Mistake 4: Forgetting Diphthongs

**Symptom**: Words like իւր transcribed incorrectly (treating ի and ւ separately)

**Fix**:
1. Check if ARMENIAN_DIGRAPHS has the letter pair
2. If missing, add it: `'իւ': {'ipa': 'ju', 'english': 'yoo', ...}`
3. Verify get_phonetic_transcription() checks digraphs before single letters
4. Test: իւր should come out as "yur" not "i-v-ur"

**Prevention**: Review ARMENIAN_DIGRAPHS at start of phonetics.py

---

## File Navigation Quick Reference

| File | Purpose | Edit When |
|------|---------|-----------|
| ARMENIAN_QUICK_REFERENCE.md | Quick lookup (START HERE) | Never (reference only) |
| WESTERN_ARMENIAN_PHONETICS_GUIDE.md | Complete phoneme reference | When phonetics change |
| 02-src/lousardzag/phonetics.py | Implementation | Adding/fixing phonemes |
| 02-src/lousardzag/dialect_classifier.py | Dialect classification | Adding WA/EA markers |
| 07-tools/gen_vocab_simple.py | Vocabulary generation | Changing ordering logic |
| 07-tools/analysis/classify_dialect.py | Dialect CLI | Adding classifier features |
| 08-data/vocab_n_standard.csv | Output vocabulary | Generated by gen_vocab_simple.py |
| 08-data/armenian_cards.db | Primary data source | After enrichment scripts |
| IMPLEMENTATION_ACTION_PLAN.md | Package extraction plan | Architecture changes |
| 01-docs/development/planning/FUTURE_IDEAS.md | Feature backlog | New ideas, TTS planning |
| 01-docs/development/planning/NEXT_STEPS_MARCH2026.md | Active task tracker | After completing/adding tasks |
| /memories/western-armenian-requirement.md | Persistent reminder | When updating memory |

---

## Git Workflow

### Branch Strategy
- Work on `pr/copilot-swe-agent/2` or feature branch
- Atomic commits per logical change
- Rebase before pushing to consolidate related commits
- Clear commit messages with scope: `fix(phonetics):`, `feat(ordering):`, `docs:`

### Commit Pattern
```bash
# Good
git commit -m "fix(phonetics): correct Western Armenian բ mapping to p

- Updated ARMENIAN_PHONEMES['բ'] IPA to p (was b)
- English approximation: pat (English p sound)
- Regenerated 08-data/vocab_n_standard.csv
- Tested with պետք: outputs bedk correctly"

# Not good
git commit -m "fixed phonetics"
git commit -m "WIP: testing stuff"
```

---

## Session Template

**At Start:**
1. Read ARMENIAN_QUICK_REFERENCE.md
2. Run tests: `python -m pytest 04-tests/ -q`
3. Check current branch and uncommitted changes

**During Work:**
1. Make small, focused changes
2. Test immediately: `python -m pytest 04-tests/ -q`
3. Commit after each logical unit

**At End:**
1. Run full test suite
2. Regenerate vocabulary if phonetics changed
3. Commit or push
4. Update this document if workflow changed

---

## Quick Decision Tree

**"Should I work on phonetics?"**
1. Do you understand Western Armenian voicing reversal? → NO → Read ARMENIAN_QUICK_REFERENCE.md first
2. Is it context-aware letters (ո, ե, յ, ւ)? → YES → Check if implementation is documented
3. Is it adding a new diphthong? → YES → Add to ARMENIAN_DIGRAPHS, test, commit
4. Is it fixing a voicing pair? → YES → Update both ipa and english fields, regenerate vocab, test

**"Should I work on vocabulary ordering?"**
1. Does gen_vocab_simple.py exist? → YES, it works
2. Do all 4 presets work? → YES (l1-core, l2-expand, l3-bridge, n-standard)
3. Need new mode? → Add to ORDERING_MODES dict, implement logic, test, commit

**"Should I work on card generation?"**
1. Does generate_ordered_cards.py work? → YES
2. Are tests passing? → CHECK: `pytest 04-tests/test_card_generator.py -v`
3. Need new feature? → Implement, test, commit with clear scope

---

## Resources

- 📖 ARMENIAN_QUICK_REFERENCE.md — Start here
- 📖 WESTERN_ARMENIAN_PHONETICS_GUIDE.md — Complete reference (to be created)
- 🔗 /memories/western-armenian-requirement.md — Persistent reminder
- 🧪 04-tests/ — Test examples for any feature
- 💾 08-data/ — Vocabulary outputs and HTML previews
- 🔧 .github/copilot-instructions.md — Project-wide guidelines

---

## Questions?

If you get stuck:
1. **Phonetic questions**: Check ARMENIAN_QUICK_REFERENCE.md test words first
2. **Vocabulary questions**: See 08-data/vocab_n_standard.csv examples
3. **Git questions**: Read recent commits: `git log --oneline -10`
4. **Test failures**: Run failing test with `-v`: `pytest 04-tests/test_x.py -v`

Remember: When in doubt about Armenian phonetics, **verify the voicing pattern** (backwards from appearance).

---

Last Updated: March 3, 2026
Branch: pr/copilot-swe-agent/2
