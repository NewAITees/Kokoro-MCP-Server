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
        self.client = TestClient(app)
        self.path = path
        self.ws = None

    def __enter__(self):
        """同期コンテキストマネージャーのエントリーポイント"""
        self.ws = self.client.websocket_connect(self.path).__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """同期コンテキストマネージャーの終了処理"""
        if self.ws:
            self.ws.__exit__(exc_type, exc_val, exc_tb)
            self.ws = None

    def send_json(self, data: dict):
        """JSONデータを送信"""
        if not self.ws:
            raise RuntimeError("WebSocket connection not established")
        self.ws.send_json(data)

    def receive_json(self) -> dict:
        """JSONデータを受信"""
        if not self.ws:
            raise RuntimeError("WebSocket connection not established")
        return self.ws.receive_json()

@pytest.mark.unit
class TestMCPServer:
    """MCPServerクラスのテスト"""
    
    def test_server_initialization(self):
        """サーバーの初期化テスト"""
        server = MCPServer()
        assert isinstance(server.app, FastAPI)
        assert server.context_store is not None
    
    def test_health_check(self, running_app: FastAPI):
        """ヘルスチェックエンドポイントのテスト"""
        client = TestClient(running_app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

@pytest.mark.unit
class TestWebSocketEndpoint:
    """WebSocketエンドポイントのテスト"""
    
    def test_websocket_connection(self, running_app: FastAPI, websocket_url: str):
        """WebSocket接続のテスト"""
        with WebSocketTestSession(running_app, websocket_url) as ws:
            ws.send_json({"type": "ping"})
            response = ws.receive_json()
            assert response["type"] == "pong"
    
    def test_get_context(self, running_app: FastAPI, websocket_url: str):
        """コンテキスト取得のテスト"""
        with WebSocketTestSession(running_app, websocket_url) as ws:
            # コンテキストの設定
            ws.send_json({
                "type": "set_context",
                "context_id": "test-context",
                "content": {"key": "value"},
                "scope": "session"
            })
            response = ws.receive_json()
            assert response["type"] == "success"
            
            # コンテキストの取得
            ws.send_json({
                "type": "get_context",
                "context_id": "test-context"
            })
            response = ws.receive_json()
            assert response["type"] == "context"
            assert response["context_id"] == "test-context"
            assert response["content"] == {"key": "value"}
    
    def test_set_context(self, running_app: FastAPI, websocket_url: str):
        """コンテキスト設定のテスト"""
        with WebSocketTestSession(running_app, websocket_url) as ws:
            ws.send_json({
                "type": "set_context",
                "context_id": "test-context",
                "content": {"key": "value"},
                "scope": "session"
            })
            response = ws.receive_json()
            assert response["type"] == "success"
    
    def test_delete_context(self, running_app: FastAPI, websocket_url: str):
        """コンテキスト削除のテスト"""
        with WebSocketTestSession(running_app, websocket_url) as ws:
            # コンテキストの設定
            ws.send_json({
                "type": "set_context",
                "context_id": "test-context",
                "content": {"key": "value"},
                "scope": "session"
            })
            response = ws.receive_json()
            assert response["type"] == "success"
            
            # コンテキストの削除
            ws.send_json({
                "type": "delete_context",
                "context_id": "test-context"
            })
            response = ws.receive_json()
            assert response["type"] == "success"
            
            # 削除されたことの確認
            ws.send_json({
                "type": "get_context",
                "context_id": "test-context"
            })
            response = ws.receive_json()
            assert response["type"] == "error"
            assert "Context not found" in response["message"]
    
    def test_function_call(self, running_app: FastAPI, websocket_url: str):
        """関数呼び出しのテスト"""
        with WebSocketTestSession(running_app, websocket_url) as ws:
            ws.send_json({
                "type": "function_call",
                "function": {
                    "name": "test_function",
                    "arguments": {"param1": "value1"}
                }
            })
            response = ws.receive_json()
            assert response["type"] == "function_response"
            assert "result" in response
            assert response["result"] == {"param1": "value1"}
    
    def test_invalid_message_type(self, running_app: FastAPI, websocket_url: str):
        """無効なメッセージ型のテスト"""
        with WebSocketTestSession(running_app, websocket_url) as ws:
            ws.send_json({
                "type": "invalid_type",
                "content": "test"
            })
            response = ws.receive_json()
            assert response["type"] == "error"
            assert "Unknown message type" in response["message"]
    
    def test_malformed_message(self, running_app: FastAPI, websocket_url: str):
        """不正な形式のメッセージのテスト"""
        with WebSocketTestSession(running_app, websocket_url) as ws:
            ws.send_json({
                "type": "get_context"
                # context_idが欠落
            })
            response = ws.receive_json()
            assert response["type"] == "error"
            assert "Validation error" in response["message"]
    
    def test_context_not_found(self, running_app: FastAPI, websocket_url: str):
        """存在しないコンテキストのテスト"""
        with WebSocketTestSession(running_app, websocket_url) as ws:
            ws.send_json({
                "type": "get_context",
                "context_id": "nonexistent-context"
            })
            response = ws.receive_json()
            assert response["type"] == "error"
            assert "Context not found" in response["message"]
    
    def test_websocket_disconnect(self, running_app: FastAPI, websocket_url: str):
        """WebSocket切断のテスト"""
        with WebSocketTestSession(running_app, websocket_url) as ws:
            ws.send_json({"type": "ping"})
            response = ws.receive_json()
            assert response["type"] == "pong"

        # 新しい接続を確立できることを確認
        with WebSocketTestSession(running_app, websocket_url) as ws:
            ws.send_json({"type": "ping"})
            response = ws.receive_json()
            assert response["type"] == "pong" 