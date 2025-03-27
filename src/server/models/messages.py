"""
Model Context Protocol (MCP) メッセージモデルの定義
"""

from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field

class MCPBaseMessage(BaseModel):
    """基本メッセージモデル"""
    type: str = Field(..., description="メッセージタイプ")

class MCPErrorMessage(MCPBaseMessage):
    """エラーメッセージモデル"""
    type: str = "error"
    message: str = Field(..., description="エラーメッセージ")

class MCPSuccessMessage(MCPBaseMessage):
    """成功メッセージモデル"""
    type: str = "success"
    message: Optional[str] = None

class MCPPingMessage(MCPBaseMessage):
    """Pingメッセージモデル"""
    type: str = "ping"

class MCPPongMessage(MCPBaseMessage):
    """Pongメッセージモデル"""
    type: str = "pong"

class MCPContextRequest(MCPBaseMessage):
    """コンテキスト取得リクエストモデル"""
    type: str = "get_context"
    context_id: str = Field(..., description="コンテキストID")

class MCPContextResponse(MCPBaseMessage):
    """コンテキスト取得レスポンスモデル"""
    type: str = "context"
    context_id: str = Field(..., description="コンテキストID")
    content: Dict[str, Any] = Field(..., description="コンテキストの内容")

class MCPSetContextRequest(MCPBaseMessage):
    """コンテキスト設定リクエストモデル"""
    type: str = "set_context"
    context_id: str = Field(..., description="コンテキストID")
    content: Dict[str, Any] = Field(..., description="コンテキストの内容")
    scope: str = Field(default="session", description="スコープ (session, user, global)")
    ttl: Optional[int] = Field(None, description="有効期限（秒）")

class MCPDeleteContextRequest(MCPBaseMessage):
    """コンテキスト削除リクエストモデル"""
    type: str = "delete_context"
    context_id: str = Field(..., description="コンテキストID")

class MCPFunctionCall(BaseModel):
    """関数呼び出しモデル"""
    name: str = Field(..., description="関数名")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="関数の引数")

class MCPFunctionCallRequest(MCPBaseMessage):
    """関数呼び出しリクエストモデル"""
    type: str = "function_call"
    function: MCPFunctionCall = Field(..., description="呼び出す関数の情報")

class MCPFunctionCallResponse(MCPBaseMessage):
    """関数呼び出しレスポンスモデル"""
    type: str = "function_response"
    result: Optional[Any] = Field(None, description="関数の実行結果")
    error: Optional[str] = Field(None, description="エラーメッセージ（エラー時）")

# メッセージタイプとモデルのマッピング
MESSAGE_TYPES = {
    "error": MCPErrorMessage,
    "success": MCPSuccessMessage,
    "get_context": MCPContextRequest,
    "context": MCPContextResponse,
    "set_context": MCPSetContextRequest,
    "delete_context": MCPDeleteContextRequest,
    "function_call": MCPFunctionCallRequest,
    "function_response": MCPFunctionCallResponse,
    "ping": MCPPingMessage,
    "pong": MCPPongMessage,
}

def parse_message(data: Dict[str, Any]) -> Union[MCPBaseMessage, MCPErrorMessage]:
    """
    メッセージのパース
    
    Args:
        data (Dict[str, Any]): パースするデータ
    
    Returns:
        Union[MCPBaseMessage, MCPErrorMessage]: パースされたメッセージ
    """
    try:
        if "type" not in data:
            return MCPErrorMessage(message="Message type is required")
        
        message_type = data["type"]
        if message_type not in MESSAGE_TYPES:
            return MCPErrorMessage(message=f"Unknown message type: {message_type}")
        
        return MESSAGE_TYPES[message_type](**data)
    except Exception as e:
        return MCPErrorMessage(message=f"Validation error: {str(e)}") 