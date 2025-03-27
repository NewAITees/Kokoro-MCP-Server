"""Kokoro音声合成エンジンのモック実装モジュール"""

import os
from pathlib import Path
import asyncio
from typing import Dict, Optional, Tuple, Union
import logging

logger = logging.getLogger(__name__)

class MockKokoroEngine:
    """Kokoro音声合成エンジンのモック実装"""
    
    def __init__(self, sample_dir: str = None):
        """
        初期化
        
        Args:
            sample_dir (str, optional): サンプル音声ディレクトリ
        """
        self.sample_dir = Path(sample_dir or "./audio_samples")
        self._samples: Dict[str, Dict[str, bytes]] = {
            'japanese': {},
            'english': {}
        }
        self._load_samples()
        # 初期化時にダミーデータを準備
        if not any(self._samples.values()):
            self._prepare_dummy_samples()
    
    async def generate_speech(
        self,
        text: str,
        language: str = "auto",
        options: Optional[Dict] = None
    ) -> Tuple[bytes, str, float]:
        """
        モック音声生成

        Args:
            text (str): 音声化するテキスト
            language (str, optional): 言語指定 ('japanese', 'english', 'auto')
            options (dict, optional): 音声オプション（速度、ピッチなど）

        Returns:
            Tuple[bytes, str, float]: (音声データ, 形式, 音声の長さ)
        """
        # オプションの処理
        options = options or {}
        speed = options.get('speed', 1.0)
        pitch = options.get('pitch', 0.0)
        voice_id = options.get('voice_id', 'default')

        # 言語の自動検出（簡易的な実装）
        if language == "auto":
            language = self._detect_language(text)

        # サンプル音声の選択
        audio_data = self._get_sample_audio(language, len(text))
        
        # 音声の長さを計算（テキストの長さに基づく簡易的な計算）
        duration = len(text) * 0.1 * (1.0 / speed)

        return audio_data, 'mp3', duration

    def _load_samples(self):
        """サンプル音声をロード"""
        try:
            # 日本語サンプル
            jp_path = self.sample_dir / "japanese"
            if jp_path.exists():
                for file in jp_path.glob("*.mp3"):
                    with open(file, 'rb') as f:
                        self._samples['japanese'][file.stem] = f.read()

            # 英語サンプル
            en_path = self.sample_dir / "english"
            if en_path.exists():
                for file in en_path.glob("*.mp3"):
                    with open(file, 'rb') as f:
                        self._samples['english'][file.stem] = f.read()

        except Exception as e:
            logger.warning(f"Failed to load sample audio files: {e}")
            # デフォルトのダミーデータを用意
            self._prepare_dummy_samples()

    def _prepare_dummy_samples(self):
        """ダミーのサンプルデータを準備"""
        # 実際の音声の代わりに空のバイトデータを使用
        dummy_data = b'DUMMY_AUDIO_DATA'
        self._samples = {
            'japanese': {'short': dummy_data, 'medium': dummy_data, 'long': dummy_data},
            'english': {'short': dummy_data, 'medium': dummy_data, 'long': dummy_data}
        }

    def _detect_language(self, text: str) -> str:
        """
        簡易的な言語検出

        Args:
            text (str): 検出対象のテキスト

        Returns:
            str: 検出された言語 ('japanese' or 'english')
        """
        # 日本語の文字が含まれているかチェック
        if any(ord(char) > 0x3040 for char in text):
            return 'japanese'
        return 'english'

    def _get_sample_audio(self, language: str, text_length: int) -> bytes:
        """
        テキストの長さに応じたサンプル音声を取得

        Args:
            language (str): 言語
            text_length (int): テキストの長さ

        Returns:
            bytes: 音声データ
        """
        # テキストの長さに応じてサンプルを選択
        if text_length < 50:
            key = 'short'
        elif text_length < 200:
            key = 'medium'
        else:
            key = 'long'

        # 言語とサイズに応じたサンプルを返す
        samples = self._samples.get(language, self._samples['english'])
        if not samples:
            # サンプルがない場合はダミーデータを返す
            return b'DUMMY_AUDIO_DATA'
        return samples.get(key, next(iter(samples.values()))) 