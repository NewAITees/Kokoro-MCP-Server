"""
Model Context Protocol (MCP) コンテキストモデルの定義
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

class MCPContext(BaseModel):
    """MCPコンテキストモデル"""
    context_id: str = Field(..., description="コンテキストの一意識別子")
    content: Dict[str, Any] = Field(default_factory=dict, description="コンテキストの内容")
    scope: str = Field(default="session", description="コンテキストのスコープ (session, user, global)")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="作成日時")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新日時")
    expires_at: Optional[datetime] = Field(default=None, description="有効期限")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="メタデータ")

    def is_expired(self) -> bool:
        """
        コンテキストが期限切れかどうかを確認
        
        Returns:
            bool: 期限切れの場合はTrue
        """
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def update(self, content: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """
        コンテキストの更新
        
        Args:
            content (Dict[str, Any]): 新しいコンテキスト内容
            ttl (Optional[int]): 有効期限（秒）
        """
        self.content = content
        self.updated_at = datetime.utcnow()
        
        if ttl is not None:
            self.expires_at = self.updated_at + timedelta(seconds=ttl)

class ContextStore:
    """コンテキストストア"""
    def __init__(self):
        """初期化"""
        self._contexts: Dict[str, MCPContext] = {}

    def get(self, context_id: str) -> Optional[MCPContext]:
        """
        コンテキストの取得
        
        Args:
            context_id (str): コンテキストID
        
        Returns:
            Optional[MCPContext]: コンテキスト（存在しない場合はNone）
        """
        context = self._contexts.get(context_id)
        if context is None or context.is_expired():
            if context is not None:
                del self._contexts[context_id]
            return None
        return context

    def set(self, context: MCPContext) -> None:
        """
        コンテキストの設定
        
        Args:
            context (MCPContext): コンテキスト
        """
        self._contexts[context.context_id] = context

    def delete(self, context_id: str) -> bool:
        """
        コンテキストの削除
        
        Args:
            context_id (str): コンテキストID
        
        Returns:
            bool: 削除に成功した場合はTrue
        """
        if context_id in self._contexts:
            del self._contexts[context_id]
            return True
        return False

    def cleanup_expired(self) -> List[str]:
        """
        期限切れコンテキストのクリーンアップ
        
        Returns:
            List[str]: 削除されたコンテキストIDのリスト
        """
        expired_ids = []
        for context_id, context in list(self._contexts.items()):
            if context.is_expired():
                del self._contexts[context_id]
                expired_ids.append(context_id)
        return expired_ids 