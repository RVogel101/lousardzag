"""
Armenian Letter Practice - Interactive Training Exercises

Provides progressively structured practice for learning Armenian letters:
- Letter recognition drills
- Sound matching exercises
- Part-of-word identification
- Diphthong practice sequences
- Difficulty-based progression
"""

from typing import List, Dict, Optional, Tuple, Set, Union, Any
from enum import Enum
import random
from dataclasses import dataclass
from . import letter_data


class PracticeMode(Enum):
    """Different types of letter practice exercises."""
    RECOGNITION = "recognition"          # Show letter, identify name
    PRONUNCIATION = "pronunciation"      # Hear sound, pick letter
    WORD_IDENTIFICATION = "word_id"      # Find letter in word
    DIPHTHONG = "diphthong"             # Learn ու, իւ combinations
    COMPARISON = "comparison"            # Compare similar letters
    DIFFICULTY_PROGRESSION = "progression"  # Guided learning sequence


@dataclass
class PracticeQuestion:
    """Single practice question."""
    mode: PracticeMode
    letter: str
    question_text: str
    options: List[str]
    correct_answer: str
    explanation: str
    difficulty: int


class LetterPractice:
    """Manages interactive letter learning exercises."""

    def __init__(self):
        self.all_letters = letter_data.get_all_letters_ordered()
        self.Easy = letter_data.get_all_letters_ordered()[:15]  # First 15
        self.medium = letter_data.get_all_letters_ordered()[15:30]  # Middle
        self.hard = letter_data.get_all_letters_ordered()[30:]  # Last 8

    def get_recognition_drill(
        self,
        num_questions: int = 5,
        difficulty: Optional[int] = None,
        include_uppercase: bool = False,
    ) -> List[PracticeQuestion]:
        """Generate letter recognition drill (show letter, guess name).
        
        Args:
            num_questions: Number of questions to generate
            difficulty: Filter by difficulty (1-5), None for all
            include_uppercase: Mix in uppercase forms
        """
        # Filter letters by difficulty if specified
        if difficulty:
            letters = [
                l for l in self.all_letters
                if (info := letter_data.get_letter_info(l)) is not None
                and info["difficulty"] >= difficulty
            ]
        else:
            letters = self.all_letters

        questions = []
        selected = random.sample(letters, min(num_questions, len(letters)))

        for letter in selected:
            info = letter_data.get_letter_info(letter)
            if info is None:
                continue
            display_letter = info["uppercase"] if include_uppercase and random.random() > 0.5 else letter

            # Create options: correct name + 3 random other names
            correct_name = info["name"]
            wrong_names = [
                inf["name"]
                for l in random.sample(letters, 3)
                if l != letter and (inf := letter_data.get_letter_info(l)) is not None
            ]

            options = [correct_name] + wrong_names
            random.shuffle(options)

            question = PracticeQuestion(
                mode=PracticeMode.RECOGNITION,
                letter=letter,
                question_text=f"What is the name of this letter? → {display_letter}",
                options=options,
                correct_answer=correct_name,
                explanation=f"This is {correct_name} ({info['english']}). Example: {info['example_words'][0] if info['example_words'] else ''}",  # type: ignore[reportUnknownMemberType]
                difficulty=(info["difficulty"] or 0),  # type: ignore[reportUnknownMemberType]
            )
            questions.append(question)

        return questions

    def get_pronunciation_drill(
        self,
        num_questions: int = 5,
        difficulty: Optional[int] = None,
    ) -> List[PracticeQuestion]:
        """Generate pronunciation drill (show IPA/sound, pick letter).
        
        Args:
            num_questions: Number of questions
            difficulty: Filter by difficulty (1-5)
        """
        if difficulty:
            letters = [
                l for l in self.all_letters
                if (info := letter_data.get_letter_info(l)) is not None
                and info["difficulty"] >= difficulty
            ]
        else:
            letters = self.all_letters

        questions = []
        selected = random.sample(letters, min(num_questions, len(letters)))

        for letter in selected:
            info = letter_data.get_letter_info(letter)
            if info is None:
                continue

            # Create options: correct letter + 3 random others
            wrong_letters = random.sample(
                [l for l in letters if l != letter], 3
            )
            options = [letter] + wrong_letters
            random.shuffle(options)
            option_names = [
                f"{l} ({inf['name']})" for l in options if (inf := letter_data.get_letter_info(l)) is not None
            ]

            question = PracticeQuestion(
                mode=PracticeMode.PRONUNCIATION,
                letter=letter,
                question_text=f"Which letter makes this sound? IPA: /{info['ipa']}/ (English: {info['english']})",
                options=option_names,
                correct_answer=f"{letter} ({info['name']})",
                explanation=f"The answer is {letter} ({info['name']}). {info.get('pronunciation_tip', '')}",
                difficulty=info["difficulty"],
            )
            questions.append(question)

        return questions

    def get_word_identification_drill(
        self,
        num_questions: int = 5,
        difficulty: Optional[int] = None,
    ) -> List[PracticeQuestion]:
        """Generate word identification drill (find letter in word).
        
        Args:
            num_questions: Number of questions
            difficulty: Filter by difficulty (1-5)
        """
        if difficulty:
            letters = [
                l for l in self.all_letters
                if (info := letter_data.get_letter_info(l)) is not None
                and info["difficulty"] >= difficulty
            ]
        else:
            letters = self.all_letters

        questions = []
        selected = random.sample(letters, min(num_questions, len(letters)))

        for letter in selected:
            info = letter_data.get_letter_info(letter)
            if info is None:
                continue

            # Use example words
            if not info.get("example_words"):
                continue

            example_word = random.choice(info["example_words"])
            # Extract just the Armenian word (before parenthesis)
            arm_word = example_word.split("(")[0].strip() if "(" in example_word else example_word

            # Create options: correct answer + distractors
            wrong_letters = random.sample(
                [l for l in letters if l != letter], 3
            )
            options = [letter] + wrong_letters
            random.shuffle(options)
            option_texts = [
                f"{l} ({inf['name']})" for l in options if (inf := letter_data.get_letter_info(l)) is not None
            ]

            question = PracticeQuestion(
                mode=PracticeMode.WORD_IDENTIFICATION,
                letter=letter,
                question_text=f"Which letter appears in this word? → {arm_word}",
                options=option_texts,
                correct_answer=f"{letter} ({info['name']})",
                explanation=f"The letter {letter} ({info['name']}) appears in {arm_word}. Meaning: {example_word}",
                difficulty=info["difficulty"],
            )
            questions.append(question)

        return questions

    def get_diphthong_drill(
        self,
        num_questions: int = 3,
    ) -> List[PracticeQuestion]:
        """Generate diphthong practice (ու, իւ combinations).
        
        Args:
            num_questions: Number of questions (limited by available diphthongs)
        """
        diphthongs = list(letter_data.ARMENIAN_DIPHTHONGS.items())
        if not diphthongs:
            return []

        questions = []
        selected = random.sample(diphthongs, min(num_questions, len(diphthongs)))

        for diph, info in selected:
            letters_in_diph = info["letters"]

            # Question 1: Identify what letters form diphthong
            options = [
                f"{letters_in_diph[0]} + {letters_in_diph[1]}",
                f"{random.choice(self.all_letters)} + {random.choice(self.all_letters)}",
                f"{random.choice(self.all_letters)} + {random.choice(self.all_letters)}",
            ]
            random.shuffle(options)

            question = PracticeQuestion(
                mode=PracticeMode.DIPHTHONG,
                letter=diph,
                question_text=f"What letters form this diphthong? → {diph} ({info['ipa']})",
                options=options,
                correct_answer=f"{letters_in_diph[0]} + {letters_in_diph[1]}",
                explanation=f"The diphthong {diph} is formed by {letters_in_diph[0]} + {letters_in_diph[1]}, "
                           f"creating the sound /{info['ipa']}/ ({info['english']}). {info['note']}",
                difficulty=1,
            )
            questions.append(question)

        return questions

    def get_comparison_drill(
        self,
        num_questions: int = 5,
    ) -> List[PracticeQuestion]:
        """Generate letter comparison drill (distinguish similar letters).
        
        Helps with commonly confused letters like:
        - բ (b sound) vs պ (p sound)
        - գ (g sound) vs կ (k sound)
        - դ (d sound) vs տ (t sound)
        """
        # Pairs that are commonly confused (reversed voicing in Western Armenian)
        confusable_pairs = [
            ("բ", "պ"),  # p vs b
            ("գ", "կ"),  # k vs g
            ("դ", "տ"),  # t vs d
            ("ծ", "ձ"),  # dz pairs
            ("ճ", "ջ"),  # j/ch pairs
        ]

        questions = []

        for _ in range(min(num_questions, len(confusable_pairs))):
            letter1, letter2 = random.choice(confusable_pairs)
            info1 = letter_data.get_letter_info(letter1)
            info2 = letter_data.get_letter_info(letter2)
            if info1 is None or info2 is None:
                continue

            # Which one sounds like X?
            if random.random() > 0.5:
                target = info1
                correct_letter = letter1
            else:
                target = info2
                correct_letter = letter2

            correct_info = letter_data.get_letter_info(correct_letter)
            correct_name = correct_info["name"] if correct_info else correct_letter
            question = PracticeQuestion(
                mode=PracticeMode.COMPARISON,
                letter=correct_letter,
                question_text=f"Which sounds like '{target['english']}'? Choose between: {letter1} or {letter2}",
                options=[letter1, letter2],
                correct_answer=correct_letter,
                explanation=f"{correct_letter} ({correct_name}) "
                           f"sounds like {target['english']}. Western Armenian has reversed voicing: "
                           f"{letter1} = {info1['english']}, {letter2} = {info2['english']}",
                difficulty=3,
            )
            questions.append(question)

        return questions

    def get_difficulty_progression(
        self,
        current_level: int = 1,
        num_questions: int = 10,
    ) -> Tuple[List[PracticeQuestion], Dict[str, Any]]:
        """Generate guided learning progression (easy → hard).
        
        Args:
            current_level: 1-5, determines difficulty range
            num_questions: Number of questions at this level
            
        Returns:
            Tuple of (questions, progression_metadata)
        """
        difficulty_ranges = {
            1: [1],           # Level 1: only difficulty 1
            2: [1, 2],        # Level 2: difficulty 1-2
            3: [1, 2, 3],     # Level 3: difficulty 1-3
            4: [2, 3, 4],     # Level 4: difficulty 2-4
            5: [3, 4, 5],     # Level 5: difficulty 3-5
        }

        target_difficulties = difficulty_ranges.get(current_level, [1, 2, 3, 4, 5])
        letters = [
            l for l in self.all_letters
            if (info := letter_data.get_letter_info(l)) is not None
            and info["difficulty"] in target_difficulties
        ]

        # Mix different question types
        questions = []
        mode_weights = {
            PracticeMode.RECOGNITION: 3,
            PracticeMode.PRONUNCIATION: 3,
            PracticeMode.WORD_IDENTIFICATION: 2,
            PracticeMode.DIPHTHONG: 1 if current_level >= 3 else 0,
            PracticeMode.COMPARISON: 1 if current_level >= 2 else 0,
        }

        # Generate questions proportionally
        remaining = num_questions
        for mode, weight in mode_weights.items():
            if weight == 0:
                continue

            num_for_mode = max(1, (weight * num_questions) // 10)
            num_for_mode = min(num_for_mode, remaining)

            if mode == PracticeMode.RECOGNITION:
                q = self.get_recognition_drill(num_for_mode, difficulty=min(target_difficulties))
            elif mode == PracticeMode.PRONUNCIATION:
                q = self.get_pronunciation_drill(num_for_mode, difficulty=min(target_difficulties))
            elif mode == PracticeMode.WORD_IDENTIFICATION:
                q = self.get_word_identification_drill(num_for_mode, difficulty=min(target_difficulties))
            elif mode == PracticeMode.DIPHTHONG:
                q = self.get_diphthong_drill(num_for_mode)
            elif mode == PracticeMode.COMPARISON:
                q = self.get_comparison_drill(num_for_mode)
            else:
                continue

            questions.extend(q[:num_for_mode])
            remaining -= num_for_mode

        random.shuffle(questions)

        metadata = {
            "level": current_level,
            "difficulty_range": target_difficulties,
            "available_letters": len(letters),
            "total_questions": len(questions),
            "recommended_next_level": min(5, current_level + 1) if len(questions) > 0 else current_level,
        }

        return questions[:num_questions], metadata

    def generate_practice_session(
        self,
        mode: PracticeMode,
        num_questions: int = 10,
        difficulty: Optional[int] = None,
    ) -> List[PracticeQuestion]:
        """Generate a practice session of specified type.
        
        Args:
            mode: Type of practice (recognition, pronunciation, etc.)
            num_questions: Questions to generate
            difficulty: Optional difficulty filter (1-5)
        """
        if mode == PracticeMode.RECOGNITION:
            return self.get_recognition_drill(num_questions, difficulty)
        elif mode == PracticeMode.PRONUNCIATION:
            return self.get_pronunciation_drill(num_questions, difficulty)
        elif mode == PracticeMode.WORD_IDENTIFICATION:
            return self.get_word_identification_drill(num_questions, difficulty)
        elif mode == PracticeMode.DIPHTHONG:
            return self.get_diphthong_drill(num_questions)
        elif mode == PracticeMode.COMPARISON:
            return self.get_comparison_drill(num_questions)
        else:
            return []

    def format_question_for_display(self, question: PracticeQuestion) -> Dict[str, Union[str, List[str]]]:
        """Format question for console/UI display.
        
        Returns:
            Dictionary with formatted question and options
        """
        return {
            "mode": question.mode.value,
            "question": question.question_text,
            "options": question.options,
            "letter": question.letter,
            "difficulty": f"{question.difficulty}/5",
        }

    def check_answer(
        self,
        question: PracticeQuestion,
        answer: str,
    ) -> Tuple[bool, str]:
        """Check if answer is correct and return explanation.
        
        Args:
            question: The practice question
            answer: User's answer
            
        Returns:
            Tuple of (is_correct, explanation)
        """
        is_correct = answer.strip() == question.correct_answer.strip()
        return is_correct, question.explanation
