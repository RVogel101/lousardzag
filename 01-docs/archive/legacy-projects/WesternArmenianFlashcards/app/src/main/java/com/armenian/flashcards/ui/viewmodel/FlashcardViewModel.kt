package com.armenian.flashcards.ui.viewmodel

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.viewModelScope
import com.armenian.flashcards.data.database.FlashcardDatabase
import com.armenian.flashcards.data.model.Deck
import com.armenian.flashcards.data.model.Flashcard
import com.armenian.flashcards.data.repository.DeckRepository
import com.armenian.flashcards.data.repository.FlashcardRepository
import kotlinx.coroutines.launch

/**
 * ViewModel for the main flashcard review screen.
 */
class FlashcardViewModel(application: Application) : AndroidViewModel(application) {
    
    private val flashcardRepository: FlashcardRepository
    private val deckRepository: DeckRepository
    
    private val _currentCard = MutableLiveData<Flashcard?>()
    val currentCard: LiveData<Flashcard?> = _currentCard
    
    private val _isShowingAnswer = MutableLiveData<Boolean>(false)
    val isShowingAnswer: LiveData<Boolean> = _isShowingAnswer
    
    private val _currentDeck = MutableLiveData<Deck?>()
    val currentDeck: LiveData<Deck?> = _currentDeck
    
    private val _newCardsCount = MutableLiveData<Int>(0)
    val newCardsCount: LiveData<Int> = _newCardsCount
    
    private val _reviewCardsCount = MutableLiveData<Int>(0)
    val reviewCardsCount: LiveData<Int> = _reviewCardsCount
    
    private val _cardsStudiedToday = MutableLiveData<Int>(0)
    val cardsStudiedToday: LiveData<Int> = _cardsStudiedToday
    
    private var cardQueue: MutableList<Flashcard> = mutableListOf()
    private val currentDeckId: Long = 1 // Default deck
    
    init {
        val database = FlashcardDatabase.getDatabase(application)
        val flashcardDao = database.flashcardDao()
        val deckDao = database.deckDao()
        
        flashcardRepository = FlashcardRepository(flashcardDao)
        deckRepository = DeckRepository(deckDao, flashcardDao)
        
        loadDeck()
        loadNextCard()
    }
    
    private fun loadDeck() {
        viewModelScope.launch {
            val deck = deckRepository.getDeckById(currentDeckId)
            _currentDeck.value = deck
            updateCardCounts()
        }
    }
    
    private fun updateCardCounts() {
        viewModelScope.launch {
            val newCount = flashcardRepository.getNewCardCount(currentDeckId)
            val dueCount = flashcardRepository.getDueCardCount(currentDeckId)
            
            _newCardsCount.value = newCount
            _reviewCardsCount.value = dueCount
        }
    }
    
    fun loadNextCard() {
        viewModelScope.launch {
            if (cardQueue.isEmpty()) {
                // Load new cards and due review cards
                val deck = _currentDeck.value
                val newLimit = deck?.newCardsPerDay ?: 20
                
                val newCards = flashcardRepository.getNewFlashcards(currentDeckId, newLimit)
                val reviewCards = flashcardRepository.getReviewFlashcards(currentDeckId)
                
                // Mix new and review cards
                cardQueue.addAll(newCards)
                cardQueue.addAll(reviewCards)
                cardQueue.shuffle()
            }
            
            _currentCard.value = cardQueue.firstOrNull()
            _isShowingAnswer.value = false
        }
    }
    
    fun showAnswer() {
        _isShowingAnswer.value = true
    }
    
    fun rateCard(quality: Int) {
        viewModelScope.launch {
            val card = _currentCard.value ?: return@launch
            
            // Update card with spaced repetition algorithm
            flashcardRepository.reviewFlashcard(card, quality)
            
            // Remove from queue and load next
            if (cardQueue.isNotEmpty()) {
                cardQueue.removeAt(0)
            }
            
            _cardsStudiedToday.value = (_cardsStudiedToday.value ?: 0) + 1
            
            updateCardCounts()
            loadNextCard()
        }
    }
    
    fun getAllFlashcards(): LiveData<List<Flashcard>> {
        return flashcardRepository.getFlashcardsByDeck(currentDeckId)
    }
}
