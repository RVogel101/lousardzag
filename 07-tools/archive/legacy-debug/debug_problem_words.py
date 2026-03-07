#!/usr/bin/env python3
"""Debug script to understand why syllable constraints aren't working."""

import csv
import json
import sys
sys.path.insert(0, '02-src')

from lousardzag.morphology.difficulty import count_syllables_with_context

# Load frequency list 
freq_dict = {}
with open('02-src/wa_corpus/data/wa_frequency_list.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        if len(row) >= 2:
            word = row[1].strip()
            freq_dict[word] = int(row[0])

# Load extracted vocab with metadata
with open('02-src/wa_corpus/data/wa_extracted_vocab.json', 'r', encoding='utf-8') as f:
    vocab_meta = json.load(f)

# Check problem words
problem_words = ['Ô±Õ¦Õ¡Õ¿', 'Ô¿Õ¡ÕµÕ½Ö€', 'Õ”Õ¶Õ¡Ö€', 'Ô±Õ²Õ¢Õ«Ö‚Ö€', 'Ô±Õ¶Õ£Õ¬Õ«Õ¡']

print("PROBLEM WORDS ANALYSIS:")
print("="*70)

for word in problem_words:
    print(f"\nWord: {word}")
    
    if word in vocab_meta:
        info = vocab_meta[word]
        pos = info.get('pos', '?')
        syls = info.get('syllables', '?')
        print(f"  From metadata: POS={pos}, Syllables={syls}")
    else:
        print(f"  NOT IN VOCAB METADATA")
    
    # Count syllables
    try:
        counted_syls = count_syllables_with_context(word, with_epenthesis=True)
        print(f"  Counted syllables: {counted_syls}")
    except Exception as e:
        print(f"  Error counting: {e}")
    
    # Check frequency
    if word in freq_dict:
        print(f"  Frequency rank: {freq_dict[word]}")
    else:
        print(f"  NOT IN FREQUENCY LIST")

print("\n" + "="*70)
print("VOCAB METADATA SAMPLE:")
print("="*70)

for i, (word, info) in enumerate(list(vocab_meta.items())[:10]):
    pos = info.get('pos', '?')
    syls = info.get('syllables', '?') 
    print(f"{word:20s} | POS: {pos:6s} | Syllables: {syls}")

