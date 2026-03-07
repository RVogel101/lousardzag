package com.armenian.flashcards.data.database

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.sqlite.db.SupportSQLiteDatabase
import com.armenian.flashcards.data.dao.DeckDao
import com.armenian.flashcards.data.dao.FlashcardDao
import com.armenian.flashcards.data.dao.StudySessionDao
import com.armenian.flashcards.data.model.Deck
import com.armenian.flashcards.data.model.Flashcard
import com.armenian.flashcards.data.model.StudySession
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

/**
 * Room Database for the Western Armenian Flashcards app.
 * Contains tables for flashcards, decks, and study sessions.
 */
@Database(
    entities = [
        Flashcard::class,
        Deck::class,
        StudySession::class
    ],
    version = 1,
    exportSchema = false
)
abstract class FlashcardDatabase : RoomDatabase() {
    
    abstract fun flashcardDao(): FlashcardDao
    abstract fun deckDao(): DeckDao
    abstract fun studySessionDao(): StudySessionDao
    
    companion object {
        @Volatile
        private var INSTANCE: FlashcardDatabase? = null
        
        fun getDatabase(context: Context): FlashcardDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    FlashcardDatabase::class.java,
                    "flashcard_database"
                )
                    .addCallback(DatabaseCallback())
                    .build()
                INSTANCE = instance
                instance
            }
        }
        
        /**
         * Callback to populate initial data when database is created.
         */
        private class DatabaseCallback : RoomDatabase.Callback() {
            override fun onCreate(db: SupportSQLiteDatabase) {
                super.onCreate(db)
                INSTANCE?.let { database ->
                    CoroutineScope(Dispatchers.IO).launch {
                        populateDatabase(database.deckDao())
                    }
                }
            }
        }
        
        /**
         * Populate database with a default deck.
         * Cards will be added by the user in future.
         */
        suspend fun populateDatabase(deckDao: DeckDao) {
            // Create a default deck
            val defaultDeck = Deck(
                name = "Western Armenian Basics",
                description = "Essential vocabulary and phrases for beginners",
                color = "#4CAF50",
                newCardsPerDay = 20,
                reviewCardsPerDay = 100
            )
            deckDao.insertDeck(defaultDeck)
        }
    }
}
