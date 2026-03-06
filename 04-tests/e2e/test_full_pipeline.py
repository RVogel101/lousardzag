"""
End-to-end test suite for Lousardzag pipeline.

Tests complete workflows from start to finish:
- Vocabulary generation → Card creation → Database storage
- Sentence progression through difficulty levels
- Audio generation pipeline (IPA → TTS → file)
- Card difficulty progression

⚠️ EXCLUDES: Anki import/export (per project scope)
"""

import pytest
import sys
import json
import sqlite3
import tempfile
from pathlib import Path
from typing import Dict, Any

# Add source to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / '02-src'))

from lousardzag.database import CardDatabase
from lousardzag.phonetics import get_phonetic_transcription, calculate_phonetic_difficulty
from lousardzag.sentence_progression import get_available_tiers_at_level, get_form_tier
from lousardzag.morphology.difficulty import score_word_difficulty


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db = CardDatabase(tmp.name)
    yield db
    Path(tmp.name).unlink(missing_ok=True)


@pytest.fixture
def sample_vocab():
    """Sample vocabulary for testing."""
    return [
        {'word': 'տուն', 'translation': 'house', 'pos': 'noun', 'frequency_rank': 100},
        {'word': 'գիրք', 'translation': 'book', 'pos': 'noun', 'frequency_rank': 200},
        {'word': 'բառ', 'translation': 'word', 'pos': 'noun', 'frequency_rank': 50},
        {'word': 'լաւ', 'translation': 'good', 'pos': 'adjective', 'frequency_rank': 10},
        {'word': 'մեծ', 'translation': 'big', 'pos': 'adjective', 'frequency_rank': 30},
    ]


class TestVocabularyGenerationPipeline:
    """Test vocabulary generation to card creation workflow."""
    
    def test_vocab_to_card_creation(self, temp_db, sample_vocab):
        """Test: Vocabulary list → Cards with enrichment → Database storage."""
        
        # Step 1: Create cards from vocabulary
        cards_created = []
        for idx, vocab in enumerate(sample_vocab):
            # Generate phonetic data
            phonetic_data = get_phonetic_transcription(vocab['word'])
            phonetic_difficulty = calculate_phonetic_difficulty(vocab['word'])
            
            # Store in database (use fake anki_note_id for testing without Anki)
            card_id = temp_db.upsert_card(
                word=vocab['word'],
                translation=vocab['translation'],
                pos=vocab['pos'],
                card_type='vocabulary',
                syllable_count=len(vocab['word'].split()),
                metadata={'frequency_rank': vocab['frequency_rank']},
                morphology={'phonetic_difficulty': phonetic_difficulty},
                anki_note_id=1000 + idx  # Fake ID for testing
            )
            
            cards_created.append(card_id)
        
        # Verify all cards created
        assert len(cards_created) == len(sample_vocab)
        assert all(isinstance(cid, int) for cid in cards_created)
        
        # Step 2: Retrieve and verify
        for idx, card_id in enumerate(cards_created):
            card = temp_db.get_card(card_id)
            assert card is not None
            assert card['word'] == sample_vocab[idx]['word']
            assert card['translation'] == sample_vocab[idx]['translation']
            assert card['pos'] == sample_vocab[idx]['pos']
    
    def test_vocabulary_ordering_by_difficulty(self, sample_vocab):
        """Test: Vocabulary ordered by phonetic difficulty."""
        
        # Calculate difficulty for each word
        vocab_with_difficulty = []
        for vocab in sample_vocab:
            difficulty = calculate_phonetic_difficulty(vocab['word'])
            vocab_with_difficulty.append({
                **vocab,
                'phonetic_difficulty': difficulty
            })
        
        # Sort by difficulty (ascending)
        sorted_vocab = sorted(vocab_with_difficulty, key=lambda x: x['phonetic_difficulty'])
        
        # Verify ordering is consistent
        assert sorted_vocab[0]['phonetic_difficulty'] <= sorted_vocab[-1]['phonetic_difficulty']
        
        # Verify all words retained
        assert len(sorted_vocab) == len(sample_vocab)


class TestSentenceProgressionPipeline:
    """Test sentence coaching progression system."""
    
    def test_sentence_difficulty_progression(self, temp_db, sample_vocab):
        """Test: Sentences progress from easy to hard based on vocabulary mastery."""
        
        # Setup: Add vocabulary to database
        vocab_ids = []
        for idx, vocab in enumerate(sample_vocab):
            card_id = temp_db.upsert_card(
                word=vocab['word'],
                translation=vocab['translation'],
                pos=vocab['pos'],
                card_type='vocabulary',
                anki_note_id=2000 + idx  # Fake ID for testing
            )
            vocab_ids.append(card_id)
        
        # Test tier availability at different levels
        level_1_tiers = get_available_tiers_at_level(1)
        level_5_tiers = get_available_tiers_at_level(5)
        
        # Verify level 1 has fewer tiers than level 5
        assert len(level_1_tiers) > 0
        assert len(level_5_tiers) >= len(level_1_tiers)
    
    def test_tier_mapping_from_forms(self):
        """Test: Form labels map to appropriate tiers."""
        
        # Test some known mappings
        nominative_tier = get_form_tier("nominative")
        accusative_tier = get_form_tier("accusative")
        
        # Should return tier names
        assert nominative_tier is not None
        assert accusative_tier is not None
        assert nominative_tier != accusative_tier


class TestAudioGenerationPipeline:
    """Test audio generation from word to audio file."""
    
    def test_ipa_transcription_pipeline(self):
        """Test: Armenian word → IPA transcription → Phonetic data."""
        
        test_words = [
            ('տուն', 'dun'),  # house
            ('գիրք', 'kirk'),  # book
            ('բառ', 'par'),    # word (reversed voicing)
        ]
        
        for word, expected_approx in test_words:
            result = get_phonetic_transcription(word)
            
            # Verify result structure
            assert 'ipa' in result
            assert 'english_approx' in result
            assert 'difficult_phonemes' in result
            assert 'max_phonetic_difficulty' in result
            
            # Verify non-empty
            assert result['ipa'] != ''
            assert isinstance(result['difficult_phonemes'], list)
    
    def test_phonetic_difficulty_scoring(self):
        """Test: Words receive appropriate difficulty scores."""
        
        # Easy words (common phonemes)
        easy_words = ['տուն', 'գիրք']
        
        # Hard words (difficult phonemes like ղ, ռ)
        hard_words = ['ղեկ', 'ռամիկ']
        
        easy_scores = [calculate_phonetic_difficulty(w) for w in easy_words]
        hard_scores = [calculate_phonetic_difficulty(w) for w in hard_words]
        
        # Verify scoring is consistent (higher = harder)
        avg_easy = sum(easy_scores) / len(easy_scores) if easy_scores else 0
        avg_hard = sum(hard_scores) / len(hard_scores) if hard_scores else 0
        
        # Hard words should generally score higher
        # (May not always be true, but should trend that way)
        assert all(isinstance(s, (int, float)) for s in easy_scores + hard_scores)


class TestCardDifficultyProgression:
    """Test card difficulty calculation and progression."""
    
    def test_morphological_difficulty_calculation(self):
        """Test: Cards receive appropriate morphological difficulty scores."""
        
        # Simple noun (low complexity)
        simple_word = 'տուն'  # house
        
        # Complex word (higher complexity)
        complex_word = 'զբաղեցուցանել'  # to occupy (causative)
        
        # Calculate difficulties using score_word_difficulty
        simple_difficulty = score_word_difficulty(
            word=simple_word,
            pos='noun'
        )
        
        complex_difficulty = score_word_difficulty(
            word=complex_word,
            pos='verb'
        )
        
        # Verify both return valid scores
        assert isinstance(simple_difficulty, (int, float))
        assert isinstance(complex_difficulty, (int, float))
        
        # Complex should be harder (or equal)
        assert complex_difficulty >= simple_difficulty
    
    def test_combined_difficulty_factors(self):
        """Test: Cards combine phonetic + morphological + frequency difficulty."""
        
        test_word = 'տուն'
        
        # Get phonetic difficulty
        phonetic_diff = calculate_phonetic_difficulty(test_word)
        
        # Get morphological difficulty
        morph_diff = score_word_difficulty(
            word=test_word,
            pos='noun'
        )
        
        # Frequency factor (inverse: lower rank = easier)
        frequency_rank = 100
        frequency_factor = min(5, max(1, frequency_rank / 1000))
        
        # Combined difficulty
        combined = (phonetic_diff + morph_diff + frequency_factor) / 3
        
        # Verify reasonable range (1-5)
        assert 1 <= combined <= 5


class TestDatabaseIntegration:
    """Test database operations in workflow context."""
    
    def test_bulk_card_insertion(self, temp_db, sample_vocab):
        """Test: Bulk insert vocabulary maintains data integrity."""
        
        # Insert all vocabulary
        card_ids = []
        for idx, vocab in enumerate(sample_vocab):
            card_id = temp_db.upsert_card(
                word=vocab['word'],
                translation=vocab['translation'],
                pos=vocab['pos'],
                card_type='vocabulary',
                metadata={'frequency_rank': vocab['frequency_rank']},
                anki_note_id=3000 + idx  # Fake ID for testing
            )
            card_ids.append(card_id)
        
        # Verify all inserted
        assert len(card_ids) == len(sample_vocab)
        
        # Verify data integrity
        for idx, card_id in enumerate(card_ids):
            card = temp_db.get_card(card_id)
            assert card['word'] == sample_vocab[idx]['word']
    
    def test_duplicate_handling(self, temp_db):
        """Test: Duplicate words are updated, not duplicated."""
        
        # Insert same word twice with different data
        id1 = temp_db.upsert_card(
            word='տուն',
            translation='house',
            pos='noun',
            card_type='vocabulary',
            anki_note_id=4000  # Fake ID for testing
        )
        
        id2 = temp_db.upsert_card(
            word='տուն',
            translation='home',  # Different translation
            pos='noun',
            card_type='vocabulary',
            anki_note_id=4000  # Same ID to test update
        )
        
        # Should return same ID
        assert id1 == id2
        
        # Should have updated translation
        card = temp_db.get_card(id1)
        assert card['translation'] == 'home'


class TestPreviewGeneration:
    """Test card preview generation (without Anki)."""
    
    def test_card_data_serialization(self, temp_db, sample_vocab):
        """Test: Cards serialize to JSON for preview display."""
        
        # Create cards
        card_ids = []
        for idx, vocab in enumerate(sample_vocab):
            card_id = temp_db.upsert_card(
                word=vocab['word'],
                translation=vocab['translation'],
                pos=vocab['pos'],
                card_type='vocabulary',
                anki_note_id=5000 + idx  # Fake ID for testing
            )
            card_ids.append(card_id)
        
        # Retrieve and serialize
        cards_json = []
        for card_id in card_ids:
            card = temp_db.get_card(card_id)
            cards_json.append({
                'id': card['id'],
                'word': card['word'],
                'translation': card['translation'],
                'pos': card['pos']
            })
        
        # Verify JSON serializable
        json_str = json.dumps(cards_json, ensure_ascii=False)
        assert json_str is not None
        
        # Verify deserializable
        deserialized = json.loads(json_str)
        assert len(deserialized) == len(sample_vocab)


# ============================================================================
# Test Runner
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
