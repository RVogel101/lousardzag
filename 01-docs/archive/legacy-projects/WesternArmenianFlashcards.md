# WesternArmenianFlashcards — Legacy Project Archive

**Status:** Decommissioned (March 2025)  
**Reason:** Flashcard functionality consolidated into **Lousardzag** (Python/Anki-based). No direct code migration (Android/Kotlin vs Python).

## Overview

WesternArmenianFlashcards was an Android application for learning Western Armenian through flashcards with a spaced repetition system similar to Anki.

## Schema Summary

### Flashcard Entity (Room)
| Field | Type | Description |
|-------|------|-------------|
| frontText | String | Western Armenian word/phrase |
| backText | String | English translation or explanation |
| pronunciation | String? | Optional IPA/pronunciation guide |
| exampleSentence | String? | Optional example usage |
| deckId | Long | Foreign key to deck |
| easeFactor | Float | SM-2 ease factor (default 2.5) |
| interval | Int | Days until next review |
| repetitions | Int | Successful review count |
| nextReviewDate | Long | Next review timestamp |
| isLearning | Boolean | New vs review card |
| difficultyRating | Int | 0=new, 1=again, 2=hard, 3=good, 4=easy |

### Deck Entity
| Field | Type | Description |
|-------|------|-------------|
| name | String | Deck name (e.g. "Basic Vocabulary") |
| description | String? | Optional description |
| color | String | Hex color for UI |
| cardCount | Int | Cached card count |
| newCardsPerDay | Int | Daily new card limit |
| reviewCardsPerDay | Int | Daily review limit |

### StudySession Entity
- Session statistics, cards studied, accuracy tracking

## Design Notes

- **Algorithm:** SM-2 (SuperMemo 2) spaced repetition
- **Architecture:** MVVM, Room, Kotlin Coroutines
- **UI:** Material Design 3, flip animations
- **Min SDK:** API 24 (Android 7.0)

## Successor

**Lousardzag** provides flashcard generation and review via:
- Anki integration (AnkiConnect)
- armenian-corpus-core for phonetics, morphology, dialect classification
- Python-based pipeline for card creation and export

Full archived source: `01-docs/archive/legacy-projects/WesternArmenianFlashcards/`
