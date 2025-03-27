"""
MCPサーバーの統合テスト
"""

import pytest
import asyncio
import json
import websockets
import anyio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.server.mcp import MCPServer
from src.server.models.context import MCPContext
from src.server.models.messages import (
    MCPContextRequest,
    MCPSetContextRequest,
    MCPDeleteContextRequest,
    MCPFunctionCallRequest,
    MCPFunctionCall
)
from contextlib import asynccontextmanager

class WebSocketTestSession:
    """WebSocketテストセッション"""
    def __init__(self, app: FastAPI, path: str):
        self.app = app
        self.path = path
        self.client = TestClient(app)
        self.ws = None

    async def __aenter__(self):
        """非同期コンテキストマネージャーのエントリーポイント"""
        self.ws = self.client.websocket_connect(self.path)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーの終了処理"""
        if self.ws:
            self.ws.close()

    async def send_json(self, data: dict):
        """JSONデータを送信"""
        if not self.ws:
            raise RuntimeError("WebSocket connection not established")
        self.ws.send_json(data)

    async def receive_json(self) -> dict:
        """JSONデータを受信"""
        if not self.ws:
            raise RuntimeError("WebSocket connection not established")
        return self.ws.receive_json()

@pytest.fixture
async def running_app(test_config):
    """FastAPIアプリケーションのフィクスチャ"""
    server = MCPServer(test_config)
    await server.startup()
    yield server.app
    await server.shutdown()

@pytest.mark.integration
class TestMCPServerIntegration:
    """MCPサーバーの統合テスト"""
    
    async def client_session(self, running_app: FastAPI, websocket_url: str, client_id: str) -> dict:
        """クライアントセッションの実行"""
        async with WebSocketTestSession(running_app, websocket_url) as ws:
            # コンテキストの設定
            await ws.send_json({
                "type": "set_context",
                "context_id": f"test-context-{client_id}",
                "content": {"value": client_id},
                "scope": "session"
            })
            response = await ws.receive_json()
            assert response["type"] == "success"

            # コンテキストの取得
            await ws.send_json({
                "type": "get_context",
                "context_id": f"test-context-{client_id}"
            })
            response = await ws.receive_json()
            assert response["type"] == "context"
            assert response["content"]["value"] == client_id

            return {"client_id": client_id, "success": True}

    @pytest.mark.asyncio
    async def test_multiple_clients(self, running_app: FastAPI, websocket_url: str):
        """複数クライアントの同時接続テスト"""
        num_clients = 3
        tasks = [
            self.client_session(running_app, websocket_url, str(i))
            for i in range(num_clients)
        ]
        results = await asyncio.gather(*tasks)
        assert all(result["success"] for result in results)
    
    @pytest.mark.asyncio
    async def test_context_persistence(self, running_app: FastAPI, websocket_url: str):
        """コンテキストの永続性テスト"""
        async with WebSocketTestSession(running_app, websocket_url) as ws:
            # コンテキストの設定
            await ws.send_json({
                "type": "set_context",
                "context_id": "persistent-context",
                "content": {"key": "value"},
                "scope": "session"
            })
            response = await ws.receive_json()
            assert response["type"] == "success"

        # 新しい接続でコンテキストを取得
        async with WebSocketTestSession(running_app, websocket_url) as ws:
            await ws.send_json({
                "type": "get_context",
                "context_id": "persistent-context"
            })
            response = await ws.receive_json()
            assert response["type"] == "context"
            assert response["content"]["key"] == "value"
    
    @pytest.mark.asyncio
    async def test_context_expiration(self, running_app: FastAPI, websocket_url: str):
        """コンテキストの有効期限テスト"""
        async with WebSocketTestSession(running_app, websocket_url) as ws:
            # 短い有効期限でコンテキストを設定
            await ws.send_json({
                "type": "set_context",
                "context_id": "expiring-context",
                "content": {"key": "value"},
                "scope": "session",
                "ttl": 1  # 1秒後に期限切れ
            })
            response = await ws.receive_json()
            assert response["type"] == "success"

            # すぐに取得できることを確認
            await ws.send_json({
                "type": "get_context",
                "context_id": "expiring-context"
            })
            response = await ws.receive_json()
            assert response["type"] == "context"
            assert response["content"]["key"] == "value"

            # 期限切れを待つ
            await asyncio.sleep(1.5)

            # 期限切れ後は取得できないことを確認
            await ws.send_json({
                "type": "get_context",
                "context_id": "expiring-context"
            })
            response = await ws.receive_json()
            assert response["type"] == "error"
            assert "Context not found" in response["message"]
    
    async def set_and_get_context(self, running_app: FastAPI, websocket_url: str, context_id: str, value: str) -> dict:
        """コンテキストの設定と取得"""
        async with WebSocketTestSession(running_app, websocket_url) as ws:
            # コンテキストの設定
            await ws.send_json({
                "type": "set_context",
                "context_id": context_id,
                "content": {"value": value},
                "scope": "session"
            })
            response = await ws.receive_json()
            assert response["type"] == "success"

            # コンテキストの取得
            await ws.send_json({
                "type": "get_context",
                "context_id": context_id
            })
            response = await ws.receive_json()
            assert response["type"] == "context"
            assert response["content"]["value"] == value

            return {"context_id": context_id, "value": value, "success": True}

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, running_app: FastAPI, websocket_url: str):
        """並行操作のテスト"""
        num_operations = 5
        tasks = [
            self.set_and_get_context(running_app, websocket_url, f"concurrent-context-{i}", f"value-{i}")
            for i in range(num_operations)
        ]
        results = await asyncio.gather(*tasks)
        assert all(result["success"] for result in results)
    
    @pytest.mark.asyncio
    async def test_error_recovery(self, running_app: FastAPI, websocket_url: str):
        """エラーからの回復テスト"""
        async with WebSocketTestSession(running_app, websocket_url) as ws:
            # 無効なメッセージを送信
            await ws.send_json({
                "type": "invalid_type",
                "content": "test"
            })
            response = await ws.receive_json()
            assert response["type"] == "error"

            # 有効なメッセージを送信
            await ws.send_json({
                "type": "set_context",
                "context_id": "recovery-context",
                "content": {"key": "value"},
                "scope": "session"
            })
            response = await ws.receive_json()
            assert response["type"] == "success"
    
    @pytest.mark.asyncio
    async def test_function_call_chain(self, running_app: FastAPI, websocket_url: str):
        """関数呼び出しチェーンのテスト"""
        async with WebSocketTestSession(running_app, websocket_url) as ws:
            # コンテキストの初期設定
            await ws.send_json({
                "type": "set_context",
                "context_id": "chain-context",
                "content": {"counter": 0},
                "scope": "session"
            })
            response = await ws.receive_json()
            assert response["type"] == "success"

            # カウンターをインクリメントする関数呼び出し
            for i in range(3):
                await ws.send_json({
                    "type": "function_call",
                    "function_name": "increment_counter",
                    "args": {"context_id": "chain-context"}
                })
                response = await ws.receive_json()
                assert response["type"] == "function_response"
                assert response["result"]["counter"] == i + 1

            # 最終的なコンテキストの確認
            await ws.send_json({
                "type": "get_context",
                "context_id": "chain-context"
            })
            response = await ws.receive_json()
            assert response["type"] == "context"
            assert response["content"]["counter"] == 3 