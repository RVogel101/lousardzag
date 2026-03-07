package com.armenian.flashcards.data.dao

import androidx.lifecycle.LiveData
import androidx.room.*
import com.armenian.flashcards.data.model.StudySession

/**
 * Data Access Object for StudySession operations.
 */
@Dao
interface StudySessionDao {
    
    @Query("SELECT * FROM study_sessions ORDER BY session_date DESC")
    fun getAllSessions(): LiveData<List<StudySession>>
    
    @Query("SELECT * FROM study_sessions WHERE deck_id = :deckId ORDER BY session_date DESC")
    fun getSessionsByDeck(deckId: Long): LiveData<List<StudySession>>
    
    @Query("SELECT * FROM study_sessions WHERE session_date >= :startDate ORDER BY session_date DESC")
    suspend fun getSessionsSince(startDate: Long): List<StudySession>
    
    @Insert
    suspend fun insertSession(session: StudySession): Long
    
    @Update
    suspend fun updateSession(session: StudySession)
    
    @Delete
    suspend fun deleteSession(session: StudySession)
}
