"""
Model Context Protocol (MCP) サーバーの実装
"""

import asyncio
import json
from typing import Dict, Optional, Any, Callable, Awaitable
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from loguru import logger
from contextlib import asynccontextmanager

from .models.context import MCPContext, ContextStore
from .models.messages import (
    MCPBaseMessage,
    MCPErrorMessage,
    MCPSuccessMessage,
    MCPPingMessage,
    MCPPongMessage,
    MCPContextRequest,
    MCPContextResponse,
    MCPSetContextRequest,
    MCPDeleteContextRequest,
    MCPFunctionCallRequest,
    MCPFunctionCallResponse,
    parse_message
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPIのライフスパンイベントハンドラー
    """
    # スタートアップ時の処理
    logger.info("Starting up MCP server...")
    yield
    # シャットダウン時の処理
    logger.info("Shutting down MCP server...")

class MCPServer:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        MCPサーバーの初期化
        
        Args:
            config (Optional[Dict[str, Any]], optional): サーバーの設定. Defaults to None.
        """
        self.config = config or {
            "host": "localhost",
            "port": 8000,
            "debug": False,
            "log_dir": "logs",
            "context_ttl": 3600,
            "cleanup_interval": 60
        }
        self.app = FastAPI(lifespan=lifespan)
        self.context_store = ContextStore()
        self.functions: Dict[str, Callable[..., Awaitable[Any]]] = {}
        
        # 定期的なクリーンアップタスクの設定
        self.cleanup_task: Optional[asyncio.Task] = None
        
        # ルートの設定
        self._setup_routes()
    
    async def cleanup_loop(self):
        """期限切れコンテキストの定期的なクリーンアップ"""
        while True:
            try:
                expired_ids = self.context_store.cleanup_expired()
                if expired_ids:
                    logger.info(f"Cleaned up expired contexts: {expired_ids}")
                await asyncio.sleep(60)  # 1分ごとにクリーンアップ
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Error in cleanup loop: {e}")
                await asyncio.sleep(60)
    
    def register_function(self, name: str, func: Callable[..., Awaitable[Any]]):
        """
        関数の登録
        
        Args:
            name (str): 関数名
            func (Callable[..., Awaitable[Any]]): 非同期関数
        """
        self.functions[name] = func
    
    def _setup_routes(self):
        """ルートの設定"""
        
        @self.app.on_event("startup")
        async def startup_event():
            """起動時のイベントハンドラ"""
            # クリーンアップタスクの開始
            self.cleanup_task = asyncio.create_task(self.cleanup_loop())
        
        @self.app.on_event("shutdown")
        async def shutdown_event():
            """シャットダウン時のイベントハンドラ"""
            # クリーンアップタスクの停止
            if self.cleanup_task:
                self.cleanup_task.cancel()
                try:
                    await self.cleanup_task
                except asyncio.CancelledError:
                    pass
        
        @self.app.get("/health")
        async def health_check():
            """ヘルスチェックエンドポイント"""
            return {"status": "ok"}
        
        @self.app.websocket("/mcp")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocketエンドポイント"""
            await websocket.accept()
            try:
                while True:
                    data = await websocket.receive_json()
                    message = parse_message(data)

                    if isinstance(message, MCPErrorMessage):
                        await websocket.send_json({
                            "type": "error",
                            "message": message.message
                        })
                        continue

                    response = await self._handle_message(message)
                    await websocket.send_json(response)
            except WebSocketDisconnect:
                logger.info("Client disconnected")
            except Exception as e:
                logger.error(f"Error in websocket connection: {str(e)}")
                await websocket.close()
    
    async def _handle_message(self, message: Any) -> Dict[str, Any]:
        """
        メッセージの処理
        
        Args:
            message (Any): 処理するメッセージ
        
        Returns:
            Dict[str, Any]: レスポンスメッセージ
        """
        try:
            if isinstance(message, MCPErrorMessage):
                return {
                    "type": "error",
                    "error": message.error
                }
            
            if isinstance(message, MCPPingMessage):
                return {"type": "pong"}
            
            if message.type == "get_context":
                context = self.context_store.get(message.context_id)
                if context is None:
                    return {
                        "type": "error",
                        "message": "Context not found"
                    }
                return {
                    "type": "context",
                    "context_id": message.context_id,
                    "content": context.content
                }
            elif message.type == "set_context":
                try:
                    context = MCPContext(
                        context_id=message.context_id,
                        content=message.content,
                        scope=message.scope
                    )
                    if message.ttl is not None:
                        context.update(message.content, message.ttl)
                    
                    self.context_store.set(context)
                    return {
                        "type": "success",
                        "message": f"Context {context.context_id} set successfully"
                    }
                except Exception as e:
                    return {
                        "type": "error",
                        "message": f"Failed to set context: {str(e)}"
                    }
            elif message.type == "delete_context":
                if self.context_store.delete(message.context_id):
                    return {
                        "type": "success",
                        "message": f"Context {message.context_id} deleted successfully"
                    }
                else:
                    return {
                        "type": "error",
                        "message": f"Context {message.context_id} not found"
                    }
            elif message.type == "function_call":
                # 関数呼び出しの処理
                func_name = message.function.name
                if func_name not in self.functions:
                    return {
                        "type": "error",
                        "message": f"Function {func_name} not found"
                    }
                
                try:
                    result = await self.functions[func_name](**message.function.arguments)
                    return {
                        "type": "function_response",
                        "result": result
                    }
                except Exception as e:
                    return {
                        "type": "error",
                        "message": str(e)
                    }
            else:
                return {
                    "type": "error",
                    "message": f"Unknown message type: {message.type}"
                }
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            return {
                "type": "error",
                "message": str(e)
            }
    
    def get_app(self) -> FastAPI:
        """FastAPIアプリケーションの取得"""
        return self.app 

    async def startup(self):
        """サーバーの起動処理"""
        # クリーンアップタスクの開始
        self.cleanup_task = asyncio.create_task(self.cleanup_loop())
        logger.info("MCP server started")

    async def shutdown(self):
        """サーバーの終了処理"""
        # クリーンアップタスクの停止
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("MCP server stopped") 