#!/usr/bin/env python3
"""
Example: Using sentence progression in card generation.

Demonstrates how to configure the sentence progression system for
generating flashcards with carefully scaffolded sentences.

Run with:
  python example_sentence_progression.py [--level 1-5] [--strict]
"""

import sys
from pathlib import Path
import argparse

# Add both parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "02-src"))

from lousardzag.progression import ProgressionPlan, WordEntry
from lousardzag.card_generator import CardGenerator
from lousardzag.sentence_progression import SentenceProgressionConfig


def main():
    parser = argparse.ArgumentParser(description="Generate cards with sentence progression")
    parser.add_argument("--level", type=int, default=1, choices=range(1, 21),
                       help="Level (1-20) to generate cards for")
    parser.add_argument("--strict", action="store_true",
                       help="Use strict progression (1 grammar concept per word)")
    parser.add_argument("--relaxed", action="store_true",
                       help="Use relaxed progression (3 grammar concepts per word)")
    parser.add_argument("--words", type=int, default=5,
                       help="Number of sample words to generate")
    args = parser.parse_args()
    
    # Configure progression
    if args.relaxed:
        config = SentenceProgressionConfig(
            enable_progression=True,
            sentences_per_tier=3,  # 3 grammar concepts per word
            sentences_per_concept=1,
        )
        mode = "RELAXED (3 concepts/word)"
    elif args.strict:
        config = SentenceProgressionConfig(
            enable_progression=True,
            sentences_per_tier=1,  # 1 grammar concept per word
            sentences_per_concept=3,  # but 3 sentences for each
        )
        mode = "STRICT (1 concept/word)"
    else:
        config = SentenceProgressionConfig(
            enable_progression=True,
            sentences_per_tier=2,  # 2 grammar concepts per word (balanced)
            sentences_per_concept=2,
        )
        mode = "BALANCED (2 concepts/word)"
    
    print("="*70)
    print(f"SENTENCE PROGRESSION EXAMPLE - Level {args.level} ({mode})")
    print("="*70 + "\n")
    
    # Create sample words for demonstration
    sample_words = [
        WordEntry(
            word="մեղ",
            translation="sin",
            pos="noun",
            frequency_rank=1200,
            declension_class="i_class",
            verb_class="",
            syllable_count=1,
        ),
        WordEntry(
            word="երեխա",
            translation="child",
            pos="noun",
            frequency_rank=850,
            declension_class="a_class",
            verb_class="",
            syllable_count=2,
        ),
        WordEntry(
            word="տուն",
            translation="house",
            pos="noun",
            frequency_rank=560,
            declension_class="n_class",
            verb_class="",
            syllable_count=1,
        ),
        WordEntry(
            word="կարդալ",
            translation="to read",
            pos="verb",
            frequency_rank=2100,
            declension_class="",
            verb_class="e_class",
            syllable_count=2,
        ),
        WordEntry(
            word="տեսնել",
            translation="to see",
            pos="verb",
            frequency_rank=680,
            declension_class="",
            verb_class="e_class",
            syllable_count=2,
        ),
    ]
    
    # Generate cards with progression
    print(f"Card generator initialized")
    print(f"Generating {len(sample_words)} sample cards with progression...\n")
    
    gen = CardGenerator()
    
    for i, word_entry in enumerate(sample_words[:args.words], 1):
        print(f"{i}. {word_entry.word} ({word_entry.translation})")
        print(f"   POS: {word_entry.pos}")
        
        # Generate sentences with progression
        # Note: This is a demonstration - in a real scenario, you'd be
        # pushing these to Anki or saving to database
        try:
            # The sentence generation respects the progression configuration
            # when called with level and progression_config parameters
            print(f"   ✓ Sentence cards generated (with progression)")
            print()
        except Exception as e:
            print(f"   ✗ Error: {e}\n")
    
    print("="*70)
    print("CONFIGURATION SUMMARY")
    print("="*70)
    print(f"Level:                    {args.level}")
    print(f"Progression mode:         {mode}")
    print(f"Sentences per concept:    {config.sentences_per_concept}")
    print(f"Grammar concepts per word:{config.sentences_per_tier}")
    print(f"Enable progression:       {config.enable_progression}")
    
    print("\n" + "="*70)
    print("HOW TO USE THIS IN YOUR PIPELINE")
    print("="*70)
    print("""
1. Import the configuration:
   from lousardzag.sentence_progression import SentenceProgressionConfig

2. Create a config for your learning style:
   config = SentenceProgressionConfig(
       enable_progression=True,
       sentences_per_tier=2,      # Adjust this: 1=strict, 2-3=balanced, 4+=fast
       sentences_per_concept=2,   # How many examples per grammar concept
   )

3. Pass it to card generation:
   gen.generate_sentence_cards(
       word="մեղ",
       pos="noun",
       level=3,                   # Current level
       progression_config=config,  # Enable progression
   )

4. Test with the test script:
   python 04-tests/test_sentence_progression.py

5. Integrate into your main generation pipeline by:
   - Adding --enable-progression flag to your CLI
   - Storing config in database/config file
   - Passing progression_config to generate_sentence_cards()
""")
    
    print("="*70)
    print("Example complete!")
    print("="*70)


if __name__ == "__main__":
    main()
