"""
Shared CLI utilities for Lousardzag tool scripts.

Provides:
- Common argument parsers for database and analysis tools
- Decorators for dry-run handling and error management
- Helper functions for safe argument extraction
- Standard option builders (--dry-run, --limit, --backup, etc.)

Reduces boilerplate across 40+ tool scripts by centralizing CLI patterns.
"""

import argparse
import sys
from functools import wraps
from pathlib import Path
from typing import Optional, Callable, Any, Dict


# ============================================================================
# Argument Parsers (Reusable Builders)
# ============================================================================

def create_database_operation_parser(
    prog: Optional[str] = None,
    description: Optional[str] = None,
    add_limit: bool = False,
    add_backup: bool = True
) -> argparse.ArgumentParser:
    """Create a standard parser for database operation tools.
    
    Args:
        prog: Program name for help text
        description: Tool description
        add_limit: If True, add --limit option (for processing N cards)
        add_backup: If True, add --backup option (default: create backup)
        
    Returns:
        Configured ArgumentParser
        
    Example:
        parser = create_database_operation_parser(
            prog='cleanup',
            description='Clean up Anki database'
        )
        args = parser.parse_args()
        
        cleanup = AnkiDatabaseCleanup(
            db_path=DB_PATH,
            dry_run=args.dry_run,
            create_backup=args.backup
        )
    """
    parser = argparse.ArgumentParser(
        prog=prog,
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Common database operation options
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Don't make changes, just report what would be done"
    )
    
    if add_backup:
        parser.add_argument(
            '--no-backup',
            action='store_true',
            help="Don't create backup before modifying (default: create backup)"
        )
    
    if add_limit:
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Process only first N items (useful for testing)'
        )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    return parser


def create_analysis_parser(
    prog: Optional[str] = None,
    description: Optional[str] = None
) -> argparse.ArgumentParser:
    """Create a standard parser for analysis tools.
    
    Args:
        prog: Program name for help text
        description: Tool description
        
    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog=prog,
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=None,
        help='Output file for results (JSON or CSV)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit analysis to first N items'
    )
    
    return parser


def create_audio_parser(
    prog: Optional[str] = None,
    description: Optional[str] = None
) -> argparse.ArgumentParser:
    """Create a standard parser for audio generation tools.
    
    Args:
        prog: Program name for help text
        description: Tool description
        
    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog=prog,
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        type=Path,
        default=None,
        help='Output directory for audio files'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Test audio generation without saving files"
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Process only first N items'
    )
    
    return parser


# ============================================================================
# Decorators (For Common Behaviors)
# ============================================================================

def handle_dry_run(func: Callable) -> Callable:
    """Decorator that handles dry-run mode before/after function execution.
    
    Prints dry-run warning before execution, completion message after.
    
    Example:
        @handle_dry_run
        def run_cleanup(args):
            return cleanup.run()
    """
    @wraps(func)
    def wrapper(*args, dry_run: bool = False, **kwargs):
        if dry_run:
            print("\n[DRY RUN MODE] No changes will be made\n")
        
        result = func(*args, **kwargs)
        
        if dry_run:
            print("\n[DRY RUN COMPLETE] Preview only - no changes made\n")
        
        return result
    
    return wrapper


def safe_parse_args(
    expected_args: Dict[str, Any],
    allow_extras: bool = True
) -> Dict[str, Any]:
    """Safely parse command-line arguments with fallback to defaults.
    
    Args:
        expected_args: Dict of arg_name -> (type, default_value)
        allow_extras: If False, exit on unexpected arguments
        
    Returns:
        Dictionary of parsed arguments
        
    Example:
        args = safe_parse_args({
            'db_path': (Path, Path('08-data/armenian_cards.db')),
            'dry_run': (bool, False),
            'limit': (int, None),
        })
    """
    result = {}
    i = 1
    
    while i < len(sys.argv):
        arg = sys.argv[i]
        
        if arg.startswith('--'):
            # Long option
            arg_name = arg[2:].replace('-', '_')
            
            if arg_name not in expected_args:
                if not allow_extras:
                    print(f"Error: Unknown argument '{arg}'", file=sys.stderr)
                    sys.exit(1)
                i += 1
                continue
            
            arg_type, _ = expected_args[arg_name]
            
            if arg_type is bool:
                result[arg_name] = True
                i += 1
            else:
                # Expects a value
                if i + 1 >= len(sys.argv):
                    print(f"Error: {arg} requires a value", file=sys.stderr)
                    sys.exit(1)
                
                try:
                    value = arg_type(sys.argv[i + 1])
                    result[arg_name] = value
                    i += 2
                except (ValueError, TypeError) as e:
                    print(f"Error: {arg} value '{sys.argv[i + 1]}' is invalid: {e}", file=sys.stderr)
                    sys.exit(1)
        else:
            i += 1
    
    # Fill in defaults for missing arguments
    for arg_name, (_, default_value) in expected_args.items():
        if arg_name not in result:
            result[arg_name] = default_value
    
    return result


# ============================================================================
# Helper Functions
# ============================================================================

def get_bool_arg(arg_name: str, default: bool = False) -> bool:
    """Extract boolean argument from sys.argv.
    
    Args:
        arg_name: Argument name (without -- prefix)
        default: Default value if not present
        
    Returns:
        True if argument is present, False otherwise
    """
    flag = f"--{arg_name}"
    return flag in sys.argv


def get_str_arg(arg_name: str, default: Optional[str] = None) -> str | None:
    """Extract string argument value from sys.argv.
    
    Args:
        arg_name: Argument name (without -- prefix)
        default: Default value if not present or parsing fails
        
    Returns:
        Argument value or default
    """
    flag = f"--{arg_name}"
    try:
        idx = sys.argv.index(flag)
        if idx + 1 < len(sys.argv):
            return sys.argv[idx + 1]
    except (ValueError, IndexError):
        pass
    
    return default or None


def get_int_arg(arg_name: str, default: Optional[int] = None) -> int | None:
    """Extract integer argument value from sys.argv.
    
    Args:
        arg_name: Argument name (without -- prefix)
        default: Default value if not present or parsing fails
        
    Returns:
        Argument value as int or default
    """
    flag = f"--{arg_name}"
    try:
        idx = sys.argv.index(flag)
        if idx + 1 < len(sys.argv):
            return int(sys.argv[idx + 1])
    except (ValueError, IndexError):
        pass
    
    return default or None  # type: ignore[reportUnknownReturn]


def print_section(title: str, width: int = 80) -> None:
    """Print a formatted section header.
    
    Example:
        print_section("DATABASE CLEANUP", 80)
        # Output:
        # ================================================================
        # DATABASE CLEANUP
        # ================================================================
    """
    line = "=" * width
    print(f"\n{line}")
    print(title.center(width))
    print(line)


def print_stat(label: str, value: Any, width: int = 40) -> None:
    """Print a statistic line with label and value aligned.
    
    Example:
        print_stat('Total cards', 8395)
        # Output: Total cards                           8395
    """
    print(f"{label:<width} {value:>6}")


# ============================================================================
# Validation Helpers
# ============================================================================

def validate_database_path(db_path: Path) -> Path:
    """Validate that database file exists and is accessible.
    
    Args:
        db_path: Path to database file
        
    Returns:
        Path object if valid
        
    Raises:
        FileNotFoundError: If database doesn't exist
        PermissionError: If database isn't readable
    """
    db_path = Path(db_path)
    
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    
    if not db_path.is_file():
        raise ValueError(f"Not a file: {db_path}")
    
    if not db_path.stat().st_mode & 0o400:
        raise PermissionError(f"Cannot read database: {db_path}")
    
    return db_path


def validate_output_dir(output_dir: Path) -> Path:
    """Validate or create output directory.
    
    Args:
        output_dir: Path to output directory
        
    Returns:
        Path object (created if necessary)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir
