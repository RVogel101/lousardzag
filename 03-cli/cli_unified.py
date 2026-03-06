#!/usr/bin/env python3
"""
Unified CLI dispatcher for Lousardzag tools.

Consolidates 40+ script entry points into a single command-line interface.
Provides a consistent, discoverable way to access all tools.

Usage:
    python 03-cli/cli_unified.py <command> [args...]
    python 03-cli/cli_unified.py --help
    python 03-cli/cli_unified.py audio --help

Commands are organized by function:
  - Audio:      generate, convert, test audio processing
  - Analysis:   analyze vocabulary, morphology, quality metrics  
  - Database:   cleanup, enrich, manage Anki data
  - Generation: create cards, content, datasets
  - Validation: check data integrity, consistency, coverage
"""

import sys
import argparse
from pathlib import Path
from typing import Optional, List

# Add source directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / '02-src'))

# ============================================================================
# Command Groups & Registry
# ============================================================================

class CommandGroup:
    """Organizes related commands by function."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.commands = {}
    
    def register(self, name: str, description: str, module_path: str, entry_function: str = 'main'):
        """Register a command in this group."""
        self.commands[name] = {
            'description': description,
            'module_path': module_path,
            'entry': entry_function
        }


# Initialize command groups
audio_group = CommandGroup('audio', 'Audio generation and processing')
analysis_group = CommandGroup('analysis', 'Analysis tools (vocabulary, morphology, quality)')
database_group = CommandGroup('database', 'Database operations (cleanup, enrichment)')
generation_group = CommandGroup('generation', 'Card and content generation')
validation_group = CommandGroup('validation', 'Data validation and integrity checks')

# Register audio commands
audio_group.register(
    'generate-letter-mms',
    'Generate Western Armenian letter audio using MMS TTS',
    '07-tools/generate_letter_audio_mms.py'
)
audio_group.register(
    'generate-letter-espeak',
    'Generate Western Armenian letter audio using eSpeak-NG',
    '07-tools/generate_letter_audio_ipa_espeak.py'
)
audio_group.register(
    'generate-vocab',
    'Generate Armenian vocabulary audio using MMS TTS',
    '07-tools/generate_vocab_audio_mms.py'
)
audio_group.register(
    'test-mms',
    'Test MMS TTS audio generation and quality',
    '07-tools/test_mms_tts.py'
)
audio_group.register(
    'test-bark',
    'Test Bark TTS for Armenian',
    '07-tools/test_bark_armenian.py'
)
audio_group.register(
    'test-espeak',
    'Test eSpeak-NG for IPA pronunciation',
    '07-tools/test_espeakng_ipa.py'
)
audio_group.register(
    'test-gcloud',
    'Test Google Cloud TTS for Armenian',
    '07-tools/test_gcloud_tts.py'
)
audio_group.register(
    'test-xtts',
    'Test Coqui XTTS for Armenian',
    '07-tools/test_xtts_armenian.py'
)

# Register analysis commands
analysis_group.register(
    'analyze-vocab',
    'Analyze vocabulary frequency, distribution, and quality',
    '07-tools/check_vocab_phrases.py'
)
analysis_group.register(
    'analyze-morphology',
    'Analyze case forms, suffixes, and morphological patterns',
    '07-tools/analyze_case_forms_strict.py'
)
analysis_group.register(
    'analyze-unmatched',
    'Analyze unmatched words and missing data',
    '07-tools/analyze_unmatched.py'
)
analysis_group.register(
    'analyze-stemming',
    'Analyze stemming impact on vocabulary',
    '07-tools/analyze_stemming_impact.py'
)
analysis_group.register(
    'analyze-ipa',
    'Analyze IPA mapping coverage and quality',
    '07-tools/test_ipa_mapping.py'
)

# Register database commands
database_group.register(
    'cleanup',
    'Clean up Anki database: remove duplicates, fix missing data',
    '07-tools/cleanup_anki_database.py'
)
database_group.register(
    'enrich',
    'Enrich Anki database with computed fields (syllables, difficulty, phonetics)',
    '07-tools/enrich_anki_database.py'
)

# Register generation commands
generation_group.register(
    'generate-cards',
    'Generate Anki cards from vocabulary',
    '07-tools/generate_vocab_cards.py'
)
generation_group.register(
    'example-progression',
    'Example: Demonstrate sentence progression system',
    '07-tools/example_sentence_progression.py'
)

# Validate command (validation_group)
validation_group.register(
    'validate-letters',
    'Validate letter card data and audio',
    '07-tools/test_letter_cards_offline.py'
)

# All groups
ALL_GROUPS = {
    'audio': audio_group,
    'analysis': analysis_group,
    'database': database_group,
    'generation': generation_group,
    'validation': validation_group,
}

# ============================================================================
# CLI Implementation
# ============================================================================

def create_parser() -> argparse.ArgumentParser:
    """Create main argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog='lousardzag',
        description='Lousardzag: Western Armenian Learning Platform - Unified CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python 03-cli/cli_unified.py audio generate-letter-mms
  python 03-cli/cli_unified.py database cleanup --dry-run
  python 03-cli/cli_unified.py analysis analyze-vocab
  python 03-cli/cli_unified.py audio --help    # Show audio subcommands
        """
    )
    
    # Global options
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--version', action='version', version='lousardzag 1.0')
    
    # Subparsers for command groups
    subparsers = parser.add_subparsers(dest='group', help='Command group')
    subparsers.required = True
    
    for group_name, group in ALL_GROUPS.items():
        group_parser = subparsers.add_parser(
            group_name,
            help=group.description,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # Subparser for individual commands in this group
        cmd_subparsers = group_parser.add_subparsers(dest='command', help='Command')
        cmd_subparsers.required = True
        
        for cmd_name, cmd_info in group.commands.items():
            cmd_subparsers.add_parser(
                cmd_name,
                help=cmd_info['description']
            )
    
    return parser


def dispatch_command(group_name: str, command_name: str, args: List[str]) -> None:
    """Dispatch to the appropriate tool script."""
    
    if group_name not in ALL_GROUPS:
        print(f"Error: Unknown command group '{group_name}'", file=sys.stderr)
        sys.exit(1)
    
    group = ALL_GROUPS[group_name]
    
    if command_name not in group.commands:
        print(f"Error: Unknown command '{command_name}' in group '{group_name}'", file=sys.stderr)
        sys.exit(1)
    
    cmd_info = group.commands[command_name]
    module_path = cmd_info['module_path']
    entry_fn = cmd_info['entry']
    
    # Dynamic import of tool module
    try:
        # Build absolute path
        tool_path = Path(__file__).parent.parent / module_path
        
        if not tool_path.exists():
            print(f"Error: Tool script not found: {tool_path}", file=sys.stderr)
            sys.exit(1)
        
        # Import and run
        spec = __import__('importlib.util').util.spec_from_file_location(
            'tool_module',
            str(tool_path)
        )
        module = __import__('importlib.util').util.module_from_spec(spec)
        
        # Update sys.argv so the tool sees correct arguments
        sys.argv = [str(tool_path)] + args
        
        # Execute module
        spec.loader.exec_module(module)
        
        # Call entry function if it exists
        if hasattr(module, entry_fn):
            getattr(module, entry_fn)()
        
    except Exception as e:
        print(f"Error running command '{group_name} {command_name}': {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = create_parser()
    
    # Parse only known arguments (let unknowns pass through to tool)
    args, unknown_args = parser.parse_known_args()
    
    # Dispatch to tool, passing through unknown arguments
    dispatch_command(args.group, args.command, unknown_args)


if __name__ == '__main__':
    main()
