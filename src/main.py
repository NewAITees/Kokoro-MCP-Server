#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VoiceStudio MCP サーバーのメインエントリーポイント
"""

import os
import sys
import click
import uvicorn
from pathlib import Path

from .config import Config
from .server.mcp import MCPServer
from .utils.logging import setup_logging

def run_server(
    host: str,
    port: int,
    debug: bool = False,
    workers: int = 1,
    log_dir: Path = None,
    ssl_cert: Path = None,
    ssl_key: Path = None
) -> None:
    """
    サーバーの実行
    
    Args:
        host (str): ホスト名
        port (int): ポート番号
        debug (bool, optional): デバッグモードの有効/無効
        workers (int, optional): ワーカープロセス数
        log_dir (Path, optional): ログディレクトリ
        ssl_cert (Path, optional): SSLサーバー証明書のパス
        ssl_key (Path, optional): SSLサーバー秘密鍵のパス
    """
    # ロギングの設定
    setup_logging(log_dir=log_dir, debug=debug)
    
    # サーバーの初期化
    server = MCPServer()
    
    # uvicornの設定
    config = {
        "app": server.get_app(),
        "host": host,
        "port": port,
        "reload": debug,
        "workers": workers if not debug else 1,
        "log_level": "debug" if debug else "info",
        "loop": "uvloop" if sys.platform != "win32" else "asyncio",
        "timeout_keep_alive": 60,
        "ws_ping_interval": 20,
        "ws_ping_timeout": 20,
    }
    
    # SSL設定の追加（指定された場合）
    if ssl_cert is not None and ssl_key is not None:
        config.update({
            "ssl_keyfile": str(ssl_key),
            "ssl_certfile": str(ssl_cert)
        })
    
    # サーバーの起動
    uvicorn.run(**config)

@click.command()
@click.option("--host", help="サーバーのホスト名")
@click.option("--port", type=int, help="サーバーのポート番号")
@click.option("--debug", is_flag=True, help="デバッグモードの有効化")
@click.option("--workers", type=int, help="ワーカープロセス数")
@click.option("--log-dir", type=click.Path(path_type=Path), help="ログディレクトリ")
@click.option("--ssl-cert", type=click.Path(exists=True, path_type=Path), help="SSLサーバー証明書のパス")
@click.option("--ssl-key", type=click.Path(exists=True, path_type=Path), help="SSLサーバー秘密鍵のパス")
def main(
    host: str = None,
    port: int = None,
    debug: bool = None,
    workers: int = None,
    log_dir: Path = None,
    ssl_cert: Path = None,
    ssl_key: Path = None
) -> None:
    """VoiceStudio MCP サーバー"""
    # 設定の読み込み
    config = Config.load()
    
    # コマンドライン引数で上書き
    if host is not None:
        config.server.host = host
    if port is not None:
        config.server.port = port
    if debug is not None:
        config.server.debug = debug
    if workers is not None:
        config.server.workers = workers
    if log_dir is not None:
        config.server.log_dir = log_dir
    if ssl_cert is not None:
        config.server.ssl_cert = ssl_cert
    if ssl_key is not None:
        config.server.ssl_key = ssl_key
    
    # サーバーの実行
    run_server(
        host=config.server.host,
        port=config.server.port,
        debug=config.server.debug,
        workers=config.server.workers,
        log_dir=config.server.log_dir,
        ssl_cert=config.server.ssl_cert,
        ssl_key=config.server.ssl_key
    )

if __name__ == "__main__":
    main() 