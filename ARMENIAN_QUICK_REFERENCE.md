# Armenian Quick Reference Card

**For quick lookup during implementation. For complete details see comprehensive guides at project root.**

## ⚠️ CRITICAL: The Voicing Reversal (START HERE)

Western Armenian has **BACKWARDS VOICING** — letter appearance ≠ pronunciation:

| Letter | Looks Like | Actually Sounds Like | Example |
|--------|-----------|----------------------|---------|
| **բ** | voiced b | **p** (unvoiced) | բան = bahn |
| **պ** | unvoiced p | **b** (voiced) | պետք = BEDIK |
| **դ** | voiced d | **t** (unvoiced) | դուռ = dur |
| **տ** | unvoiced t | **d** (voiced) | տուն = doon |
| **գ** | voiced g | **k** (unvoiced) | գիտ = git |
| **կ** | unvoiced k | **g** (voiced) | կտուր = gdur |

**TEST WORD**: պետք = "be-dik" (NOT "pe-tik")  
If you get the [p] sound, you're using Eastern Armenian ❌

---

## Context-Aware Letters (Position Changes Pronunciation)

| Letter | Position | Sound | Example |
|--------|----------|-------|---------|
| **յ** | word start | h | յուղ = hugh |
| **յ** | word middle/end | y | բայ = bay |
| **ո** | before consonant | v | ոչ = voch |
| **ո** | after vowel/alone | o | որ = vor |
| **ե** | word start | ye | ե = ye |
| **ե** | word middle/end | e | ե = e |
| **ւ** | between vowels | v~oo | (complex, see diphthongs) |

---

## Consonant Quick Map

| Sound | Western | NOT | Notes |
|-------|---------|-----|-------|
| p | բ | պ | Remember: opposite of appearance |
| b | պ | բ | Remember: opposite of appearance |
| t | դ | տ | Remember: opposite of appearance |
| d | տ | դ | Remember: opposite of appearance |
| k | գ | կ | Remember: opposite of appearance |
| g | կ | գ | Remember: opposite of appearance |
| j (like "job") | ճ | ջ | ճ is voiced affricate [dʒ] |
| ch (like "chop") | ջ | ճ | ջ is unvoiced affricate [tʃ] |
| ch (like "chop") | չ | - | Same as ջ |
| ts | ց | - | |
| dz | ծ | - | |
| sh | շ | - | |
| zh | ժ | - | |
| s | ս | - | |
| t (regular) | թ | th | NOT "th" sound — just regular t |
| r (flap) | ր | - | Like English "better" |
| r (trill) | ռ | - | Spanish rolled r |
| f | ֆ | - | |
| h | հ | - | |
| kh (guttural) | խ | - | Difficult (difficulty 4) |
| voiced gh | ղ | - | Difficult (difficulty 4) |
| m | մ | - | |
| n | ն | - | |
| l | լ | - | |

---

## Vowels (Complete Set)

| Letter | Sound | Example |
|--------|-------|---------|
| **ա** | a (father) | ամ = am |
| **ե** | e (bed) or ye* | (context) |
| **ի** | i (fleece) | իմ = im |
| **ո** | o (lot) or v* | (context) |
| **օ** | o (go) | օր = or |

*Context-dependent, see above

**NOTE**: ւ is NOT a standalone vowel!

---

## Diphthongs (Two-Letter Vowel Combos)

| Pair | Sound | Example |
|------|-------|---------|
| **ու** | oo | ուր = ur (where) |
| **իւ** | yoo | իւր = yur |

---

## Test Words (Verify Your Phonetics)

Use these to check if you're using Western Armenian (correct) or Eastern (wrong):

```
Correct (Western Armenian):
պետք → be-dik (պ=b, տ=d)
ճամ → jam (ճ=dʒ like "j")
ջուր → chur (ջ=tʃ like "ch")
ոչ → voch (ո=v at start)
իւր → yur (իւ=yoo diphthong)

Wrong (Eastern Armenian - if you get these, STOP):
պետք → pe-tik (wrong voicing)
ճամ → chyam (wrong affricate)
ջուր → jayur (wrong affricate)
թ → th (doesn't exist in Western)
```

---

## The WRONG Way ❌

```python
# EASTERN ARMENIAN (NOT THIS PROJECT)
mapping = {
    'բ': 'b',     # WRONG: Should be p
    'պ': 'p',     # WRONG: Should be b
    'դ': 'd',     # WRONG: Should be t
    'տ': 't',     # WRONG: Should be d
    'կ': 'k',     # WRONG: Should be g
    'գ': 'g',     # WRONG: Should be k
    'ճ': 'tʃ',    # WRONG: Should be dʒ
    'ջ': 'dʒ',    # WRONG: Should be tʃ
    'թ': 'θ',     # WRONG: Should be t (no "th" sound)
    'ե': 'ɛ',     # INCOMPLETE: Missing ye variant
    'ո': 'ɔ',     # INCOMPLETE: Missing v variant
    'յ': 'j',     # INCOMPLETE: Missing h variant
    'ւ': 'u',     # INCOMPLETE: Missing v variant
    'է': ...,     # WRONG: Eastern only, exclude!
}
```

---

## The RIGHT Way ✅

```python
# WESTERN ARMENIAN (THIS PROJECT)
mapping = {
    'բ': {'ipa': 'p', 'english': 'p', ...},
    'պ': {'ipa': 'b', 'english': 'b', ...},
    'դ': {'ipa': 't', 'english': 't', ...},
    'տ': {'ipa': 'd', 'english': 'd', ...},
    'կ': {'ipa': 'g', 'english': 'g', ...},
    'գ': {'ipa': 'k', 'english': 'k', ...},
    'ճ': {'ipa': 'dʒ', 'english': 'j', ...},
    'ջ': {'ipa': 'tʃ', 'english': 'ch', ...},
    'թ': {'ipa': 't', 'english': 't', ...},
    'ե': {'ipa': 'ɛ~jɛ', 'english': 'e/ye', ...},  # Context-aware
    'ո': {'ipa': 'v~ɔ', 'english': 'v/o', ...},   # Context-aware
    'յ': {'ipa': 'j~h', 'english': 'y/h', ...},   # Context-aware
    'ւ': {'ipa': 'v~u', 'english': 'v/oo', ...},  # Context-aware
    # NO 'է' entry — Eastern Armenian only
}
```

---

## One-Sentence Summary

**Western Armenian voicing is backwards from letter appearance: բ/պ, դ/տ, κ/կ pairs are REVERSED. Test with պետք (be-dik, not pe-tik). Always verify before implementing.**

---

For complete details: See comprehensive guides at project root (WESTERN_ARMENIAN_PHONETICS_GUIDE.md, etc.)
