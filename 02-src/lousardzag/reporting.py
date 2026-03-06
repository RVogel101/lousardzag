"""
Shared reporting module for Lousardzag tools.

Consolidates report generation patterns from:
- cleanup_anki_database.py
- enrich_anki_database.py
- analysis_utils.py and analysis scripts

Provides:
- StandardReport: Base report class with common structure
- Report builders for different analysis types
- Export to JSON, CSV, console
- Report formatting and statistics
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict


class StandardReport:
    """Base report class with common structure across tools.
    
    All Lousardzag reports follow this schema:
    {
        "metadata": {
            "timestamp": ISO datetime,
            "tool": Tool name,
            "version": Version number,
            "duration_seconds": float
        },
        "summary": {
            "total_items": int,
            "items_processed": int,
            "errors": int,
            "warnings": int
        },
        "results": {...},  # Tool-specific results
        "statistics": {...},  # Tool-specific statistics
        "errors": [...]  # List of error messages
    }
    """
    
    def __init__(
        self,
        tool_name: str,
        version: str = "1.0"
    ):
        """Initialize standard report.
        
        Args:
            tool_name: Name of the tool (e.g., "cleanup_anki_database")
            version: Version string
        """
        self.tool_name = tool_name
        self.version = version
        self.start_time = datetime.now()
        
        self.report = {
            'metadata': {
                'timestamp': self.start_time.isoformat(),
                'tool': tool_name,
                'version': version,
                'duration_seconds': None,
            },
            'summary': {
                'total_items': 0,
                'items_processed': 0,
                'errors': 0,
                'warnings': 0,
            },
            'results': {},
            'statistics': {},
            'errors': [],
            'warnings': [],
        }
    
    def set_summary(self, **kwargs) -> None:
        """Update summary section.
        
        Args:
            total_items: Total items in dataset
            items_processed: Items successfully processed
            errors: Error count
            warnings: Warning count
        """
        for key, value in kwargs.items():
            if key in self.report['summary']:
                self.report['summary'][key] = value
    
    def add_error(self, message: str) -> None:
        """Add error message to report.
        
        Args:
            message: Error message
        """
        self.report['errors'].append(message)
        self.report['summary']['errors'] += 1
    
    def add_warning(self, message: str) -> None:
        """Add warning message to report.
        
        Args:
            message: Warning message
        """
        self.report['warnings'].append(message)
        self.report['summary']['warnings'] += 1
    
    def add_result(self, key: str, value: Any) -> None:
        """Add result to results section.
        
        Args:
            key: Result key
            value: Result value (dict, list, or scalar)
        """
        self.report['results'][key] = value
    
    def add_statistics(self, **kwargs) -> None:
        """Add statistics to statistics section.
        
        Args:
            **kwargs: Key-value pairs of statistics
        """
        self.report['statistics'].update(kwargs)
    
    def finalize(self) -> None:
        """Finalize report (set duration, etc.)."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        self.report['metadata']['duration_seconds'] = duration
    
    def to_dict(self) -> Dict[str, Any]:
        """Get report as dictionary.
        
        Returns:
            Report dictionary
        """
        return self.report
    
    def to_json_string(self, pretty: bool = True) -> str:
        """Convert report to JSON string.
        
        Args:
            pretty: If True, format with indentation
            
        Returns:
            JSON string
        """
        indent = 2 if pretty else None
        return json.dumps(self.report, indent=indent, ensure_ascii=False)
    
    def save_json(self, path: Path) -> None:
        """Save report as JSON file.
        
        Args:
            path: Path to save file
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.to_json_string(pretty=True))


class DatabaseOperationReport(StandardReport):
    """Report for database operations (cleanup, enrichment, etc.).
    
    Extends StandardReport with database-specific fields.
    """
    
    def __init__(
        self,
        tool_name: str,
        operation_type: str,
        db_path: Optional[str] = None
    ):
        """Initialize database operation report.
        
        Args:
            tool_name: Name of the tool
            operation_type: Type of operation (cleanup, enrichment, query, etc.)
            db_path: Path to database (optional)
        """
        super().__init__(tool_name)
        
        self.report['metadata']['operation_type'] = operation_type
        if db_path:
            self.report['metadata']['database_path'] = str(db_path)
        
        # Add database-specific result categories
        self.report['results']['database_changes'] = {}
        self.report['results']['detailed_changes'] = {}
        self.report['statistics']['pre_state'] = {}
        self.report['statistics']['post_state'] = {}
    
    def add_change(
        self,
        category: str,
        count: int,
        description: str = ""
    ) -> None:
        """Add a database change entry.
        
        Args:
            category: Change category (e.g., "duplicates_removed")
            count: Number of items changed
            description: Optional description
        """
        self.report['results']['database_changes'][category] = {
            'count': count,
            'description': description,
        }
    
    def add_pre_post_state(
        self,
        total_cards: int = None,
        total_enriched: int = None,
        missing_fields: Dict[str, int] = None
    ) -> None:
        """Add pre/post database state.
        
        Args:
            total_cards: Total card count
            total_enriched: Cards with enrichment data
            missing_fields: Dict of field -> count of missing values
        """
        if total_cards is not None:
            self.report['statistics']['post_state']['total_cards'] = total_cards
        
        if total_enriched is not None:
            self.report['statistics']['post_state']['total_enriched'] = total_enriched
        
        if missing_fields is not None:
            self.report['statistics']['post_state']['missing_fields'] = missing_fields


class AnalysisReport(StandardReport):
    """Report for corpus/vocabulary analysis.
    
    Extends StandardReport with analysis-specific fields.
    """
    
    def __init__(
        self,
        tool_name: str,
        analysis_type: str
    ):
        """Initialize analysis report.
        
        Args:
            tool_name: Name of the analysis tool
            analysis_type: Type of analysis (frequency, morphology, stemming, etc.)
        """
        super().__init__(tool_name)
        
        self.report['metadata']['analysis_type'] = analysis_type
        self.report['results']['analysis_data'] = {}
        self.report['results']['top_items'] = {}
    
    def add_distribution(
        self,
        key: str,
        distribution: Dict[str, int],
        top_n: int = 10
    ) -> None:
        """Add frequency/distribution analysis.
        
        Args:
            key: Distribution key (e.g., "pos_distribution", "word_length")
            distribution: Dict of item -> count
            top_n: Number of top items to include
        """
        sorted_items = sorted(distribution.items(), key=lambda x: x[1], reverse=True)
        
        self.report['results']['analysis_data'][key] = {
            'total_unique': len(distribution),
            'total_count': sum(distribution.values()),
            'distribution': distribution,
        }
        
        self.report['results']['top_items'][key] = dict(sorted_items[:top_n])


class ReportFormatter:
    """Utilities for formatting reports for console output."""
    
    @staticmethod
    def print_summary(report: StandardReport) -> None:
        """Print a formatted summary of the report.
        
        Args:
            report: StandardReport instance
        """
        r = report.report
        
        print(f"\n{'='*80}")
        print(f"REPORT: {r['metadata']['tool']}")
        print(f"{'='*80}\n")
        
        print(f"Timestamp: {r['metadata']['timestamp']}")
        print(f"Duration: {r['metadata'].get('duration_seconds', 'N/A')}s")
        print()
        
        print("SUMMARY:")
        for key, value in r['summary'].items():
            print(f"  {key}: {value}")
        print()
        
        if r['statistics']:
            print("STATISTICS:")
            for key, value in r['statistics'].items():
                if isinstance(value, dict):
                    print(f"  {key}:")
                    for k, v in value.items():
                        print(f"    {k}: {v}")
                else:
                    print(f"  {key}: {value}")
            print()
        
        if r['errors']:
            print(f"ERRORS ({len(r['errors'])} total):")
            for error in r['errors'][:5]:  # Show first 5
                print(f"  - {error}")
            if len(r['errors']) > 5:
                print(f"  ... and {len(r['errors']) - 5} more")
            print()
        
        if r['warnings']:
            print(f"WARNINGS ({len(r['warnings'])} total):")
            for warning in r['warnings'][:5]:  # Show first 5
                print(f"  - {warning}")
            if len(r['warnings']) > 5:
                print(f"  ... and {len(r['warnings']) - 5} more")
            print()
    
    @staticmethod
    def print_database_changes(report: DatabaseOperationReport) -> None:
        """Print formatted database changes.
        
        Args:
            report: DatabaseOperationReport instance
        """
        changes = report.report['results'].get('database_changes', {})
        
        if changes:
            print("\nDATABASE CHANGES:")
            for category, info in changes.items():
                count = info['count']
                desc = info.get('description', '')
                print(f"  {category}: {count}")
                if desc:
                    print(f"    ({desc})")
    
    @staticmethod
    def print_distribution(
        report: AnalysisReport,
        key: str = None
    ) -> None:
        """Print formatted distribution analysis.
        
        Args:
            report: AnalysisReport instance
            key: Specific distribution key to print (None = all)
        """
        analysis_data = report.report['results'].get('analysis_data', {})
        
        if not analysis_data:
            return
        
        keys = [key] if key else analysis_data.keys()
        
        for k in keys:
            if k not in analysis_data:
                continue
            
            data = analysis_data[k]
            print(f"\n{k.upper().replace('_', ' ')}:")
            print(f"  Unique items: {data['total_unique']}")
            print(f"  Total count: {data['total_count']}")
            
            top_items = report.report['results'].get('top_items', {}).get(k, {})
            if top_items:
                print(f"  Top items:")
                for item, count in list(top_items.items())[:10]:
                    print(f"    {item}: {count}")
