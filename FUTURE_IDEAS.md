# Future Ideas

- Conversation practice mode: revisit piping responses from a Western Armenian LLM to support guided dialogue practice without adding heavy learner friction.

- **Custom Western Armenian TTS model**: The `facebook/mms-tts-hyw` model (Meta MMS) works well with 3-pass denoising + 0.90x speed, but quality could be improved further. Options: (1) Fine-tune XTTS v2 or train a Piper voice with ~30 min of clean native speaker audio — this would give the highest quality. (2) Explore multi-speaker MMS fine-tuning if Meta releases training code. (3) Use the project's `phonetics.py` Western Armenian phoneme set to inform any phoneme mapping. Current MMS output is usable for flashcards but still has some synthesis artifacts that averaging can't fully remove. Key challenge remains data collection — no existing high-quality WA TTS datasets exist. Potential audio sources: record a native speaker reading the vocabulary list, diaspora radio/TV archives, or clean existing Anki audio files.

- **Letter audio upgrade**: Replace the 76 espeak-ng letter audio files (`08-data/letter_audio/`) with MMS-generated versions using the same 3-pass denoising technique from `generate_vocab_audio_mms.py`. This would give consistent quality across letter and vocabulary audio.
