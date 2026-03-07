"""
Flashcard Practice Viewer
A minimal, interactive flashcard system for vocabulary and sentence learning.
Supports vocabulary cards (with progressive reveal) and sentence cards (with word focus).
"""

import json
import sqlite3
import sys
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_from_directory  # type: ignore[reportMissingImports]
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(
    __name__,
    template_folder='../02-src/lousardzag/templates',
    static_folder='../02-src/lousardzag/templates',
)

# Configuration
WORKSPACE_ROOT = Path(__file__).parent.parent
DATA_DIR = WORKSPACE_ROOT / '08-data'
AUDIO_DIR = WORKSPACE_ROOT / '08-data' / 'vocab_audio'
sys.path.insert(0, str(WORKSPACE_ROOT / '02-src'))

from lousardzag.anki_connect import AnkiConnect, AnkiConnectError

LOCAL_DB_PATH = WORKSPACE_ROOT / '08-data' / 'armenian_cards.db'
ANKI_ALLOWED_DECKS = [
    'Armenian (Western)',
]


def _resolve_local_db_path():
    """Return the canonical local database path used by this viewer."""
    if not LOCAL_DB_PATH.exists():
        raise FileNotFoundError(f"Required local DB not found: {LOCAL_DB_PATH}")
    return LOCAL_DB_PATH


def _ensure_cards_table(conn):
    """Ensure cards table exists for local caching from Anki."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cards (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            word             TEXT    NOT NULL,
            translation      TEXT    NOT NULL DEFAULT '',
            pos              TEXT    NOT NULL DEFAULT '',
            declension_class TEXT    NOT NULL DEFAULT '',
            verb_class       TEXT    NOT NULL DEFAULT '',
            frequency_rank   INTEGER NOT NULL DEFAULT 9999,
            syllable_count   INTEGER NOT NULL DEFAULT 0,
            level            INTEGER NOT NULL DEFAULT 1,
            batch_index      INTEGER NOT NULL DEFAULT 0,
            card_type        TEXT    NOT NULL DEFAULT '',
            template_version TEXT    NOT NULL DEFAULT 'v1',
            metadata_json    TEXT    NOT NULL DEFAULT '{}',
            morphology_json  TEXT    NOT NULL DEFAULT '{}',
            anki_note_id     INTEGER,
            created_at       TEXT    NOT NULL,
            UNIQUE (word, card_type)
        )
        """
    )


def _upsert_anki_notes_to_local_db(notes):
    """Persist full Anki note payloads into local cards table."""
    db_path = _resolve_local_db_path()

    now_iso = datetime.now().isoformat()
    saved = 0

    with sqlite3.connect(db_path) as conn:
        _ensure_cards_table(conn)

        for note in notes:
            raw_fields = note.get('fields', {})
            field_values = {
                name: info.get('value', '') if isinstance(info, dict) else ''
                for name, info in raw_fields.items()
            }

            word = _first_nonempty(field_values, ['Word', 'Armenian', 'word'])
            if not word:
                continue

            translation = _first_nonempty(
                field_values,
                ['Translation', 'English', 'Meaning', 'translation'],
            )
            pos = _first_nonempty(
                field_values,
                ['PartOfSpeech', 'POS', 'Type', 'pos'],
            )

            metadata = {
                'anki_note_id': note.get('noteId'),
                'anki_model_name': note.get('modelName', ''),
                'anki_deck_name': note.get('deckName', ''),
                'anki_tags': note.get('tags', []),
                'anki_fields': field_values,
                'anki_fields_raw': raw_fields,
            }

            note_id = note.get('noteId')
            card_type = f"anki_note:{note_id}" if note_id is not None else 'anki_note:unknown'

            conn.execute(
                """
                INSERT INTO cards
                    (word, translation, pos, declension_class, verb_class,
                     frequency_rank, syllable_count, level, batch_index,
                     card_type, template_version, metadata_json, morphology_json,
                     anki_note_id, created_at)
                VALUES
                    (?, ?, ?, '', '',
                     9999, 0, 1, 0,
                     ?, 'v1', ?, '{}',
                     ?, ?)
                ON CONFLICT(word, card_type) DO UPDATE SET
                    translation      = excluded.translation,
                    pos              = excluded.pos,
                    metadata_json    = excluded.metadata_json,
                    anki_note_id     = COALESCE(excluded.anki_note_id, cards.anki_note_id)
                """,
                (
                    word,
                    translation,
                    pos,
                    card_type,
                    json.dumps(metadata, ensure_ascii=False),
                    note_id,
                    now_iso,
                ),
            )
            saved += 1

        conn.commit()

    logger.info(f"Saved {saved} Anki notes into local DB: {db_path}")
    return db_path, saved


def _load_cached_anki_cards(max_cards):
    """Load locally cached Anki cards from SQLite for viewer consumption."""
    db_path = _resolve_local_db_path()

    cards = []
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT word, translation, pos, frequency_rank, syllable_count,
                   metadata_json, morphology_json, anki_note_id
            FROM cards
            WHERE card_type LIKE 'anki_note:%'
            ORDER BY CASE WHEN frequency_rank IS NULL THEN 999999999 ELSE frequency_rank END ASC,
                     anki_note_id ASC
            LIMIT ?
            """,
            (max_cards,),
        ).fetchall()

    for i, row in enumerate(rows):
        metadata = {}
        if row['metadata_json']:
            try:
                metadata = json.loads(row['metadata_json'])
            except json.JSONDecodeError:
                metadata = {}

        # Preserve legacy behavior for letter rows when syllable_count is unset.
        syllables = int(row['syllable_count'] or 0)
        if syllables == 0 and (row['pos'] or '').strip().lower() == 'letter':
            syllables = 1

        cards.append({
            'id': f"vocab_{i}",
            'type': 'vocabulary',
            'word': row['word'] or '',
            'translation': row['translation'] or '',
            'pos': row['pos'] or '',
            'difficulty': float(metadata.get('difficulty', 2.5)),
            'syllables': syllables,
            'band': metadata.get('band', ''),
            'ipa': metadata.get('ipa', ''),
            'transliteration': metadata.get('transliteration', ''),
            'phonetic_difficulty': float(metadata.get('phonetic_difficulty', 2) or 2),
            'root': None,
            'verb_class': None,
            'example_sentences': [],
            'loanword_origin': None,
            'audio_file': f"vocab_{row['word']}.mp3" if row['word'] else None,
            'anki_note_id': metadata.get('anki_note_id', row['anki_note_id']),
            'anki_model_name': metadata.get('anki_model_name', ''),
            'anki_deck_name': metadata.get('anki_deck_name', ''),
            'anki_tags': metadata.get('anki_tags', []),
            'anki_fields': metadata.get('anki_fields', {}),
            'anki_fields_raw': metadata.get('anki_fields_raw', {}),
        })

    return cards


def _first_nonempty(field_values, candidate_names):
    """Return first non-empty field by name from Anki note values."""
    for name in candidate_names:
        value = field_values.get(name, '')
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ''

# Session state (in-memory for now, can be enhanced with persistence)
session_state = {
    'current_card_index': 0,
    'cards': [],
    'results': {
        'correct': [],
        'wrong': [],
        'skipped': []
    },
    'stats': {
        'total_reviewed': 0,
        'correct_count': 0,
        'wrong_count': 0,
        'start_time': datetime.now().isoformat()
    }
}


def load_vocabulary_cards(max_cards=None):
    """Sync from AnkiConnect into local SQLite, then load cached cards."""
    anki = AnkiConnect()
    if not anki.ping():
        logger.warning("AnkiConnect is not reachable; no vocabulary cards loaded")
        return []

    limit = int(max_cards) if max_cards else 50

    try:
        note_ids = []
        for deck_name in ANKI_ALLOWED_DECKS:
            note_ids.extend(anki.find_notes(f'"deck:{deck_name}"'))

        if not note_ids:
            logger.warning(f"No notes found in allowed decks: {ANKI_ALLOWED_DECKS}")
            return []

        # Preserve order while removing duplicates.
        unique_note_ids = list(dict.fromkeys(note_ids))[:limit]
        batch_size = 200
        notes = []
        for i in range(0, len(unique_note_ids), batch_size):
            notes.extend(anki.notes_info(unique_note_ids[i:i + batch_size]))

        db_path, saved_count = _upsert_anki_notes_to_local_db(notes)
        cards = _load_cached_anki_cards(limit)
        logger.info(
            f"Loaded {len(cards)} vocabulary cards after syncing {saved_count} notes to {db_path}"
        )
        return cards

    except AnkiConnectError as e:
        logger.error(f"Error loading vocabulary cards from AnkiConnect: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error loading vocabulary cards from AnkiConnect: {e}")
        return []

def load_sentence_cards(json_file='sentences.json', max_cards=None):
    """Load sentence cards from JSON file."""
    json_path = DATA_DIR / json_file
    
    if not json_path.exists():
        logger.info(f"Sentence file not found: {json_path} (optional)")
        return []
    
    cards = []
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            sentences = data if isinstance(data, list) else data.get('sentences', [])
            
            for i, sent in enumerate(sentences):
                if max_cards and i >= max_cards:
                    break
                
                card = {
                    'id': f"sentence_{i}",
                    'type': 'sentence',
                    'sentence': sent.get('sentence', ''),
                    'sentence_translation': sent.get('translation', ''),
                    'focused_word': sent.get('focused_word', ''),
                    'focused_word_translation': sent.get('focused_word_translation', ''),
                    'focused_word_pos': sent.get('focused_word_pos', ''),
                    'focused_word_tense': sent.get('focused_word_tense', ''),
                    'focused_word_ipa': sent.get('focused_word_ipa', ''),
                    'grammar_note': sent.get('grammar_note', ''),
                    'context_words': sent.get('context_words', []),
                    'loanword_origin': sent.get('loanword_origin', None),
                    'audio_file': sent.get('audio_file', None),
                }
                cards.append(card)
        
        logger.info(f"Loaded {len(cards)} sentence cards from {json_file}")
        return cards
    
    except Exception as e:
        logger.error(f"Error loading sentence cards: {e}")
        return []


# Routes

@app.route('/')
def index():
    """Main flashcard interface."""
    return render_template('flashcard_viewer.html')


@app.route('/api/cards/load', methods=['POST'])
def load_cards():
    """Load cards (vocabulary, sentences, or mixed) based on request."""
    data = request.json or {}
    
    card_type = data.get('type', 'vocabulary')  # 'vocabulary', 'sentence', or 'mixed'
    max_cards = data.get('max_cards', 50)
    
    cards = []
    
    if card_type in ['vocabulary', 'mixed']:
        vocab_cards = load_vocabulary_cards(max_cards=max_cards if card_type == 'vocabulary' else max_cards // 2)
        cards.extend(vocab_cards)
    
    if card_type in ['sentence', 'mixed']:
        sent_cards = load_sentence_cards(max_cards=max_cards if card_type == 'sentence' else max_cards // 2)
        cards.extend(sent_cards)
    
    # Initialize session
    session_state['cards'] = cards
    session_state['current_card_index'] = 0
    session_state['results'] = {
        'correct': [],
        'wrong': [],
        'skipped': []
    }
    session_state['stats'] = {
        'total_reviewed': 0,
        'correct_count': 0,
        'wrong_count': 0,
        'start_time': datetime.now().isoformat()
    }
    
    return jsonify({
        'status': 'success',
        'total_cards': len(cards),
        'card_type': card_type
    })


@app.route('/api/card/current')
def get_current_card():
    """Get the current card to display."""
    cards = session_state['cards']
    index = session_state['current_card_index']
    
    if not cards or index >= len(cards):
        return jsonify({
            'status': 'finished',
            'stats': session_state['stats'],
            'results': session_state['results']
        })
    
    card = cards[index]
    return jsonify({
        'status': 'success',
        'card': card,
        'progress': {
            'current': index + 1,
            'total': len(cards)
        }
    })


@app.route('/api/card/mark', methods=['POST'])
def mark_card():
    """Mark the current card as correct/wrong and advance."""
    data = request.json or {}
    action = data.get('action', 'wrong')  # 'correct' or 'wrong'
    
    cards = session_state['cards']
    index = session_state['current_card_index']
    
    if not cards or index >= len(cards):
        return jsonify({'status': 'error', 'message': 'No card to mark'})
    
    card = cards[index]
    
    # Record result
    result = {
        'card_id': card['id'],
        'card_type': card['type'],
        'word_or_sentence': card.get('word') or card.get('sentence'),
        'timestamp': datetime.now().isoformat()
    }
    
    if action == 'correct':
        session_state['results']['correct'].append(result)
        session_state['stats']['correct_count'] += 1
    else:
        session_state['results']['wrong'].append(result)
        session_state['stats']['wrong_count'] += 1
    
    session_state['stats']['total_reviewed'] += 1
    
    # Advance to next card
    session_state['current_card_index'] += 1
    
    return jsonify({
        'status': 'success',
        'action': action,
        'next_index': session_state['current_card_index'],
        'total_cards': len(cards)
    })


@app.route('/api/stats')
def get_stats():
    """Get study statistics."""
    stats = session_state['stats'].copy()
    stats['accuracy'] = (
        session_state['stats']['correct_count'] / session_state['stats']['total_reviewed'] * 100
        if session_state['stats']['total_reviewed'] > 0
        else 0
    )
    
    return jsonify({
        'stats': stats,
        'results': session_state['results']
    })


@app.route('/api/reset')
def reset_session():
    """Reset the session."""
    session_state['current_card_index'] = 0
    session_state['results'] = {
        'correct': [],
        'wrong': [],
        'skipped': []
    }
    session_state['stats'] = {
        'total_reviewed': 0,
        'correct_count': 0,
        'wrong_count': 0,
        'start_time': datetime.now().isoformat()
    }
    
    return jsonify({'status': 'success'})


# Static file serving (for audio files)
@app.route('/audio/<path:filename>')
def serve_audio(filename):
    """Serve audio files from vocab_audio directory."""
    try:
        return send_from_directory(AUDIO_DIR, filename)
    except Exception as e:
        logger.error(f"Error serving audio file {filename}: {e}")
        return jsonify({'error': 'Audio file not found'}), 404


@app.route('/api/audio/check/<filename>')
def check_audio(filename):
    """Check if an audio file exists."""
    audio_path = AUDIO_DIR / filename
    exists = audio_path.exists()
    return jsonify({
        'filename': filename,
        'exists': exists,
        'url': f'/audio/{filename}' if exists else None
    })


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    logger.warning(f"404 error: {request.path}")
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    logger.error(f"500 error: {e}")
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    logger.info("Starting Flashcard Practice Viewer...")
    logger.info(f"Workspace root: {WORKSPACE_ROOT}")
    logger.info(f"Data directory: {DATA_DIR}")
    
    # Check if data directory exists
    if not DATA_DIR.exists():
        logger.warning(f"Data directory does not exist: {DATA_DIR}")
    
    app.run(
        debug=True,
        host='127.0.0.1',
        port=5005,
        use_reloader=False  # Disable reloader for cleaner output
    )
