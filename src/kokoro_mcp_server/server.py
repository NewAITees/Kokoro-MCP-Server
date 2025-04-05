"""
Kokoro MCP Server implementation - Enhanced Version
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
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl
import mcp.server.stdio
from pathlib import Path
from .kokoro.kokoro import KokoroTTSService
from .kokoro.base import TTSRequest


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

# 状態管理のための変数
generated_audio_files: List[Dict[str, Any]] = []
last_audio_file: Optional[str] = None
tts_settings: Dict[str, Any] = {"default_voice": "jf_alpha", "default_speed": 1.0}

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
    利用可能なTTSリソースの一覧を取得する
    """
    resources = [
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
        ),
        types.Resource(
            uri=AnyUrl("settings://tts"),
            name="TTS Settings",
            description="Current TTS settings",
            mimeType="application/json",
        )
    ]
    
    # 生成済み音声ファイルをリソースとして追加
    for idx, audio_file in enumerate(generated_audio_files):
        resources.append(
            types.Resource(
                uri=AnyUrl(f"audio://history/{idx}"),
                name=f"Audio File {idx}",
                description=f"Generated audio for: {audio_file.get('text', '')[:30]}...",
                mimeType="audio/wav",
            )
        )
    
    return resources

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """
    特定のリソースをURIから読み込む
    """
    if uri.scheme == "voices":
        voices = list_available_voices()
        return json.dumps({"voices": voices})
    
    elif uri.scheme == "audio":
        if uri.path and uri.path.startswith("/history/"):
            try:
                idx = int(uri.path.split("/")[-1])
                if 0 <= idx < len(generated_audio_files):
                    file_path = generated_audio_files[idx].get("file_path")
                    if file_path and os.path.exists(file_path):
                        with open(file_path, "rb") as f:
                            audio_data = base64.b64encode(f.read()).decode("utf-8")
                        return json.dumps({"audio": audio_data, "metadata": generated_audio_files[idx]})
                return json.dumps({"error": "Audio file not found"})
            except (ValueError, IndexError):
                return json.dumps({"error": "Invalid audio index"})
        
        # 最近生成された音声ファイル
        if last_audio_file and os.path.exists(last_audio_file):
            with open(last_audio_file, "rb") as f:
                audio_data = base64.b64encode(f.read()).decode("utf-8")
            return json.dumps({"audio": audio_data})
        else:
            return json.dumps({"error": "No recent audio files found"})
    
    elif uri.scheme == "settings":
        return json.dumps(tts_settings)
    
    else:
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    利用可能なTTSツールの一覧を取得する
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
        ),
        types.Tool(
            name="update-tts-settings",
            description="Update default TTS settings",
            inputSchema={
                "type": "object",
                "properties": {
                    "default_voice": {"type": "string"},
                    "default_speed": {"type": "number", "minimum": 0.5, "maximum": 2.0},
                },
            },
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    ツールの実行リクエストを処理する
    """
    global last_audio_file, tts_settings
    
    if name == "text-to-speech":
        if not arguments:
            raise ValueError("Missing arguments")
            
        text = arguments.get("text")
        voice = arguments.get("voice", tts_settings["default_voice"])
        speed = arguments.get("speed", tts_settings["default_speed"])
        
        if not validate_tts_arguments({"text": text, "voice": voice, "speed": speed}):
            raise ValueError("Invalid arguments")
            
        request = TTSRequest(text=text, voice=voice, speed=speed)
        success, file_path = tts_service.generate(request)
        
        if success and file_path:
            # 生成された音声ファイルを状態として記録
            audio_metadata = {
                "text": text,
                "voice": voice,
                "speed": speed,
                "file_path": file_path,
                "timestamp": asyncio.get_event_loop().time()
            }
            generated_audio_files.append(audio_metadata)
            last_audio_file = file_path
            
            # クライアントに状態変更を通知
            await server.request_context.session.send_resource_list_changed()
            
            with open(file_path, "rb") as f:
                audio_data = base64.b64encode(f.read()).decode("utf-8")
            return [types.ImageContent(type="image", data=audio_data)]
        else:
            raise ValueError("Failed to generate audio")
            
    elif name == "list-voices":
        voices = list_available_voices()
        return [types.TextContent(type="text", text=json.dumps({"voices": voices}))]
        
    elif name == "update-tts-settings":
        if not arguments:
            raise ValueError("Missing arguments")
            
        # 設定の更新
        if "default_voice" in arguments:
            tts_settings["default_voice"] = arguments["default_voice"]
        
        if "default_speed" in arguments:
            speed = arguments["default_speed"]
            if not isinstance(speed, (int, float)) or speed < 0.5 or speed > 2.0:
                raise ValueError("Speed must be a number between 0.5 and 2.0")
            tts_settings["default_speed"] = speed
            
        # 設定変更を通知
        await server.request_context.session.send_resource_list_changed()
        
        return [types.TextContent(type="text", text=json.dumps({"message": "Settings updated", "settings": tts_settings}))]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    """
    利用可能なプロンプトの一覧を取得する
    """
    return [
        types.Prompt(
            name="tts-recommendation",
            description="Recommend appropriate TTS settings for a given text",
            arguments=[
                types.PromptArgument(
                    name="text",
                    description="Text to analyze for TTS recommendation",
                    required=True,
                ),
                types.PromptArgument(
                    name="tone",
                    description="Desired tone (casual/formal/emotional)",
                    required=False,
                )
            ],
        ),
        types.Prompt(
            name="analyze-audio-history",
            description="Analyze previous TTS usage patterns",
            arguments=[],
        )
    ]

@server.get_prompt()
async def handle_get_prompt(
    name: str, arguments: dict[str, str] | None
) -> types.GetPromptResult:
    """
    特定のプロンプトを取得する
    """
    if name == "tts-recommendation":
        if not arguments or "text" not in arguments:
            raise ValueError("Missing required 'text' argument")
            
        text = arguments.get("text", "")
        tone = arguments.get("tone", "casual")
        
        return types.GetPromptResult(
            description="Recommend TTS settings for the given text",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"""Please analyze this text and recommend the best TTS settings for it.
                        
Text to synthesize: "{text}"

Desired tone: {tone}

Available voices: {list_available_voices()}

Please recommend:
1. Which voice would be most appropriate
2. The optimal speech speed (between 0.5 and 2.0)
3. Any specific pronunciation considerations
4. How to break the text into natural speaking segments if it's long

Base your recommendations on the content, intended tone, and best practices for speech synthesis.""",
                    ),
                )
            ],
        )
        
    elif name == "analyze-audio-history":
        history_text = ""
        for idx, audio in enumerate(generated_audio_files[-10:]):  # 最新の10件を取得
            history_text += f"{idx+1}. Text: \"{audio.get('text', '')[:50]}...\"\n"
            history_text += f"   Voice: {audio.get('voice')}, Speed: {audio.get('speed')}\n\n"
            
        return types.GetPromptResult(
            description="Analyze TTS usage patterns",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"""Please analyze my recent TTS usage patterns and provide insights.

Recent TTS history:
{history_text}

Based on this history, please provide:
1. Common patterns in my text content
2. My preferred voice and speed settings
3. Recommendations for optimizing my TTS usage
4. Suggested new features that might benefit my workflow

Also, what could be improved about my text formatting to achieve better speech synthesis results?""",
                    ),
                )
            ],
        )
    
    else:
        raise ValueError(f"Unknown prompt: {name}")

async def main():
    """メインの実行関数"""
    try:
        print("=" * 50, file=sys.stderr)
        print("server.py: main関数が呼び出されました", file=sys.stderr)
        print("=" * 50, file=sys.stderr)
        
        # サーバーをstdin/stdoutストリームで実行
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
            
    except Exception as e:
        print(f"サーバー初期化エラー: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)