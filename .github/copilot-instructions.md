# Project: Lousardzag (Western Armenian Learning Platform)

## Environment & Running Commands

- **OS**: Windows 11, PowerShell 5.1
- **Python**: 3.12.3 via conda `base` environment
- **Python is NOT on PATH** without conda activation. Every terminal must activate conda first:
  ```powershell
  (C:\Users\litni\anaconda3\shell\condabin\conda-hook.ps1) ; (conda activate base)
  ```
- After activation, `python` works normally for the rest of that terminal session.
- **Project root**: `C:\Users\litni\OneDrive\Documents\anki\anki-note-generation-pipelines` (on OneDrive)

## Common Commands

| Task | Command |
|------|---------|
| Generate vocabulary (n-standard) | `python 07-tools/gen_vocab_simple.py --preset n-standard --max-words 140 --csv-output 08-data/vocab_n_standard.csv` |
| Generate vocabulary (custom) | `python 07-tools/gen_vocab_simple.py --preset l1-core --max-words 60 --proficiency-enabled` |
| Generate ordered cards | `python 07-tools/generate_ordered_cards.py --max-words 40 --english-mode strict` |
| Preview server | `python 03-cli/preview_server.py --pretty` |
| Run tests | `python -m pytest` |
| Build corpus (newspapers) | `python -m wa_corpus.build_corpus --newspapers` |
| Build corpus (IA) | `python -m wa_corpus.build_corpus --ia` |

## AnkiConnect

- REST API on **localhost:8765** (Anki desktop must be running with AnkiConnect add-on)
- Profile name: `armenians_global`
- Anki data directory: `%APPDATA%\Anki2\` (standard location, NOT on OneDrive)
- Wrapper: `lousardzag/anki_connect.py`
- **READ-ONLY by default** — do not modify Anki data without explicit user permission

## Key Directories

- `lousardzag/` — Core package (morphology, card gen, progression, DB, AnkiConnect)
  - `phonetics.py` — Western Armenian phonetic transcription & difficulty scoring
  - `sentence_progression.py` — Difficulty-aware sentence coaching system
- `wa_corpus/` — Western Armenian frequency corpus tools (wiki, newspapers, IA, nayiri scrapers)
- `wa_corpus/data/` — Downloaded corpus data (gitignored, large)
- `07-tools/gen_vocab_simple.py` — Configurable vocabulary ordering with N-level proficiency
- `07-tools/generate_ordered_cards.py` — Cards with syllable, sentence, and level controls
- `anki_media/` — Exported media files from Anki (gitignored)
- `anki_export.json` — Full Anki note export (gitignored)

---

## 🚨 CRITICAL: NEVER USE INVENTED EXAMPLES — ALWAYS USE REAL DATA

**THIS IS NON-NEGOTIABLE.** When creating documentation, specifications, or examples involving Armenian words, sentences, or data:

1. **NEVER invent Armenian words or examples** — No matter how logical they seem
2. **ALWAYS pull from your local databases FIRST**:
   - `08-data/armenian_cards.db` — PRIMARY source: local SQLite database with actual Anki card data (cards table: word, translation, pos, frequency_rank, metadata_json, morphology_json)
   - `08-data/anki_export.json` — Real Anki deck export (for reference only)
   - `wa_corpus/data/` — Corpus sentences and phrases (not primary vocab source)
   - `02-src/lousardzag/letter_data.py` — Letter information
   - **NOTE**: CSV files like `vocab_n_standard.csv`, `vocab_l1_core.csv`, etc. are DERIVED/SECONDARY and contain assumptions that may be outdated. Always query the database directly instead.
3. **BEFORE creating any example**, ask yourself:
   - "Is this word actually in vocab_n_standard.csv?"
   - "Did I verify the IPA against the database?"
   - "Is this POS tag from the actual data?"
4. **DO NOT use placeholder text** — Placeholders like `[Real Armenian sentence]` are dangerous because they get filled with invented Eastern Armenian. Instead:
   - Only create sections with ACTUAL data already loaded
   - OR use code/JSON template variables with `{...}` syntax that clearly indicate where data will come from
   - EXAMPLES OF WHAT NOT TO DO:
     - ❌ `[Real Armenian sentence from corpus]` (gets confused with Armenian text)
     - ❌ `Նա գալ ես` (invented Eastern Armenian)
     - ❌ Any Armenian text you haven't verified in the actual database
   - EXAMPLES OF WHAT TO DO:
     - ✅ Load the sentence from corpus FIRST, then include it
     - ✅ Use JSON like `"sentence": "{load_from_wa_corpus_data}"` (not Armenian)
     - ✅ Leave the section empty or note "To be populated from actual corpus on integration"

**Why?** You made the mistake of using "ամուսնալ" (to marry) — an Eastern Armenian word, NOT from the Western Armenian database. This breaks consistency and wastes time. Never again.

**Procedure on every spec/doc with Armenian content:**
1. Query `08-data/armenian_cards.db` FIRST (PRIMARY source from Anki — cards table)
2. Copy real examples directly (word, translation, pos, frequency_rank, metadata_json, morphology_json)
3. If real data is unavailable:
   - Use code template variables with `{...}` syntax (e.g., `{load_from_wa_corpus_data}`)
   - OR note "To be populated from actual corpus on integration" (English-only)
   - NEVER use placeholder text like `[Real Armenian sentence]`
4. Cite the source: "(from armenian_cards.db, cards table, frequency_rank X)" or "(from anki_export.json)"

---

## ⚠️ CRITICAL: WESTERN ARMENIAN PHONETICS & TRANSLITERATION

**This is the #1 source of implementation errors. Follow STRICTLY.**

### Core Principle
Western Armenian has **REVERSED VOICING** compared to letter shapes:
- Visual voiced shapes → unvoiced sounds (բ=p, գ=k, դ=t, ջ=j, ծ=dz)
- Visual unvoiced shapes → voiced sounds (պ=b, կ=g, տ=d, չ=ch, ճ=j)

### Reference Authority
- **Source**: `/memories/western-armenian-requirement.md` in agent memory
- **Update procedure**: Before EVERY Armenian phonetic work, READ this file first
- **Never assume** — always verify against the reference

### Phoneme Mapping Rules

**Critical Mappings (most commonly misapplied):**
| Letter | IPA | English | Difficulty | NO NOT |
|--------|-----|---------|------------|--------|
| բ | p | pat | 1 | Do NOT use b (Eastern value) |
| պ | b | bat | 1 | Do NOT use p (Eastern value) |
| գ | k | kit | 1 | Do NOT use g (Eastern value) |
| կ | g | go | 1 | Do NOT use k (Eastern value) |
| դ | t | top | 1 | Do NOT use d (Eastern value) |
| տ | d | dog | 1 | Do NOT use t (Eastern value) |
| ճ | dʒ | job | 1 | Do NOT use tʃ/ch (that's ջ or չ) |
| ջ | tʃ | chop | 1 | Do NOT use dʒ/j (that's ճ) |

**Contextual Vowels:**
- ե: /ɛ/ (e) in word middle, /jɛ/ (ye) at word start
- ո: /vo/ before consonants (ոչ=voch), /o/ vowel otherwise
- ւ: **NOT A VOWEL** — /v/ between vowels, /u/ in diphthongs (ու, իւ)
- է: /ɛ/ (eh) like bed — vowel, not consonant

**Diphthongs:**
- ու (ո+ւ) → /u/ "oo" like goose
- իւ (ի+ւ) → /ju/ "yoo" like "you"

### Implementation Checklist
- [ ] Reading IPA values? Check `/memories/western-armenian-requirement.md` FIRST
- [ ] Creating phoneme data? Cross-check all 38 consonants/vowels against reference
- [ ] Using letter→sound mappings? Verify EACH letter against the phoneme table
- [ ] Testing transcription? Use real Western Armenian words from vocab, NOT made-up examples
- [ ] Diphthongs? Only ու and իւ exist; check digraphs list doesn't have false entries

### Common Mistakes to Avoid
1. ❌ Copy-pasting Eastern Armenian phonetics (happens every session unless referenced)
2. ❌ Using English voicing conventions (բ is NOT b; պ is NOT p here)
3. ❌ Forgetting ւ is NOT a vowel (is semi-vowel, only vowel in diphthongs)
4. ❌ Missing է as vowel (is vowel like ե, just without y-glide)
5. ❌ Assuming ջ and ճ are the same (ջ=ch, ճ=j)

### Transliteration Validation (CRITICAL)
**Whenever you output ANY transliteration, Armenian phonetic mapping, or IPA:** 
1. **STOP and ask yourself:** "Is this the correct WESTERN Armenian transliteration/IPA?"
2. **Cross-check immediately against:**
   - `02-src/lousardzag/phonetics.py` — `ARMENIAN_PHONEMES` dict (38 entries with verified WA mappings)
   - `02-src/lousardzag/letter_data.py` — Letter name and IPA data
   - `08-data/anki_export.json` or `armenian_cards.db` — Real examples with correct IPA values
   - `/memories/western-armenian-requirement.md` — Reference authority for phoneme mappings
3. **If uncertain, DO NOT OUTPUT** — Leave a note "(verify Western Armenian IPA from phonetics.py)" instead
4. **COMPLETE list of common transposition errors to catch:**

**CRITICAL REVERSED VOICING (Visual shape ≠ sound):**
| Wrong | Correct | Letter | IPA |
|-------|---------|--------|-----|
| ❌ պ = p | ✅ պ = b | պ | b |
| ❌ բ = b | ✅ բ = p | բ | p |
| ❌ կ = k | ✅ կ = g | կ | g |
| ❌ գ = g | ✅ գ = k | գ | k |
| ❌ տ = t | ✅ տ = d | տ | d |
| ❌ դ = d | ✅ դ = t | դ | t |
| ❌ ջ = j | ✅ ջ = ch (tʃ) | ջ | tʃ |
| ❌ ճ = ch | ✅ ճ = j (dʒ) | ճ | dʒ |

**OTHER WESTERN ARMENIAN SPECIFIC ERRORS:**
| Wrong | Correct | Letter | Notes |
|-------|---------|--------|-------|
| ❌ թ = th | ✅ թ = t | թ | aspirated t, NOT English "th" |
| ❌ ո = o always | ✅ ո = v~ɔ | ո | vo before consonants (ոչ=voch, որ=vor), o vowel otherwise |
| ❌ ե = ɛ always | ✅ ե = ɛ~jɛ | ե | e in middle, **ye at word start** |
| ❌ ե | ✅ ե ≠ է | ե ≠ է | These are DIFFERENT letters with DIFFERENT sounds |
| ❌ ղ = g | ✅ ղ = gh | ղ | voiced velar fricative (guttural, strict English: gh), NOT plain g |
| ❌ ռ = tap r | ✅ ռ = r (trilled) | ռ | Spanish-style TRILLED r, NOT English r |
| ❌ ր = ɾ equally | ✅ ր = ɾ (flap) | ր | Flapped r, different from trilled ռ |
| ❌ ց = dz | ✅ ց = ts | ց | ts NOT dz |
| ❌ ծ = dz | ✅ ծ = dz | ծ | voiced dz, NOT ts |
| ❌ ձ = dz | ✅ ձ = ts | ձ | ts (different from ծ), NOT dz |
| ❌ ւ = vowel | ✅ ւ = v~u | ւ | **NOT a vowel** — v between vowels, u in diphthongs (ու, իւ) |
| ❌ յ = y always | ✅ յ = j~h | յ | y in middle, **h at word start** |
| ❌ չ = ch vs ջ=ch | ✅ Both ch but different | չ ≠ ջ | Both are tʃ (ch) but different letters — verify context |
| ❌ փ = f or other | ✅ փ = p | փ | p sound (variant shape) |
| ❌ ք = q or other | ✅ ք = k | ք | k sound (variant shape) |
| ❌ ժ = j | ✅ ժ = ʒ | ժ | zh (voiced), NOT j |

**VOWEL CONFUSION ERRORS:**
| Wrong | Correct | Notes |
|-------|---------|-------|
| ❌ ա = ə | ✅ ա = ɑ | Different from ը (schwa) |
| ❌ ը = ɛ | ✅ ը = ə | Schwa only, NOT plain e |
| ❌ ե = ɛ only | ✅ ե = ɛ~jɛ | **CONTEXT:** ye at start, e elsewhere |
| ❌ ո = o only | ✅ ո = v~ɔ | **CONTEXT:** vo before consonants, o vowel otherwise |
| ❌ ու = o | ✅ ու = u | Diphthong = long oo (goose), NOT short o |
| ❌ իւ = u | ✅ իւ = ju | Diphthong = yoo (you), NOT u |

**CONSISTENCY ERRORS (Context matters):**
| Letter | WRONG | CORRECT |
|--------|-------|---------|
| ե at word start | ɛ | jɛ (ye) |
| ե in middle | jɛ | ɛ (e) |
| ո before consonant | o | vo (voch, vor) |
| ո as vowel | v | o (lot) |
| ւ between vowels | u | v (vet) |
| ւ in diphthongs | v | u (goose) |
| յ at start | y | h (hat) |
| յ in middle | h | j (yes) |

---

## New Features (March 2026)

### Phonetic Transcription Module
- **File**: `02-src/lousardzag/phonetics.py`
- **Functions**:
  - `get_phonetic_transcription(armenian_word)` → {ipa, english_approx, max_phonetic_difficulty, difficult_phonemes}
  - `calculate_phonetic_difficulty(armenian_word)` → 1-5 score
  - `get_pronunciation_guide(armenian_word)` → full guide with tips
- **Data**: `ARMENIAN_PHONEMES` dict (38 entries), `ARMENIAN_DIGRAPHS` dict (2 diphthongs)
- **Integration**: Used in vocabulary ordering and card difficulty calculation

### Vocabulary Ordering System
- **File**: `07-tools/gen_vocab_simple.py`
- **Modes**: frequency, pos_frequency, band_pos_frequency, difficulty, difficulty_band
- **Batch strategies**: fixed, growth (with step), banded
- **Presets**: l1-core (60), l2-expand (80), l3-bridge (100), n-standard (flexible)
- **Proficiency**: N1-N7 blocks matching language standards (JLPT style)
- **Outputs**: CSV with IPA/phonetic columns, HTML preview
- **Filters**: Removes sentences (>4 words, question marks, sentence starters)

### Sentence Progression Framework
- **File**: `02-src/lousardzag/sentence_progression.py`
- **Tracks**: Morphological complexity, word prerequisites, sentence difficulty
- **Strategies**: Linear and adaptive (based on vocab difficulty)
- **Filtering**: Prevents use of unreleased vocabulary in sentences
- **Tests**: `04-tests/test_sentence_progression.py` with comprehensive coverage

---

# Session Tracking Instructions

After every conversation compaction (context window reset), update the session progress file at `/memories/session/session-progress.md` with the following:

1. **What was accomplished** — List each task completed since the last update, with specific results (numbers, file names, outcomes). Group by topic area.

2. **Clarifying questions & answers** — Maintain a table of every question the user asked during the session and the answer/finding. Format as a markdown table with Question and Answer columns.

3. **Key findings** — Any technical discoveries, verifications, or facts learned during the session that might need to be referenced later (e.g., API endpoints, tool versions, config values, confirmed behaviors).

4. **Current state** — What's in progress, what's blocked, and what the immediate next step is.

5. **Remaining work** — Checklist of outstanding tasks with `[ ]` / `[x]` markers.

## Rules

- Append new information rather than overwriting previous sections (so the file becomes a running log).
- Be specific — include counts, file paths, error messages, and concrete outcomes rather than vague summaries.
- If a previous finding was wrong or updated, note the correction explicitly.
- Do this automatically on every compaction without being asked.

---

## Git Cleanup Procedures

**⚠️ IMPORTANT: Sensitive files must be handled carefully**

When user requests "clean up git changes":

1. **Identify sensitive files** (credentials, API keys, private config):
   - Google Cloud service account keys (`.json` with credentials)
   - AWS credentials, GitHub tokens, any authentication material
   - Local environment configs with secrets
   - Private data files

2. **Action for sensitive files**:
   - ❌ DO NOT simply delete them (they may be needed later)
   - ✅ DO add to `.gitignore` so they won't be tracked
   - ✅ Verify file is untracked and safe before committing .gitignore change
   - Example: `arm-speech-converter-*.json` pattern in .gitignore

3. **Action for normal untracked development files**:
   - Remove diagnostic scripts (`diag_*.py`, `test_*.py` temporary tools)
   - Remove experimental outputs (`08-data/letter_audio_ipa/`, etc.)
   - Delete with `Remove-Item -Force` or `git clean -fd`

4. **Final step**:
   - `git status` should show only legitimate changes
   - Commit legitimate work with clear message
   - Leave sensitive files untracked but safe in working directory
