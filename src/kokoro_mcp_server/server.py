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
        
        # Windowsの場合はインストールをスキップするオプション    
        if platform.system().lower() == 'windows':
            try:
                # 既にインストールされているか確認
                import fugashi
                logger.info("fugashiはすでにインストールされています")
                return True
            except ImportError:
                # インストールを試みる
                pass
            
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
    if platform.system().lower() == 'windows':
        # Windows環境では通常pipを使う
        return "pip"
    elif shutil.which("uv"):
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
        try:
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
            logger.warning(f"misaki.cutletモジュールが見つかりません: {e}")
            # misakiパッケージのインストールを試みる
            try:
                pkg_manager = select_package_manager()
                if pkg_manager:
                    install_cmd = create_package_command(pkg_manager, "install", ["misaki-cutlet"])
                    subprocess.run(install_cmd, check=True)
                    logger.info("misaki-cutletのインストールに成功しました")
                    # 再度インポート試行
                    from misaki.cutlet import Cutlet
                    return apply_fugashi_patch()  # 再帰的に試行
                return False
            except Exception as e2:
                logger.warning(f"misaki-cutletのインストールに失敗しました: {e2}")
                return False
    except ImportError as e:
        logger.warning(f"Fugashiライブラリが見つからないため、パッチを適用できません: {e}")
        return False

# 引数検証関数
def validate_tts_arguments(arguments: dict) -> bool:
    """
    TTS引数を検証する
    
    Args:
        arguments: 検証する引数
        
    Returns:
        bool: 引数が有効かどうか
    """
    # 必須項目
    if "text" not in arguments or not isinstance(arguments["text"], str):
        return False
        
    # オプション項目
    if "voice" in arguments and not isinstance(arguments["voice"], str):
        return False
        
    if "speed" in arguments:
        speed = arguments["speed"]
        if not isinstance(speed, (int, float)) or speed < 0.5 or speed > 2.0:
            return False
            
    return True

# 出力ディレクトリの設定
OUTPUT_DIR = "output"
AUDIO_DIR = os.path.join(OUTPUT_DIR, "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

# 依存関係のセットアップを実行
setup_dependencies()

# サーバーの準備
mcp = FastMCP("kokoro-mcp-server")

# TTSサービスの初期化をより堅牢に
try:
    if os.getenv("MOCK_TTS", "false").lower() in ("true", "1", "yes"):
        from kokoro_mcp_server.kokoro.mock import MockKokoroTTSService
        from kokoro_mcp_server.kokoro.base import TTSRequest
        kokoro_service = MockKokoroTTSService()
        logger.info("Using MOCK TTS service")
    else:
        # 依存パッケージのインストールを試みる
        try:
            import torch
            import librosa
            import soundfile
        except ImportError:
            logger.info("必要な依存パッケージをインストールします...")
            pkg_manager = select_package_manager()
            if pkg_manager:
                packages = ["torch", "librosa", "soundfile", "numpy"]
                for package in packages:
                    try:
                        install_cmd = create_package_command(pkg_manager, "install", [package])
                        subprocess.run(install_cmd, check=True)
                        logger.info(f"{package}のインストールに成功しました")
                    except subprocess.SubprocessError as e:
                        logger.error(f"{package}のインストールに失敗しました: {e}")
            
        # KokoroTTSを使用
        from kokoro_mcp_server.kokoro.kokoro import KokoroTTSService
        from kokoro_mcp_server.kokoro.base import TTSRequest
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
        
        # 必要なパッケージをインストール
        pkg_manager = select_package_manager()
        if pkg_manager:
            packages = ["torch", "librosa", "soundfile", "numpy", "pyopenjtalk"]
            for package in packages:
                try:
                    install_cmd = create_package_command(pkg_manager, "install", [package])
                    subprocess.run(install_cmd, env=env, check=True)
                    logger.info(f"{package}のインストールに成功しました")
                except subprocess.SubprocessError as e:
                    logger.error(f"{package}のインストールに失敗しました: {e}")
        
        # 再度インポート試行
        if os.getenv("MOCK_TTS", "false").lower() in ("true", "1", "yes"):
            from kokoro_mcp_server.kokoro.mock import MockKokoroTTSService
            from kokoro_mcp_server.kokoro.base import TTSRequest
            kokoro_service = MockKokoroTTSService()
        else:
            from kokoro_mcp_server.kokoro.kokoro import KokoroTTSService
            from kokoro_mcp_server.kokoro.base import TTSRequest
            kokoro_service = KokoroTTSService()
    except Exception as e:
        logger.error(f"自動インストールにも失敗しました: {e}")
        # フォールバックとしてモックサービスを使用
        from kokoro_mcp_server.kokoro.mock import MockKokoroTTSService
        from kokoro_mcp_server.kokoro.base import TTSRequest
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

# リソースの登録
@mcp.resource("voices://available")
def get_available_voices() -> str:
    """利用可能な音声の一覧を返す"""
    voices = list_available_voices()
    return json.dumps({"voices": voices})

@mcp.resource("audio://recent")
def get_recent_audio() -> str:
    """最近生成された音声ファイルの一覧を返す"""
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

# TTSツール
@mcp.tool()
def text_to_speech(text: str, voice: str = "jf_alpha", speed: float = 1.0) -> Union[str, Image]:
    """
    テキストを音声に変換します
    
    Args:
        text: 変換するテキスト
        voice: 使用する音声ID (デフォルト: jf_alpha)
        speed: 音声の速度 (0.5〜2.0の範囲, デフォルト: 1.0)
        
    Returns:
        Union[str, Image]: 生成結果または音声データ
    """
    if not text:
        return "テキストが指定されていません"
    
    if speed < 0.5 or speed > 2.0:
        return "速度は0.5から2.0の範囲で指定してください"
    
    try:
        # TTSRequestオブジェクトを作成
        request = TTSRequest(text=text, voice=voice, speed=speed)
        
        # 音声生成
        success, file_path = kokoro_service.generate(request)
        
        if success and file_path:
            # 音声ファイルをロード
            with open(file_path, "rb") as f:
                audio_data = f.read()
                
            # ファイル名を取得
            filename = os.path.basename(file_path)
            
            # 音声データをImageオブジェクトとして返す
            return Image(
                data=audio_data,
                format="wav",
                filename=filename
            )
        else:
            return "音声の生成に失敗しました"
        
    except Exception as e:
        logger.error(f"音声生成エラー: {e}", exc_info=True)
        return f"音声の生成中にエラーが発生しました: {str(e)}"

@mcp.tool()
def list_voices() -> str:
    """
    利用可能な音声の一覧を表示します
    
    Returns:
        str: 利用可能な音声の一覧
    """
    voices = list_available_voices()
    return f"利用可能な音声:\n{', '.join(voices)}"

async def shutdown():
    """
    シャットダウン処理
    """
    logger.info("Shutting down...")
    # クリーンアップ処理を実装
    sys.exit(0)

async def main():
    """
    メイン関数。プラットフォーム依存のシグナルハンドリングを適切に処理します。
    
    Returns:
        FastMCP: MCPサーバーインスタンス
        
    Raises:
        Exception: サーバー起動時のエラー
    """
    try:
        # シグナルハンドラの設定（プラットフォーム依存）
        try:
            # UNIXシステム用のシグナルハンドラ
            for sig in (signal.SIGTERM, signal.SIGINT):
                asyncio.get_event_loop().add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))
            logger.info("Signal handlers registered successfully.")
        except (NotImplementedError, AttributeError):
            # Windowsではシグナルハンドラをスキップ
            logger.info("Signal handlers not supported on this platform, skipping.")
        
        logger.info("Starting Kokoro MCP server...")
        return mcp
        
    except Exception as e:
        logger.error(f"サーバー起動エラー: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    # asyncioのイベントループでmain関数を実行
    server = asyncio.run(main())
    if server:
        server.run()