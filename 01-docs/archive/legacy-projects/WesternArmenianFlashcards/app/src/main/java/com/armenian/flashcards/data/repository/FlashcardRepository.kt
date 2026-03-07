package com.armenian.flashcards.data.repository

import androidx.lifecycle.LiveData
import com.armenian.flashcards.data.dao.FlashcardDao
import com.armenian.flashcards.data.model.Flashcard
import kotlin.math.max

/**
 * Repository for managing flashcard data and spaced repetition logic.
 * Implements SM-2 (SuperMemo 2) algorithm for spaced repetition.
 */
class FlashcardRepository(private val flashcardDao: FlashcardDao) {
    
    val allFlashcards: LiveData<List<Flashcard>> = flashcardDao.getAllFlashcards()
    
    fun getFlashcardsByDeck(deckId: Long): LiveData<List<Flashcard>> {
        return flashcardDao.getFlashcardsByDeck(deckId)
    }
    
    suspend fun getFlashcardById(id: Long): Flashcard? {
        return flashcardDao.getFlashcardById(id)
    }
    
    suspend fun getDueFlashcards(deckId: Long): List<Flashcard> {
        return flashcardDao.getDueFlashcards(deckId)
    }
    
    suspend fun getNewFlashcards(deckId: Long, limit: Int): List<Flashcard> {
        return flashcardDao.getNewFlashcards(deckId, limit)
    }
    
    suspend fun getReviewFlashcards(deckId: Long): List<Flashcard> {
        return flashcardDao.getReviewFlashcards(deckId)
    }
    
    suspend fun getCardCountByDeck(deckId: Long): Int {
        return flashcardDao.getCardCountByDeck(deckId)
    }
    
    suspend fun getDueCardCount(deckId: Long): Int {
        return flashcardDao.getDueCardCount(deckId)
    }
    
    suspend fun getNewCardCount(deckId: Long): Int {
        return flashcardDao.getNewCardCount(deckId)
    }
    
    suspend fun insertFlashcard(flashcard: Flashcard): Long {
        return flashcardDao.insertFlashcard(flashcard)
    }
    
    suspend fun insertFlashcards(flashcards: List<Flashcard>) {
        flashcardDao.insertFlashcards(flashcards)
    }
    
    suspend fun updateFlashcard(flashcard: Flashcard) {
        flashcardDao.updateFlashcard(flashcard)
    }
    
    suspend fun deleteFlashcard(flashcard: Flashcard) {
        flashcardDao.deleteFlashcard(flashcard)
    }
    
    /**
     * Update flashcard based on user rating using SM-2 algorithm.
     * @param flashcard The flashcard to update
     * @param quality Rating from 0-5 (0=again, 1=hard, 2=good, 3=easy)
     * @return Updated flashcard
     */
    suspend fun reviewFlashcard(flashcard: Flashcard, quality: Int): Flashcard {
        val currentTime = System.currentTimeMillis()
        
        val updatedCard = when (quality) {
            0 -> { // Again - restart the card
                flashcard.copy(
                    easeFactor = max(1.3f, flashcard.easeFactor - 0.2f),
                    interval = 0,
                    repetitions = 0,
                    isLearning = true,
                    nextReviewDate = currentTime + (10 * 60 * 1000), // 10 minutes
                    lastReviewedAt = currentTime,
                    totalReviews = flashcard.totalReviews + 1,
                    difficultyRating = quality
                )
            }
            1 -> { // Hard
                val newInterval = if (flashcard.interval == 0) 1 else (flashcard.interval * 1.2).toInt()
                flashcard.copy(
                    easeFactor = max(1.3f, flashcard.easeFactor - 0.15f),
                    interval = newInterval,
                    repetitions = flashcard.repetitions + 1,
                    isLearning = false,
                    nextReviewDate = currentTime + (newInterval * 24 * 60 * 60 * 1000L),
                    lastReviewedAt = currentTime,
                    totalReviews = flashcard.totalReviews + 1,
                    correctReviews = flashcard.correctReviews + 1,
                    difficultyRating = quality
                )
            }
            2 -> { // Good
                val newInterval = when {
                    flashcard.interval == 0 -> 1
                    flashcard.interval == 1 -> 6
                    else -> (flashcard.interval * flashcard.easeFactor).toInt()
                }
                flashcard.copy(
                    interval = newInterval,
                    repetitions = flashcard.repetitions + 1,
                    isLearning = false,
                    nextReviewDate = currentTime + (newInterval * 24 * 60 * 60 * 1000L),
                    lastReviewedAt = currentTime,
                    totalReviews = flashcard.totalReviews + 1,
                    correctReviews = flashcard.correctReviews + 1,
                    difficultyRating = quality
                )
            }
            3 -> { // Easy
                val newInterval = when {
                    flashcard.interval == 0 -> 4
                    else -> (flashcard.interval * flashcard.easeFactor * 1.3f).toInt()
                }
                flashcard.copy(
                    easeFactor = flashcard.easeFactor + 0.15f,
                    interval = newInterval,
                    repetitions = flashcard.repetitions + 1,
                    isLearning = false,
                    nextReviewDate = currentTime + (newInterval * 24 * 60 * 60 * 1000L),
                    lastReviewedAt = currentTime,
                    totalReviews = flashcard.totalReviews + 1,
                    correctReviews = flashcard.correctReviews + 1,
                    difficultyRating = quality
                )
            }
            else -> flashcard
        }
        
        updateFlashcard(updatedCard)
        return updatedCard
    }
}
