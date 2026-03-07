# Western Armenian Flashcards

An Android application for learning Western Armenian through flashcards with a spaced repetition system similar to Anki.

## Features

- **Spaced Repetition Algorithm**: Uses the SM-2 (SuperMemo 2) algorithm to optimize learning
- **Anki-like Interface**: Familiar card review interface with flip animations
- **Card Management**: View and manage all your flashcards
- **Progress Tracking**: Keep track of new cards and review cards
- **Deck System**: Organize cards into different decks by topic

## Database Schema

The app uses Room Database with the following entities:

### Flashcard
- Front text (Western Armenian)
- Back text (English translation)
- Pronunciation guide (optional)
- Example sentence (optional)
- Spaced repetition metrics (ease factor, interval, repetitions)
- Review statistics

### Deck
- Deck name and description
- Daily card limits
- Card count

### StudySession
- Session statistics
- Cards studied
- Accuracy tracking

## Technical Stack

- **Language**: Kotlin
- **Database**: Room (SQLite)
- **Architecture**: MVVM (Model-View-ViewModel)
- **UI**: Material Design 3
- **Concurrency**: Kotlin Coroutines
- **Lifecycle**: LiveData & ViewModel

## Getting Started

1. Open the project in Android Studio
2. Sync Gradle files
3. Run the app on an emulator or physical device (API 24+)

## Adding Cards

The database structure is ready to store cards. Future updates will include:
- UI for adding new cards
- Import/export functionality
- Audio pronunciation support
- Image support for visual learning

## Spaced Repetition

The app implements the SM-2 algorithm with four rating levels:
- **Again**: Restart the card (10 minutes)
- **Hard**: Slightly increase interval
- **Good**: Standard interval increase
- **Easy**: Larger interval increase with ease factor boost

## Project Structure

```
app/
├── data/
│   ├── dao/              # Data Access Objects
│   ├── database/         # Room Database configuration
│   ├── model/            # Data models (entities)
│   └── repository/       # Repository pattern implementation
├── ui/
│   ├── adapter/          # RecyclerView adapters
│   ├── viewmodel/        # ViewModels for UI logic
│   ├── MainActivity.kt   # Main flashcard review screen
│   └── CardListActivity.kt  # Card list management
└── res/
    ├── layout/           # XML layouts
    ├── values/           # Strings, colors, themes
    └── animator/         # Card flip animations
```

## Requirements

- Android Studio Arctic Fox or later
- Minimum SDK: API 24 (Android 7.0)
- Target SDK: API 34 (Android 14)

## License

This project is open source and available for educational purposes.
