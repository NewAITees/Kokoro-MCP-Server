"""
モックTTSサービス
"""

import os
import random
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from .base import BaseTTSService, TTSRequest

logger = logging.getLogger(__name__)

class MockKokoroTTSService(BaseTTSService):
    """モックTTSサービス"""
    
    def __init__(self):
        """初期化"""
        self.logger = logger
        
        # サンプル音声ファイルのパス
        self.sample_files = [
            os.path.join(os.path.dirname(__file__), "samples", f"sample{i}.wav")
            for i in range(1, 4)
        ]
        
        # サンプルディレクトリの作成
        sample_dir = os.path.join(os.path.dirname(__file__), "samples")
        os.makedirs(sample_dir, exist_ok=True)
        
        # サンプルファイルの作成（存在しない場合）
        for sample_file in self.sample_files:
            if not os.path.exists(sample_file):
                self._create_dummy_wav(sample_file)
    
    def _create_dummy_wav(self, file_path: str):
        """
        ダミーのWAVファイルを作成する
        
        Args:
            file_path: 作成するファイルのパス
        """
        import numpy as np
        import soundfile as sf
        
        # 1秒のサイン波を生成
        sample_rate = 44100
        t = np.linspace(0, 1, sample_rate)
        data = np.sin(2 * np.pi * 440 * t)  # 440Hz
        
        # WAVファイルとして保存
        sf.write(file_path, data, sample_rate)
    
    def generate(self, request: TTSRequest) -> Tuple[bool, Optional[str]]:
        """
        音声を生成する
        
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