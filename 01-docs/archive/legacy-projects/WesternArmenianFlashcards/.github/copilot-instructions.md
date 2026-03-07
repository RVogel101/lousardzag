# 🗂️ Project Overview for AI Agents

This repository contains a single Android application written in Kotlin. The app is a Western Armenian flashcards/SM‑2 spaced‑repetition learner built with MVVM and Room. An AI agent should become productive by focusing on a few core packages and conventions listed below.

---

## 🧱 Architecture & Core Components

1. **MVVM + Repository Pattern**
   - **Data Layer** (`app/src/main/java/com/armenian/flashcards/data`)
     - `model` holds `@Entity` classes (`Flashcard`, `Deck`, `StudySession`).
     - `dao` contains Room DAOs (`FlashcardDao`, `DeckDao`, etc.).
     - `repository` wraps DAOs with business logic (see `FlashcardRepository.reviewFlashcard` for SM‑2 algorithm).
     - `database/FlashcardDatabase.kt` builds the singleton and seeds a default deck on first launch.
   - **UI Layer** (`app/src/main/java/com/armenian/flashcards/ui`)
     - `viewmodel/FlashcardViewModel` drives the main review screen and card list.
     - Activities: `MainActivity.kt` (review cards) and `CardListActivity.kt` (list + future add UI).
     - `adapter/FlashcardAdapter.kt` is a simple `RecyclerView` adapter for the card list.
   - **Data flow**: DAO ⇢ Repository ⇢ ViewModel ⇢ Activity/Adapter.  All repository calls that touch the DB use Kotlin coroutines (`suspend` and `viewModelScope.launch`).
   - **Default deck** is created in `FlashcardDatabase.populateDatabase`; view models hardcode `currentDeckId = 1`.

2. **Spaced‑Repetition Logic**
   - The SM‑2 algorithm is implemented in `FlashcardRepository.reviewFlashcard` with four quality scores (0‑3) and updates fields such as `easeFactor`, `interval`, `nextReviewDate`.
   - New vs. review cards are loaded in `FlashcardViewModel.loadNextCard()`; cards are shuffled before presenting.

3. **Room/Database Patterns**
   - Use `FlashcardDatabase.getDatabase(context)` to obtain instance.
   - DAOs return `LiveData` for lists; other read/write operations are `suspend`.
   - Entities and DAOs are all under `data/model` and `data/dao` respectively.

4. **UI & Animations**
   - Flip animations are defined in `res/animator/flip_in.xml` and `flip_out.xml`.
   - Layouts reside in `res/layout`; naming corresponds to activity/adapter (`activity_main.xml`, `item_flashcard.xml`).
   - Material 3 theming configured in `res/values/themes.xml`.

---

## 🚧 Developer Workflows

- **Building / Running**
  - Primary tool: Android Studio Arctic Fox+.
  - CLI: from project root run `./gradlew assembleDebug`, `./gradlew installDebug` (Windows: `gradlew.bat`).
  - The `app` module is the only Android module.

- **Debugging**
  - Use standard Android Studio debugger; set breakpoints in Kotlin files (e.g. within `FlashcardViewModel` or repositories).
  - Database is in `getDatabase` singleton; you can access via `adb shell` if needed (`/data/data/.../databases/flashcard_database`).

- **No test suite** (unit or instrumentation) currently exists. When adding tests, follow existing package structure; place unit tests in `app/src/test/java` mirroring production packages.

- **Database migrations**: version is `1` and `exportSchema=false`; any schema change must increment version and add migration logic in `FlashcardDatabase`.

---

## 🛠️ Conventions and Patterns

- **Coroutines** are used everywhere for asynchronous DB work; do not use `AsyncTask` or blocking calls.
- **LiveData** is the reactive type for UI; view models expose `MutableLiveData` privately and `LiveData` publicly.
- **Hardcoded defaults**:
  - `currentDeckId` is 1 in `FlashcardViewModel` (assume default deck exists).
  - New card limit is taken from deck property: `deck.newCardsPerDay ?: 20`.
- **Repository responsibilities**: perform data access and compute intervals/ratings. UI logic stays in view models.

- **Naming**: classes follow PascalCase; layout files use snake_case.
- **UI strings**: mostly defined in `res/values/strings.xml`; many hard‑coded values exist in code (snackbar messages etc.) which should be moved when adding features.

- **Future work hints**:
  - AddCard feature shows a placeholder SnackBar in `CardListActivity`.
  - Deck management is minimal; only one default deck is seeded.

---

## 🔌 External Dependencies

- Room (androidx.room)
- Lifecycle components (LiveData, ViewModel)
- Kotlin Coroutines
- Material Design (com.google.android.material)

There are no network calls or other external APIs. All data lives locally in the Room database.

---

## 📁 Key Files to Inspect First

- `FlashcardRepository.kt` – business logic and SM‑2 algorithm
- `FlashcardViewModel.kt` – how the deck/card queue is managed
- `FlashcardDatabase.kt` – singleton and initial data
- `DeckRepository.kt` – simple deck queries and counts
- `MainActivity.kt` / `CardListActivity.kt` – UI entry points

---

> ⚠️ **Note for Agents**: There is no existing `.github/copilot-instructions.md`. The file you are reading will be used to seed that document. When in doubt, reference the README or inspect the `data` package.

Please review and let me know if any particular area is unclear or needs more detail.