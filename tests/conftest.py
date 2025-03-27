"""
テストのヘルパー関数とフィクスチャ
"""

import os
import pytest
import asyncio
import uvicorn
from pathlib import Path
from typing import AsyncGenerator, Generator, Dict, Any
from fastapi import FastAPI
from httpx import AsyncClient

from src.config import Config
from src.server.mcp import MCPServer

@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """テスト用の設定"""
    return {
        "host": "localhost",
        "port": 8888,
        "debug": True,
        "log_dir": "logs",
        "context_ttl": 3600,
        "cleanup_interval": 60
    }

@pytest.fixture(scope="session")
def event_loop():
    """イベントループのフィクスチャ"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def app(test_config: Dict[str, Any]) -> AsyncGenerator[FastAPI, None]:
    """FastAPIアプリケーションのフィクスチャ"""
    server = MCPServer(test_config)
    await server.startup()
    yield server.app
    await server.shutdown()

@pytest.fixture
async def running_app(app: FastAPI, test_config):
    """
    WebSocketのURLを生成
    """
    config = uvicorn.Config(
        app=app,
        host=test_config["host"],
        port=test_config["port"],
        loop="asyncio",
        log_level="error"
    )
    server = uvicorn.Server(config=config)
    await server.startup()
    yield app
    await server.shutdown()

@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """
    テスト用の非同期HTTPクライアント
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def websocket_url(test_config: Dict[str, Any]) -> str:
    """WebSocketのURLを生成"""
    return f"ws://{test_config['host']}:{test_config['port']}/mcp"

@pytest.fixture
def test_context_data() -> dict:
    """
    テスト用のコンテキストデータ
    """
    return {
        "context_id": "test-context",
        "content": {"key": "value"},
        "scope": "session"
    }

@pytest.fixture
def test_function_data() -> dict:
    """
    テスト用の関数呼び出しデータ
    """
    return {
        "name": "test_function",
        "arguments": {"arg1": "value1", "arg2": "value2"}
    } 