# Card Redesign Specification (March 2026)

## ⚠️ IMPORTANT: All Armenian Examples From SQLite Database

**ALL examples, words, and sentences in this spec are extracted from the actual Anki database:**
- Words are queried from `08-data/armenian_cards.db` (PRIMARY source: local SQLite with actual Anki card data)
- IPA values come directly from `anki_export.json` or morphology_json in database, NOT invented
- POS tags from actual `pos` column in cards table
- CSV files like `vocab_n_standard.csv` are SECONDARY/DERIVED and should not be used as primary source

## Overview
Minimalist, interactive flashcard system with two distinct card types (Vocabulary & Sentence), optimized for both mobile and desktop. Focus on clean design with progressive disclosure of details.

---

## VOCABULARY CARD

### Front (MINIMAL - Real Example)
```
┌─────────────────────────────────────┐
│                                     │
│         տուն                        │
│      (Real vocab from database)     │
│                                     │
│         [Click or press SPACE]      │
└─────────────────────────────────────┘
```

**Fields on Front** (Real example from SQLite database: տուն = house, frequency_rank 381):
- `word`: Armenian word (uppercase, 48px, bold, centered)
- `difficulty_badge`: Subtle indicator (1-5 dots or color, top-right corner, optional)

**Data Structure** (extracted from SQLite database `armenian_cards.db`):
```python
{
    "word": "տուն",               # Armenian text (from cards.word)
  "translation": "home, house" # From cards.translation
}
```

### Back (PROGRESSIVE REVEAL - Real Example)
```
┌─────────────────────────────────────┐
│                                     │
│         HOME, HOUSE                 │
│         [Main reveal]               │
│                                     │
├─────────────────────────────────────┤
│                                     │
│  📚 MORE EXAMPLES [dropdown]         │  (collapsed by default)
│  🔊 PRONUNCIATION [button]           │  (collapsed by default)
│     (IPA + transliteration)          │
│                                     │
│  ⏸️  MARK AS: ✓ CORRECT | ✗ WRONG   │  (always visible)
│                                     │
└─────────────────────────────────────┘
```

**Fields on Back** (from SQLite database: տուն, frequency_rank 381):
- `translation`: "home, house" (32px, bold, top) — extracted from Definition column
- `more_examples` (collapsed): List of sentences containing տուն from corpus
- `pronunciation` (collapsed): IPA + transliteration from database
- `interaction`: Two buttons for marking ✓/✗

---

## SENTENCE CARD

### Front (MINIMAL)
```
┌─────────────────────────────────────┐
│                                     │
│    {sentence_from_corpus}           │
│    (Armenian sentence)              │
│                                     │
│    [Click to reveal]                │
└─────────────────────────────────────┘
```

**Fields on Front**:
- `sentence`: Armenian sentence (40px, centered)
- `focused_word`: Optional highlight of target word in dull color

**Data Structure**:
```python
{
  "sentence": "{sentence_from_corpus}",
  "translation": "{sentence_translation_from_corpus}",
  "focused_word": "{focused_word_from_sentence}",
  "focused_translation": "{focused_word_translation}",
  "context_note": "{context_note_if_applicable}",
    "loanword_origin": null            # For future
}
```

### Back (PROGRESSIVE REVEAL)
```
┌─────────────────────────────────────┐
│                                     │
│    SENTENCE TRANSLATION             │
│    ({sentence_translation})          │
│    [Main reveal]                    │
│                                     │
├─────────────────────────────────────┤
│                                     │
│  📖 WORD FOCUS: {focused_word}      │  (clickable)
│     ({focused_translation}) - {pos} │
│                                     │
│  🔊 PRONUNCIATION [button]          │  (collapsed by default)
│  💡 GRAMMAR NOTES [dropdown]        │  (collapsed by default)
│  ⏸️  MARK AS: ✓ CORRECT | ✗ WRONG  │  (always visible)
│                                     │
└─────────────────────────────────────┘
```

**Fields on Back**:
- `sentence_translation`: Full sentence translation (32px, bold)
- `word_focus`: Highlight the specific word being taught + its translation
- `word_pos`: Part of speech tag
- `word_tense` (verb-only, for future): tense/aspect info
- `pronunciation` (collapsed): IPA + audio button
- `grammar_notes` (collapsed): Grammatical context
- `interaction`: Two buttons for marking ✓/✗

---

## DATA STRUCTURE SUMMARY

### Vocabulary Card Fields (Full) - Real Example
```json
{
  "type": "vocabulary",
  "word": "տուն",
  "translation": "home, house",
  "pos": "noun",
  "difficulty": 1.9,
  "syllables": "{pending_syllable_counter}",
  "band": "101-500",
  "ipa": "dv~ɔun",
  "transliteration": "{from_armenian_cards.db}",
  "phonetic_difficulty": 2,
  "root": null,
  "example_sentences": [],
  "loanword_origin": null,
  "audio_file": "vocab_տուն.mp3"
}
```

Note: Syllable counting needs a dedicated fix. Example: "doon" should be counted as 1 syllable.

**Source:** `02-src/armenian_cards.db` — cards table, word="տուն" with frequency_rank=381

### Sentence Card Fields (Full) - Template for Real Data
```json
{
  "type": "sentence",
  "sentence": "[From Western Armenian corpus or Anki deck]",
  "sentence_translation": "[Actual translation from corpus]",
  "focused_word": "[vocab word from armenian_cards.db]",
  "focused_word_translation": "[From Definition column]",
  "focused_word_pos": "[From POS column]",
  "focused_word_tense": "[Detected from corpus context]",
  "focused_word_ipa": "[From IPA column]",
  "context_words": [
    {"word": "[from sentence]", "translation": "[actual]"}
  ],
  "loanword_origin": "[if applicable]",
  "grammar_note": "[from corpus metadata]",
  "audio_file": "[if available]"
}
```

**IMPORTANT:** Sentence cards will integrate ACTUAL examples from these sources when implemented:
- `wa_corpus/data/` — corpus sentences
- `08-data/anki_export.json` — Anki deck sentences

⚠️ **DO NOT** create placeholder sentences like `[Real Armenian sentence]` or invent Armenian examples. Wait until actual corpus data can be loaded.

---

## CSS STYLING APPROACH

### Color System
- **Primary text** (Armenian): #1a237e (dark blue)
- **Secondary text** (English): #555 (dark gray)
- **Difficulty 1-2**: #4caf50 (green)
- **Difficulty 2.5-3.5**: #ff9800 (orange)
- **Difficulty 4+**: #f44336 (red)
- **Background**: #f5f5f5 (light gray)
- **Card background**: #ffffff (white)

### Typography
- **Armenian word (front)**: 48px, bold, Noto Sans Armenian
- **Armenian sentence (front)**: 40px, bold
- **English translation (back)**: 32px, bold
- **Details text**: 16px, regular
- **Labels**: 14px, uppercase, letter-spacing

### Responsive Breakpoints
- **Mobile**: 320px - 768px
  - Card height: Auto (full viewport height on front, scroll on back)
  - Font sizes: -2-4px from desktop
  - Padding: 16px
  - Buttons: Full-width stack vertically
- **Tablet**: 768px - 1024px
  - Card height: Auto
  - Padding: 24px
  - Buttons: Side-by-side with flex
- **Desktop**: 1024px+
  - Card max-width: 600px
  - Card height: 500px-600px (fixed or flexible)
  - Padding: 32px
  - Buttons: Side-by-side

### Interaction States
- **Normal**: Shadow, subtle rounded corners
- **Hover**: Slight scale (1.02), enhanced shadow
- **Active/Selected**: Thin border highlight (#1976d2)
- **Marked correct (✓)**: Subtle green background tint
- **Marked wrong (✗)**: Subtle red background tint

---

## FUTURE ENHANCEMENTS (PLANNED)

### Phase 2: Morphological Breakdown
- Verb: Root + conjugation class + suffix breakdown
- Noun/Adjective: Root + case + number visualization
- Interactive highlighting of morphemes

### Phase 3: Declension/Conjugation Cards
- Full paradigm tables on back
- Side-by-side comparison of forms
- Etymology and loanword tagging

### Phase 4: Audio & Pronunciation
- Integrated TTS for Armenian/English
- User recording option
- Pronunciation feedback

### Phase 5: Spaced Repetition & Progress
- Track correct/wrong per card
- Difficulty adjustment based on performance
- Estimated time to mastery

---

## IMPLEMENTATION CHECKLIST

- [ ] Create vocabulary card HTML template (minimal front/back)
- [ ] Create sentence card HTML template (minimal front/back)
- [ ] Fix syllable counting logic ("doon" should be 1 syllable)
- [ ] Build responsive CSS (mobile-first)
- [ ] Create flashcard practice viewer (Flask app)
- [ ] Connect card data to viewer
- [ ] Implement ✓/✗ marking system
- [ ] Test on mobile devices
- [ ] Add dropdown/expand interactions
- [ ] Prepare data structure for future root/declension fields
- [ ] Document component API for future integration
