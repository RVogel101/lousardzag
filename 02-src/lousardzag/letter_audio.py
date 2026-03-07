"""
Armenian Letter Audio Support - Text-to-Speech and Audio Integration

Provides audio generation and management for Armenian letter pronunciation:
- Text-to-speech synthesis for letter names and example words
- Audio file management and caching
- Phonetic transcription for pronunciation guides
- Multi-language support (English and Armenian)
"""

from typing import Optional, Dict, List, Tuple
from pathlib import Path
import json
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class AudioFormat(Enum):
    """Supported audio file formats."""
    MP3 = "mp3"
    OGG = "ogg"
    WAV = "wav"


class TextToSpeechEngine(Enum):
    """Available TTS engines."""
    GCLOUD = "google-cloud"      # Google Cloud Text-to-Speech
    AZURE = "azure"              # Azure Speech Service
    GTTS = "gtts"                # Google Translate TTS (simple, free)
    ESPEAK = "espeak"            # eSpeak (offline, quick)


class LetterAudioManager:
    """Manages audio generation and file handling for Armenian letters."""

    def __init__(
        self,
        audio_dir: Optional[Path] = None,
        engine: TextToSpeechEngine = TextToSpeechEngine.GTTS,
        cache_metadata: bool = True,
    ):
        """Initialize audio manager.
        
        Args:
            audio_dir: Directory to store audio files. Defaults to anki_media/
            engine: TTS engine to use
            cache_metadata: Whether to cache audio file metadata
        """
        if audio_dir is None:
            from . import config
            audio_dir = Path(__file__).parent.parent.parent / "08-data" / "letter_audio"
        
        self.audio_dir = Path(audio_dir)
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.engine = engine
        self.metadata_file = self.audio_dir / "audio_metadata.json"
        self.metadata: Dict = self._load_metadata() if cache_metadata else {}

    def _load_metadata(self) -> Dict:
        """Load audio metadata from cache file."""
        if self.metadata_file.exists():
            try:
                return json.loads(self.metadata_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_metadata(self) -> None:
        """Save audio metadata to cache file."""
        self.metadata_file.write_text(
            json.dumps(self.metadata, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def generate_letter_audio(
        self,
        letter: str,
        language: str = "hy",  # Armenian
        voice_gender: str = "neutral",
        format: AudioFormat = AudioFormat.MP3,
    ) -> Optional[Path]:
        """Generate audio for a letter pronunciation.
        
        Args:
            letter: Armenian letter
            language: Language code (hy=Armenian, en=English)
            voice_gender: Gender of voice (male, female, neutral)
            format: Audio file format
            
        Returns:
            Path to generated audio file, or None if generation failed
        """
        cache_key = f"{letter}_{language}_{voice_gender}_{format.value}"

        # Check cache first
        if cache_key in self.metadata:
            cached_path = Path(self.metadata[cache_key]["file_path"])
            if cached_path.exists():
                return cached_path

        try:
            if self.engine == TextToSpeechEngine.GTTS:
                return self._generate_gtts(letter, language, format, cache_key)
            elif self.engine == TextToSpeechEngine.ESPEAK:
                return self._generate_espeak(letter, language, format, cache_key)
            else:
                logger.warning(f"Engine {self.engine.value} not yet implemented")
                return None

        except Exception as e:
            logger.error(f"Failed to generate audio for {letter}: {e}")
            return None

    def _generate_gtts(
        self,
        letter: str,
        language: str,
        format: AudioFormat,
        cache_key: str,
    ) -> Optional[Path]:
        """Generate audio using gTTS (Google Translate TTS).
        
        Requires: pip install gtts
        """
        try:
            from gtts import gTTS  # type: ignore[reportMissingModuleSource]
            from . import letter_data
            
            info = letter_data.get_letter_info(letter)
            if not info:
                return None

            # Determine text to speak
            if language == "hy":
                # Armenian: letter name
                text = f"{info['name']}"
            else:
                # English: letter name and pronunciation
                text = f"{info['name']}, sounds like {info['english']}"

            filename = self.audio_dir / f"letter_{letter}_{language}.{format.value}"

            # Generate audio
            tts = gTTS(text=text, lang=language, slow=False)
            
            if format == AudioFormat.MP3:
                tts.save(str(filename))
            else:
                # Convert if needed
                tts.save(str(filename.with_suffix(".mp3")))
                self._convert_audio(filename.with_suffix(".mp3"), filename, format)

            # Cache metadata
            self.metadata[cache_key] = {
                "file_path": str(filename),
                "letter": letter,
                "language": language,
                "format": format.value,
                "engine": self.engine.value,
                "text": text,
            }
            self._save_metadata()

            logger.info(f"Generated audio for {letter} ({language}): {filename.name}")
            return filename

        except ImportError:
            logger.error("gtts not installed. Run: pip install gtts")
            return None

    def _generate_espeak(
        self,
        letter: str,
        language: str,
        format: AudioFormat,
        cache_key: str,
    ) -> Optional[Path]:
        """Generate audio using eSpeak (offline synthesis).
        
        Requires: espeak system package
        """
        try:
            import subprocess
            from . import letter_data

            info = letter_data.get_letter_info(letter)
            if not info:
                return None

            # Determine text and language code
            if language == "hy":
                text = f"{info['name']}"
                lang_code = "hy"
            else:
                text = f"{info['name']}, sounds like {info['english']}"
                lang_code = "en"

            filename = self.audio_dir / f"letter_{letter}_{language}.{format.value}"

            # Generate using espeak
            cmd = [
                "espeak",
                "-v", lang_code,
                "-w", str(filename.with_suffix(".wav")),
                text,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"eSpeak failed: {result.stderr}")
                return None

            # Convert format if needed
            if format != AudioFormat.WAV:
                self._convert_audio(filename.with_suffix(".wav"), filename, format)

            # Cache metadata
            self.metadata[cache_key] = {
                "file_path": str(filename),
                "letter": letter,
                "language": language,
                "format": format.value,
                "engine": self.engine.value,
                "text": text,
            }
            self._save_metadata()

            logger.info(f"Generated audio for {letter} ({language}): {filename.name}")
            return filename

        except FileNotFoundError:
            logger.error("espeak not found. Install with: apt-get install espeak (Linux) or brew install espeak (macOS)")
            return None

    def _convert_audio(
        self,
        input_file: Path,
        output_file: Path,
        target_format: AudioFormat,
    ) -> bool:
        """Convert audio between formats.
        
        Requires: ffmpeg
        """
        try:
            import subprocess

            if target_format == AudioFormat.MP3:
                # WAV -> MP3
                cmd = [
                    "ffmpeg", "-i", str(input_file),
                    "-acodec", "libmp3lame", "-ab", "128k",
                    str(output_file), "-y",
                ]
            elif target_format == AudioFormat.OGG:
                # WAV -> OGG
                cmd = [
                    "ffmpeg", "-i", str(input_file),
                    "-c:a", "libvorbis", "-q:a", "7",
                    str(output_file), "-y",
                ]
            else:
                return False

            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0

        except FileNotFoundError:
            logger.error("ffmpeg not found")
            return False

    def get_letter_audio_path(
        self,
        letter: str,
        language: str = "hy",
    ) -> Optional[Path]:
        """Get path to audio file for a letter (generate if needed).
        
        Args:
            letter: Armenian letter
            language: Language code
            
        Returns:
            Path to audio file, or None
        """
        cache_key = f"{letter}_{language}_neutral_mp3"
        
        if cache_key in self.metadata:
            path = Path(self.metadata[cache_key]["file_path"])
            if path.exists():
                return path

        return self.generate_letter_audio(letter, language)

    def get_anki_audio_reference(
        self,
        letter: str,
        language: str = "hy",
    ) -> Optional[str]:
        """Get Anki audio field reference [sound:...].
        
        Args:
            letter: Armenian letter
            language: Language code
            
        Returns:
            Anki audio field string, or None
        """
        audio_path = self.get_letter_audio_path(letter, language)
        if not audio_path:
            return None

        filename = audio_path.name
        return f"[sound:{filename}]"

    def batch_generate_letter_audio(
        self,
        letters: Optional[List[str]] = None,
        languages: Optional[List[str]] = None,
    ) -> Dict[str, List[Path]]:
        """Generate audio for multiple letters.
        
        Args:
            letters: Letters to generate (None = all)
            languages: Languages to generate (default: Armenian)
            
        Returns:
            Dictionary mapping letters to generated file paths
        """
        if letters is None:
            from . import letter_data
            letters = letter_data.get_all_letters_ordered()

        if languages is None:
            languages = ["hy"]

        results = {}

        for letter in letters:
            results[letter] = []
            for lang in languages:
                path = self.generate_letter_audio(letter, lang)
                if path:
                    results[letter].append(path)

        return results

    def list_generated_audio(self) -> List[Dict]:
        """List all generated audio files with metadata.
        
        Returns:
            List of audio file metadata dictionaries
        """
        audio_files = list(self.audio_dir.glob("letter_*.*"))
        return [{"file": f.name, "size_kb": f.stat().st_size / 1024} for f in audio_files]

    def clear_audio_cache(self, letter: Optional[str] = None) -> int:
        """Delete generated audio files to free space.
        
        Args:
            letter: Specific letter to clear (None = all)
            
        Returns:
            Number of files deleted
        """
        deleted_count = 0

        if letter:
            pattern = f"letter_{letter}_*.*"
        else:
            pattern = "letter_*.*"

        for file in self.audio_dir.glob(pattern):
            try:
                file.unlink()
                deleted_count += 1
            except OSError as e:
                logger.error(f"Failed to delete {file}: {e}")

        # Update metadata
        deleted_keys = [k for k in self.metadata.keys() if letter is None or letter in k]
        for key in deleted_keys:
            del self.metadata[key]

        if deleted_keys:
            self._save_metadata()

        return deleted_count
