"""
モック版のKokoro TTSサービス
"""

import logging
import os
from datetime import datetime
from pathlib import Path
import random
import numpy as np
import soundfile as sf

from kokoro_mcp_server.kokoro.base import BaseTTSService, TTSRequest

class MockKokoroTTSService(BaseTTSService):
    """Kokoro TTSサービスのモック実装クラス"""

    def __init__(self):
        """サービスの初期化"""
        self.logger = logging.getLogger(__name__)
        self.logger.info("MockKokoroTTSService initialized")
        
        # サンプル音声ファイルのパス
        self.sample_files = [
            os.path.join(os.path.dirname(__file__), "samples", "sample1.wav"),
            os.path.join(os.path.dirname(__file__), "samples", "sample2.wav")
        ]
        
        # samples ディレクトリがない場合は作成
        samples_dir = os.path.join(os.path.dirname(__file__), "samples")
        os.makedirs(samples_dir, exist_ok=True)
        
        # サンプル音声ファイルがない場合は作成
        if not os.path.exists(self.sample_files[0]):
            self._create_sample_audio(self.sample_files[0])
        if not os.path.exists(self.sample_files[1]):
            self._create_sample_audio(self.sample_files[1])

    def _create_sample_audio(self, file_path: str):
        """
        サンプル音声ファイルを作成する
        
        Args:
            file_path: 保存先のパス
        """
        self.logger.info(f"Creating sample audio file: {file_path}")
        # 簡単なサイン波を生成
        sample_rate = 44100
        duration = 3.0  # 3秒
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        tone = np.sin(2 * np.pi * 440 * t) * 0.3  # 440Hzのサイン波
        
        # ファイルに保存
        sf.write(file_path, tone, sample_rate)
        self.logger.info(f"Sample audio file created: {file_path}")

    def generate(self, request: TTSRequest) -> tuple[bool, str | None]:
        """音声を生成する

        Args:
            request: TTSリクエスト

        Returns:
            tuple[bool, Optional[str]]: 成功したかどうかとファイルパス
        """
        try:
            self.logger.info(
                f"[MOCK] Starting voice generation for text: {request.text[:50]}..."
            )

            # 出力ディレクトリの作成
            voice_folder = Path("output/audio")
            voice_folder.mkdir(parents=True, exist_ok=True)

            # 出力ファイル名の生成
            base_filename = request.voice or "mock_output"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 出力ファイル名
            filename = voice_folder / f"{base_filename}_{timestamp}.wav"
            
            # ランダムにサンプルファイルを選択
            sample_file = random.choice(self.sample_files)
            
            # サンプルファイルをコピー
            import shutil
            shutil.copy(sample_file, str(filename))
            
            self.logger.info(f"[MOCK] Generated mock audio file: {filename}")
            return True, str(filename)

        except Exception as e:
            self.logger.error(f"[MOCK] Error: {e}", exc_info=True)
            return False, None 