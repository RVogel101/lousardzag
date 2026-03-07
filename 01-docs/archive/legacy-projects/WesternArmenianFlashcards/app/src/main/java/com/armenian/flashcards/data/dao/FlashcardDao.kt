package com.armenian.flashcards.data.dao

import androidx.lifecycle.LiveData
import androidx.room.*
import com.armenian.flashcards.data.model.Flashcard

/**
 * Data Access Object for Flashcard operations.
 */
@Dao
interface FlashcardDao {
    
    @Query("SELECT * FROM flashcards ORDER BY next_review_date ASC")
    fun getAllFlashcards(): LiveData<List<Flashcard>>
    
    @Query("SELECT * FROM flashcards WHERE id = :id")
    suspend fun getFlashcardById(id: Long): Flashcard?
    
    @Query("SELECT * FROM flashcards WHERE deck_id = :deckId ORDER BY next_review_date ASC")
    fun getFlashcardsByDeck(deckId: Long): LiveData<List<Flashcard>>
    
    @Query("SELECT * FROM flashcards WHERE deck_id = :deckId AND next_review_date <= :currentTime ORDER BY next_review_date ASC")
    suspend fun getDueFlashcards(deckId: Long, currentTime: Long = System.currentTimeMillis()): List<Flashcard>
    
    @Query("SELECT * FROM flashcards WHERE deck_id = :deckId AND is_learning = 1 LIMIT :limit")
    suspend fun getNewFlashcards(deckId: Long, limit: Int): List<Flashcard>
    
    @Query("SELECT * FROM flashcards WHERE deck_id = :deckId AND is_learning = 0 AND next_review_date <= :currentTime ORDER BY next_review_date ASC")
    suspend fun getReviewFlashcards(deckId: Long, currentTime: Long = System.currentTimeMillis()): List<Flashcard>
    
    @Query("SELECT COUNT(*) FROM flashcards WHERE deck_id = :deckId")
    suspend fun getCardCountByDeck(deckId: Long): Int
    
    @Query("SELECT COUNT(*) FROM flashcards WHERE deck_id = :deckId AND next_review_date <= :currentTime")
    suspend fun getDueCardCount(deckId: Long, currentTime: Long = System.currentTimeMillis()): Int
    
    @Query("SELECT COUNT(*) FROM flashcards WHERE deck_id = :deckId AND is_learning = 1")
    suspend fun getNewCardCount(deckId: Long): Int
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertFlashcard(flashcard: Flashcard): Long
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertFlashcards(flashcards: List<Flashcard>)
    
    @Update
    suspend fun updateFlashcard(flashcard: Flashcard)
    
    @Delete
    suspend fun deleteFlashcard(flashcard: Flashcard)
    
    @Query("DELETE FROM flashcards WHERE deck_id = :deckId")
    suspend fun deleteFlashcardsByDeck(deckId: Long)
    
    @Query("DELETE FROM flashcards")
    suspend fun deleteAllFlashcards()
}
