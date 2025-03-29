import os
import json
import logging
import asyncio
import base64
from typing import Any, Dict, List, Optional, Sequence
from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource
)
from pydantic import AnyUrl

# 環境変数の読み込み
load_dotenv()

# ログの準備
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voicestudio-server")

# 出力ディレクトリの設定
OUTPUT_DIR = "output"
AUDIO_DIR = os.path.join(OUTPUT_DIR, "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

# サーバの準備
app = Server("voicestudio-server")

# TTSサービスの初期化
if os.getenv("MOCK_TTS", "false").lower() in ("true", "1", "yes"):
    from kokoro_mcp_server.kokoro.mock import MockKokoroTTSService
    kokoro_service = MockKokoroTTSService()
    logger.info("Using MOCK TTS service")
else:
    from kokoro_mcp_server.kokoro.kokoro import KokoroTTSService
    kokoro_service = KokoroTTSService()
    logger.info("Using real Kokoro TTS service")

# 利用可能な音声の一覧を取得する関数
def list_available_voices() -> List[str]:
    """
    利用可能な音声の一覧を取得する関数。
    
    Returns:
        List[str]: 音声IDのリスト
    """
    # 現在は固定の音声リストを返す
    return ["jf_alpha", "jf_beta", "jf_gamma"]

# 利用可能なリソース一覧の取得
@app.list_resources()
async def list_resources() -> list[Resource]:
    resources = []
    
    # 音声リソース
    resources.extend([
        Resource(
            uri=AnyUrl("voicestudio://voices/all"),
            name="Available Voices",
            mimeType="application/json",
            description="List of all available voices"
        ),
        Resource(
            uri=AnyUrl("voicestudio://audio/recent"),
            name="Recent Audio Files",
            mimeType="application/json",
            description="List of recently generated audio files"
        )
    ])
    
    return resources

# リソースの読み込み
@app.read_resource()
async def read_resource(uri: AnyUrl) -> str:
    """
    リソースの内容を読み込む関数。
    
    Args:
        uri: リソースのURI
        
    Returns:
        str: リソースの内容（JSON形式）
    """
    if uri.path == "/voices/all":
        return json.dumps({"voices": list_available_voices()})
    elif uri.path == "/audio/recent":
        # 最近生成された音声ファイルの一覧を取得
        audio_files = []
        for file in os.listdir(AUDIO_DIR):
            if file.endswith(".wav"):
                file_path = os.path.join(AUDIO_DIR, file)
                audio_files.append({
                    "name": file,
                    "path": file_path,
                    "created": os.path.getctime(file_path)
                })
        return json.dumps({"audio_files": sorted(audio_files, key=lambda x: x["created"], reverse=True)})
    else:
        raise ValueError(f"Unknown resource URI: {uri}")

# 利用可能なツール一覧の取得
@app.list_tools()
async def list_tools() -> list[Tool]:
    """
    利用可能なツールの一覧を取得する関数。
    
    Returns:
        list[Tool]: ツールのリスト
    """
    return [
        Tool(
            name="text_to_speech",
            description="テキストを音声に変換します",
            parameters={
                "text": {"type": "string", "description": "変換するテキスト"},
                "voice": {"type": "string", "description": "使用する音声ID", "optional": True},
                "speed": {"type": "number", "description": "音声の速度（0.5〜2.0）", "optional": True}
            }
        ),
        Tool(
            name="list_voices",
            description="利用可能な音声の一覧を表示します",
            parameters={}
        )
    ]

# ツールの呼び出し
@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """
    ツールを呼び出す関数。
    
    Args:
        name: ツール名
        arguments: 引数
        
    Returns:
        Sequence[TextContent | ImageContent | EmbeddedResource]: ツールの実行結果
    """
    if name == "text_to_speech":
        text = arguments.get("text", "")
        voice = arguments.get("voice", "jf_alpha")
        speed = arguments.get("speed", 1.0)
        
        if not text:
            return [TextContent(text="テキストが指定されていません")]
        
        try:
            # 音声生成
            success, file_path = kokoro_service.generate({
                "text": text,
                "voice": voice,
                "speed": speed
            })
            
            if success and file_path:
                # 音声ファイルをBase64エンコード
                with open(file_path, "rb") as f:
                    audio_data = base64.b64encode(f.read()).decode("utf-8")
                
                return [
                    TextContent(text=f"音声を生成しました：\nファイル: {os.path.basename(file_path)}"),
                    EmbeddedResource(
                        uri=AnyUrl(f"file://{file_path}"),
                        mimeType="audio/wav",
                        data=audio_data
                    )
                ]
            else:
                return [TextContent(text="音声の生成に失敗しました")]
                
        except Exception as e:
            logger.error(f"音声生成エラー: {e}", exc_info=True)
            return [TextContent(text=f"音声の生成中にエラーが発生しました: {str(e)}")]
            
    elif name == "list_voices":
        voices = list_available_voices()
        return [TextContent(text=f"利用可能な音声:\n{', '.join(voices)}")]
    else:
        return [TextContent(text=f"不明なツール: {name}")]

async def main():
    """
    メイン関数。
    """
    # サーバーの起動
    await app.run()

if __name__ == "__main__":
    # asyncioのイベントループでmain関数を実行
    asyncio.run(main())