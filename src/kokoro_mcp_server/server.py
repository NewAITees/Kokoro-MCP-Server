"""
Kokoro MCP Server implementation
"""

import os
import json
import logging
import asyncio
import base64
import subprocess
import sys
import platform
import shutil
import signal
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP, Context, Image
from pathlib import Path
from .kokoro.kokoro import KokoroTTSService
from .kokoro.base import TTSRequest


# 環境変数の読み込み
load_dotenv()

# ログの準備
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kokoro-mcp-server")

# MeCab関連の環境変数設定
if os.path.exists('/usr/lib/x86_64-linux-gnu/mecab/etc/mecabrc'):
    os.environ['MECABRC'] = '/usr/lib/x86_64-linux-gnu/mecab/etc/mecabrc'
elif os.path.exists('/usr/local/etc/mecabrc'):
    os.environ['MECABRC'] = '/usr/local/etc/mecabrc'
elif os.path.exists('/etc/mecabrc'):
    os.environ['MECABRC'] = '/etc/mecabrc'

# fugashiのフォールバック設定
os.environ['FUGASHI_ENABLE_FALLBACK'] = '1'

# TTSサービスの初期化
tts_service = KokoroTTSService()

# MCPサーバーの設定
mcp = FastMCP(
    name="kokoro-mcp-server",
    description="AI アシスタントと連携し、テキストを高品質な音声に変換する MCP サーバー"
)

def validate_tts_arguments(arguments: dict) -> bool:
    """
    TTSの引数を検証する
    
    Args:
        arguments: 検証する引数の辞書
        
    Returns:
        bool: 引数が有効かどうか
    """
    required_args = ['text']
    for arg in required_args:
        if arg not in arguments:
            logger.error(f"必須の引数が不足しています: {arg}")
            return False
            
    if not isinstance(arguments['text'], str):
        logger.error("textは文字列である必要があります")
        return False
        
    if 'voice' in arguments and not isinstance(arguments['voice'], str):
        logger.error("voiceは文字列である必要があります")
        return False
        
    if 'speed' in arguments:
        speed = arguments['speed']
        if not isinstance(speed, (int, float)) or speed <= 0:
            logger.error("speedは正の数値である必要があります")
            return False
            
    return True

def list_available_voices() -> List[str]:
    """
    利用可能な音声の一覧を取得する
    
    Returns:
        List[str]: 利用可能な音声のリスト
    """
    return ["jf_alpha"]

@mcp.resource("voices://available")
def get_available_voices() -> str:
    """利用可能な音声の一覧をJSON形式で返す"""
    voices = list_available_voices()
    return json.dumps({"voices": voices})

@mcp.resource("audio://recent")
def get_recent_audio() -> str:
    """最近生成された音声ファイルのパスを返す"""
    audio_dir = Path("output/audio")
    if not audio_dir.exists():
        return json.dumps({"error": "No audio files found"})
        
    files = sorted(audio_dir.glob("*.wav"), key=lambda x: x.stat().st_mtime, reverse=True)
    if not files:
        return json.dumps({"error": "No audio files found"})
        
    with open(files[0], "rb") as f:
        audio_data = base64.b64encode(f.read()).decode("utf-8")
    return json.dumps({"audio": audio_data})

@mcp.tool()
def text_to_speech(text: str, voice: str = "jf_alpha", speed: float = 1.0) -> Union[str, Image]:
    """
    テキストを音声に変換する
    
    Args:
        text: 変換するテキスト
        voice: 使用する音声（デフォルト: "jf_alpha"）
        speed: 音声の速度（デフォルト: 1.0）
        
    Returns:
        Union[str, Image]: 生成された音声ファイルのパスまたはエラーメッセージ
    """
    try:
        # 引数の検証
        if not validate_tts_arguments({"text": text, "voice": voice, "speed": speed}):
            return "Invalid arguments"
            
        # TTSリクエストの作成
        request = TTSRequest(text=text, voice=voice, speed=speed)
        
        # 音声生成
        success, file_path = tts_service.generate(request)
        
        if success and file_path:
            # 音声ファイルを読み込んでbase64エンコード
            with open(file_path, "rb") as f:
                audio_data = base64.b64encode(f.read()).decode("utf-8")
            return Image(audio_data)
        else:
            logger.error("音声生成に失敗しました")
            return "Failed to generate audio"
        
    except Exception as e:
        logger.error(f"音声生成エラー: {e}", exc_info=True)
        return f"Error: {str(e)}"

@mcp.tool()
def list_voices() -> str:
    """
    利用可能な音声の一覧を取得する
    
    Returns:
        str: 音声の一覧（JSON形式）
    """
    voices = list_available_voices()
    return json.dumps({"voices": voices})

async def shutdown():
    """シャットダウン時の処理"""
    logger.info("シャットダウンを開始します...")
    # クリーンアップ処理をここに追加
    logger.info("シャットダウンが完了しました")

async def main():
    """メインの実行関数"""
    try:
        # シグナルハンドラの設定
        for sig in (signal.SIGTERM, signal.SIGINT):
            asyncio.get_event_loop().add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown()))
            
        logger.info("MCPサーバーを起動します...")
        return mcp
        
    except Exception as e:
        logger.error(f"サーバー初期化エラー: {e}", exc_info=True)
        return None

if __name__ == "__main__":
    # asyncioのイベントループでmain関数を実行
    server = asyncio.run(main())
    if server:
        server.run()