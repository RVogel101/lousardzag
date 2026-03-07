#!/usr/bin/env python3
"""Generate Western Armenian letter audio from IPA input using espeak-ng.

This script supports two separate IPA concepts:
1) letter-name IPA (the spoken name of a grapheme)
2) letter-sound IPA (the phoneme value of a grapheme)
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "02-src"))

from lousardzag.core_shims.linguistics_core import LETTER_NAME_IPA, LETTER_SOUND_IPA

OUT_DIR = ROOT / "08-data" / "letter_audio_ipa"
MANIFEST_PATH = OUT_DIR / "letter_audio_ipa_manifest.json"

# Resolve espeak-ng binary: PATH first, then common Windows install location.
_ESPEAK_BIN = shutil.which("espeak-ng") or r"C:\Program Files\eSpeak NG\espeak-ng.exe"


def synthesize_ipa_to_audio(ipa: str, out_mp3: Path) -> bool:
    """Use espeak-ng to synthesize IPA to audio.
    
    Args:
        ipa: IPA string (with or without slashes)
        out_mp3: Output MP3 file path
        
    Returns:
        True if successful, False otherwise
    """
    # Remove IPA slashes if present
    ipa_clean = ipa.strip("/")
    
    # espeak-ng uses [[...]] brackets for direct IPA/phoneme input.
    phoneme_input = f"[[{ipa_clean}]]"
    
    # espeak-ng on Windows can't write to paths containing non-ASCII characters.
    # Use a temp file with an ASCII name, then convert/move to the final path.
    tmp_fd, tmp_wav = tempfile.mkstemp(suffix=".wav", prefix="espeak_")
    import os
    os.close(tmp_fd)
    
    cmd = [
        _ESPEAK_BIN,
        "-v", "hy",   # Armenian voice (closest available)
        "-a", "100",  # Amplitude
        "-s", "120",  # Speed (words per minute)
        "-m",         # Interpret input as SSML/phoneme markup
        "-w", tmp_wav,
        phoneme_input,
    ]
    
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        tmp_wav_path = Path(tmp_wav)
        if tmp_wav_path.exists() and tmp_wav_path.stat().st_size > 0:
            convert_wav_to_mp3(tmp_wav_path, out_mp3)
            tmp_wav_path.unlink(missing_ok=True)
            return out_mp3.exists()
        return False
    except subprocess.CalledProcessError as e:
        print(f"  ! espeak-ng failed: {e.stderr or e.stdout}")
        return False
    except FileNotFoundError:
        print("  ! espeak-ng not found. Install with: choco install espeak-ng (or apt/brew)")
        return False
    finally:
        Path(tmp_wav).unlink(missing_ok=True)


def convert_wav_to_mp3(wav_file: Path, mp3_file: Path) -> bool:
    """Convert WAV to MP3 using lameenc (in-process) or ffmpeg as fallback."""
    import wave

    try:
        with wave.open(str(wav_file), "rb") as wf:
            sample_rate = wf.getframerate()
            channels = wf.getnchannels()
            pcm_data = wf.readframes(wf.getnframes())
    except Exception as e:
        print(f"  ! WAV read failed: {e}")
        return False

    # Prefer lameenc (in-process, no external binary issues).
    try:
        import lameenc  # type: ignore[reportMissingImports]
        encoder = lameenc.Encoder()
        encoder.set_bit_rate(128)
        encoder.set_in_sample_rate(sample_rate)
        encoder.set_channels(channels)
        encoder.set_quality(2)
        mp3_data = encoder.encode(pcm_data) + encoder.flush()
        mp3_file.write_bytes(mp3_data)
        return mp3_file.exists()
    except Exception:
        pass

    # Fallback to ffmpeg via temp file.
    tmp_fd, tmp_mp3 = tempfile.mkstemp(suffix=".mp3", prefix="espeak_")
    import os
    os.close(tmp_fd)
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(wav_file),
        "-codec:a", "libmp3lame", "-q:a", "2",
        tmp_mp3,
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        tmp_path = Path(tmp_mp3)
        if tmp_path.exists() and tmp_path.stat().st_size > 0:
            shutil.move(str(tmp_path), str(mp3_file))
            return mp3_file.exists()
        return False
    except Exception as e:
        print(f"  ! ffmpeg conversion failed: {e}")
        Path(tmp_mp3).unlink(missing_ok=True)
        return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Western Armenian letter audio from IPA using espeak-ng"
    )
    parser.add_argument(
        "--kind",
        choices=["name", "sound"],
        default="sound",
        help="Choose IPA dataset: letter name IPA or letter sound IPA",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Generate only first N letters (0=all 38)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing MP3 files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not synthesize; only print planned outputs",
    )
    parser.add_argument(
        "--test",
        type=str,
        default=None,
        help="Test single letter (e.g. ա)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    ipa_map = LETTER_NAME_IPA if args.kind == "name" else LETTER_SOUND_IPA
    file_suffix = "name" if args.kind == "name" else "sound"

    # Get letters to process
    if args.test:
        letters = [args.test]
    else:
        letters = list(ipa_map.keys())
        if args.limit > 0:
            letters = letters[:args.limit]

    manifest = {}
    created = 0
    skipped = 0
    failed = 0

    for idx, letter in enumerate(letters, start=1):
        ipa = ipa_map.get(letter)
        if not ipa:
            print(f"[{idx}/{len(letters)}] {letter} - NO IPA DATA")
            continue

        out_mp3 = OUT_DIR / f"letter_{letter}_{file_suffix}_ipa.mp3"
        ipa_display = f"/{ipa}/"

        manifest[letter] = {
            "kind": args.kind,
            "ipa": ipa_display,
            "file": str(out_mp3.name),
            "source": "espeak-ng",
        }

        print(f"[{idx}/{len(letters)}] {letter} | IPA='{ipa_display}'")

        if not args.overwrite and out_mp3.exists():
            skipped += 1
            print("  - skip existing")
            continue

        if args.dry_run:
            continue

        if synthesize_ipa_to_audio(ipa, out_mp3):
            created += 1
            print(f"  ✓ created")
        else:
            failed += 1
            print(f"  ✗ failed")

    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\nDone")
    print(f"Created: {created}")
    print(f"Skipped: {skipped}")
    print(f"Failed: {failed}")
    print(f"Manifest: {MANIFEST_PATH}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
