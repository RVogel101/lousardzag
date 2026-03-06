"""Base class for Anki database operations.

Provides common functionality for database operations like cleanup and enrichment:
- Connection management
- Statistics gathering
- Backup and rotation
- Report generation and saving

This module consolidates code duplication between cleanup_anki_database.py
and enrich_anki_database.py, reducing maintenance burden.
"""

import sqlite3
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any


class DatabaseOperation:
    """Base class for Anki database operations (cleanup, enrichment, etc).
    
    Subclasses should override report_path property and enrich report dict.
    """
    
    def __init__(
        self,
        db_path: Path,
        dry_run: bool = False,
        create_backup: bool = True
    ):
        """Initialize database operation.
        
        Args:
            db_path: Path to SQLite database file
            dry_run: If True, report changes without applying them
            create_backup: If True, create backup before modifications
        """
        self.db_path = Path(db_path)
        self.dry_run = dry_run
        self.create_backup = create_backup
        
        # Initialize base report structure (subclasses can extend)
        self.report = {
            'timestamp': datetime.now().isoformat(),
            'dry_run': dry_run,
            'errors': [],
            'stats_before': {},
            'stats_after': {}
        }
    
    @property
    def report_path(self) -> Path:
        """Subclasses must override this to define report save location."""
        raise NotImplementedError("Subclasses must define report_path property")
    
    @property
    def backup_path(self) -> Path:
        """Path for database backups (subclass-specific)."""
        return self.db_path.parent / f"{self.db_path.name}.backup"
    
    def connect(self) -> sqlite3.Connection:
        """Connect to Anki database.
        
        Returns:
            sqlite3.Connection object or Row factory variant as needed
        """
        conn = sqlite3.connect(str(self.db_path))
        return conn
    
    def get_stats(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Get current database statistics.
        
        Base implementation provides card count. Subclasses can override
        to add operation-specific statistics.
        
        Args:
            conn: sqlite3 database connection
            
        Returns:
            Dictionary of statistics
        """
        c = conn.cursor()
        
        c.execute('SELECT COUNT(*) FROM anki_cards')
        total_cards = c.fetchone()[0]
        
        c.execute('SELECT COUNT(DISTINCT word) FROM anki_cards WHERE word NOT NULL AND word != ""')
        unique_words = c.fetchone()[0]
        
        return {
            'total_cards': total_cards,
            'unique_words': unique_words,
        }
    
    def backup_database(self) -> None:
        """Create backup of database with rotation of old backups.
        
        Keeps up to 10 versions of backups, rotating old ones to .1, .2, etc.
        Skipped if dry_run is True.
        """
        if not self.create_backup or self.dry_run:
            return
        
        # Rotate old backups
        if self.backup_path.exists():
            for i in range(9, 0, -1):
                old_backup = self.backup_path.parent / f"{self.backup_path.name}.{i}"
                new_backup = self.backup_path.parent / f"{self.backup_path.name}.{i+1}"
                if old_backup.exists():
                    old_backup.rename(new_backup)
        
        # Create new backup
        shutil.copy(self.db_path, self.backup_path)
        print(f"✓ Created backup: {self.backup_path}")
    
    def save_report(self) -> None:
        """Save operation report as JSON.
        
        Report path is defined by subclass property report_path.
        Skipped if dry_run is True (no changes made, so don't save report).
        """
        if self.dry_run:
            return
        
        report_path = self.report_path
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Saved report: {report_path}")
    
    def add_error(self, message: str) -> None:
        """Log an error to the report.
        
        Args:
            message: Error message to log
        """
        self.report['errors'].append(message)
        print(f"  ✗ Error: {message}")
