"""
Vocabulary and phrase validation tool.

Consolidates check_vocab_phrases.py and check_vocab_phrases2.py.

Validates vocabulary entries for:
- Sentence-like translations (multiple words)
- Suspicious phrase patterns
- Missing or invalid data
- Consistency issues
"""

import sys
sys.path.insert(0, '02-src')

from pathlib import Path
from typing import List, Dict, Any, Optional
import sqlite3
import json

from lousardzag.database import CardDatabase
from lousardzag.analysis_utils import Analysis
from lousardzag.reporting import AnalysisReport


class PhraseValidator(Analysis):
    """Validates vocabulary entries for phrase-like or suspicious translations.
    
    Checks for:
    - Multi-word translations (potential sentences)
    - Phrase patterns like "phone", "kettle", "am here"
    - Inconsistent entry formats
    """
    
    # Phrase patterns that suggest sentence-like content
    SUSPICIOUS_PHRASES = {
        'phone': 'Technology/context word',
        'kettle': 'Kitchen object, context dependent',
        'am here': 'Sentence fragment',
        "isn't it": 'Sentence structure',
        'be able to': 'Verb phrase',
        'have to': 'Verb phrase',
        'come to': 'Verb phrase',
        'make': 'Generic verb',
        'put': 'Generic verb',
    }
    
    def __init__(
        self,
        db_path: Path = Path('08-data/armenian_cards.db'),
        min_words_threshold: int = 4,
        check_patterns: bool = True,
        output_dir: Path = Path('08-data'),
        dry_run: bool = False
    ):
        """Initialize phrase validator.
        
        Args:
            db_path: Path to SQLite database
            min_words_threshold: Min word count to flag as sentence-like
            check_patterns: If True, check for suspicious phrase patterns
            output_dir: Directory for output reports
            dry_run: If True, don't save results
        """
        super().__init__(db_path, output_dir, dry_run)
        
        self.min_words_threshold = min_words_threshold
        self.check_patterns = check_patterns
        self.report = AnalysisReport('validate_vocab_phrases', 'phrase_validation')
        
        self.phrases_found = []
        self.pattern_matches = defaultdict(list)
    
    def analyze(self) -> Dict[str, Any]:
        """Run phrase validation analysis.
        
        Returns:
            Dictionary with validation results
        """
        conn = self.connect()
        c = conn.cursor()
        
        # Get all cards with translations
        c.execute('''
            SELECT id, word, translation, pos 
            FROM anki_cards 
            WHERE translation NOT NULL AND translation != ""
        ''')
        
        cards = c.fetchall()
        total_cards = len(cards)
        
        print(f"\nAnalyzing {total_cards} cards for phrase-like translations...")
        
        for i, card in enumerate(cards):
            if self.limit and i >= self.limit:
                break
            
            card_id = card[0]
            word = card[1]
            translation = card[2]
            pos = card[3] or ""
            
            # Check word count
            word_count = len(translation.split())
            
            is_phrase = False
            reasons = []
            
            # Check if translation looks like sentence
            if word_count > self.min_words_threshold:
                is_phrase = True
                reasons.append(f"multi-word ({word_count} words)")
            
            # Check for suspicious phrase patterns
            if self.check_patterns:
                for phrase, category in self.SUSPICIOUS_PHRASES.items():
                    if phrase.lower() in translation.lower():
                        is_phrase = True
                        reasons.append(f"pattern match: {phrase} ({category})")
                        self.pattern_matches[phrase].append({
                            'word': word,
                            'translation': translation[:100],
                            'pos': pos
                        })
            
            if is_phrase:
                self.phrases_found.append({
                    'id': card_id,
                    'word': word,
                    'translation': translation[:150],
                    'pos': pos,
                    'reasons': reasons,
                    'word_count': word_count
                })
        
        conn.close()
        
        # Prepare results
        results = {
            'total_cards_checked': total_cards,
            'cards_with_phrases': len(self.phrases_found),
            'phrase_percentage': round(100 * len(self.phrases_found) / total_cards, 2),
            'phrases': self.phrases_found[:50],  # Top 50
            'phrase_patterns_found': dict(self.pattern_matches),
        }
        
        # Update report
        self.report.add_result('validation_summary', {
            'total_cards': total_cards,
            'phrase_like_entries': len(self.phrases_found),
            'unique_patterns': len(self.pattern_matches),
        })
        
        self.report.add_distribution(
            'phrase_patterns',
            {phrase: len(entries) for phrase, entries in self.pattern_matches.items()},
            top_n=10
        )
        
        return results
    
    def run(self) -> None:
        """Execute validation and display results."""
        print(f"\n{'='*80}")
        print("VOCABULARY PHRASE VALIDATOR")
        print(f"{'='*80}")
        
        results = self.analyze()
        
        print(f"\nValidation Results:")
        print(f"  Total cards: {results['total_cards_checked']}")
        print(f"  Phrase-like translations: {results['cards_with_phrases']}")
        print(f"  Percentage: {results['phrase_percentage']}%")
        
        if results['phrase_patterns_found']:
            print(f"\nSuspicious Phrases:")
            for pattern, entries in sorted(
                results['phrase_patterns_found'].items(),
                key=lambda x: len(x[1]),
                reverse=True
            )[:10]:
                print(f"  '{pattern}': {len(entries)} entries")
                for entry in entries[:3]:
                    print(f"    - {entry['word']:15} → {entry['translation']}")
                if len(entries) > 3:
                    print(f"    ... and {len(entries) - 3} more")
        
        if results['phrases']:
            print(f"\nSample Phrase-Like Entries (first 10):")
            for phrase in results['phrases'][:10]:
                print(f"  {phrase['word']:15} → {phrase['translation']}")
                for reason in phrase['reasons']:
                    print(f"    • {reason}")
        
        self.report.finalize()
        self.save_report()
        
        print(f"\n✓ Validation complete")
        if not self.dry_run:
            print(f"✓ Report saved")


if __name__ == '__main__':
    import argparse
    from collections import defaultdict
    
    parser = argparse.ArgumentParser(
        description='Validate vocabulary translations for phrase-like content'
    )
    parser.add_argument(
        '--db',
        type=Path,
        default='08-data/armenian_cards.db',
        help='Path to database (default: 08-data/armenian_cards.db)'
    )
    parser.add_argument(
        '--min-words',
        type=int,
        default=4,
        help='Minimum word count to flag as phrase (default: 4)'
    )
    parser.add_argument(
        '--skip-patterns',
        action='store_true',
        help='Skip phrase pattern matching (only check word count)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default='08-data',
        help='Output directory for report (default: 08-data)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Don't save results, only display"
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Process only first N cards (for testing)'
    )
    
    args = parser.parse_args()
    
    validator = PhraseValidator(
        db_path=args.db,
        min_words_threshold=args.min_words,
        check_patterns=not args.skip_patterns,
        output_dir=args.output,
        dry_run=args.dry_run
    )
    validator.limit = args.limit
    validator.run()
