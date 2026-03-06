#!/usr/bin/env python3
"""Generate Western Armenian vocabulary audio using MMS TTS with 3-pass denoising."""
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from pathlib import Path
import torch
from transformers import VitsModel, AutoTokenizer
import scipy.io.wavfile
import scipy.signal
import librosa
import numpy as np
import sys
import io
from lousardzag.audio_utils import minimal_declick

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

OUT_DIR = Path(__file__).parent.parent / "08-data" / "vocab_audio"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_ID = "facebook/mms-tts-hyw"
print(f"Loading model: {MODEL_ID}")

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = VitsModel.from_pretrained(MODEL_ID)

def generate_smooth_inference(word: str, speed_factor: float = 0.90) -> np.ndarray:
    """Generate audio 3 times and average to reduce artifacts (3-pass denoising)."""
    audios = []
    for i in range(3):
        inputs = tokenizer(word, return_tensors="pt")
        with torch.no_grad():
            output = model(**inputs).waveform
        audio = output.squeeze().cpu().numpy()
        if speed_factor != 1.0:
            audio = librosa.effects.time_stretch(audio, rate=speed_factor)
        audios.append(audio)
    
    # Pad to same length before averaging
    max_len = max(len(a) for a in audios)
    audios_padded = [np.pad(a, (0, max_len - len(a)), mode='constant') for a in audios]
    audio = np.mean(audios_padded, axis=0)
    return audio

# Vocabulary list (all 10 words)
vocab = [
    ('հայ', 'hay'),
    ('գիր', 'gir'),
    ('մեծ', 'medz'),
    ('փոքր', 'pokr'),
    ('տուն', 'dun'),
    ('մարդ', 'mard'),
    ('լաու', 'lau'),
    ('ջուր', 'jur'),
    ('երկու', 'yergu'),
    ('մեկ', 'mek'),
]

print(f"Generating {len(vocab)} vocabulary words with 3-pass denoising...")
print(f"Output directory: {OUT_DIR}")
print()

for word_arm, word_latin in vocab:
    try:
        print(f"Generating: {word_arm} ({word_latin})")
        
        # Generate with 3-pass smoothing + gentle denoising
        audio = generate_smooth_inference(word_arm, speed_factor=0.90)
        audio = minimal_declick(audio)
        
        # Convert to int16
        audio_int16 = (audio * 32767).astype("int16")
        
        # Save
        fname = f"{word_latin}_mms.wav"
        out_path = OUT_DIR / fname
        scipy.io.wavfile.write(str(out_path), rate=model.config.sampling_rate, data=audio_int16)
        
        size_kb = out_path.stat().st_size / 1024
        print(f"  ✓ {fname}: {size_kb:.1f}KB")
        
    except Exception as e:
        print(f"  ✗ ERROR: {e}")

print()
print("Done! All vocabulary audio generated.")
print(f"Files saved to: {OUT_DIR}")
