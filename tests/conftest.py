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
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """イベントループのフィクスチャ"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def app(test_config: Dict[str, Any]) -> AsyncGenerator[FastAPI, None]:
    """FastAPIアプリケーションのフィクスチャ"""
    server = MCPServer(test_config)
    yield server.app

@pytest.fixture
async def running_app(test_config: Dict[str, Any]) -> AsyncGenerator[FastAPI, None]:
    """実行中のFastAPIアプリケーションのフィクスチャ"""
    server = MCPServer(test_config)
    
    # テスト用の関数を登録
    async def test_function(param1: str) -> dict:
        return {"param1": param1}
    server.register_function("test_function", test_function)
    
    await server.startup()
    yield server.app
    await server.shutdown()

@pytest.fixture
async def client(running_app: FastAPI, test_config: Dict[str, Any]) -> AsyncGenerator[AsyncClient, None]:
    """テスト用の非同期HTTPクライアント"""
    base_url = f"http://{test_config['host']}:{test_config['port']}"
    async with AsyncClient(base_url=base_url) as client:
        yield client

@pytest.fixture
def websocket_url(test_config: Dict[str, Any]) -> str:
    """WebSocketのURLを生成"""
    return f"ws://{test_config['host']}:{test_config['port']}/mcp"

@pytest.fixture
def test_context_data() -> dict:
    """テスト用のコンテキストデータ"""
    return {
        "context_id": "test-context",
        "content": {"key": "value"},
        "scope": "session"
    }

@pytest.fixture
def test_function_data() -> dict:
    """テスト用の関数呼び出しデータ"""
    return {
        "name": "test_function",
        "arguments": {"arg1": "value1", "arg2": "value2"}
    }

@pytest.fixture(autouse=True)
def configure_anyio_backend():
    """anyioのバックエンドを設定"""
    pytest.anyio_backend = "asyncio" 