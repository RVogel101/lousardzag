#!/usr/bin/env python3
"""Generate Armenian vocab audio using Google Cloud TTS (hy-AM WaveNet)."""
import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "arm-speech-converter-8bf4999c6dfb.json"
)

from google.cloud import texttospeech
from pathlib import Path

OUT_DIR = Path(__file__).parent.parent / "08-data" / "audio_comparison"
OUT_DIR.mkdir(parents=True, exist_ok=True)

client = texttospeech.TextToSpeechClient()

# List ALL available voices to find Armenian
print("Checking all voices for Armenian (hy)...")
all_voices = client.list_voices()
hy_voices = [v for v in all_voices.voices if any(lc.startswith("hy") for lc in v.language_codes)]
if hy_voices:
    print(f"Found {len(hy_voices)} Armenian voice(s):")
    for voice in hy_voices:
        ssml = texttospeech.SsmlVoiceGender(voice.ssml_gender).name
        print(f"  {voice.name}  langs={voice.language_codes}  ({ssml})  rate={voice.natural_sample_rate_hertz}Hz")
else:
    print("No Armenian voices found! Listing all available language codes:")
    all_langs = sorted(set(lc for v in all_voices.voices for lc in v.language_codes))
    print(f"  Total languages: {len(all_langs)}")
    # Check for nearby codes
    for lc in all_langs:
        if lc.startswith(("hy", "ar", "ka")):
            print(f"  Near match: {lc}")

# Test words
tests = [
    ("\u0574\u0561\u0580\u0564", "50_gcloud_mard"),      # մartar = person
    ("\u0570\u0561\u0575", "51_gcloud_hay"),               # հay = Armenian
    ("\u0565\u0580\u056f\u0578\u0582", "52_gcloud_yergu"), # երkou = two
    ("\u057f\u0578\u0582\u0576", "53_gcloud_dun"),         # տun = house
    ("\u0574\u0565\u056e", "54_gcloud_medz"),              # մeδ = big
]

if not hy_voices:
    print("\nNo Armenian voices available. Enable the Text-to-Speech API and check your project.")
    exit(1)

# Use the best available voice (prefer WaveNet/Neural/Studio)
voice_name = None
for v in hy_voices:
    if "Wavenet" in v.name or "Neural" in v.name or "Studio" in v.name:
        voice_name = v.name
        break
if not voice_name:
    voice_name = hy_voices[0].name

lang_code = [lc for lc in hy_voices[0].language_codes if lc.startswith("hy")][0]
print(f"\nUsing voice: {voice_name} (lang={lang_code})")

voice_params = texttospeech.VoiceSelectionParams(
    language_code=lang_code,
    name=voice_name,
)
audio_config = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.LINEAR16,
    speaking_rate=0.9,
)

for word, fname in tests:
    print(f"Generating: {word} -> {fname}.wav")
    synthesis_input = texttospeech.SynthesisInput(text=word)
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice_params, audio_config=audio_config
    )
    out_path = OUT_DIR / f"{fname}.wav"
    out_path.write_bytes(response.audio_content)
    print(f"  Written: {len(response.audio_content):,} bytes")

print("\nDone!")
