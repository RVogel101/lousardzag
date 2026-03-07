#!/usr/bin/env python3
"""
Populate enrichment fields in Anki database: frequency_rank, syllable_count, 
morphology_json, custom_level, POS tags.

Uses existing lousardzag utilities for:
  - Syllable counting (morphology.core.count_syllables)  
  - Difficulty scoring (morphology.difficulty.score_word_difficulty)
  - Phonetic transcription (phonetics.get_phonetic_transcription)

Usage:
    python 07-tools/enrich_anki_database.py [--dry-run] [--limit N]

Options:
    --dry-run    Don't make changes, just report what would be done
    --limit N    Process only first N cards (for testing)
"""

import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Add source directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / '02-src'))

from lousardzag.morphology.core import count_syllables
from lousardzag.morphology.difficulty import (
    analyze_word,
    score_word_difficulty,
)
from lousardzag.core_shims.linguistics_core import get_phonetic_transcription
from lousardzag.db_operations import DatabaseOperation

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────

DB_PATH = Path('08-data/armenian_cards.db')
REPORT_PATH = Path('08-data/enrichment_report.json')

# ──────────────────────────────────────────────────────────────────────────────
# Main enrichment class
# ──────────────────────────────────────────────────────────────────────────────

class AnkiDatabaseEnrichment(DatabaseOperation):
    """Enrich Anki database with computed fields."""
    
    def __init__(self, db_path: Path, dry_run: bool = False, limit: Optional[int] = None):
        super().__init__(db_path, dry_run, create_backup=False)
        self.limit = limit
        
        # Extend base report with enrichment-specific fields
        self.report.update({
            'limit': limit,
            'enrichment_summary': {
                'syllable_count_added': 0,
                'difficulty_score_added': 0,
                'phonetics_added': 0,
                'morphology_added': 0,
                'pos_inferred': 0,
            },
        })
    
    @property
    def report_path(self) -> Path:
        """Path to save enrichment report."""
        return REPORT_PATH
    
    def connect(self) -> sqlite3.Connection:
        """Connect to database with Row factory."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_stats(self, conn: sqlite3.Connection) -> Dict:
        """Get enrichment level statistics."""
        c = conn.cursor()
        
        c.execute('SELECT COUNT(*) FROM anki_cards WHERE syllable_count IS NOT NULL')
        with_syllables = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM anki_cards')
        total = c.fetchone()[0]
        
        return {
            'total_cards': total,
            'cards_with_syllable_count': with_syllables,
            'cards_needing_syllable_count': total - with_syllables,
        }
    
    def infer_pos(self, word: str, translation: str) -> Optional[str]:
        """
        Infer part of speech from translation or word patterns.
        
        Very basic heuristic-based approach.
        """
        # Look for common suffixes
        if word.endswith('ով') or word.endswith('ոտ'):
            return 'adverb'
        
        if word.endswith('ել') or word.endswith('ա'):
            if len(word) > 3 and word[-3:] == 'ալ':
                return 'verb'
        
        # Check translation patterns
        if translation:
            trans_lower = translation.lower()
            if 'to ' in trans_lower or ' verb' in trans_lower:
                return 'verb'
            if 'adjective' in trans_lower or 'adj' in trans_lower:
                return 'adjective'
            if 'adverb' in trans_lower or 'adv' in trans_lower:
                return 'adverb'
        
        # Default to noun if no pattern matches
        return 'noun'
    
    def enrich_card(self, card: sqlite3.Row) -> Dict[str, Any]:
        """Compute enrichment data for a single card."""
        word = card['word']
        translation = card['translation']
        
        enrichment = {}
        errors = []
        
        try:
            # Syllable count
            syllable_count = count_syllables(word)
            enrichment['syllable_count'] = syllable_count
        except Exception as e:
            errors.append(f"syllable_count error: {e}")
        
        try:
            # Infer POS if not present
            pos = card['pos'] or self.infer_pos(word, translation)
            enrichment['pos'] = pos
            
            # Difficulty score
            difficulty = score_word_difficulty(word, pos or "noun")
            # Store as JSON in metadata field for now
            enrichment['difficulty_score'] = difficulty
        except Exception as e:
            errors.append(f"difficulty_score error: {e}")
        
        try:
            # Phonetic data
            phonetics = get_phonetic_transcription(word)
            morphology_data = {
                'ipa': phonetics.get('ipa', ''),
                'english_approx': phonetics.get('english_approx', ''),
                'phonetic_difficulty': phonetics.get('max_phonetic_difficulty', 0),
            }
            enrichment['morphology_json'] = json.dumps(morphology_data, ensure_ascii=False)
        except Exception as e:
            errors.append(f"phonetics error: {e}")
        
        enrichment['errors'] = errors
        return enrichment
    
    def run(self) -> None:
        """Execute enrichment process."""
        print("\n" + "=" * 80)
        print("ANKI DATABASE ENRICHMENT")
        print("=" * 80)
        
        if self.dry_run:
            print("\n[DRY RUN MODE] No changes will be made")
        
        if self.limit:
            print(f"\n[LIMITED MODE] Processing only {self.limit} cards")
        
        # Connect to database
        conn = self.connect()
        c = conn.cursor()
        
        # Get stats before
        print("\n--- BEFORE ENRICHMENT ---")
        stats_before = self.get_stats(conn)
        self.report['stats_before'] = stats_before
        for key, value in stats_before.items():
            print(f"{key:30} {value:>6}")
        
        # Get cards to enrich
        query = 'SELECT * FROM anki_cards WHERE word IS NOT NULL AND word != "" ORDER BY id'
        if self.limit:
            query += f' LIMIT {self.limit}'
        
        c.execute(query)
        cards = c.fetchall()
        
        print(f"\n--- ENRICHING {len(cards)} CARDS ---")
        
        enriched_count = 0
        syllable_updates = 0
        pos_updates = 0
        morphology_updates = 0
        errors_encountered = 0
        
        for i, card in enumerate(cards):
            if (i + 1) % 100 == 0:
                print(f"  Progress: {i + 1}/{len(cards)}")
            
            try:
                enrichment = self.enrich_card(card)
                
                if enrichment.get('errors'):
                    for error in enrichment['errors']:
                        print(f"  ⚠  Card {card['id']} ({card['word']}): {error}")
                        errors_encountered += 1
                        self.report['errors'].append({
                            'card_id': card['id'],
                            'word': card['word'],
                            'error': error
                        })
                
                # Update database
                if not self.dry_run:
                    updates = []
                    params = []
                    
                    if 'syllable_count' in enrichment:
                        updates.append('syllable_count = ?')
                        params.append(enrichment['syllable_count'])
                        syllable_updates += 1
                    
                    if 'pos' in enrichment and not card['pos']:
                        updates.append('pos = ?')
                        params.append(enrichment['pos'])
                        pos_updates += 1
                    
                    if 'morphology_json' in enrichment:
                        updates.append('morphology_json = ?')
                        params.append(enrichment['morphology_json'])
                        morphology_updates += 1
                    
                    if updates:
                        params.append(card['id'])
                        update_sql = f"UPDATE anki_cards SET {', '.join(updates)} WHERE id = ?"
                        c.execute(update_sql, params)
                        enriched_count += 1
                else:
                    # Dry run: just count
                    if 'syllable_count' in enrichment or 'pos' in enrichment or 'morphology_json' in enrichment:
                        enriched_count += 1
                        if 'syllable_count' in enrichment:
                            syllable_updates += 1
                        if 'pos' in enrichment:
                            pos_updates += 1
                        if 'morphology_json' in enrichment:
                            morphology_updates += 1
                        
                        if i < 3:  # Show first 3 examples
                            print(f"  [DRY RUN] Card {card['id']} ({card['word']}): {enrichment}")
                
            except Exception as e:
                print(f"  [ERROR] Card {card['id']} failed: {e}")
                self.report['errors'].append({
                    'card_id': card['id'],
                    'word': card['word'],
                    'error': str(e)
                })
                errors_encountered += 1
        
        if not self.dry_run:
            conn.commit()
        
        # Update summary
        self.report['enrichment_summary'] = {
            'cards_enriched': enriched_count,
            'syllable_count_added': syllable_updates,
            'pos_inferred': pos_updates,
            'morphology_added': morphology_updates,
            'errors_encountered': errors_encountered,
        }
        
        print(f"\n--- ENRICHMENT SUMMARY ---")
        print(f"Cards enriched:             {enriched_count:>6}")
        print(f"Syllable counts added:      {syllable_updates:>6}")
        print(f"POS tags inferred:          {pos_updates:>6}")
        print(f"Morphology data added:      {morphology_updates:>6}")
        print(f"Errors encountered:         {errors_encountered:>6}")
        
        # Get stats after
        print(f"\n--- AFTER ENRICHMENT ---")
        stats_after = self.get_stats(conn)
        self.report['stats_after'] = stats_after
        for key, value in stats_after.items():
            print(f"{key:30} {value:>6}")
        
        # Save report
        self.save_report()
        
        conn.close()
        print("\n" + "=" * 80)
        print("ENRICHMENT COMPLETE")
        print("=" * 80)


def main():
    """Main entry point."""
    dry_run = '--dry-run' in sys.argv
    limit = None
    
    for i, arg in enumerate(sys.argv[1:]):
        if arg == '--limit' and i + 1 < len(sys.argv[1:]):
            try:
                limit = int(sys.argv[i + 2])
            except (ValueError, IndexError):
                print("Error: --limit requires an integer argument")
                sys.exit(1)
    
    enrichment = AnkiDatabaseEnrichment(
        db_path=DB_PATH,
        dry_run=dry_run,
        limit=limit
    )
    enrichment.run()


if __name__ == '__main__':
    main()
