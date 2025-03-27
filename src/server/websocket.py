"""
WebSocketサーバーの実装
"""

import asyncio
import json
from typing import Dict, Set, Optional

import websockets
from loguru import logger
from websockets.server import WebSocketServerProtocol

class MCPWebSocketServer:
    def __init__(self, host: str = '127.0.0.1', port: int = 8080):
        """
        MCPWebSocketServerの初期化
        
        Args:
            host (str): サーバーのホストアドレス
            port (int): サーバーのポート番号
        """
        self.host = host
        self.port = port
        self.clients: Set[WebSocketServerProtocol] = set()
        self.server: Optional[websockets.WebSocketServer] = None
    
    async def handle_client(self, websocket: WebSocketServerProtocol, path: str) -> None:
        """
        クライアント接続のハンドリング
        
        Args:
            websocket (WebSocketServerProtocol): WebSocketクライアント
            path (str): リクエストパス
        """
        try:
            # クライアントを登録
            self.clients.add(websocket)
            logger.info(f"Client connected. Total clients: {len(self.clients)}")
            
            # クライアントからのメッセージを待機
            async for message in websocket:
                try:
                    data = json.loads(message)
                    # TODO: メッセージの処理を実装
                    logger.debug(f"Received message: {data}")
                    
                    # エコーバック（テスト用）
                    await websocket.send(json.dumps({
                        "type": "echo",
                        "data": data
                    }))
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received: {message}")
                    continue
                
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client connection closed normally")
        except Exception as e:
            logger.exception(f"Error handling client: {e}")
        finally:
            # クライアントの登録解除
            self.clients.remove(websocket)
            logger.info(f"Client disconnected. Total clients: {len(self.clients)}")
    
    async def broadcast(self, message: Dict) -> None:
        """
        全クライアントにメッセージをブロードキャスト
        
        Args:
            message (Dict): 送信するメッセージ
        """
        if not self.clients:
            return
        
        # JSON文字列に変換
        data = json.dumps(message)
        
        # 全クライアントに送信
        await asyncio.gather(
            *[client.send(data) for client in self.clients],
            return_exceptions=True
        )
    
    async def start(self) -> None:
        """
        サーバーの起動
        """
        self.server = await websockets.serve(
            self.handle_client,
            self.host,
            self.port
        )
        logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")
        
        # サーバーを継続実行
        await self.server.wait_closed()
    
    async def stop(self) -> None:
        """
        サーバーの停止
        """
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("WebSocket server stopped")