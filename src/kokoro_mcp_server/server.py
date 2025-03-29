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
from typing import Any, Dict, List, Optional, Sequence, Tuple
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
from pathlib import Path

# 環境変数の読み込み
load_dotenv()

# ログの準備
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kokoro-mcp-server")

# 自動セットアップ関数
def setup_dependencies() -> bool:
    """
    必要な依存関係を自動的にセットアップする関数
    
    Returns:
        bool: セットアップが成功したかどうか
    """
    logger.info("依存関係の自動セットアップを開始します...")
    
    success = True
    success &= setup_mecab()
    success &= setup_fugashi()
    success &= apply_fugashi_patch()
    
    logger.info("依存関係の自動セットアップが完了しました")
    return success

def setup_mecab() -> bool:
    """
    MeCabのセットアップを行う
    
    Returns:
        bool: セットアップが成功したかどうか
    """
    os_name = platform.system().lower()
    if os_name != 'linux':
        logger.warning(f"未サポートのOS: {os_name}")
        return False
        
    mecabrc_path = find_mecab_config()
    if not mecabrc_path:
        mecabrc_path = install_mecab()
        
    if not mecabrc_path:
        logger.error("MeCabのセットアップに失敗しました")
        return False
        
    return create_mecab_symlink(mecabrc_path)

def find_mecab_config() -> Optional[str]:
    """
    MeCabの設定ファイルを探索する
    
    Returns:
        Optional[str]: 設定ファイルのパス。見つからない場合はNone
    """
    possible_paths = [
        '/etc/mecabrc',
        '/usr/local/etc/mecabrc',
        '/usr/lib/x86_64-linux-gnu/mecab/etc/mecabrc',
        '/usr/share/mecab/mecabrc'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"MeCabの設定ファイルを発見: {path}")
            return path
    return None

def install_mecab() -> Optional[str]:
    """
    MeCabとIPAdicをインストールする
    
    Returns:
        Optional[str]: インストール後の設定ファイルのパス。失敗時はNone
    """
    try:
        logger.info("MeCabとIPAdicをインストールします...")
        subprocess.run(["sudo", "apt-get", "update"], check=True)
        subprocess.run(
            ["sudo", "apt-get", "install", "-y", "mecab", "libmecab-dev", "mecab-ipadic-utf8"],
            check=True
        )
        return find_mecab_config()
    except subprocess.SubprocessError as e:
        logger.error(f"MeCabのインストールに失敗しました: {e}")
        return None

def create_mecab_symlink(mecabrc_path: str) -> bool:
    """
    MeCabの設定ファイルのシンボリックリンクを作成する
    
    Args:
        mecabrc_path: 設定ファイルのパス
        
    Returns:
        bool: 成功したかどうか
    """
    os.environ['MECABRC'] = mecabrc_path
    
    if os.path.exists('/usr/local/etc/mecabrc'):
        return True
        
    try:
        os.makedirs('/usr/local/etc', exist_ok=True)
        try:
            os.symlink(mecabrc_path, '/usr/local/etc/mecabrc')
        except PermissionError:
            subprocess.run(
                ["sudo", "ln", "-sf", mecabrc_path, "/usr/local/etc/mecabrc"],
                check=True
            )
        logger.info("MeCabの設定ファイルのシンボリックリンクを作成しました")
        return True
    except (OSError, subprocess.SubprocessError) as e:
        logger.error(f"シンボリックリンクの作成に失敗しました: {e}")
        return False

def setup_fugashi() -> bool:
    """
    fugashiと関連する日本語辞書をセットアップする
    
    Returns:
        bool: セットアップが成功したかどうか
    """
    try:
        logger.info("fugashiと関連パッケージをインストールします...")
        
        # パッケージマネージャの選択
        pkg_manager = select_package_manager()
        if not pkg_manager:
            return False
            
        # 既存のパッケージをアンインストール
        uninstall_cmd = create_package_command(pkg_manager, "uninstall", ["fugashi", "ipadic"])
        subprocess.run(uninstall_cmd, stderr=subprocess.PIPE)
        
        # 必要なパッケージをインストール
        packages = ["fugashi[unidic]", "unidic-lite", "ipadic"]
        for package in packages:
            try:
                install_cmd = create_package_command(pkg_manager, "install", [package])
                subprocess.run(install_cmd, check=True)
            except subprocess.SubprocessError as e:
                if package == "ipadic":
                    logger.info("ipadicのインストールに失敗しましたが、unidic-liteが利用可能です")
                else:
                    raise e
        
        # GenericTaggerのフォールバックを有効化
        os.environ['FUGASHI_ENABLE_FALLBACK'] = '1'
        
        logger.info("日本語辞書とfugashiのインストールが完了しました")
        return True
        
    except subprocess.SubprocessError as e:
        logger.error(f"fugashiと辞書のインストールに失敗しました: {e}")
        return False

def select_package_manager() -> Optional[str]:
    """
    利用可能なパッケージマネージャを選択する
    
    Returns:
        Optional[str]: 選択されたパッケージマネージャ。見つからない場合はNone
    """
    if shutil.which("uv"):
        return "uv"
    elif shutil.which("pip"):
        return "pip"
    else:
        logger.error("利用可能なパッケージマネージャが見つかりません")
        return None

def create_package_command(manager: str, action: str, packages: list[str]) -> list[str]:
    """
    パッケージ管理コマンドを生成する
    
    Args:
        manager: パッケージマネージャ名
        action: 実行するアクション（install/uninstall）
        packages: パッケージ名のリスト
    
    Returns:
        list[str]: 実行コマンドのリスト
    """
    if manager == "uv":
        return ["uv", "pip", action] + (["-y"] if action == "uninstall" else []) + packages
    else:  # pip
        return [sys.executable, "-m", "pip", action] + (["-y"] if action == "uninstall" else []) + packages

def apply_fugashi_patch() -> bool:
    """
    Fugashiライブラリにパッチを適用する
    
    Returns:
        bool: パッチの適用が成功したかどうか
    """
    try:
        # 必要なモジュールのインポート
        import fugashi
        from misaki.cutlet import Cutlet
        
        # Cutletクラスをモンキーパッチ
        old_init = Cutlet.__init__
        
        def patched_init(self, *args, **kwargs):
            try:
                from fugashi import GenericTagger
                self.tagger = GenericTagger('-Owakati')
                logger.info("GenericTaggerを使用して初期化しました")
            except Exception as e:
                logger.warning(f"GenericTaggerの初期化に失敗しました: {e}")
                old_init(self, *args, **kwargs)
        
        Cutlet.__init__ = patched_init
        logger.info("Cutletクラスにパッチを適用しました")
        return True
        
    except ImportError as e:
        logger.warning(f"Fugashiライブラリが見つからないため、パッチを適用できません: {e}")
        return False

# 出力ディレクトリの設定
OUTPUT_DIR = "output"
AUDIO_DIR = os.path.join(OUTPUT_DIR, "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

# 依存関係のセットアップを実行
setup_dependencies()

# サーバの準備
app = Server("kokoro-mcp-server")

# TTSサービスの初期化をより堅牢に
try:
    if os.getenv("MOCK_TTS", "false").lower() in ("true", "1", "yes"):
        from kokoro_mcp_server.kokoro.mock import MockKokoroTTSService
        kokoro_service = MockKokoroTTSService()
        logger.info("Using MOCK TTS service")
    else:
        from kokoro_mcp_server.kokoro.kokoro import KokoroTTSService
        kokoro_service = KokoroTTSService()
        logger.info("Using real Kokoro TTS service")
except ImportError as e:
    logger.error(f"TTSサービスの初期化に失敗しました: {e}")
    logger.info("必要なパッケージをインストールします...")
    
    # PyOpenJTalkのインストールに失敗した場合の対応
    try:
        # 環境変数を設定してインストール
        env = os.environ.copy()
        env['CMAKE_POLICY_VERSION_MINIMUM'] = '3.5'
        subprocess.run([sys.executable, "-m", "pip", "install", "pyopenjtalk"], env=env, check=True)
        
        # 再度インポート試行
        if os.getenv("MOCK_TTS", "false").lower() in ("true", "1", "yes"):
            from kokoro_mcp_server.kokoro.mock import MockKokoroTTSService
            kokoro_service = MockKokoroTTSService()
        else:
            from kokoro_mcp_server.kokoro.kokoro import KokoroTTSService
            kokoro_service = KokoroTTSService()
    except Exception as e:
        logger.error(f"自動インストールにも失敗しました: {e}")
        # フォールバックとしてモックサービスを使用
        from kokoro_mcp_server.kokoro.mock import MockKokoroTTSService
        kokoro_service = MockKokoroTTSService()
        logger.warning("TTSサービスの初期化に失敗したため、MOCKサービスを使用します")

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
    try:
        # 引数の型チェックを追加
        if not isinstance(arguments, dict):
            return [TextContent(text="Invalid arguments format")]
            
        if name == "text_to_speech":
            # 引数のバリデーションを追加
            if not validate_tts_arguments(arguments):
                return [TextContent(text="Invalid arguments for text_to_speech")]
                
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
    except Exception as e:
        logger.error(f"ツール呼び出しエラー: {e}", exc_info=True)
        return [TextContent(text=f"ツール呼び出しエラー: {str(e)}")]

async def main():
    """
    メイン関数。
    """
    try:
        # シグナルハンドラの設定を追加
        for sig in (signal.SIGTERM, signal.SIGINT):
            asyncio.get_event_loop().add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))
        
        # 初期化オプション
        initialization_options = {
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "max_audio_size": int(os.getenv("MAX_AUDIO_SIZE", "10485760"))  # 10MB
        }
        
        logger.info("Starting MCP server...")
        
        # 最新のMCP SDKに対応するためのstdio_server関数を使用
        from mcp.server.stdio import stdio_server
        
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                initialization_options
            )
    except Exception as e:
        logger.error(f"サーバー起動エラー: {e}", exc_info=True)
        sys.exit(1)

async def shutdown():
    """
    シャットダウン処理
    """
    logger.info("Shutting down...")
    # クリーンアップ処理を実装
    sys.exit(0)

if __name__ == "__main__":
    # asyncioのイベントループでmain関数を実行
    asyncio.run(main())