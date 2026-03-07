package com.armenian.flashcards.data.dao

import androidx.lifecycle.LiveData
import androidx.room.*
import com.armenian.flashcards.data.model.Deck

/**
 * Data Access Object for Deck operations.
 */
@Dao
interface DeckDao {
    
    @Query("SELECT * FROM decks ORDER BY name ASC")
    fun getAllDecks(): LiveData<List<Deck>>
    
    @Query("SELECT * FROM decks WHERE id = :id")
    suspend fun getDeckById(id: Long): Deck?
    
    @Query("SELECT * FROM decks WHERE id = :id")
    fun getDeckByIdLiveData(id: Long): LiveData<Deck?>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertDeck(deck: Deck): Long
    
    @Update
    suspend fun updateDeck(deck: Deck)
    
    @Delete
    suspend fun deleteDeck(deck: Deck)
    
    @Query("UPDATE decks SET card_count = :count WHERE id = :deckId")
    suspend fun updateCardCount(deckId: Long, count: Int)
}
