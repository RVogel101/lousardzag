"""
Armenian Letter Progression System - FSRS-based Learning Sequences

Manages difficulty-based progression for letter learning with:
- Spaced repetition scheduling
- Prerequisite tracking (learn component letters before diphthongs)
- Difficulty-based grouping
- Progress tracking
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from . import letter_data


class LetterStatus(Enum):
    """Progress status for a letter."""
    NEW = "new"              # Never seen
    LEARNING = "learning"    # In active practice
    REVIEWING = "reviewing"  # Spaced repetition phase
    MASTERED = "mastered"    # Fully learned


@dataclass
class LetterProgress:
    """Track progress on a single letter."""
    letter: str
    status: LetterStatus
    times_practiced: int = 0
    correct_count: int = 0
    incorrect_count: int = 0
    interval_days: int = 1          # Spaced repetition interval
    next_review_date: Optional[datetime] = None
    date_started: Optional[datetime] = None
    date_mastered: Optional[datetime] = None
    last_reviewed: Optional[datetime] = None


class LetterProgressionSystem:
    """Manages difficulty-based letter learning progression."""

    def __init__(self):
        self.all_letters = letter_data.get_all_letters_ordered()
        self.diphthongs = list(letter_data.ARMENIAN_DIPHTHONGS.keys())
        self.progress: Dict[str, LetterProgress] = {}
        self._initialize_progress()

    def _initialize_progress(self):
        """Initialize progress tracking for all letters."""
        for letter in self.all_letters:
            self.progress[letter] = LetterProgress(
                letter=letter,
                status=LetterStatus.NEW,
            )

    def get_learning_sequence(
        self,
        max_per_group: int = 5,
    ) -> Dict[int, List[str]]:
        """Get recommended learning sequence by difficulty.
        
        Returns:
            Dictionary mapping difficulty level to letters
        """
        grouped = {}
        for letter in self.all_letters:
            info = letter_data.get_letter_info(letter)
            difficulty = info["difficulty"]
            if difficulty not in grouped:
                grouped[difficulty] = []
            grouped[difficulty].append(letter)

        # Sort each group (prefer consonants before vowels for specific levels)
        for difficulty in grouped:
            grouped[difficulty].sort(
                key=lambda l: (
                    0 if letter_data.get_letter_info(l)["type"] == "vowel" else 1,
                    self.all_letters.index(l),
                )
            )

        return grouped

    def get_current_level_letters(
        self,
        level: int,
    ) -> List[str]:
        """Get letters for a specific learning level (1-5).
        
        Args:
            level: Learning level (1=easiest, 5=hardest)
        """
        difficulty_map = {
            1: [1],
            2: [1, 2],
            3: [1, 2, 3],
            4: [2, 3, 4],
            5: [3, 4, 5],
        }

        target_difficulties = difficulty_map.get(level, [1, 2, 3, 4, 5])
        return [
            l for l in self.all_letters
            if letter_data.get_letter_info(l)["difficulty"] in target_difficulties
        ]

    def mark_correct(self, letter: str) -> None:
        """Record correct answer for a letter."""
        if letter not in self.progress:
            return

        prog = self.progress[letter]
        prog.times_practiced += 1
        prog.correct_count += 1
        prog.last_reviewed = datetime.now()

        # Progression logic (simplified FSRS)
        if prog.status == LetterStatus.NEW:
            if prog.correct_count >= 2:  # 2 correct → learning
                prog.status = LetterStatus.LEARNING
                prog.date_started = datetime.now()
                prog.interval_days = 1
        elif prog.status == LetterStatus.LEARNING:
            if prog.correct_count >= 5:  # 5 total correct → reviewing
                prog.status = LetterStatus.REVIEWING
                prog.interval_days = 3
        elif prog.status == LetterStatus.REVIEWING:
            if prog.times_practiced >= 10:  # 10 practice sessions → mastered
                prog.status = LetterStatus.MASTERED
                prog.date_mastered = datetime.now()

        # Update next review
        prog.next_review_date = datetime.now() + timedelta(days=prog.interval_days)

    def mark_incorrect(self, letter: str) -> None:
        """Record incorrect answer for a letter (reset interval)."""
        if letter not in self.progress:
            return

        prog = self.progress[letter]
        prog.times_practiced += 1
        prog.incorrect_count += 1
        prog.last_reviewed = datetime.now()

        # Reset interval on incorrect
        prog.interval_days = max(1, prog.interval_days // 2)
        prog.next_review_date = datetime.now() + timedelta(days=prog.interval_days)

    def get_due_letters(self) -> List[str]:
        """Get letters that are due for review right now.
        
        Returns:
            Sorted list of letters ready to practice
        """
        now = datetime.now()
        due = []

        for letter, prog in self.progress.items():
            if prog.status == LetterStatus.NEW:
                due.append(letter)
            elif prog.next_review_date and prog.next_review_date <= now:
                due.append(letter)

        # Sort by status priority: NEW > LEARNING > REVIEWING
        status_order = {LetterStatus.NEW: 0, LetterStatus.LEARNING: 1, LetterStatus.REVIEWING: 2}
        due.sort(key=lambda l: (status_order.get(self.progress[l].status, 3), self.all_letters.index(l)))

        return due

    def get_diphthong_prerequisites(self, diphthong: str) -> List[str]:
        """Get prerequisite letters before learning a diphthong.
        
        Args:
            diphthong: Diphthong to learn (e.g., "ու")
            
        Returns:
            List of component letters that must be learned first
        """
        if diphthong not in letter_data.ARMENIAN_DIPHTHONGS:
            return []

        component_letters = letter_data.ARMENIAN_DIPHTHONGS[diphthong]["letters"]
        return component_letters

    def can_learn_diphthong(self, diphthong: str) -> bool:
        """Check if prerequisites are met to learn a diphthong.
        
        Args:
            diphthong: Diphthong to check (e.g., "ու")
        """
        prerequisites = self.get_diphthong_prerequisites(diphthong)
        
        for prereq in prerequisites:
            if prereq not in self.progress:
                return False
            if self.progress[prereq].status not in (LetterStatus.LEARNING, LetterStatus.REVIEWING, LetterStatus.MASTERED):
                return False

        return True

    def get_progress_stats(self) -> Dict[str, any]:
        """Get overall learning statistics.
        
        Returns:
            Dictionary with progress metrics
        """
        total_letters = len(self.all_letters)
        status_counts = {status.value: 0 for status in LetterStatus}

        total_practice_sessions = 0
        total_correct = 0
        total_incorrect = 0

        for prog in self.progress.values():
            status_counts[prog.status.value] += 1
            total_practice_sessions += prog.times_practiced
            total_correct += prog.correct_count
            total_incorrect += prog.incorrect_count

        accuracy = (
            total_correct / (total_correct + total_incorrect)
            if (total_correct + total_incorrect) > 0
            else 0
        )

        return {
            "total_letters": total_letters,
            "status_breakdown": status_counts,
            "completion_percentage": (status_counts["mastered"] / total_letters * 100) if total_letters > 0 else 0,
            "total_practice_sessions": total_practice_sessions,
            "total_correct_answers": total_correct,
            "total_incorrect_answers": total_incorrect,
            "overall_accuracy": f"{accuracy * 100:.1f}%",
            "letters_due_now": len(self.get_due_letters()),
        }

    def get_letter_status(self, letter: str) -> Optional[LetterProgress]:
        """Get progress details for a specific letter."""
        return self.progress.get(letter)

    def reset_letter_progress(self, letter: str) -> None:
        """Reset progress for a letter (start over)."""
        if letter in self.progress:
            self.progress[letter] = LetterProgress(
                letter=letter,
                status=LetterStatus.NEW,
            )

    def get_mastery_timeline(self) -> Tuple[List[str], List[str], List[str]]:
        """Get estimated timeline for mastery milestones.
        
        Returns:
            Tuple of (completed_soon, weeks_away, months_away)
        """
        now = datetime.now()
        week_from_now = now + timedelta(days=7)
        month_from_now = now + timedelta(days=30)

        completed_soon = []
        weeks_away = []
        months_away = []

        for letter, prog in self.progress.items():
            if prog.status == LetterStatus.MASTERED:
                continue
            if not prog.next_review_date:
                continue

            if prog.next_review_date <= week_from_now:
                completed_soon.append(letter)
            elif prog.next_review_date <= month_from_now:
                weeks_away.append(letter)
            else:
                months_away.append(letter)

        return completed_soon, weeks_away, months_away

    def export_progress_json(self) -> Dict[str, any]:
        """Export progress data for persistence.
        
        Returns:
            JSON-serializable dictionary
        """
        return {
            letter: {
                "status": prog.status.value,
                "times_practiced": prog.times_practiced,
                "correct_count": prog.correct_count,
                "incorrect_count": prog.incorrect_count,
                "interval_days": prog.interval_days,
                "next_review_date": prog.next_review_date.isoformat() if prog.next_review_date else None,
                "date_started": prog.date_started.isoformat() if prog.date_started else None,
                "date_mastered": prog.date_mastered.isoformat() if prog.date_mastered else None,
                "last_reviewed": prog.last_reviewed.isoformat() if prog.last_reviewed else None,
            }
            for letter, prog in self.progress.items()
        }

    def import_progress_json(self, data: Dict[str, any]) -> None:
        """Import progress data.
        
        Args:
            data: JSON data from export_progress_json()
        """
        for letter, prog_data in data.items():
            self.progress[letter] = LetterProgress(
                letter=letter,
                status=LetterStatus(prog_data["status"]),
                times_practiced=prog_data.get("times_practiced", 0),
                correct_count=prog_data.get("correct_count", 0),
                incorrect_count=prog_data.get("incorrect_count", 0),
                interval_days=prog_data.get("interval_days", 1),
                next_review_date=datetime.fromisoformat(prog_data["next_review_date"]) 
                    if prog_data.get("next_review_date") else None,
                date_started=datetime.fromisoformat(prog_data["date_started"])
                    if prog_data.get("date_started") else None,
                date_mastered=datetime.fromisoformat(prog_data["date_mastered"])
                    if prog_data.get("date_mastered") else None,
                last_reviewed=datetime.fromisoformat(prog_data["last_reviewed"])
                    if prog_data.get("last_reviewed") else None,
            )
