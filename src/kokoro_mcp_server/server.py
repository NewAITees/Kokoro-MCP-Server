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
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl
import mcp.server.stdio
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
server = Server("kokoro-mcp-server")

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

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """
    List available TTS resources.
    """
    return [
        types.Resource(
            uri=AnyUrl("voices://available"),
            name="Available Voices",
            description="List of available TTS voices",
            mimeType="application/json",
        ),
        types.Resource(
            uri=AnyUrl("audio://recent"),
            name="Recent Audio",
            description="Most recently generated audio file",
            mimeType="audio/wav",
        )
    ]

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """
    Read a specific resource by its URI.
    """
    if uri.scheme == "voices":
        voices = list_available_voices()
        return json.dumps({"voices": voices})
    elif uri.scheme == "audio":
        audio_dir = Path("output/audio")
        if not audio_dir.exists():
            return json.dumps({"error": "No audio files found"})
            
        files = sorted(audio_dir.glob("*.wav"), key=lambda x: x.stat().st_mtime, reverse=True)
        if not files:
            return json.dumps({"error": "No audio files found"})
            
        with open(files[0], "rb") as f:
            audio_data = base64.b64encode(f.read()).decode("utf-8")
        return json.dumps({"audio": audio_data})
    else:
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available TTS tools.
    """
    return [
        types.Tool(
            name="text-to-speech",
            description="Convert text to speech",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "voice": {"type": "string", "default": "jf_alpha"},
                    "speed": {"type": "number", "default": 1.0},
                },
                "required": ["text"],
            },
        ),
        types.Tool(
            name="list-voices",
            description="List available voices",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests.
    """
    if name == "text-to-speech":
        if not arguments:
            raise ValueError("Missing arguments")
            
        text = arguments.get("text")
        voice = arguments.get("voice", "jf_alpha")
        speed = arguments.get("speed", 1.0)
        
        if not validate_tts_arguments({"text": text, "voice": voice, "speed": speed}):
            raise ValueError("Invalid arguments")
            
        request = TTSRequest(text=text, voice=voice, speed=speed)
        success, file_path = tts_service.generate(request)
        
        if success and file_path:
            with open(file_path, "rb") as f:
                audio_data = base64.b64encode(f.read()).decode("utf-8")
            return [types.ImageContent(type="image", data=audio_data)]
        else:
            raise ValueError("Failed to generate audio")
            
    elif name == "list-voices":
        voices = list_available_voices()
        return [types.TextContent(type="text", text=json.dumps({"voices": voices}))]
    else:
        raise ValueError(f"Unknown tool: {name}")

async def shutdown():
    """シャットダウン時の処理"""
    logger.info("シャットダウンを開始します...")
    # クリーンアップ処理をここに追加
    logger.info("シャットダウンが完了しました")

async def main():
    """メインの実行関数"""
    try:
        print("=" * 50, file=sys.stderr)
        print("server.py: main関数が呼び出されました", file=sys.stderr)
        print("=" * 50, file=sys.stderr)
        
        # Run the server using stdin/stdout streams
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="kokoro-mcp-server",
                    server_version="0.1.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
            
        # シグナルハンドラの設定
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                asyncio.get_event_loop().add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown()))
            except Exception as e:
                print(f"シグナルハンドラの設定に失敗しました: {e}", file=sys.stderr)
                
        print("MCPサーバーを起動します...", file=sys.stderr)
        return server
        
    except Exception as e:
        print(f"サーバー初期化エラー: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return None

if __name__ == "__main__":
    # asyncioのイベントループでmain関数を実行
    server = asyncio.run(main())
    if server:
        server.run()