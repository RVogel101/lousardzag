#!/usr/bin/env python3
"""Generate Armenian vocab audio using Meta MMS TTS (Western Armenian hyw) with speed control."""
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

OUT_DIR = Path(__file__).parent.parent / "08-data" / "audio_comparison"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_ID = "facebook/mms-tts-hyw"
print(f"Loading model: {MODEL_ID}")

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = VitsModel.from_pretrained(MODEL_ID)

def generate_and_slow(word: str, speed_factor: float = 0.75) -> np.ndarray:
    """Generate audio and apply pitch-preserving time stretching."""
    inputs = tokenizer(word, return_tensors="pt")
    with torch.no_grad():
        output = model(**inputs).waveform
    audio = output.squeeze().cpu().numpy()
    
    # Apply time stretching (slower = longer duration, preserved pitch)
    if speed_factor != 1.0:
        audio = librosa.effects.time_stretch(audio, rate=speed_factor)
    
    return audio

def generate_smooth_inference(word: str, speed_factor: float = 0.75) -> np.ndarray:
    """Generate audio multiple times and blend to reduce artifacts."""
    # Generate 3 times and average - reduces noise artifacts
    audios = []
    for _ in range(3):
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

def generate_ultra_smooth_inference(word: str, speed_factor: float = 0.75) -> np.ndarray:
    """Generate 5 times and average for maximum denoising."""
    audios = []
    for _ in range(5):
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

def apply_clarity_enhancer(audio: np.ndarray, sr: int = 22050) -> np.ndarray:
    """Apply gentle post-processing: high-pass filter + soft compression + light EQ."""
    # High-pass filter to remove rumble (80 Hz cutoff)
    sos = scipy.signal.butter(4, 80, 'hp', fs=sr, output='sos')
    audio = scipy.signal.sosfilt(sos, audio)
    
    # Soft compression (make dynamic range smoother)
    # Simple soft-knee compressor
    threshold = 0.3
    ratio = 4.0
    mask = np.abs(audio) > threshold
    audio[mask] = threshold + (audio[mask] - threshold) / ratio
    
    # Normalize to prevent clipping
    audio = audio / (np.max(np.abs(audio)) + 1e-10)
    
    return audio

def apply_smooth_enhancement(audio: np.ndarray, sr: int = 22050) -> np.ndarray:
    """Apply gentle smoothing: compression + reverb-like effect."""
    # Soft compression
    threshold = 0.25
    ratio = 3.0
    mask = np.abs(audio) > threshold
    audio[mask] = threshold + (audio[mask] - threshold) / ratio
    
    # Simple reverb simulation (very gentle blend of delayed copies)
    delay_samples = int(sr * 0.05)  # 50ms delay
    delayed = np.pad(audio, (delay_samples, 0), mode='constant')[:-delay_samples]
    audio = audio * 0.85 + delayed * 0.15
    
    # Smooth via light low-pass (reduce harshness)
    # Use max 7000 Hz cutoff for 16kHz sample rate (Nyquist = 8000 Hz)
    cutoff = min(7000, sr / 2 - 100)
    sos = scipy.signal.butter(2, cutoff, 'lp', fs=sr, output='sos')
    audio = scipy.signal.sosfilt(sos, audio)
    
    # Normalize
    audio = audio / (np.max(np.abs(audio)) + 1e-10)
    
    return audio

def apply_warm_enhancement(audio: np.ndarray, sr: int = 22050) -> np.ndarray:
    """Add warmth: boost low-mids (200-600Hz), gentle compression."""
    # Soft compression for consistency
    threshold = 0.28
    ratio = 2.5
    mask = np.abs(audio) > threshold
    audio[mask] = threshold + (audio[mask] - threshold) / ratio
    
    # Parametric EQ: boost low-mid presence (300-500 Hz)
    # Using peaking filter centered at 400Hz with Q=2, gain=+6dB
    from scipy import signal
    freq = 400  # Hz
    Q = 2.0
    gain_db = 6.0
    w0 = 2 * np.pi * freq / sr
    alpha = np.sin(w0) / (2 * Q)
    A = 10 ** (gain_db / 40)
    
    b = [1 + alpha*A, -2*np.cos(w0), 1 + alpha/A]
    b = [b[0]*A, b[1], b[2]/A]
    a = [1 + alpha/A, -2*np.cos(w0), 1 + alpha*A]
    
    audio = scipy.signal.lfilter(b, a, audio)
    audio = audio / (np.max(np.abs(audio)) + 1e-10)
    
    return audio

def apply_resonant_enhancement(audio: np.ndarray, sr: int = 22050) -> np.ndarray:
    """Enhance natural resonances via parametric EQ at 2-3kHz and 4-5kHz."""
    # Light compression
    threshold = 0.26
    ratio = 3.0
    mask = np.abs(audio) > threshold
    audio[mask] = threshold + (audio[mask] - threshold) / ratio
    
    # EQ peak at 2.8kHz (presence boost)
    freq1 = 2800
    Q1 = 1.5
    gain_db1 = 4.0
    w0_1 = 2 * np.pi * freq1 / sr
    alpha_1 = np.sin(w0_1) / (2 * Q1)
    A_1 = 10 ** (gain_db1 / 40)
    
    b1 = [1 + alpha_1*A_1, -2*np.cos(w0_1), 1 + alpha_1/A_1]
    b1 = [b1[0]*A_1, b1[1], b1[2]/A_1]
    a1 = [1 + alpha_1/A_1, -2*np.cos(w0_1), 1 + alpha_1*A_1]
    
    audio = scipy.signal.lfilter(b1, a1, audio)
    
    # Slight low-pass to remove harshness above 6kHz
    cutoff = min(6500, sr / 2 - 100)
    sos = scipy.signal.butter(2, cutoff, 'lp', fs=sr, output='sos')
    audio = scipy.signal.sosfilt(sos, audio)
    
    audio = audio / (np.max(np.abs(audio)) + 1e-10)
    
    return audio

def apply_saturation_enhancement(audio: np.ndarray, sr: int = 22050) -> np.ndarray:
    """Add subtle harmonic distortion (analog warmth) without harshness."""
    # Very light soft-knee compression
    threshold = 0.30
    ratio = 2.2
    mask = np.abs(audio) > threshold
    audio[mask] = threshold + (audio[mask] - threshold) / ratio
    
    # Apply gentle soft saturation (tanh creates natural harmonic distortion)
    # Use a conservative drive amount
    drive = 1.2  # Controls saturation amount
    audio = np.tanh(audio * drive) / drive
    
    # Light low-pass to smooth harsh artifacts
    cutoff = min(7000, sr / 2 - 100)
    sos = scipy.signal.butter(2, cutoff, 'lp', fs=sr, output='sos')
    audio = scipy.signal.sosfilt(sos, audio)
    
    audio = audio / (np.max(np.abs(audio)) + 1e-10)
    
    return audio

def apply_pitch_shift_warmth(audio: np.ndarray, sr: int = 22050) -> np.ndarray:
    """Apply light downward pitch shift (50 cents = 3% slower) for maturity/warmth."""
    # Compress for consistency
    threshold = 0.27
    ratio = 2.8
    mask = np.abs(audio) > threshold
    audio[mask] = threshold + (audio[mask] - threshold) / ratio
    
    # Downward pitch shift using time-stretch
    # 50 cents down ≈ 0.97x pitch ratio (very subtle)
    shift_factor = 1.0  # 1.0 = no shift; <1.0 = lower pitch (slower speed stretch)
    # Actually, to lower pitch with librosa, we need to time-stretch less (ratio > 1)
    # Pitch shift down by ~50 cents ≈ time stretch by 1.03x
    audio = librosa.effects.time_stretch(audio, rate=0.97)
    
    # Light low-pass
    cutoff = min(7000, sr / 2 - 100)
    sos = scipy.signal.butter(2, cutoff, 'lp', fs=sr, output='sos')
    audio = scipy.signal.sosfilt(sos, audio)
    
    audio = audio / (np.max(np.abs(audio)) + 1e-10)
    
    return audio

# Test words
tests = [
    ("մարդ", "mard"),
    ("հայ", "hay"),
    ("երկու", "yergu"),
    ("տուն", "dun"),
    ("մեծ", "medz"),
]

print("Generating with different noise scales (less harsh/staticky)...")
for word, label in tests:
    try:
        # Smooth inference variant (100-104) - noise_scale 0.4
        audio_smooth = generate_smooth_inference(word, speed_factor=0.90)
        audio_smooth = minimal_declick(audio_smooth)
        audio_smooth_int16 = (audio_smooth * 32767).astype("int16")
        fname_smooth = f"100_mms_smooth_noise_{label}.wav"
        out_path_smooth = OUT_DIR / fname_smooth
        scipy.io.wavfile.write(str(out_path_smooth), rate=model.config.sampling_rate, data=audio_smooth_int16)
        print(f"  {fname_smooth}: {out_path_smooth.stat().st_size:,} bytes")
        
        # Ultra-smooth inference variant (105-109) - noise_scale 0.25
        audio_ultra = generate_ultra_smooth_inference(word, speed_factor=0.90)
        audio_ultra = minimal_declick(audio_ultra)
        audio_ultra_int16 = (audio_ultra * 32767).astype("int16")
        fname_ultra = f"105_mms_ultra_smooth_{label}.wav"
        out_path_ultra = OUT_DIR / fname_ultra
        scipy.io.wavfile.write(str(out_path_ultra), rate=model.config.sampling_rate, data=audio_ultra_int16)
        print(f"  {fname_ultra}: {out_path_ultra.stat().st_size:,} bytes")
        
    except Exception as e:
        print(f"  ERROR for {label}: {e}")

print("Done!")

