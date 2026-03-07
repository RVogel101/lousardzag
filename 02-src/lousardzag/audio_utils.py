"""Shared audio processing utilities for TTS and audio cleanup.

Consolidates common audio operations used across multiple TTS engines
(MMS, eSpeak, Bark, etc.) to avoid code duplication.
"""

import numpy as np
from typing import Optional
import scipy.signal as sp


def minimal_declick(audio: np.ndarray, sample_rate: int = 22050) -> np.ndarray:
    """Remove DC offset and click artifacts with gentle high-pass filter.
    
    Applies a 2nd-order high-pass Butterworth filter at 50 Hz to remove
    low-frequency noise and clicks that TTS engines often introduce.
    
    Args:
        audio: Audio signal as numpy array
        sample_rate: Sample rate in Hz (default: 22050)
    
    Returns:
        Filtered audio signal
    """
    if len(audio) < 4:  # Need minimum length for butter filter
        return audio
    
    coefs = sp.butter(2, 50, btype='high', fs=sample_rate)
    if coefs is None:
        return audio
    b, a = coefs[0], coefs[1]
    return sp.filtfilt(b, a, audio)


def normalize_audio(
    audio: np.ndarray,
    target_db: float = -20.0,
    method: str = 'rms'
) -> np.ndarray:
    """Normalize audio to target loudness.
    
    Args:
        audio: Audio signal as numpy array
        target_db: Target loudness in dB (default: -20.0)
        method: Normalization method ('rms', 'peak', or 'loudness')
    
    Returns:
        Normalized audio signal
    """
    if len(audio) == 0:
        return audio
    
    if method == 'peak':
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            # Peak normalization: scale so max value reaches target
            scale_factor = (10 ** (target_db / 20.0)) / max_val
            return audio * scale_factor
    
    elif method == 'rms':
        # RMS normalization
        rms = np.sqrt(np.mean(audio ** 2))
        if rms > 0:
            target_linear = 10 ** (target_db / 20.0)
            scale_factor = target_linear / rms
            return audio * scale_factor
    
    # Default: peak normalization
    return normalize_audio(audio, target_db, 'peak')


def pad_silence(
    audio: np.ndarray,
    duration_seconds: float = 0.5,
    sample_rate: int = 22050,
    position: str = 'both'
) -> np.ndarray:
    """Pad audio with silence.
    
    Args:
        audio: Audio signal
        duration_seconds: Duration of silence to add
        sample_rate: Sample rate in Hz
        position: 'start', 'end', or 'both'
    
    Returns:
        Padded audio signal
    """
    num_samples = int(duration_seconds * sample_rate)
    silence = np.zeros(num_samples)
    
    if position == 'start':
        return np.concatenate([silence, audio])
    elif position == 'end':
        return np.concatenate([audio, silence])
    else:  # 'both'
        return np.concatenate([silence, audio, silence])


def load_tts_model(engine: str, device: str = 'cpu'):
    """Lazy-load TTS model by engine name.
    
    Args:
        engine: TTS engine ('mms', 'espeak', 'bark', 'gcloud', 'xtts')
        device: Device to load model on ('cpu' or 'cuda')
    
    Returns:
        Loaded model object
    
    Raises:
        ValueError: If engine is not supported
    """
    if engine.lower() == 'mms':
        try:
            from transformers import VitsModel
            return VitsModel.from_pretrained('facebook/mms-tts-hyw')
        except Exception as e:
            raise RuntimeError(f"Failed to load MMS TTS model: {e}")
    
    elif engine.lower() == 'espeak':
        # eSpeak-ng is typically available as system command, not Python module
        return None  # Will use subprocess
    
    elif engine.lower() == 'bark':
        try:
            from bark import SAMPLE_RATE as BARK_SR  # type: ignore[reportMissingModuleSource]
            return None  # Use bark directly in caller
        except Exception as e:
            raise RuntimeError(f"Failed to load Bark TTS: {e}")
    
    elif engine.lower() == 'xtts':
        try:
            from TTS.models.glow_tts import Glow_TTS  # type: ignore[reportMissingModuleSource]
            return Glow_TTS.init_from_random()
        except Exception as e:
            raise RuntimeError(f"Failed to load XTTS model: {e}")
    
    else:
        raise ValueError(f"Unsupported TTS engine: {engine}")


def resample_audio(
    audio: np.ndarray,
    orig_sr: int,
    target_sr: int
) -> np.ndarray:
    """Resample audio to target sample rate.
    
    Args:
        audio: Audio signal
        orig_sr: Original sample rate
        target_sr: Target sample rate
    
    Returns:
        Resampled audio
    """
    if orig_sr == target_sr:
        return audio
    
    # Use scipy resampling (simple but reliable)
    num_samples = int(len(audio) * target_sr / orig_sr)
    return sp.resample(audio, num_samples)  # type: ignore[reportUnknownReturn]
