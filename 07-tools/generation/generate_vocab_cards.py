#!/usr/bin/env python3
"""
Generate vocabulary-only flashcards with pure word ordering logic.
No sentence generation - focus on vocabulary sorting and progression only.
"""

import csv
import json
import argparse
import sys
from pathlib import Path
from collections import defaultdict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "02-src"))

from lousardzag.card_generator import CardGenerator


def load_vocab_data():
    """Load vocabulary data from the frequency list CSV file."""
    vocab_file = '02-src/wa_corpus/data/wa_frequency_list.csv'
    vocab = {}
    with open(vocab_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)  # Skip header row
        for row in reader:
            if len(row) >= 2:
                try:
                    rank = int(row[0])
                    word = row[1].strip()
                    vocab[word] = {'rank': rank}
                except (ValueError, IndexError):
                    continue
    return vocab


def load_vocab_metadata():
    """Load metadata from extracted vocab JSON (syllables, POS, etc)."""
    try:
        with open('02-src/wa_corpus/data/wa_extracted_vocab.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def group_vocabulary_by_level(vocab_data, vocab_metadata, max_words=None):
    """
    Group vocabulary by level based on frequency ranking.
    Simpler approach: just organize by frequency rank.
    """
    # Sort by frequency rank
    sorted_vocab = sorted(vocab_data.items(), key=lambda x: x[1]['rank'])
    
    if max_words:
        sorted_vocab = sorted_vocab[:max_words]
    
    return sorted_vocab


def get_definition(word, vocab_metadata, generator):
    """
    Get definition for a word using CardGenerator's translation lookup.
    Falls back to basic definition if not available.
    """
    try:
        # Try to get from generator's translation system
        definition = generator.get_definition(word)
        if definition:
            return definition
    except:
        pass
    
    # Fallback to metadata if available
    if word in vocab_metadata:
        meta = vocab_metadata[word]
        if 'definition' in meta:
            return meta['definition']
        if 'english' in meta:
            return meta['english']
    
    return f"[Definition needed for {word}]"


def generate_html_table(vocab_list, vocab_metadata, definitions_dict):
    """Generate HTML table with vocabulary cards."""
    html = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vocabulary Cards</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: white;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #333; margin-bottom: 20px; }
        .stats {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th {
            background-color: #2196F3;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border: 1px solid #1976D2;
        }
        td {
            padding: 12px;
            border: 1px solid #ddd;
            border-bottom: 1px solid #ddd;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        tr:hover {
            background-color: #eef2f9;
        }
        .rank {
            width: 60px;
            text-align: center;
            font-weight: 600;
            color: #2196F3;
        }
        .word {
            width: 200px;
            font-size: 18px;
            font-weight: 500;
            direction: rtl;
            text-align: right;
        }
        .definition {
            flex: 1;
            font-size: 14px;
            color: #555;
        }
        .metadata {
            width: 100px;
            font-size: 12px;
            color: #999;
        }
        .note {
            margin-top: 20px;
            padding: 15px;
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            border-radius: 4px;
            font-size: 13px;
            color: #856404;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Vocabulary Cards</h1>
        <div class="stats">
"""
    
    html += f"<p>Total cards: {len(vocab_list)}</p>\n"
    html += """
        </div>
        <table>
            <thead>
                <tr>
                    <th class="rank">Rank</th>
                    <th class="word">Word (Armenian)</th>
                    <th class="definition">Definition (English)</th>
                </tr>
            </thead>
            <tbody>
"""
    
    # Add vocabulary rows
    for word, data in vocab_list:
        rank = data['rank']
        definition = definitions_dict.get(word, f"[Definition needed]")
        
        # Escape HTML characters
        word_escaped = word.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
        definition_escaped = definition.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
        
        html += f"""                <tr>
                    <td class="rank">{rank}</td>
                    <td class="word">{word_escaped}</td>
                    <td class="definition">{definition_escaped}</td>
                </tr>
"""
    
    html += """            </tbody>
        </table>
        <div class="note">
            <strong>Vocabulary-only cards:</strong> Focus is on word ordering and filtering.
            Sentence generation is a separate pipeline step.
        </div>
    </div>
</body>
</html>
"""
    
    return html


def main():
    parser = argparse.ArgumentParser(
        description='Generate vocabulary-only flashcards with pure word ordering logic.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python 07-tools/generate_vocab_cards.py --max-words 50
  python 07-tools/generate_vocab_cards.py --max-words 100 --output custom_cards.html
"""
    )
    
    parser.add_argument('--max-words', type=int, default=50,
                        help='Maximum number of vocabulary items to generate (default: 50)')
    parser.add_argument('--output', type=str, default='08-data/vocabulary_preview.html',
                        help='Output HTML file path (default: 08-data/vocabulary_preview.html)')
    parser.add_argument('--csv-output', type=str, default=None,
                        help='Optional: Also export as CSV to specified file')
    
    args = parser.parse_args()
    
    print("Loading vocabulary data...")
    vocab_data = load_vocab_data()
    vocab_metadata = load_vocab_metadata()
    
    print(f"Loaded {len(vocab_data)} words from frequency list")
    print(f"Loaded metadata for {len(vocab_metadata)} words")
    
    print("\nGrouping vocabulary by level...")
    vocab_list = group_vocabulary_by_level(vocab_data, vocab_metadata, args.max_words)
    
    print(f"Selected {len(vocab_list)} vocabulary items for generation")
    
    # Get definitions using CardGenerator
    print("\nRetrieving definitions...")
    generator = CardGenerator()
    definitions_dict = {}
    
    for word, data in vocab_list:
        try:
            definition = getattr(generator, "get_definition", lambda w: None)(word)
            if definition:
                definitions_dict[word] = definition
            else:
                # Try metadata
                if word in vocab_metadata and 'definition' in vocab_metadata[word]:
                    definitions_dict[word] = vocab_metadata[word]['definition']
                else:
                    definitions_dict[word] = "[Definition needed]"
        except Exception as e:
            definitions_dict[word] = f"[Error: {str(e)[:50]}]"
    
    # Generate HTML output
    print(f"\nGenerating HTML output to {args.output}...")
    html_content = generate_html_table(vocab_list, vocab_metadata, definitions_dict)
    
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ Generated {args.output}")
    
    # Optional CSV export
    if args.csv_output:
        print(f"\nExporting to CSV: {args.csv_output}...")
        Path(args.csv_output).parent.mkdir(parents=True, exist_ok=True)
        
        with open(args.csv_output, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Rank', 'Word', 'Definition', 'Syllables', 'POS'])
            
            for word, data in vocab_list:
                rank = data['rank']
                definition = definitions_dict.get(word, '')
                
                # Get metadata
                syllables = ''
                pos = ''
                if word in vocab_metadata:
                    meta = vocab_metadata[word]
                    syllables = meta.get('syllable_count', '')
                    pos = meta.get('pos', '')
                
                writer.writerow([rank, word, definition, syllables, pos])
        
        print(f"✓ Exported to {args.csv_output}")
    
    print("\n" + "="*70)
    print(f"SUMMARY: Generated {len(vocab_list)} vocabulary-only cards")
    print(f"Output: {args.output}")
    if args.csv_output:
        print(f"CSV: {args.csv_output}")
    print("="*70)


if __name__ == '__main__':
    main()
