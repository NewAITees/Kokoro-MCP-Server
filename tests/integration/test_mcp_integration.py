"""
MCPサーバーの統合テスト
"""

import pytest
import asyncio
import json
import websockets
from fastapi import FastAPI
from src.server.mcp import MCPServer
from src.server.models.context import MCPContext
from src.server.models.messages import (
    MCPContextRequest,
    MCPSetContextRequest,
    MCPDeleteContextRequest,
    MCPFunctionCallRequest,
    MCPFunctionCall
)

@pytest.fixture
async def mcp_server():
    """MCPサーバーのフィクスチャ"""
    server = MCPServer()
    await server.start()
    yield server
    await server.stop()

@pytest.fixture
async def running_app():
    """FastAPIアプリケーションのフィクスチャ"""
    app = FastAPI()
    await app.router.startup()
    yield app
    await app.router.shutdown()

@pytest.mark.integration
class TestMCPServerIntegration:
    """MCPサーバーの統合テスト"""
    
    @pytest.mark.asyncio
    async def test_multiple_clients(self, running_app: FastAPI, websocket_url: str):
        """複数クライアントの同時接続テスト"""
        async def client_session(client_id: str, shared_context_id: str):
            async with websockets.connect(websocket_url) as websocket:
                # コンテキストの設定
                await websocket.send(json.dumps({
                    "type": "set_context",
                    "context_id": shared_context_id,
                    "content": {"client": client_id},
                    "scope": "session"
                }))
                response = json.loads(await websocket.recv())
                assert response["type"] == "success"
                
                # コンテキストの取得
                await websocket.send(json.dumps({
                    "type": "get_context",
                    "context_id": shared_context_id
                }))
                response = json.loads(await websocket.recv())
                assert response["type"] == "context"
                assert response["context_id"] == shared_context_id
                
                return response["content"]
        
        # 複数クライアントの同時実行
        shared_context_id = "shared-context"
        tasks = [
            client_session(f"client-{i}", shared_context_id)
            for i in range(3)
        ]
        results = await asyncio.gather(*tasks)
        
        # 最後のクライアントの内容が保存されていることを確認
        assert len(results) == 3
        assert all("client" in result for result in results)
    
    @pytest.mark.asyncio
    async def test_context_persistence(self, running_app: FastAPI, websocket_url: str):
        """コンテキストの永続性テスト"""
        context_id = "persistent-context"
        test_data = {"key": "value"}
        
        # 最初の接続でコンテキストを設定
        async with websockets.connect(websocket_url) as websocket:
            await websocket.send(json.dumps({
                "type": "set_context",
                "context_id": context_id,
                "content": test_data,
                "scope": "session"
            }))
            response = json.loads(await websocket.recv())
            assert response["type"] == "success"
        
        # 新しい接続で同じコンテキストを取得
        async with websockets.connect(websocket_url) as websocket:
            await websocket.send(json.dumps({
                "type": "get_context",
                "context_id": context_id
            }))
            response = json.loads(await websocket.recv())
            assert response["type"] == "context"
            assert response["content"] == test_data
    
    @pytest.mark.asyncio
    async def test_context_expiration(self, running_app: FastAPI, websocket_url: str):
        """コンテキストの有効期限テスト"""
        context_id = "expiring-context"
        test_data = {"key": "value"}
        
        # 短い有効期限でコンテキストを設定
        async with websockets.connect(websocket_url) as websocket:
            await websocket.send(json.dumps({
                "type": "set_context",
                "context_id": context_id,
                "content": test_data,
                "scope": "session",
                "ttl": 1  # 1秒後に期限切れ
            }))
            response = json.loads(await websocket.recv())
            assert response["type"] == "success"
        
        # 有効期限前にコンテキストを取得
        async with websockets.connect(websocket_url) as websocket:
            await websocket.send(json.dumps({
                "type": "get_context",
                "context_id": context_id
            }))
            response = json.loads(await websocket.recv())
            assert response["type"] == "context"
            assert response["content"] == test_data
        
        # 有効期限切れを待つ
        await asyncio.sleep(1.5)
        
        # 有効期限後にコンテキストを取得
        async with websockets.connect(websocket_url) as websocket:
            await websocket.send(json.dumps({
                "type": "get_context",
                "context_id": context_id
            }))
            response = json.loads(await websocket.recv())
            assert response["type"] == "error"
            assert "Context not found" in response["message"]
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, running_app: FastAPI, websocket_url: str):
        """並行操作のテスト"""
        async def set_and_get_context(context_id: str, value: int):
            async with websockets.connect(websocket_url) as websocket:
                # コンテキストの設定
                await websocket.send(json.dumps({
                    "type": "set_context",
                    "context_id": context_id,
                    "content": {"value": value},
                    "scope": "session"
                }))
                response = json.loads(await websocket.recv())
                assert response["type"] == "success"
                
                # コンテキストの取得
                await websocket.send(json.dumps({
                    "type": "get_context",
                    "context_id": context_id
                }))
                response = json.loads(await websocket.recv())
                return response["content"]["value"]
        
        # 複数の並行操作を実行
        context_id = "concurrent-context"
        tasks = [
            set_and_get_context(context_id, i)
            for i in range(5)
        ]
        results = await asyncio.gather(*tasks)
        
        # すべての操作が正常に完了したことを確認
        assert len(results) == 5
        assert all(isinstance(result, int) for result in results)
    
    @pytest.mark.asyncio
    async def test_error_recovery(self, running_app: FastAPI, websocket_url: str):
        """エラーからの回復テスト"""
        async with websockets.connect(websocket_url) as websocket:
            # 無効なメッセージを送信
            await websocket.send(json.dumps({
                "type": "invalid_type",
                "content": "test"
            }))
            response = json.loads(await websocket.recv())
            assert response["type"] == "error"
            
            # 正常なメッセージを送信して回復を確認
            await websocket.send(json.dumps({
                "type": "set_context",
                "context_id": "recovery-test",
                "content": {"key": "value"},
                "scope": "session"
            }))
            response = json.loads(await websocket.recv())
            assert response["type"] == "success"
    
    @pytest.mark.asyncio
    async def test_function_call_chain(self, running_app: FastAPI, websocket_url: str):
        """関数呼び出しチェーンのテスト"""
        async with websockets.connect(websocket_url) as websocket:
            # コンテキストの設定
            await websocket.send(json.dumps({
                "type": "set_context",
                "context_id": "function-test",
                "content": {"step": 0},
                "scope": "session"
            }))
            response = json.loads(await websocket.recv())
            assert response["type"] == "success"
            
            # 関数呼び出しチェーン
            for i in range(3):
                await websocket.send(json.dumps({
                    "type": "function_call",
                    "function_name": "increment_step",
                    "args": {"step": i}
                }))
                response = json.loads(await websocket.recv())
                assert response["type"] == "function_response"
                assert response["result"]["step"] == i + 1 