"""
MCPサーバーのユニットテスト
"""

import json
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient
from src.server.mcp import MCPServer
from src.server.models.messages import (
    MCPContextRequest,
    MCPSetContextRequest,
    MCPDeleteContextRequest,
    MCPFunctionCallRequest,
    MCPFunctionCall
)

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
        self.ws.send_json(data)

    async def receive_json(self) -> dict:
        """JSONデータを受信"""
        return self.ws.receive_json()

@pytest.mark.unit
class TestMCPServer:
    """MCPServerクラスのテスト"""
    
    def test_server_initialization(self):
        """サーバーの初期化テスト"""
        server = MCPServer()
        assert isinstance(server.app, FastAPI)
        assert server.context_store is not None
    
    @pytest.mark.asyncio
    async def test_health_check(self, running_app: FastAPI, test_config):
        """ヘルスチェックエンドポイントのテスト"""
        base_url = f"http://{test_config['host']}:{test_config['port']}"
        async with AsyncClient(base_url=base_url) as client:
            response = await client.get("/health")
            assert response.status_code == 200
            assert response.json() == {"status": "healthy"}

@pytest.mark.unit
@pytest.mark.asyncio
class TestWebSocketEndpoint:
    """WebSocketエンドポイントのテスト"""
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self, running_app: FastAPI, websocket_url: str):
        """WebSocket接続のテスト"""
        async with WebSocketTestSession(running_app, websocket_url) as ws:
            await ws.send_json({"type": "ping"})
            response = await ws.receive_json()
            assert response["type"] == "pong"
    
    @pytest.mark.asyncio
    async def test_get_context(self, running_app: FastAPI, websocket_url: str):
        """コンテキスト取得のテスト"""
        async with WebSocketTestSession(running_app, websocket_url) as ws:
            # コンテキストの設定
            await ws.send_json({
                "type": "set_context",
                "context_id": "test-context",
                "content": {"key": "value"},
                "scope": "session"
            })
            response = await ws.receive_json()
            assert response["type"] == "success"
            
            # コンテキストの取得
            await ws.send_json({
                "type": "get_context",
                "context_id": "test-context"
            })
            response = await ws.receive_json()
            assert response["type"] == "context"
            assert response["context_id"] == "test-context"
            assert response["content"] == {"key": "value"}
    
    @pytest.mark.asyncio
    async def test_set_context(self, running_app: FastAPI, websocket_url: str):
        """コンテキスト設定のテスト"""
        async with WebSocketTestSession(running_app, websocket_url) as ws:
            await ws.send_json({
                "type": "set_context",
                "context_id": "test-context",
                "content": {"key": "value"},
                "scope": "session"
            })
            response = await ws.receive_json()
            assert response["type"] == "success"
    
    @pytest.mark.asyncio
    async def test_delete_context(self, running_app: FastAPI, websocket_url: str):
        """コンテキスト削除のテスト"""
        async with WebSocketTestSession(running_app, websocket_url) as ws:
            # コンテキストの設定
            await ws.send_json({
                "type": "set_context",
                "context_id": "test-context",
                "content": {"key": "value"},
                "scope": "session"
            })
            response = await ws.receive_json()
            assert response["type"] == "success"
            
            # コンテキストの削除
            await ws.send_json({
                "type": "delete_context",
                "context_id": "test-context"
            })
            response = await ws.receive_json()
            assert response["type"] == "success"
            
            # 削除されたことの確認
            await ws.send_json({
                "type": "get_context",
                "context_id": "test-context"
            })
            response = await ws.receive_json()
            assert response["type"] == "error"
            assert "Context not found" in response["message"]
    
    @pytest.mark.asyncio
    async def test_function_call(self, running_app: FastAPI, websocket_url: str):
        """関数呼び出しのテスト"""
        async with WebSocketTestSession(running_app, websocket_url) as ws:
            await ws.send_json({
                "type": "function_call",
                "function_name": "test_function",
                "args": {"param1": "value1"}
            })
            response = await ws.receive_json()
            assert response["type"] == "function_response"
            assert "result" in response
    
    @pytest.mark.asyncio
    async def test_invalid_message_type(self, running_app: FastAPI, websocket_url: str):
        """無効なメッセージ型のテスト"""
        async with WebSocketTestSession(running_app, websocket_url) as ws:
            await ws.send_json({
                "type": "invalid_type",
                "content": "test"
            })
            response = await ws.receive_json()
            assert response["type"] == "error"
            assert "Unknown message type" in response["message"]
    
    @pytest.mark.asyncio
    async def test_malformed_message(self, running_app: FastAPI, websocket_url: str):
        """不正な形式のメッセージのテスト"""
        async with WebSocketTestSession(running_app, websocket_url) as ws:
            await ws.send_json({
                "type": "get_context"
                # context_idが欠落
            })
            response = await ws.receive_json()
            assert response["type"] == "error"
            assert "Validation error" in response["message"]
    
    @pytest.mark.asyncio
    async def test_context_not_found(self, running_app: FastAPI, websocket_url: str):
        """存在しないコンテキストのテスト"""
        async with WebSocketTestSession(running_app, websocket_url) as ws:
            await ws.send_json({
                "type": "get_context",
                "context_id": "nonexistent-context"
            })
            response = await ws.receive_json()
            assert response["type"] == "error"
            assert "Context not found" in response["message"]
    
    @pytest.mark.asyncio
    async def test_websocket_disconnect(self, running_app: FastAPI, websocket_url: str):
        """WebSocket切断のテスト"""
        async with WebSocketTestSession(running_app, websocket_url) as ws:
            await ws.send_json({"type": "ping"})
            response = await ws.receive_json()
            assert response["type"] == "pong"

        # 新しい接続を確立できることを確認
        async with WebSocketTestSession(running_app, websocket_url) as ws:
            await ws.send_json({"type": "ping"})
            response = await ws.receive_json()
            assert response["type"] == "pong" 