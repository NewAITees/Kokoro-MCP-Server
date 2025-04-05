"""
Test module for Kokoro TTS implementation.
"""

import os
import tempfile
from pathlib import Path
import pytest
from kokoro_mcp_server.tts import KokoroTTS
import torch
import fugashi
import unidic_lite

@pytest.fixture
def tts():
    """Create a KokoroTTS instance for testing."""
    return KokoroTTS(lang_code='ja', voice='af_heart')

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

def test_mecab_configuration():
    """Test MeCab configuration."""
    # Test fugashi initialization
    tagger = fugashi.Tagger('-d ' + unidic_lite.DICDIR)
    assert tagger is not None
    
    # Test environment variables
    assert os.environ.get('MECABRC') == '/etc/mecabrc'
    assert os.environ.get('FUGASHI_ENABLE_FALLBACK') == '1'

def test_tts_initialization(tts):
    """Test TTS initialization."""
    assert tts.lang_code == 'ja'
    assert tts.voice == 'af_heart'
    assert tts.pipeline is not None

def test_generate_audio(tts, temp_dir):
    """Test audio generation."""
    text = "こんにちは、これはテストです。"
    output_dir = temp_dir / "output"
    
    # Generate audio
    segments = list(tts.generate_audio(text, output_dir=str(output_dir)))
    
    # Check results
    assert len(segments) > 0
    for i, gs, ps, audio in segments:
        assert isinstance(i, int)
        assert isinstance(gs, str)
        assert isinstance(ps, str)
        assert isinstance(audio, torch.Tensor)
        
        # Check if file was saved
        output_file = output_dir / f"{i}.wav"
        assert output_file.exists()
        assert output_file.stat().st_size > 0

def test_save_audio(tts, temp_dir):
    """Test saving audio to file."""
    # Generate test audio
    text = "テスト"
    _, _, _, audio = next(tts.generate_audio(text))
    
    # Save audio
    output_path = temp_dir / "test.wav"
    tts.save_audio(audio, str(output_path))
    
    # Check if file was saved
    assert output_path.exists()
    assert output_path.stat().st_size > 0 