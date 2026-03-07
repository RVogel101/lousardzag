package com.armenian.flashcards.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey
import androidx.room.ColumnInfo
import java.util.Date

/**
 * Entity representing a flashcard in the database.
 * Based on spaced repetition learning similar to Anki.
 */
@Entity(tableName = "flashcards")
data class Flashcard(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    
    // Card content
    @ColumnInfo(name = "front_text")
    val frontText: String,  // Western Armenian word/phrase
    
    @ColumnInfo(name = "back_text")
    val backText: String,   // English translation or explanation
    
    @ColumnInfo(name = "pronunciation")
    val pronunciation: String? = null,  // Optional pronunciation guide
    
    @ColumnInfo(name = "example_sentence")
    val exampleSentence: String? = null,  // Optional example usage
    
    // Deck organization
    @ColumnInfo(name = "deck_id")
    val deckId: Long = 1,  // Foreign key to deck
    
    // Spaced repetition algorithm fields
    @ColumnInfo(name = "ease_factor")
    val easeFactor: Float = 2.5f,  // How "easy" the card is (2.5 is default)
    
    @ColumnInfo(name = "interval")
    val interval: Int = 0,  // Days until next review
    
    @ColumnInfo(name = "repetitions")
    val repetitions: Int = 0,  // Number of successful reviews
    
    @ColumnInfo(name = "next_review_date")
    val nextReviewDate: Long = System.currentTimeMillis(),  // When to show next
    
    // Learning state
    @ColumnInfo(name = "is_learning")
    val isLearning: Boolean = true,  // New cards vs review cards
    
    @ColumnInfo(name = "difficulty_rating")
    val difficultyRating: Int = 0,  // 0=new, 1=again, 2=hard, 3=good, 4=easy
    
    // Metadata
    @ColumnInfo(name = "created_at")
    val createdAt: Long = System.currentTimeMillis(),
    
    @ColumnInfo(name = "last_reviewed_at")
    val lastReviewedAt: Long? = null,
    
    @ColumnInfo(name = "total_reviews")
    val totalReviews: Int = 0,
    
    @ColumnInfo(name = "correct_reviews")
    val correctReviews: Int = 0
)
