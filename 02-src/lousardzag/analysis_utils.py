"""
Shared analysis framework for Lousardzag vocabulary and corpus tools.

Provides:
- Base analysis class for standardized analysis workflow
- Common metrics and statistics calculation
- Report generation and export (JSON, CSV)
- Frequency analysis helpers
- Corpus query utilities

Consolidates duplicate logic across:
- analyze_vocab.py
- analyze_morphology.py
- analyze_stemming.py
- analyze_unmatched.py
- analyze_case_forms.py
- check_vocab_phrases.py
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from collections import defaultdict
from datetime import datetime


class Analysis:
    """Base class for vocabulary and corpus analysis.
    
    Provides standardized workflow:
    1. Connect to database
    2. Query and process data
    3. Calculate metrics/statistics
    4. Generate report
    5. Export results
    
    Subclasses override analyze() method for specific analysis type.
    """
    
    def __init__(
        self,
        db_path: Path = Path('08-data/armenian_cards.db'),
        output_dir: Path = Path('08-data'),
        dry_run: bool = False,
        limit: Optional[int] = None
    ):
        """Initialize analysis.
        
        Args:
            db_path: Path to SQLite database
            output_dir: Directory for output reports
            dry_run: If True, don't save results
            limit: Process only first N items (for testing)
        """
        self.db_path = Path(db_path)
        self.output_dir = Path(output_dir)
        self.dry_run = dry_run
        self.limit = limit
        
        self.report = {
            'timestamp': datetime.now().isoformat(),
            'analysis_type': self.__class__.__name__,
            'dry_run': dry_run,
            'limit': limit,
            'results': {},
            'statistics': {},
            'errors': []
        }
    
    def connect(self) -> sqlite3.Connection:
        """Connect to database with Row factory."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def add_error(self, message: str) -> None:
        """Log an error to the report."""
        self.report['errors'].append(message)
        print(f"  [ERROR] {message}")
    
    def analyze(self) -> Dict[str, Any]:
        """Main analysis method. Override in subclass.
        
        Returns:
            Dictionary of analysis results
        """
        raise NotImplementedError("Subclasses must implement analyze()")
    
    def run(self) -> None:
        """Execute full analysis workflow."""
        print(f"\n{'='*80}")
        print(f"{self.__class__.__name__.upper()}")
        print(f"{'='*80}")
        
        if self.dry_run:
            print("[DRY RUN MODE] Results will not be saved\n")
        
        if self.limit:
            print(f"[LIMITED MODE] Processing first {self.limit} items\n")
        
        try:
            # Run analysis
            results = self.analyze()
            self.report['results'] = results
            
            # Save report
            self.save_report()
            
        except Exception as e:
            self.add_error(f"Analysis failed: {e}")
            raise
    
    def save_report(self) -> None:
        """Save analysis report as JSON."""
        if self.dry_run:
            return
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = self.output_dir / f"{self.__class__.__name__.lower()}_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Report saved: {report_path}")


# ============================================================================
# Frequency Analysis Helpers
# ============================================================================

def calculate_frequencies(items: List[str]) -> Dict[str, int]:
    """Calculate frequency distribution of items.
    
    Args:
        items: List of items (words, tags, etc.)
        
    Returns:
        Dictionary mapping item to frequency
    """
    frequencies = defaultdict(int)
    for item in items:
        frequencies[item] += 1
    return dict(frequencies)


def get_top_n(frequencies: Dict[str, int], n: int = 10) -> List[tuple]:
    """Get top N most frequent items.
    
    Args:
        frequencies: Dictionary of item -> frequency
        n: Number of items to return
        
    Returns:
        List of (item, frequency) tuples, sorted by frequency descending
    """
    return sorted(frequencies.items(), key=lambda x: x[1], reverse=True)[:n]


def get_distribution_stats(frequencies: Dict[str, int]) -> Dict[str, Any]:
    """Calculate distribution statistics.
    
    Args:
        frequencies: Dictionary of item -> frequency
        
    Returns:
        Dictionary with min, max, mean, median, std_dev
    """
    if not frequencies:
        return {}
    
    values = list(frequencies.values())
    
    return {
        'total_items': len(frequencies),
        'total_count': sum(values),
        'min_frequency': min(values),
        'max_frequency': max(values),
        'mean_frequency': sum(values) / len(values),
        'unique_count': len(frequencies),
    }


# ============================================================================
# Database Query Helpers
# ============================================================================

def get_all_words(
    conn: sqlite3.Connection,
    limit: Optional[int] = None
) -> List[str]:
    """Get all words from Anki database.
    
    Args:
        conn: Database connection
        limit: Max number of words to fetch
        
    Returns:
        List of words
    """
    c = conn.cursor()
    
    query = 'SELECT word FROM anki_cards WHERE word NOT NULL AND word != ""'
    if limit:
        query += f' LIMIT {limit}'
    
    c.execute(query)
    return [row['word'] for row in c.fetchall()]


def get_all_translations(
    conn: sqlite3.Connection,
    limit: Optional[int] = None
) -> List[str]:
    """Get all translations from Anki database.
    
    Args:
        conn: Database connection
        limit: Max number to fetch
        
    Returns:
        List of translations
    """
    c = conn.cursor()
    
    query = 'SELECT translation FROM anki_cards WHERE translation NOT NULL AND translation != ""'
    if limit:
        query += f' LIMIT {limit}'
    
    c.execute(query)
    return [row['translation'] for row in c.fetchall()]


def get_pos_distribution(conn: sqlite3.Connection) -> Dict[str, int]:
    """Get distribution of parts of speech.
    
    Args:
        conn: Database connection
        
    Returns:
        Dictionary mapping POS -> count
    """
    c = conn.cursor()
    c.execute('SELECT pos, COUNT(*) as count FROM anki_cards WHERE pos NOT NULL GROUP BY pos')
    return {row['pos']: row['count'] for row in c.fetchall()}


def get_missing_data_summary(conn: sqlite3.Connection) -> Dict[str, int]:
    """Get summary of missing/incomplete fields.
    
    Args:
        conn: Database connection
        
    Returns:
        Dictionary with counts of missing fields
    """
    c = conn.cursor()
    
    fields = {
        'missing_translation': 'translation IS NULL OR translation = ""',
        'missing_pos': 'pos IS NULL OR pos = ""',
        'missing_syllables': 'syllable_count IS NULL',
        'missing_morphology': 'morphology_json IS NULL OR morphology_json = ""',
    }
    
    result = {}
    for field_name, where_clause in fields.items():
        c.execute(f'SELECT COUNT(*) FROM anki_cards WHERE {where_clause}')
        count = c.fetchone()[0]
        result[field_name] = count
    
    return result


def get_card_count(conn: sqlite3.Connection) -> int:
    """Get total card count.
    
    Args:
        conn: Database connection
        
    Returns:
        Total number of cards
    """
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM anki_cards')
    return c.fetchone()[0]


def get_unique_word_count(conn: sqlite3.Connection) -> int:
    """Get count of unique words.
    
    Args:
        conn: Database connection
        
    Returns:
        Count of unique words
    """
    c = conn.cursor()
    c.execute('SELECT COUNT(DISTINCT word) FROM anki_cards WHERE word NOT NULL AND word != ""')
    return c.fetchone()[0]


# ============================================================================
# Text Analysis Helpers
# ============================================================================

def get_word_length_distribution(words: List[str]) -> Dict[int, int]:
    """Get distribution of word lengths.
    
    Args:
        words: List of words (Armenian graphemes)
        
    Returns:
        Dictionary mapping length -> count
    """
    distribution = defaultdict(int)
    for word in words:
        distribution[len(word)] += 1
    return dict(distribution)


def filter_words_by_length(
    words: List[str],
    min_length: Optional[int] = None,
    max_length: Optional[int] = None
) -> List[str]:
    """Filter words by length criteria.
    
    Args:
        words: List of words
        min_length: Minimum word length (inclusive)
        max_length: Maximum word length (inclusive)
        
    Returns:
        Filtered list of words
    """
    result = words
    
    if min_length is not None:
        result = [w for w in result if len(w) >= min_length]
    
    if max_length is not None:
        result = [w for w in result if len(w) <= max_length]
    
    return result


def find_duplicates(items: List[str]) -> Dict[str, int]:
    """Find items that appear multiple times.
    
    Args:
        items: List of items
        
    Returns:
        Dictionary mapping item to count (only items with count > 1)
    """
    frequencies = calculate_frequencies(items)
    return {item: count for item, count in frequencies.items() if count > 1}


def compare_lists(
    list1: List[str],
    list2: List[str]
) -> Dict[str, Any]:
    """Compare two lists and return differences.
    
    Args:
        list1: First list
        list2: Second list
        
    Returns:
        Dictionary with 'only_in_1', 'only_in_2', 'in_both'
    """
    set1 = set(list1)
    set2 = set(list2)
    
    return {
        'only_in_1': list(set1 - set2),
        'only_in_2': list(set2 - set1),
        'in_both': list(set1 & set2),
        'count_only_in_1': len(set1 - set2),
        'count_only_in_2': len(set2 - set1),
        'count_in_both': len(set1 & set2),
    }
