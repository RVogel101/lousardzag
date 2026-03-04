#!/usr/bin/env python3
"""
Generate pronunciation audio for all Armenian letters using gTTS.

Generates 76 audio files (38 letters × 2 languages):
- Armenian (hy): Letter names and pronunciation
- English (en): English sound approximations and pronunciation tips

Audio files stored in: 08-data/letter_audio/
Metadata tracking stored in: 08-data/letter_audio/audio_metadata.json
"""

import sys
import logging
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "02-src"))

from lousardzag.letter_audio import LetterAudioManager, TextToSpeechEngine
from lousardzag import letter_data

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Generate audio for all Armenian letters."""
    logger.info("Starting Armenian letter audio generation...")
    
    # Initialize audio manager with gTTS (free, simple, no API key)
    try:
        manager = LetterAudioManager(engine=TextToSpeechEngine.GTTS)
        logger.info("✅ Initialized LetterAudioManager with gTTS engine")
    except Exception as e:
        logger.error(f"❌ Failed to initialize audio manager: {e}")
        logger.info("Make sure gtts is installed: pip install gtts")
        return False
    
    # Get all letters in order
    all_letters = letter_data.get_all_letters_ordered()
    logger.info(f"Found {len(all_letters)} Armenian letters")
    
    # Generate audio for each letter in both languages
    try:
        logger.info("Generating audio for Armenian letter names (language: hy)...")
        success_count = manager.batch_generate_letter_audio(
            letters=all_letters,
            languages=['hy']
        )
        logger.info(f"✅ Generated {success_count} Armenian pronunciation audio files")
    except Exception as e:
        logger.error(f"❌ Failed to generate Armenian audio: {e}")
        return False
    
    try:
        logger.info("Generating audio for English approximations (language: en)...")
        success_count = manager.batch_generate_letter_audio(
            letters=all_letters,
            languages=['en']
        )
        logger.info(f"✅ Generated {success_count} English approximation audio files")
    except Exception as e:
        logger.error(f"❌ Failed to generate English audio: {e}")
        return False
    
    # Verify output
    audio_dir = Path(__file__).parent.parent.parent / "08-data" / "letter_audio"
    if audio_dir.exists():
        audio_files = list(audio_dir.glob("*.mp3"))
        logger.info(f"\n📊 Summary:")
        logger.info(f"   Total audio files: {len(audio_files)}")
        logger.info(f"   Storage location: {audio_dir}")
        logger.info(f"   Metadata file: {audio_dir / 'audio_metadata.json'}")
        
        if audio_files:
            logger.info(f"\n✅ Audio generation complete!")
            logger.info(f"   Ready to integrate with Anki cards")
            return True
    
    logger.warning("Audio directory not found or no files generated")
    return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
