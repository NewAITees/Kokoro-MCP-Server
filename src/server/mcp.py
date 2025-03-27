"""
Model Context Protocol (MCP) サーバーの実装
"""

import asyncio
import json
from typing import Dict, Optional, Any, Callable, Awaitable
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from loguru import logger

from .models.context import MCPContext, ContextStore
from .models.messages import (
    MCPBaseMessage,
    MCPErrorMessage,
    MCPSuccessMessage,
    MCPContextRequest,
    MCPContextResponse,
    MCPSetContextRequest,
    MCPDeleteContextRequest,
    MCPFunctionCallRequest,
    MCPFunctionCallResponse,
    parse_message
)

class MCPServer:
    def __init__(self):
        """MCPサーバーの初期化"""
        self.app = FastAPI(title="VoiceStudio MCP Server")
        self.context_store = ContextStore()
        self.functions: Dict[str, Callable[..., Awaitable[Any]]] = {}
        
        # 定期的なクリーンアップタスクの設定
        self.cleanup_task: Optional[asyncio.Task] = None
        
        # ルートの設定
        self.setup_routes()
    
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
    
    def setup_routes(self):
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
        
        @self.app.get("/")
        async def health_check():
            """ヘルスチェックエンドポイント"""
            return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
        
        @self.app.websocket("/mcp")
        async def mcp_endpoint(websocket: WebSocket):
            """MCPエンドポイント"""
            await websocket.accept()
            
            try:
                while True:
                    # メッセージの受信とパース
                    raw_message = await websocket.receive_json()
                    message = parse_message(raw_message)
                    
                    if isinstance(message, MCPErrorMessage):
                        await websocket.send_json(message.dict())
                        continue
                    
                    # メッセージタイプに応じた処理
                    if isinstance(message, MCPContextRequest):
                        # コンテキストの取得
                        context = self.context_store.get(message.context_id)
                        await websocket.send_json(MCPContextResponse(
                            context=context.dict() if context else None
                        ).dict())
                    
                    elif isinstance(message, MCPSetContextRequest):
                        # コンテキストの設定
                        try:
                            context = MCPContext(
                                context_id=message.context_id,
                                content=message.content,
                                scope=message.scope
                            )
                            if message.ttl is not None:
                                context.update(message.content, message.ttl)
                            
                            self.context_store.set(context)
                            await websocket.send_json(MCPSuccessMessage(
                                message=f"Context {context.context_id} set successfully"
                            ).dict())
                        except Exception as e:
                            await websocket.send_json(MCPErrorMessage(
                                error=f"Failed to set context: {str(e)}"
                            ).dict())
                    
                    elif isinstance(message, MCPDeleteContextRequest):
                        # コンテキストの削除
                        if self.context_store.delete(message.context_id):
                            await websocket.send_json(MCPSuccessMessage(
                                message=f"Context {message.context_id} deleted successfully"
                            ).dict())
                        else:
                            await websocket.send_json(MCPErrorMessage(
                                error=f"Context {message.context_id} not found"
                            ).dict())
                    
                    elif isinstance(message, MCPFunctionCallRequest):
                        # 関数の呼び出し
                        func_name = message.function.name
                        if func_name not in self.functions:
                            await websocket.send_json(MCPErrorMessage(
                                error=f"Function {func_name} not found"
                            ).dict())
                            continue
                        
                        try:
                            result = await self.functions[func_name](**message.function.arguments)
                            await websocket.send_json(MCPFunctionCallResponse(
                                result=result
                            ).dict())
                        except Exception as e:
                            await websocket.send_json(MCPFunctionCallResponse(
                                result=None,
                                error=str(e)
                            ).dict())
                    
                    else:
                        # 未知のメッセージタイプ
                        await websocket.send_json(MCPErrorMessage(
                            error=f"Unknown message type: {message.type}"
                        ).dict())
            
            except WebSocketDisconnect:
                logger.info("Client disconnected")
            except Exception as e:
                logger.exception(f"Error in MCP endpoint: {e}")
                try:
                    await websocket.send_json(MCPErrorMessage(
                        error=f"Internal server error: {str(e)}"
                    ).dict())
                except:
                    pass
    
    def get_app(self) -> FastAPI:
        """FastAPIアプリケーションの取得"""
        return self.app 