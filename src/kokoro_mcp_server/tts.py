"""
Kokoro TTS implementation module.
This module provides functionality for text-to-speech conversion using Kokoro.
"""

import os
from typing import Generator, Tuple, Optional
import soundfile as sf
import torch
from kokoro import KPipeline
from loguru import logger
import fugashi
import unidic_lite

class KokoroTTS:
    """Kokoro TTS implementation class."""
    
    def __init__(self, lang_code: str = 'ja', voice: str = 'af_heart'):
        """
        Initialize Kokoro TTS.
        
        Args:
            lang_code (str): Language code for TTS
            voice (str): Voice model to use
        """
        self.lang_code = lang_code
        self.voice = voice
        
        # Configure MeCab and fugashi
        self._configure_mecab()
        
        # Initialize pipeline
        self.pipeline = KPipeline(lang_code=lang_code)
        logger.info(f"Initialized Kokoro TTS with lang_code={lang_code}, voice={voice}")

    def _configure_mecab(self):
        """Configure MeCab and fugashi settings."""
        # Set environment variables for MeCab
        os.environ['MECABRC'] = '/etc/mecabrc'
        os.environ['FUGASHI_ENABLE_FALLBACK'] = '1'
        
        # Initialize fugashi with unidic-lite
        try:
            tagger = fugashi.Tagger('-d ' + unidic_lite.DICDIR)
            logger.info("Successfully initialized MeCab with unidic-lite")
        except Exception as e:
            logger.error(f"Failed to initialize MeCab: {str(e)}")
            raise

    def generate_audio(
        self, 
        text: str, 
        output_dir: Optional[str] = None
    ) -> Generator[Tuple[int, str, str, torch.Tensor], None, None]:
        """
        Generate audio from text.
        
        Args:
            text (str): Input text to convert to speech
            output_dir (Optional[str]): Directory to save audio files
            
        Yields:
            Tuple[int, str, str, torch.Tensor]: Index, grapheme sequence, phoneme sequence, and audio data
        """
        generator = self.pipeline(text, voice=self.voice)
        
        for i, (gs, ps, audio) in enumerate(generator):
            logger.debug(f"Generated audio segment {i}: gs={gs}, ps={ps}")
            
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, f"{i}.wav")
                sf.write(output_path, audio, 24000)
                logger.info(f"Saved audio segment {i} to {output_path}")
            
            yield i, gs, ps, audio

    def save_audio(self, audio: torch.Tensor, output_path: str) -> None:
        """
        Save audio data to file.
        
        Args:
            audio (torch.Tensor): Audio data to save
            output_path (str): Path to save the audio file
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        sf.write(output_path, audio, 24000)
        logger.info(f"Saved audio to {output_path}") 