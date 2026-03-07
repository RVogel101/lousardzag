"""Test espeakng with IPA phonemes."""
import espeakng  # type: ignore[reportMissingImports]
from pathlib import Path

# Test IPA pronunciation
output_dir = Path('08-data/vocab_audio_ipa_test')
output_dir.mkdir(parents=True, exist_ok=True)

# Create speaker
speaker = espeakng.Speaker()

# Test 1: հայ = /hɑj/ (Armenian)
print("Test 1: հայ (hɑj)")
try:
    # espeak-ng IPA format: [[phoneme1 phoneme2...]]
    ipa_text = "[[hɑj]]"
    output_file = str(output_dir / "test_haj.wav")
    speaker.say(ipa_text, wait4prev=True)
    getattr(speaker, "save_to_file", lambda f: None)(output_file)
    print(f"  Generated: {output_file}")
except Exception as e:
    print(f"  ERROR: {e}")

# Test 2: Try with individual phonemes
print("\nTest 2: Individual phonemes h + ɑ + j")
try:
    ipa_text = "[[h ɑ j]]"  # space-separated
    output_file = str(output_dir / "test_h_a_j.wav")
    speaker.say(ipa_text, wait4prev=True)
    getattr(speaker, "save_to_file", lambda f: None)(output_file)
    print(f"  Generated: {output_file}")
except Exception as e:
    print(f"  ERROR: {e}")

# Test 3: Try X-SAMPA format (alternative to IPA)
print("\nTest 3: X-SAMPA format")
try:
    # X-SAMPA: h A j
    ipa_text = "[[hAj]]"
    output_file = str(output_dir / "test_xsampa.wav")
    speaker.say(ipa_text, wait4prev=True)
    getattr(speaker, "save_to_file", lambda f: None)(output_file)
    print(f"  Generated: {output_file}")
except Exception as e:
    print(f"  ERROR: {e}")

print("\nTest complete. Check output files.")
