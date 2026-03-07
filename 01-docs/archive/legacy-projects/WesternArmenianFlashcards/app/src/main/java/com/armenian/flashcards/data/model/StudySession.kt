package com.armenian.flashcards.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey
import androidx.room.ColumnInfo

/**
 * Entity for tracking study sessions and statistics.
 */
@Entity(tableName = "study_sessions")
data class StudySession(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    
    @ColumnInfo(name = "deck_id")
    val deckId: Long,
    
    @ColumnInfo(name = "session_date")
    val sessionDate: Long = System.currentTimeMillis(),
    
    @ColumnInfo(name = "cards_studied")
    val cardsStudied: Int = 0,
    
    @ColumnInfo(name = "new_cards")
    val newCards: Int = 0,
    
    @ColumnInfo(name = "review_cards")
    val reviewCards: Int = 0,
    
    @ColumnInfo(name = "duration_minutes")
    val durationMinutes: Int = 0,
    
    @ColumnInfo(name = "accuracy_percentage")
    val accuracyPercentage: Float = 0f
)
