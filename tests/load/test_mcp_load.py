"""
MCPサーバーの負荷テスト
"""

import json
from locust import HttpUser, task, between, events
from locust.contrib.fasthttp import FastHttpUser
from websocket import create_connection
import random

class MCPWebSocketClient:
    """WebSocketクライアントのラッパー"""
    
    def __init__(self, host):
        """
        WebSocketクライアントの初期化
        
        Args:
            host (str): WebSocketサーバーのホスト
        """
        self.host = host
        self.ws = None
    
    def connect(self):
        """WebSocket接続を確立"""
        if not self.ws:
            self.ws = create_connection(f"ws://{self.host}/mcp")
    
    def disconnect(self):
        """WebSocket接続を切断"""
        if self.ws:
            self.ws.close()
            self.ws = None
    
    def send_message(self, message):
        """
        メッセージを送信し、レスポンスを受信
        
        Args:
            message (dict): 送信するメッセージ
            
        Returns:
            dict: 受信したレスポンス
        """
        if not self.ws:
            self.connect()
        
        self.ws.send(json.dumps(message))
        return json.loads(self.ws.recv())

class MCPUser(FastHttpUser):
    """負荷テスト用のユーザークラス"""
    
    wait_time = between(1, 2)  # タスク間の待機時間
    
    def on_start(self):
        """テスト開始時の処理"""
        self.client = MCPWebSocketClient(f"{self.host}:{self.port}")
        self.client.connect()
        self.context_ids = []  # 作成したコンテキストのIDを保持
    
    def on_stop(self):
        """テスト終了時の処理"""
        self.client.disconnect()
    
    def generate_context_id(self):
        """ユニークなコンテキストIDを生成"""
        return f"context-{random.randint(1, 1000000)}"
    
    @task(3)
    def set_context(self):
        """コンテキスト設定のタスク"""
        context_id = self.generate_context_id()
        message = {
            "type": "set_context",
            "context_id": context_id,
            "content": {"value": random.randint(1, 100)},
            "scope": "session"
        }
        
        with self.client.ws.connect() as ws:
            start_time = self.time()
            try:
                response = self.client.send_message(message)
                if response["type"] == "success":
                    self.context_ids.append(context_id)
                self.environment.events.request_success.fire(
                    request_type="websocket",
                    name="set_context",
                    response_time=self.time() - start_time,
                    response_length=0
                )
            except Exception as e:
                self.environment.events.request_failure.fire(
                    request_type="websocket",
                    name="set_context",
                    response_time=self.time() - start_time,
                    exception=e
                )
    
    @task(4)
    def get_context(self):
        """コンテキスト取得のタスク"""
        if not self.context_ids:
            return
        
        context_id = random.choice(self.context_ids)
        message = {
            "type": "get_context",
            "context_id": context_id
        }
        
        with self.client.ws.connect() as ws:
            start_time = self.time()
            try:
                response = self.client.send_message(message)
                self.environment.events.request_success.fire(
                    request_type="websocket",
                    name="get_context",
                    response_time=self.time() - start_time,
                    response_length=0
                )
            except Exception as e:
                self.environment.events.request_failure.fire(
                    request_type="websocket",
                    name="get_context",
                    response_time=self.time() - start_time,
                    exception=e
                )
    
    @task(2)
    def delete_context(self):
        """コンテキスト削除のタスク"""
        if not self.context_ids:
            return
        
        context_id = random.choice(self.context_ids)
        message = {
            "type": "delete_context",
            "context_id": context_id
        }
        
        with self.client.ws.connect() as ws:
            start_time = self.time()
            try:
                response = self.client.send_message(message)
                if response["type"] == "success":
                    self.context_ids.remove(context_id)
                self.environment.events.request_success.fire(
                    request_type="websocket",
                    name="delete_context",
                    response_time=self.time() - start_time,
                    response_length=0
                )
            except Exception as e:
                self.environment.events.request_failure.fire(
                    request_type="websocket",
                    name="delete_context",
                    response_time=self.time() - start_time,
                    exception=e
                )
    
    @task(1)
    def function_call(self):
        """関数呼び出しのタスク"""
        message = {
            "type": "function_call",
            "function": {
                "name": "test_function",
                "parameters": {"value": random.randint(1, 100)}
            }
        }
        
        with self.client.ws.connect() as ws:
            start_time = self.time()
            try:
                response = self.client.send_message(message)
                self.environment.events.request_success.fire(
                    request_type="websocket",
                    name="function_call",
                    response_time=self.time() - start_time,
                    response_length=0
                )
            except Exception as e:
                self.environment.events.request_failure.fire(
                    request_type="websocket",
                    name="function_call",
                    response_time=self.time() - start_time,
                    exception=e
                )

@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Locustの初期化時の処理"""
    print("Starting load test for MCP Server")

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """テスト開始時の処理"""
    print("Load test is starting") 