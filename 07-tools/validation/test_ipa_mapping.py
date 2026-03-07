#!/usr/bin/env python3
"""
Test IPA→audio generation using pyttsx3 with better phonetic mappings.
Maps IPA symbols to more accurate English phonetic approximations.
"""

import pyttsx3  # type: ignore[reportMissingImports]
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path('02-src')))

from lousardzag.core_shims.linguistics_core import ARMENIAN_PHONEMES

# Mapping of IPA symbols to more accurate English pronunciations
IPA_TO_PHONETIC = {
    'ɑ': 'ah',           # /a/ - father
    'p': 'puh',          # voiceless bilabial plosive
    'b': 'buh',          # voiced bilabial plosive
    'k': 'kuh',          # voiceless velar plosive
    'g': 'guh',          # voiced velar plosive
    't': 'tuh',          # voiceless alveolar plosive
    'd': 'duh',          # voiced alveolar plosive
    'tʃ': 'chuh',        # voiceless postalveolar affricate
    'dʒ': 'juh',         # voiced postalveolar affricate
    'f': 'fuh',          # voiceless labiodental fricative
    'v': 'vuh',          # voiced labiodental fricative
    'θ': 'thuh',         # voiceless dental fricative
    'ð': 'thuh',         # voiced dental fricative
    's': 'suh',          # voiceless alveolar fricative
    'z': 'zuh',          # voiced alveolar fricative
    'ʃ': 'shah',         # voiceless postalveolar fricative
    'ʒ': 'zhuh',         # voiced postalveolar fricative
    'm': 'muh',          # bilabial nasal
    'n': 'nuh',          # alveolar nasal
    'ŋ': 'nuh',          # velar nasal
    'h': 'huh',          # voiceless glottal fricative
    'l': 'luh',          # alveolar lateral approximant
    'ɾ': 'ruh',          # alveolar tap
    'r': 'ruh',          # alveolar approximant
    'j': 'yuh',          # palatal approximant
    'w': 'wuh',          # labial-velar approximant
    'ɛ': 'eh',           # near-front unrounded vowel
    'i': 'ee',           # close front unrounded vowel
    'u': 'oo',           # close back rounded vowel
    'o': 'oh',           # close-mid back rounded vowel
    'ə': 'uh',           # schwa
    'dz': 'dzuh',        # voiced alveolar affricate
    'ts': 'tsuh',        # voiceless alveolar affricate
    'jɛ': 'yeh',         # palatal + vowel
    'vo': 'voh',         # special case for ո
}

def ipa_to_phonetic(ipa_string: str) -> str:
    """Convert IPA string to phonetic English approximation."""
    # Remove IPA stress markers and other notation
    ipa_clean = ipa_string.replace('ˈ', '').replace('ˌ', '').replace('.', '')
    
    # Try longest matches first (diphthongs/affricates before individual phonemes)
    result = []
    i = 0
    while i < len(ipa_clean):
        matched = False
        
        # Try 3-character matches first
        if i + 3 <= len(ipa_clean):
            segment = ipa_clean[i:i+3]
            if segment in IPA_TO_PHONETIC:
                result.append(IPA_TO_PHONETIC[segment])
                i += 3
                matched = True
        
        # Try 2-character matches
        if not matched and i + 2 <= len(ipa_clean):
            segment = ipa_clean[i:i+2]
            if segment in IPA_TO_PHONETIC:
                result.append(IPA_TO_PHONETIC[segment])
                i += 2
                matched = True
        
        # Try 1-character matches
        if not matched and i + 1 <= len(ipa_clean):
            segment = ipa_clean[i]
            if segment in IPA_TO_PHONETIC:
                result.append(IPA_TO_PHONETIC[segment])
                i += 1
                matched = True
        
        # Skip unknown characters
        if not matched:
            i += 1
    
    return ' '.join(result)

def generate_test_audio():
    """Test audio generation with IPA mapping."""
    engine = pyttsx3.init()
    engine.setProperty('rate', 130)
    engine.setProperty('volume', 0.9)
    
    output_dir = Path('08-data/letter_audio_ipa_test')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Test with a few Armenian letters
    test_letters = {
        'ա': ('ɑ.ip', 'ayp'),     # Correct IPA for ayp
        'բ': ('pɛn', 'ben'),       # Correct IPA for ben (p sound)
        'գ': ('kim', 'kim'),       # Correct IPA for kim (k sound)
        'դ': ('tɑ', 'ta'),         # Correct IPA for ta (t sound)
        'ե': ('jɛ', 'yech'),       # Correct IPA for yech
    }
    
    print("Testing IPA → Phonetic Mapping\n" + "="*50)
    
    for letter, (ipa, name) in test_letters.items():
        # Get phonetic approximation
        phonetic = ipa_to_phonetic(ipa)
        
        print(f"\nLetter: {letter}")
        print(f"  Name: {name}")
        print(f"  IPA: {ipa}")
        print(f"  Phonetic: {phonetic}")
        
        # Generate audio
        filepath = output_dir / f"test_{letter}_{name}.wav"
        engine.save_to_file(phonetic, str(filepath))
        engine.runAndWait()
        
        if filepath.exists():
            size_kb = filepath.stat().st_size / 1024
            print(f"  [OK] Generated: {size_kb:.1f} KB")
        else:
            print(f"  [FAIL] Generation failed")
    
    print("\n" + "="*50)
    print(f"Test audio in: {output_dir}")

if __name__ == '__main__':
    generate_test_audio()
