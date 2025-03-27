#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VoiceStudio MCP Server
メインエントリーポイント
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

import click
from dotenv import load_dotenv
from loguru import logger

from config import Config
from server.websocket import MCPWebSocketServer

# 環境変数の読み込み
load_dotenv()

@click.command()
@click.option('--host', default=None, help='Server host')
@click.option('--port', default=None, help='Server port')
@click.option('--debug/--no-debug', default=None, help='Enable debug mode')
async def main(host: Optional[str], port: Optional[int], debug: Optional[bool]) -> None:
    """
    VoiceStudio MCP Server メインエントリーポイント
    
    Args:
        host (Optional[str]): サーバーのホストアドレス
        port (Optional[int]): サーバーのポート番号
        debug (Optional[bool]): デバッグモードの有効/無効
    """
    # 設定の読み込み
    config = Config.from_env()
    
    # コマンドライン引数で上書き
    if host is not None:
        config.server.host = host
    if port is not None:
        config.server.port = port
    if debug is not None:
        config.server.debug = debug
    
    # ロギングの設定
    log_level = logging.DEBUG if config.server.debug else logging.INFO
    logger.remove()
    logger.add(
        str(config.log.file_path),
        rotation=config.log.rotation,
        retention=config.log.retention,
        level=config.log.level
    )
    logger.add(lambda msg: print(msg), level=config.log.level)
    
    # ログディレクトリの作成
    config.log.file_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting VoiceStudio MCP Server on {config.server.host}:{config.server.port}")
    
    try:
        # WebSocketサーバーの初期化と起動
        server = MCPWebSocketServer(
            host=config.server.host,
            port=config.server.port
        )
        await server.start()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        await server.stop()
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise

if __name__ == '__main__':
    # Windows環境でもuvloopを使用可能な場合は使用
    try:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    except ImportError:
        pass
    
    asyncio.run(main())