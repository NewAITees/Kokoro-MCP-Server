"""Kokoro音声合成エンジンのモックテスト"""

import pytest
from pathlib import Path
from src.kokoro.mock import MockKokoroEngine

@pytest.fixture
def mock_engine():
    """モックエンジンのフィクスチャ"""
    return MockKokoroEngine()

@pytest.mark.asyncio
async def test_generate_speech_japanese(mock_engine):
    """日本語テキストの音声生成テスト"""
    text = "こんにちは、世界"
    audio_data, format_, duration = await mock_engine.generate_speech(text)
    
    assert audio_data is not None
    assert format_ == 'mp3'
    assert duration > 0
    assert isinstance(duration, float)

@pytest.mark.asyncio
async def test_generate_speech_english(mock_engine):
    """英語テキストの音声生成テスト"""
    text = "Hello, world"
    audio_data, format_, duration = await mock_engine.generate_speech(text, language='english')
    
    assert audio_data is not None
    assert format_ == 'mp3'
    assert duration > 0
    assert isinstance(duration, float)

@pytest.mark.asyncio
async def test_generate_speech_with_options(mock_engine):
    """オプション付きの音声生成テスト"""
    text = "テストテキスト"
    options = {
        'speed': 1.5,
        'pitch': 0.5,
        'voice_id': 'test_voice'
    }
    audio_data, format_, duration = await mock_engine.generate_speech(text, options=options)
    
    assert audio_data is not None
    assert format_ == 'mp3'
    # 速度が1.5倍なので、通常の2/3の時間になるはず
    assert duration == pytest.approx(len(text) * 0.1 / 1.5, rel=1e-5)

def test_language_detection(mock_engine):
    """言語検出のテスト"""
    # 日本語テキスト
    assert mock_engine._detect_language("こんにちは") == 'japanese'
    assert mock_engine._detect_language("テスト123") == 'japanese'
    
    # 英語テキスト
    assert mock_engine._detect_language("Hello") == 'english'
    assert mock_engine._detect_language("Test 123") == 'english'

@pytest.mark.asyncio
async def test_auto_language_detection(mock_engine):
    """自動言語検出を使用した音声生成テスト"""
    # 日本語テキスト
    text_jp = "こんにちは"
    audio_data_jp, format_jp, duration_jp = await mock_engine.generate_speech(text_jp, language='auto')
    
    # 英語テキスト
    text_en = "Hello"
    audio_data_en, format_en, duration_en = await mock_engine.generate_speech(text_en, language='auto')
    
    assert audio_data_jp is not None
    assert audio_data_en is not None
    assert format_jp == format_en == 'mp3'

def test_sample_audio_selection(mock_engine):
    """テキストの長さに応じたサンプル音声選択のテスト"""
    # 短いテキスト
    short_audio = mock_engine._get_sample_audio('japanese', 30)
    assert short_audio is not None
    
    # 中程度のテキスト
    medium_audio = mock_engine._get_sample_audio('japanese', 100)
    assert medium_audio is not None
    
    # 長いテキスト
    long_audio = mock_engine._get_sample_audio('japanese', 300)
    assert long_audio is not None 