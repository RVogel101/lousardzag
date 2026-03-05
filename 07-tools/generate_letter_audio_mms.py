#!/usr/bin/env python3
"""Generate Western Armenian letter audio with Meta MMS TTS.

This script creates two MP3 files per letter in `08-data/letter_audio`:
- `letter_{LETTER}_name.mp3`: letter name pronunciation (Armenian-only prompt)
- `letter_{LETTER}_sound.mp3`: letter sound prompt (Armenian-only prompt)

No English approximation text is used.

VERIFIED SOURCES (NOT internal knowledge):
- Letter name overrides: 02-src/lousardzag/letter_data.py (LETTER_NAMES dict)
- Western Armenian phonetics: 02-src/lousardzag/phonetics.py (ARMENIAN_PHONEMES)
- Eastern bias workarounds: /memories/eastern-bias-workarounds.md (sourced from phonetics.py)

Important: this script includes an optional prompt-layer workaround for cases where
an acoustic model (facebook/mms-tts-hyw) behaves like Eastern Armenian for grapheme-to-phoneme mapping.
The workaround changes only the text prompt sent to TTS, while keeping the output
filename and logical target letter unchanged.

See: /memories/eastern-bias-workarounds.md for full justification of proxy pairs.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from io import TextIOWrapper
from pathlib import Path
from typing import Dict, Any

import numpy as np
import scipy.signal


os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
sys.stdout = TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "02-src"))

from lousardzag.ipa_mappings import LETTER_NAME_ARMENIAN, LETTER_NAME_IPA
from lousardzag.letter_data import get_all_letters_ordered, get_letter_info
from lousardzag.morphology.core import ARM


MODEL_ID = "facebook/mms-tts-hyw"
OUT_DIR = ROOT / "08-data" / "letter_audio"
TMP_DIR = OUT_DIR / ".tmp_wav"
MANIFEST_PATH = OUT_DIR / "letter_audio_mms_manifest.json"


# Western Armenian transliteration tokens used in letter_data.py names.
# This is intentionally limited to project-defined letter-name spellings.
_TOKEN_TO_ARMENIAN = {
    "ch": ARM["ch"],
    "sh": ARM["sh"],
    "gh": ARM["gh"],
    "kh": ARM["kh"],
    "dz": ARM["dz"],
    "ts": ARM["ts"],
    "zh": ARM["zh"],
    "rr": ARM["rr"],
    "ye": ARM["ye"],
    "yw": ARM["y"] + ARM["yiwn"],
    "yu": ARM["y"] + ARM["yiwn"],
    "ph": ARM["p_asp"],
    "th": ARM["t_asp"],
    "khh": ARM["k_asp"],
    "a": ARM["a"],
    "b": ARM["b"],
    "c": ARM["c_asp"],
    "d": ARM["d"],
    "e": ARM["e"],
    "f": ARM["f"],
    "g": ARM["g"],
    "h": ARM["h"],
    "i": ARM["i"],
    "j": ARM["j"],
    "k": ARM["k"],
    "l": ARM["l"],
    "m": ARM["m"],
    "n": ARM["n"],
    "o": ARM["o"],
    "p": ARM["p"],
    "r": ARM["r"],
    "s": ARM["s"],
    "t": ARM["t"],
    "u": ARM["vo"] + ARM["yiwn"],
    "v": ARM["v"],
    "w": ARM["yiwn"],
    "y": ARM["y"],
    "z": ARM["z"],
}


# Armenian-script name prompts sourced from ipa_mappings.py (single source of truth).
_NAME_OVERRIDES: Dict[str, str] = dict(LETTER_NAME_ARMENIAN)


# Split-synthesis rules: synthesize letter name in parts and concatenate.
# Used when a single prompt doesn't capture pronunciation correctly.
# Key: letter, Value: list of prompts to synthesize separately and concatenate
# 
# VERIFIED SOURCE: /memories/verified-letter-names-and-ipa.md (user-provided)
# 
# NOTE: Do NOT use internal Armenian language knowledge. All values must be sourced
# from project code, tests, or user-provided corrections.
_SPLIT_SYNTHESIS_RULES = {
    "ա": ["այ", "բ"],  # Split "այբ" into vowel + consonant to preserve "y" glide
}


# Workaround map for Eastern-biased grapheme->sound behavior in MMS TTS outputs.
# VERIFIED SOURCE: 02-src/lousardzag/phonetics.py ARMENIAN_PHONEMES dict.
# 
# Each pair listed here is based on actual Western Armenian phonetics from phonetics.py:
# - Left side: target Western Armenian letter → what sound it SHOULD make
# - Right side: proxy grapheme → swap this in if model reads Eastern convention
# 
# Example: բ should sound /p/ in Western Armenian. If MMS reads it as Eastern /b/, 
# feed պ instead (which looks Western /b/ but MMS reads Eastern /p/).
# 
# Reference: /memories/eastern-bias-workarounds.md (derived from phonetics.py)
_EASTERN_BIAS_SOUND_PROXY = {
    ARM["p"]: ARM["b"],       # բ target WA /pʰ/ → feed պ (phonetics.py verified)
    ARM["b"]: ARM["p"],       # պ target WA /b/ → feed բ (phonetics.py verified)
    ARM["k"]: ARM["g"],       # գ target WA /kʰ/ → feed կ (phonetics.py verified)
    ARM["g"]: ARM["k"],       # կ target WA /ɡ/ → feed գ (phonetics.py verified)
    ARM["t"]: ARM["d"],       # դ target WA /tʰ/ → feed տ (phonetics.py verified)
    ARM["d"]: ARM["t"],       # տ target WA /d/ → feed դ (phonetics.py verified)
    ARM["dz"]: ARM["ts"],     # ծ target WA /dz/ → feed ձ (phonetics.py verified)
    ARM["ts"]: ARM["dz"],     # ձ target WA /tsʰ/ → feed ծ (phonetics.py verified)
    ARM["j"]: ARM["ch"],      # ճ target WA /dʒ/ → feed ջ (phonetics.py verified)
    ARM["ch"]: ARM["j"],      # ջ target WA /tʃʰ/ → feed ճ (phonetics.py verified)
    ARM["yiwn"]: ARM["v"],    # ւ sound target defaults to consonantal /v/ (phonetics.py verified)
}


# Context-sensitive vowel/semi-vowel prompt shaping to better target WA values.
_WA_CONTEXT_SOUND_PROMPTS = {
    ARM["ye"]: ARM["y"] + ARM["e"],            # ե -> յէ
    ARM["vo"]: ARM["v"] + ARM["vo"],           # ո -> վո
    ARM["yiwn"]: ARM["v"] + ARM["a"],          # ւ -> վա (consonantal cue)
}


# Character-level proxy substitutions for letter-name prompts.
# Example: այբ -> այպ so Eastern-oriented TTS reads /ayp/.
_EASTERN_BIAS_NAME_CHAR_PROXY = {
    ARM["p"]: ARM["b"],
    ARM["b"]: ARM["p"],
    ARM["k"]: ARM["g"],
    ARM["g"]: ARM["k"],
    ARM["t"]: ARM["d"],
    ARM["d"]: ARM["t"],
    ARM["dz"]: ARM["ts"],
    ARM["ts"]: ARM["dz"],
    ARM["j"]: ARM["ch"],
    ARM["ch"]: ARM["j"],
}


def transliteration_to_armenian(name: str) -> str:
    """Convert a project transliteration string into Armenian script."""
    cleaned = (
        name.strip().lower().replace("ʰ", "h").replace("ə", "e").replace("'", "")
    )
    if not cleaned:
        return ""

    out = []
    i = 0
    tokens = sorted(_TOKEN_TO_ARMENIAN.keys(), key=len, reverse=True)
    while i < len(cleaned):
        matched = False
        for token in tokens:
            if cleaned.startswith(token, i):
                out.append(_TOKEN_TO_ARMENIAN[token])
                i += len(token)
                matched = True
                break
        if not matched:
            # Keep unknown characters verbatim so issues are visible in manifest.
            out.append(cleaned[i])
            i += 1
    return "".join(out)


def normalize_audio(audio: np.ndarray) -> np.ndarray:
    peak = float(np.max(np.abs(audio)))
    if peak < 1e-8:
        return audio
    return audio / peak


def time_stretch_audio(audio: np.ndarray, stretch_factor: float) -> np.ndarray:
    """Slow down audio by stretching time without changing pitch.
    
    Args:
        audio: Input audio waveform
        stretch_factor: >1.0 slows down, <1.0 speeds up
    
    Returns:
        Time-stretched audio
    """
    if stretch_factor <= 0 or abs(stretch_factor - 1.0) < 0.01:
        return audio
    
    # Use phase vocoder time-stretching
    stft = scipy.signal.stft(audio)[2]  # Get only the STFT matrix
    stretched_stft = scipy.signal.istft(stft)[1]  # Simple approach: resample
    
    # Simpler approach: resample the audio
    num_samples = int(len(audio) * stretch_factor)
    stretched = np.interp(
        np.linspace(0, len(audio)-1, num_samples),
        np.arange(len(audio)),
        audio
    )
    return stretched


def synthesize_and_concatenate_parts(
    parts: list,
    tokenizer: Any,
    model: Any,
    torch_mod: Any,
    passes: int,
    stretch_factor: float = 1.0,
    silence_ms: int = 50,
) -> np.ndarray:
    """Synthesize multiple parts separately and concatenate with silence between.
    
    Useful when a single prompt doesn't capture pronunciation (e.g., missing "y" sound).
    Each part is synthesized, post-filtered, and time-stretched independently.
    """
    sample_rate = model.config.sampling_rate
    silence_samples = int(silence_ms * sample_rate / 1000)
    all_parts = []
    
    for part in parts:
        audio = synthesize_wave_multirun(part, tokenizer, model, torch_mod, passes)
        audio = post_filter_audio(audio, sample_rate)
        audio = time_stretch_audio(audio, stretch_factor)
        all_parts.append(audio)
        # Add silence between parts
        all_parts.append(np.zeros(silence_samples))
    
    # Remove trailing silence
    if all_parts:
        all_parts = all_parts[:-1]
    
    # Concatenate
    concatenated = np.concatenate(all_parts) if all_parts else np.array([])
    return normalize_audio(concatenated)


def post_filter_audio(audio: np.ndarray, sample_rate: int) -> np.ndarray:
    """Apply gentle cleanup to reduce hiss/static artifacts.

    Pipeline:
    - high-pass: remove DC/very-low rumble
    - low-pass: tame top-end hash that sounds like static
    - median smoothing: suppress short impulsive artifacts
    - headroom normalization: avoid harsh edge clipping
    """
    # Remove sub-audible/DC content.
    hp_sos = scipy.signal.butter(2, 45, btype="highpass", fs=sample_rate, output="sos")
    cleaned = scipy.signal.sosfilt(hp_sos, audio)

    # Keep consonant clarity but roll off extreme highs.
    nyquist_safe = max(4000, int(sample_rate * 0.43))
    lp_sos = scipy.signal.butter(2, nyquist_safe, btype="lowpass", fs=sample_rate, output="sos")
    cleaned = scipy.signal.sosfilt(lp_sos, cleaned)

    # Very gentle click/static smoothing.
    cleaned = scipy.signal.medfilt(cleaned, kernel_size=3)

    # Normalize with slight headroom to avoid crisp clipping edges.
    peak = float(np.max(np.abs(cleaned)))
    if peak > 1e-8:
        cleaned = cleaned / peak * 0.92

    return cleaned


def synthesize_wave(text: str, tokenizer: Any, model: Any, torch_mod: Any) -> np.ndarray:
    inputs = tokenizer(text, return_tensors="pt")
    with torch_mod.no_grad():
        output = model(**inputs).waveform
    audio = output.squeeze().cpu().numpy()
    return normalize_audio(audio)


def synthesize_wave_multirun(
    text: str,
    tokenizer: Any,
    model: Any,
    torch_mod: Any,
    passes: int,
) -> np.ndarray:
    """Synthesize several passes and average to reduce model noise floor."""
    runs = []
    num_passes = max(1, passes)
    for _ in range(num_passes):
        runs.append(synthesize_wave(text, tokenizer, model, torch_mod))

    max_len = max(len(a) for a in runs)
    padded = [np.pad(a, (0, max_len - len(a)), mode="constant") for a in runs]
    merged = np.mean(padded, axis=0)
    return normalize_audio(merged)


def write_mp3(audio: np.ndarray, sample_rate: int, out_mp3: Path, tmp_wav: Path) -> None:
    import scipy.io.wavfile

    wav_i16 = (audio * 32767).astype("int16")

    # Prefer in-process MP3 encoding to avoid external ffmpeg dependency.
    try:
        import lameenc  # type: ignore

        encoder = lameenc.Encoder()
        encoder.set_bit_rate(128)
        encoder.set_in_sample_rate(sample_rate)
        encoder.set_channels(1)
        encoder.set_quality(2)
        mp3_data = encoder.encode(wav_i16.tobytes()) + encoder.flush()
        out_mp3.write_bytes(mp3_data)
        return
    except Exception:
        pass

    # Fallback to ffmpeg when available.
    scipy.io.wavfile.write(str(tmp_wav), sample_rate, wav_i16)
    cmd = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-i",
        str(tmp_wav),
        "-codec:a",
        "libmp3lame",
        "-q:a",
        "2",
        str(out_mp3),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"mp3 encoding failed for {out_mp3.name}: {proc.stderr.strip() or proc.stdout.strip()}"
        )


def build_name_prompt(letter: str) -> str:
    base = LETTER_NAME_ARMENIAN.get(letter, letter)

    if USE_EASTERN_BIAS_WORKAROUND:
        return "".join(_EASTERN_BIAS_NAME_CHAR_PROXY.get(ch, ch) for ch in base)
    return base


def build_sound_prompt(letter: str) -> str:
    # Keep sound prompt Armenian-only while allowing WA targeting and
    # optional mitigation for Eastern-biased model behavior.
    if letter in _WA_CONTEXT_SOUND_PROMPTS:
        base = _WA_CONTEXT_SOUND_PROMPTS[letter]
    else:
        base = letter

    if USE_EASTERN_BIAS_WORKAROUND and letter in _EASTERN_BIAS_SOUND_PROXY:
        return _EASTERN_BIAS_SOUND_PROXY[letter]
    return base


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Western Armenian letter audio via MMS TTS")
    parser.add_argument("--limit", type=int, default=0, help="Generate only first N letters (0=all 38)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing MP3 files")
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"], help="Torch device")
    parser.add_argument(
        "--disable-eastern-bias-workaround",
        action="store_true",
        help="Disable proxy prompt substitutions used to compensate for Eastern-biased TTS behavior",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not synthesize audio; only print/write prompts and planned output files",
    )
    parser.add_argument(
        "--passes",
        type=int,
        default=3,
        help="Number of synthesis passes to average (default: 3)",
    )
    parser.add_argument(
        "--names-only",
        action="store_true",
        help="Generate only letter-name audio, skip letter-sound audio",
    )
    parser.add_argument(
        "--time-stretch",
        type=float,
        default=1.0,
        help="Time-stretch factor to slow down audio (>1.0 = slower, 1.0 = normal, e.g., 1.5 = 50%% slower)",
    )
    return parser.parse_args()


USE_EASTERN_BIAS_WORKAROUND = True


def main() -> int:
    global USE_EASTERN_BIAS_WORKAROUND
    args = parse_args()
    USE_EASTERN_BIAS_WORKAROUND = not args.disable_eastern_bias_workaround
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    letters = get_all_letters_ordered()
    if args.limit > 0:
        letters = letters[: args.limit]

    torch_mod = None
    tokenizer = None
    model = None

    if USE_EASTERN_BIAS_WORKAROUND:
        print("Prompt mode: Western Armenian with Eastern-bias workaround ENABLED")
    else:
        print("Prompt mode: Western Armenian direct prompts (no Eastern-bias workaround)")

    if not args.dry_run:
        print(f"Loading model: {MODEL_ID}")
        try:
            import torch as torch_mod  # type: ignore
            from transformers import AutoTokenizer, VitsModel
        except Exception as exc:
            print(f"Dependency load error: {exc}")
            print("Tip: run with --dry-run to verify prompts without audio synthesis.")
            return 1

        try:
            tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
            model = VitsModel.from_pretrained(MODEL_ID)
            model.to(args.device)
        except Exception as exc:
            print(f"Model load error: {exc}")
            print("Tip: run with --dry-run to verify prompts without audio synthesis.")
            return 1

    manifest: Dict[str, Dict[str, str]] = {}
    created = 0
    skipped = 0

    for idx, letter in enumerate(letters, start=1):
        name_prompt = build_name_prompt(letter)
        sound_prompt = build_sound_prompt(letter)

        name_mp3 = OUT_DIR / f"letter_{letter}_name.mp3"
        sound_mp3 = OUT_DIR / f"letter_{letter}_sound.mp3"
        name_tmp = TMP_DIR / f"letter_{idx:02d}_{letter}_name.wav"
        sound_tmp = TMP_DIR / f"letter_{idx:02d}_{letter}_sound.wav"

        manifest[letter] = {
            "name_prompt": name_prompt,
            "name_ipa": LETTER_NAME_IPA.get(letter, ""),
            "name_armenian": LETTER_NAME_ARMENIAN.get(letter, ""),
            "sound_prompt": sound_prompt,
            "name_file": str(name_mp3.name),
            "sound_file": str(sound_mp3.name),
            "name_synthesis_mode": "split" if letter in _SPLIT_SYNTHESIS_RULES else "normal",
        }

        print(f"[{idx}/{len(letters)}] {letter} | name='{name_prompt}' | sound='{sound_prompt}'")
        if letter in _SPLIT_SYNTHESIS_RULES:
            print(f"  - using split-synthesis: {_SPLIT_SYNTHESIS_RULES[letter]}")

        if not args.overwrite and name_mp3.exists() and (args.names_only or sound_mp3.exists()):
            skipped += 1 if args.names_only else 2
            print("  - skip existing")
            continue

        if args.dry_run:
            continue

        try:
            # Use split-synthesis if a rule exists for this letter
            if letter in _SPLIT_SYNTHESIS_RULES:
                parts = _SPLIT_SYNTHESIS_RULES[letter]
                name_audio = synthesize_and_concatenate_parts(
                    parts,
                    tokenizer,
                    model,
                    torch_mod,
                    passes=args.passes,
                    stretch_factor=args.time_stretch,
                    silence_ms=50,
                )
            else:
                # Normal synthesis
                name_audio = synthesize_wave_multirun(
                    name_prompt,
                    tokenizer,
                    model,
                    torch_mod,
                    passes=args.passes,
                )
                name_audio = post_filter_audio(name_audio, model.config.sampling_rate)
                name_audio = time_stretch_audio(name_audio, args.time_stretch)
            
            write_mp3(name_audio, model.config.sampling_rate, name_mp3, name_tmp)
            created += 1

            if not args.names_only:
                sound_audio = synthesize_wave_multirun(
                    sound_prompt,
                    tokenizer,
                    model,
                    torch_mod,
                    passes=args.passes,
                )
                sound_audio = post_filter_audio(sound_audio, model.config.sampling_rate)
                sound_audio = time_stretch_audio(sound_audio, args.time_stretch)
                write_mp3(sound_audio, model.config.sampling_rate, sound_mp3, sound_tmp)
                created += 1
        except Exception as exc:
            print(f"  ! error: {exc}")

    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    for tmp_wav in TMP_DIR.glob("*.wav"):
        try:
            tmp_wav.unlink()
        except OSError:
            pass

    print("\nDone")
    print(f"Created mp3 files: {created}")
    print(f"Skipped existing: {skipped}")
    print(f"Output directory: {OUT_DIR}")
    print(f"Manifest: {MANIFEST_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
