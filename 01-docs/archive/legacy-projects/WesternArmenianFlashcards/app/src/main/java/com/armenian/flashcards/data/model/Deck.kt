package com.armenian.flashcards.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey
import androidx.room.ColumnInfo

/**
 * Entity representing a deck/collection of flashcards.
 * Allows organizing cards by topic, difficulty, etc.
 */
@Entity(tableName = "decks")
data class Deck(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    
    @ColumnInfo(name = "name")
    val name: String,  // e.g., "Basic Vocabulary", "Verbs", "Common Phrases"
    
    @ColumnInfo(name = "description")
    val description: String? = null,
    
    @ColumnInfo(name = "color")
    val color: String = "#2196F3",  // Hex color for deck identification
    
    @ColumnInfo(name = "created_at")
    val createdAt: Long = System.currentTimeMillis(),
    
    @ColumnInfo(name = "card_count")
    val cardCount: Int = 0,  // Cached count for performance
    
    @ColumnInfo(name = "new_cards_per_day")
    val newCardsPerDay: Int = 20,  // Limit for new cards
    
    @ColumnInfo(name = "review_cards_per_day")
    val reviewCardsPerDay: Int = 100  // Limit for review cards
)
