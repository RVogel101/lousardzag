#!/usr/bin/env python3
"""Test Bark neural TTS with Armenian text."""
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["SUNO_USE_SMALL_MODELS"] = "True"

# Force torch to load first before bark imports it transitively
import torch
print(f"PyTorch {torch.__version__} loaded")

# Monkey-patch torch.load for Bark compatibility with PyTorch >=2.6
_original_load = torch.load
def _patched_load(*args, **kwargs):
    kwargs.setdefault('weights_only', False)
    return _original_load(*args, **kwargs)
torch.load = _patched_load

from pathlib import Path
import numpy as np
import scipy.io.wavfile
from bark import SAMPLE_RATE, generate_audio, preload_models

OUT_DIR = Path(__file__).parent.parent / "08-data" / "audio_comparison"
OUT_DIR.mkdir(parents=True, exist_ok=True)

print("Loading Bark models (small)...")
preload_models()

# Test words
tests = [
    ("\u0574\u0561\u0580\u0564", "30_bark_mard"),     # մարդ = person
    ("\u0570\u0561\u0575", "31_bark_hay"),              # հայ = Armenian
    ("\u0565\u0580\u056f\u0578\u0582", "32_bark_yergu"),# երկou = two
]

for word, fname in tests:
    print(f"Generating: {word} -> {fname}.wav")
    audio = generate_audio(word)
    out_path = str(OUT_DIR / f"{fname}.wav")
    scipy.io.wavfile.write(out_path, SAMPLE_RATE, audio)
    fsize = os.path.getsize(out_path)
    print(f"  Written: {fsize:,} bytes")

print("\nDone!")
