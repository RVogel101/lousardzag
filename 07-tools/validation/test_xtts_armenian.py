#!/usr/bin/env python3
"""Test Coqui XTTS v2 with Armenian text."""
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import torch
print(f"PyTorch {torch.__version__}")

# Monkey-patch torch.load for model weight loading compatibility
_original_load = torch.load
def _patched_load(*args, **kwargs):
    kwargs.setdefault('weights_only', False)
    return _original_load(*args, **kwargs)
torch.load = _patched_load

from TTS.api import TTS
from pathlib import Path

OUT_DIR = Path(__file__).parent.parent / "08-data" / "audio_comparison"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Check XTTS v2 supported languages
print("Loading XTTS v2...")
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=True)

# Print supported languages
if hasattr(tts, 'languages'):
    print(f"Supported languages: {tts.languages}")

# XTTS v2 needs a reference audio - use one of our espeak-ng samples
# as a voice reference (it will clone the voice characteristics)
ref_audio = OUT_DIR / "08_balanced_mard.wav"
if not ref_audio.exists():
    # Try any existing wav in the directory
    wavs = list(OUT_DIR.glob("*.wav"))
    if wavs:
        ref_audio = wavs[0]
        print(f"Using reference audio: {ref_audio.name}")
    else:
        print("ERROR: No reference audio found!")
        exit(1)

# Test words - Armenian is not officially supported by XTTS v2,
# but it can sometimes handle unsupported scripts via multilingual transfer
tests = [
    ("\u0574\u0561\u0580\u0564", "40_xtts_mard"),      # մարդ = person
    ("\u0570\u0561\u0575", "41_xtts_hay"),               # հay = Armenian
    ("\u0565\u0580\u056f\u0578\u0582", "42_xtts_yergu"), # երdelays = two
]

# Try with different language hints since Armenian isn't natively supported
for lang_hint in ["en"]:
    print(f"\nTrying language hint: {lang_hint}")
    for word, fname in tests:
        out_path = str(OUT_DIR / f"{fname}.wav")
        print(f"  Generating: {word} -> {fname}.wav")
        try:
            tts.tts_to_file(
                text=word,
                speaker_wav=str(ref_audio),
                language=lang_hint,
                file_path=out_path,
            )
            fsize = os.path.getsize(out_path)
            print(f"    Written: {fsize:,} bytes")
        except Exception as e:
            print(f"    FAILED: {e}")

print("\nDone!")
