#!/usr/bin/env python3
"""
Clean up Anki database: remove duplicates, populate missing data, fix enrichment fields.

This script:
1. Adds missing enrichment columns (frequency_rank, syllable_count, morphology_json, custom_level)
2. Identifies and removes duplicate cards (keeps card with most complete data)
3. Consolidates translations for duplicate words
4. Tracks all changes in a detailed report

Usage:
    python 07-tools/cleanup_anki_database.py [--dry-run] [--backup]

Options:
    --dry-run    Don't make changes, just report what would be done
    --backup     Create backup before modifying (default: True unless --no-backup)
"""

import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Optional, Dict, List, Tuple

# Add source directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / '02-src'))

from lousardzag.db_operations import DatabaseOperation

# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────

DB_PATH = Path('08-data/armenian_cards.db')
REPORT_PATH = Path('08-data/cleanup_report.json')

# ──────────────────────────────────────────────────────────────────────────────
# Main cleanup class
# ──────────────────────────────────────────────────────────────────────────────

class AnkiDatabaseCleanup(DatabaseOperation):
    """Manages cleanup operations on Anki database."""
    
    def __init__(self, db_path: Path, dry_run: bool = False, create_backup: bool = True):
        super().__init__(db_path, dry_run, create_backup)
        
        # Extend base report with cleanup-specific fields
        self.report.update({
            'schema_updates': [],
            'duplicates_removed': [],
            'translations_fixed': [],
            'missing_data_summary': {},
        })
    
    @property
    def report_path(self) -> Path:
        """Path to save cleanup report."""
        return REPORT_PATH
    
    def get_stats(self, conn: sqlite3.Connection) -> Dict:
        """Get cleanup-specific database statistics."""
        c = conn.cursor()
        
        c.execute('SELECT COUNT(*) FROM anki_cards')
        total_cards = c.fetchone()[0]
        
        c.execute('SELECT COUNT(DISTINCT word) FROM anki_cards WHERE word NOT NULL AND word != ""')
        unique_words = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM anki_cards WHERE translation IS NULL OR translation = ""')
        no_translation = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM anki_cards WHERE pos IS NULL OR pos = ""')
        no_pos = c.fetchone()[0]
        
        # Count duplicates
        c.execute("""
            SELECT COUNT(*)
            FROM anki_cards
            WHERE word IN (
                SELECT word FROM anki_cards
                WHERE word NOT NULL AND word != ''
                GROUP BY word HAVING COUNT(*) > 1
            )
        """)
        duplicate_cards = c.fetchone()[0]
        
        return {
            'total_cards': total_cards,
            'unique_words': unique_words,
            'cards_without_translation': no_translation,
            'cards_without_pos': no_pos,
            'duplicate_cards': duplicate_cards,
        }
    
    def add_enrichment_columns(self, conn: sqlite3.Connection) -> None:
        """Add missing enrichment columns to schema."""
        c = conn.cursor()
        
        # Check which columns already exist
        c.execute('PRAGMA table_info(anki_cards)')
        existing_cols = {row[1] for row in c.fetchall()}
        
        columns_to_add = [
            ('frequency_rank', 'INTEGER', 'NULL'),
            ('syllable_count', 'INTEGER', 'NULL'),
            ('morphology_json', 'TEXT', "'{}'"),
            ('custom_level', 'TEXT', 'NULL'),
        ]
        
        for col_name, col_type, default in columns_to_add:
            if col_name not in existing_cols:
                if self.dry_run:
                    print(f"  [DRY RUN] Would add column: {col_name} {col_type} DEFAULT {default}")
                    self.report['schema_updates'].append({
                        'action': 'add_column',
                        'column': col_name,
                        'type': col_type,
                        'default': default
                    })
                else:
                    sql = f'ALTER TABLE anki_cards ADD COLUMN {col_name} {col_type} DEFAULT {default}'
                    c.execute(sql)
                    print(f"  ✓ Added column: {col_name}")
                    self.report['schema_updates'].append({
                        'action': 'add_column',
                        'column': col_name,
                        'type': col_type,
                        'status': 'completed'
                    })
        
        if not self.dry_run:
            conn.commit()
    
    def find_duplicates(self, conn: sqlite3.Connection) -> Dict[str, List[Tuple]]:
        """Find duplicate words and return grouped by word."""
        c = conn.cursor()
        
        c.execute("""
            SELECT word, GROUP_CONCAT(id) as ids
            FROM anki_cards
            WHERE word NOT NULL AND word != ''
            GROUP BY word HAVING COUNT(*) > 1
            ORDER BY word
        """)
        
        duplicates = {}
        for word, ids_str in c.fetchall():
            id_list = [int(i) for i in ids_str.split(',')]
            # Fetch full details for each duplicate
            c.execute(f"""
                SELECT id, translation, pos, deck_name, sub_deck_name, metadata_json
                FROM anki_cards
                WHERE id IN ({','.join('?' * len(id_list))})
                ORDER BY id
            """, id_list)
            duplicates[word] = c.fetchall()
        
        return duplicates
    
    def select_card_to_keep(self, cards: List[Tuple]) -> Tuple:
        """
        Select which card to keep from duplicates.
        Prioritizes cards with more complete data.
        """
        def completeness_score(card: Tuple) -> int:
            """Score card based on data completeness."""
            card_id, translation, pos, deck, subdeck, metadata = card
            score = 0
            
            # Prefer cards with translations
            if translation and translation.strip():
                score += 10
            
            # Prefer main decks over staging or letter cards
            if deck == 'Armenian (Western)':
                score += 5
            elif deck == 'Armenian Staging Deck':
                score += 2
            
            # Prefer vocab/phrase subdecks
            if subdeck in ['Vocab', 'Phrases']:
                score += 3
            
            return score
        
        # Sort by completeness, return highest-scoring card
        return max(cards, key=completeness_score)
    
    def remove_duplicates(self, conn: sqlite3.Connection) -> None:
        """Remove duplicate cards, keeping the most complete version."""
        c = conn.cursor()
        
        duplicates = self.find_duplicates(conn)
        total_removed = 0
        
        for word, cards in duplicates.items():
            if len(cards) <= 1:
                continue
            
            # Select card to keep
            card_to_keep = self.select_card_to_keep(cards)
            keep_id = card_to_keep[0]
            
            # Cards to remove
            remove_ids = [card[0] for card in cards if card[0] != keep_id]
            
            # Try to consolidate data before removing
            # (collect translations from cards being removed if current card has none)
            if not card_to_keep[1]:  # If keep card has no translation
                for remove_card in cards:
                    if remove_card[0] != keep_id and remove_card[1]:
                        # Found a translation in a card being removed
                        if self.dry_run:
                            print(f"  [DRY RUN] Would consolidate translation from card {remove_card[0]} to {keep_id}")
                            self.report['translations_fixed'].append({
                                'word': word,
                                'target_card_id': keep_id,
                                'source_card_id': remove_card[0],
                                'translation': remove_card[1]
                            })
                        else:
                            c.execute('UPDATE anki_cards SET translation = ? WHERE id = ?',
                                    (remove_card[1], keep_id))
                        break
            
            # Remove duplicates
            for remove_id in remove_ids:
                if self.dry_run:
                    print(f"  [DRY RUN] Would remove duplicate card {remove_id} (keeping {keep_id})")
                    self.report['duplicates_removed'].append({
                        'word': word,
                        'kept_card_id': keep_id,
                        'removed_card_id': remove_id,
                        'status': 'would_remove'
                    })
                else:
                    c.execute('DELETE FROM anki_cards WHERE id = ?', (remove_id,))
                    print(f"  ✓ Removed duplicate card {remove_id} (kept {keep_id})")
                    self.report['duplicates_removed'].append({
                        'word': word,
                        'kept_card_id': keep_id,
                        'removed_card_id': remove_id,
                        'status': 'removed'
                    })
                    total_removed += 1
        
        if total_removed > 0 and not self.dry_run:
            conn.commit()
            print(f"\n✓ Removed {total_removed} duplicate cards")
    
    def fix_missing_translations(self, conn: sqlite3.Connection) -> None:
        """Find and suggest fixes for cards with missing translations."""
        c = conn.cursor()
        
        c.execute("""
            SELECT id, word, deck_name, sub_deck_name
            FROM anki_cards
            WHERE translation IS NULL OR translation = ''
            ORDER BY word
        """)
        
        missing_trans = c.fetchall()
        
        if not missing_trans:
            print(f"✓ No cards with missing translations")
            return
        
        print(f"\nFound {len(missing_trans)} cards with missing translations:")
        
        # For each missing, try to find translation from same word elsewhere
        fixed = 0
        for card_id, word, deck, subdeck in missing_trans[:5]:  # Show first 5
            c.execute("""
                SELECT translation
                FROM anki_cards
                WHERE word = ? AND translation NOT NULL AND translation != ''
                LIMIT 1
            """, (word,))
            
            result = c.fetchone()
            if result:
                trans = result[0]
                if self.dry_run:
                    print(f"  [DRY RUN] Would set translation for card {card_id} ({word}): {trans}")
                    self.report['translations_fixed'].append({
                        'card_id': card_id,
                        'word': word,
                        'translation': trans,
                        'status': 'would_fix'
                    })
                else:
                    c.execute('UPDATE anki_cards SET translation = ? WHERE id = ?',
                            (trans, card_id))
                    print(f"  ✓ Fixed translation for card {card_id}: {trans}")
                    self.report['translations_fixed'].append({
                        'card_id': card_id,
                        'word': word,
                        'translation': trans,
                        'status': 'fixed'
                    })
                    fixed += 1
        
        if fixed > 0 and not self.dry_run:
            conn.commit()
    
    def run(self) -> None:
        """Execute cleanup process."""
        print("\n" + "=" * 80)
        print("ANKI DATABASE CLEANUP")
        print("=" * 80)
        
        if self.dry_run:
            print("\n[DRY RUN MODE] No changes will be made")
        
        # Connect to database
        conn = self.connect()
        
        # Get stats before
        print("\n--- BEFORE CLEANUP ---")
        stats_before = self.get_stats(conn)
        self.report['stats_before'] = stats_before
        for key, value in stats_before.items():
            print(f"{key:30} {value:>6}")
        
        # Create backup
        print()
        self.backup_database()
        
        # Upgrade schema
        print("\n--- SCHEMA UPGRADES ---")
        self.add_enrichment_columns(conn)
        
        # Remove duplicates
        print("\n--- REMOVING DUPLICATES ---")
        self.remove_duplicates(conn)
        
        # Fix missing translations
        print("\n--- FIXING MISSING TRANSLATIONS ---")
        self.fix_missing_translations(conn)
        
        # Get stats after
        print("\n--- AFTER CLEANUP ---")
        stats_after = self.get_stats(conn)
        self.report['stats_after'] = stats_after
        for key, value in stats_after.items():
            print(f"{key:30} {value:>6}")
        
        # Save report
        self.save_report()
        
        conn.close()
        print("\n" + "=" * 80)
        print("CLEANUP COMPLETE")
        print("=" * 80)


def main():
    """Main entry point."""
    dry_run = '--dry-run' in sys.argv
    no_backup = '--no-backup' in sys.argv
    
    cleanup = AnkiDatabaseCleanup(
        db_path=DB_PATH,
        dry_run=dry_run,
        create_backup=not no_backup
    )
    cleanup.run()


if __name__ == '__main__':
    main()
