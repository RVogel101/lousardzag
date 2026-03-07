package com.armenian.flashcards.data.repository

import androidx.lifecycle.LiveData
import com.armenian.flashcards.data.dao.DeckDao
import com.armenian.flashcards.data.dao.FlashcardDao
import com.armenian.flashcards.data.model.Deck

/**
 * Repository for managing deck data.
 */
class DeckRepository(
    private val deckDao: DeckDao,
    private val flashcardDao: FlashcardDao
) {
    
    val allDecks: LiveData<List<Deck>> = deckDao.getAllDecks()
    
    suspend fun getDeckById(id: Long): Deck? {
        return deckDao.getDeckById(id)
    }
    
    fun getDeckByIdLiveData(id: Long): LiveData<Deck?> {
        return deckDao.getDeckByIdLiveData(id)
    }
    
    suspend fun insertDeck(deck: Deck): Long {
        return deckDao.insertDeck(deck)
    }
    
    suspend fun updateDeck(deck: Deck) {
        deckDao.updateDeck(deck)
    }
    
    suspend fun deleteDeck(deck: Deck) {
        // Delete all flashcards in this deck first
        flashcardDao.deleteFlashcardsByDeck(deck.id)
        deckDao.deleteDeck(deck)
    }
    
    suspend fun updateDeckCardCount(deckId: Long) {
        val count = flashcardDao.getCardCountByDeck(deckId)
        deckDao.updateCardCount(deckId, count)
    }
}
