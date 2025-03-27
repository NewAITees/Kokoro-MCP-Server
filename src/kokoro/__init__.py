"""Kokoro音声合成エンジン連携モジュール"""

import os
from typing import Union
from .mock import MockKokoroEngine

def create_engine(mock: bool = None) -> Union[MockKokoroEngine, 'KokoroEngine']:
    """
    音声合成エンジンのインスタンスを作成

    Args:
        mock (bool, optional): モックモードを強制的に有効/無効にする
            Noneの場合は環境変数 MOCK_TTS に従う

    Returns:
        Union[MockKokoroEngine, KokoroEngine]: 音声合成エンジンのインスタンス
    """
    # モックモードの判定
    use_mock = mock if mock is not None else os.getenv('MOCK_TTS', 'false').lower() == 'true'

    if use_mock:
        return MockKokoroEngine()
    else:
        # TODO: 実際のKokoroエンジンの実装
        # from .engine import KokoroEngine
        # return KokoroEngine()
        return MockKokoroEngine()  # 一時的に常にモックを返す 