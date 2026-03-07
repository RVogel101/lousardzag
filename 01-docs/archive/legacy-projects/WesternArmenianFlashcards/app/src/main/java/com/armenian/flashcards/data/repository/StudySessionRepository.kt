package com.armenian.flashcards.data.repository

import androidx.lifecycle.LiveData
import com.armenian.flashcards.data.dao.StudySessionDao
import com.armenian.flashcards.data.model.StudySession

/**
 * Repository for managing study session data.
 */
class StudySessionRepository(private val studySessionDao: StudySessionDao) {
    
    val allSessions: LiveData<List<StudySession>> = studySessionDao.getAllSessions()
    
    fun getSessionsByDeck(deckId: Long): LiveData<List<StudySession>> {
        return studySessionDao.getSessionsByDeck(deckId)
    }
    
    suspend fun getSessionsSince(startDate: Long): List<StudySession> {
        return studySessionDao.getSessionsSince(startDate)
    }
    
    suspend fun insertSession(session: StudySession): Long {
        return studySessionDao.insertSession(session)
    }
    
    suspend fun updateSession(session: StudySession) {
        studySessionDao.updateSession(session)
    }
    
    suspend fun deleteSession(session: StudySession) {
        studySessionDao.deleteSession(session)
    }
}
