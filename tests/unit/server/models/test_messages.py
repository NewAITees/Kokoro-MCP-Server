"""
メッセージモデルのユニットテスト
"""

import pytest
from pydantic import ValidationError
from src.server.models.messages import (
    MCPBaseMessage,
    MCPErrorMessage,
    MCPSuccessMessage,
    MCPContextRequest,
    MCPContextResponse,
    MCPSetContextRequest,
    MCPDeleteContextRequest,
    MCPFunctionCall,
    MCPFunctionCallRequest,
    MCPFunctionCallResponse,
    parse_message
)

@pytest.mark.unit
class TestMessageModels:
    """メッセージモデルのテスト"""
    
    def test_base_message(self):
        """基本メッセージのテスト"""
        msg = MCPBaseMessage(type="test")
        assert msg.type == "test"
        
        # 型の検証
        with pytest.raises(ValidationError):
            MCPBaseMessage()
    
    def test_error_message(self):
        """エラーメッセージのテスト"""
        error_msg = "Test error"
        message = MCPErrorMessage(error=error_msg)
        assert message.type == "error"
        assert message.error == error_msg
    
    def test_success_message(self):
        """成功メッセージのテスト"""
        success_msg = "Test success"
        message = MCPSuccessMessage(message=success_msg)
        assert message.type == "success"
        assert message.message == success_msg
    
    def test_context_request(self):
        """コンテキスト取得リクエストのテスト"""
        context_id = "test-context"
        message = MCPContextRequest(context_id=context_id)
        assert message.type == "get_context"
        assert message.context_id == context_id
    
    def test_context_response(self):
        """コンテキスト取得レスポンスのテスト"""
        context = {"key": "value"}
        message = MCPContextResponse(context=context)
        assert message.type == "context"
        assert message.context == context
    
    def test_set_context_request(self):
        """コンテキスト設定リクエストのテスト"""
        context_id = "test-context"
        content = {"key": "value"}
        scope = "session"
        ttl = 3600
        message = MCPSetContextRequest(
            context_id=context_id,
            content=content,
            scope=scope,
            ttl=ttl
        )
        assert message.type == "set_context"
        assert message.context_id == context_id
        assert message.content == content
        assert message.scope == scope
        assert message.ttl == ttl
    
    def test_delete_context_request(self):
        """コンテキスト削除リクエストのテスト"""
        context_id = "test-context"
        message = MCPDeleteContextRequest(context_id=context_id)
        assert message.type == "delete_context"
        assert message.context_id == context_id
    
    def test_function_call(self):
        """関数呼び出しのテスト"""
        name = "test_function"
        arguments = {"arg1": "value1"}
        function = MCPFunctionCall(name=name, arguments=arguments)
        assert function.name == name
        assert function.arguments == arguments
    
    def test_function_call_request(self):
        """関数呼び出しリクエストのテスト"""
        function = MCPFunctionCall(name="test_function", arguments={"arg1": "value1"})
        message = MCPFunctionCallRequest(function=function)
        assert message.type == "function_call"
        assert message.function == function
    
    def test_function_call_response(self):
        """関数呼び出しレスポンスのテスト"""
        result = {"key": "value"}
        message = MCPFunctionCallResponse(result=result)
        assert message.type == "function_result"
        assert message.result == result
        assert message.error is None

@pytest.mark.unit
class TestMessageParsing:
    """メッセージパース機能のテスト"""
    
    def test_parse_message(self):
        """メッセージのパースのテスト"""
        # 正常なメッセージ
        data = {
            "type": "set_context",
            "context_id": "test-context",
            "content": {"key": "value"},
            "scope": "session"
        }
        message = parse_message(data)
        assert isinstance(message, MCPSetContextRequest)
        assert message.context_id == "test-context"

        # タイプがない場合
        data = {"content": "test"}
        message = parse_message(data)
        assert isinstance(message, MCPErrorMessage)
        assert "required" in message.error.lower()

        # 不正なタイプの場合
        data = {"type": "invalid_type"}
        message = parse_message(data)
        assert isinstance(message, MCPErrorMessage)
        assert "unknown" in message.error.lower()

        # 不正なフォーマットの場合
        data = {"type": "set_context"}  # 必須フィールドがない
        message = parse_message(data)
        assert isinstance(message, MCPErrorMessage)
        assert "invalid" in message.error.lower()
    
    def test_parse_get_context(self):
        """get_contextメッセージのパースのテスト"""
        data = {
            "type": "get_context",
            "context_id": "test-context"
        }
        msg = parse_message(data)
        assert isinstance(msg, MCPContextRequest)
        assert msg.context_id == "test-context"
    
    def test_parse_set_context(self):
        """set_contextメッセージのパースのテスト"""
        data = {
            "type": "set_context",
            "context_id": "test-context",
            "content": {"key": "value"},
            "scope": "session"
        }
        msg = parse_message(data)
        assert isinstance(msg, MCPSetContextRequest)
        assert msg.context_id == "test-context"
        assert msg.content == {"key": "value"}
        assert msg.scope == "session"
    
    def test_parse_delete_context(self):
        """delete_contextメッセージのパースのテスト"""
        data = {
            "type": "delete_context",
            "context_id": "test-context"
        }
        msg = parse_message(data)
        assert isinstance(msg, MCPDeleteContextRequest)
        assert msg.context_id == "test-context"
    
    def test_parse_function_call(self):
        """function_callメッセージのパースのテスト"""
        data = {
            "type": "function_call",
            "function": {
                "name": "test_function",
                "arguments": {"param1": "value1"}
            }
        }
        msg = parse_message(data)
        assert isinstance(msg, MCPFunctionCallRequest)
        assert msg.function.name == "test_function"
        assert msg.function.arguments == {"param1": "value1"}
    
    def test_parse_invalid_message(self):
        """無効なメッセージのパースのテスト"""
        data = {
            "type": "invalid_type",
            "content": "test"
        }
        msg = parse_message(data)
        assert isinstance(msg, MCPErrorMessage)
        assert "Unknown message type" in msg.error
    
    def test_parse_malformed_message(self):
        """不正な形式のメッセージのパースのテスト"""
        data = {
            "type": "get_context"
            # context_idが欠落
        }
        msg = parse_message(data)
        assert isinstance(msg, MCPErrorMessage)
        assert "Invalid message format" in msg.error 