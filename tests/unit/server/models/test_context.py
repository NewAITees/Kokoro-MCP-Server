"""
コンテキストモデルのユニットテスト
"""

import pytest
from datetime import datetime, timedelta
from src.server.models.context import MCPContext, ContextStore

@pytest.mark.unit
class TestMCPContext:
    """MCPContextクラスのテスト"""
    
    def test_create_context(self):
        """コンテキストの作成テスト"""
        context = MCPContext(
            context_id="test-context",
            content={"key": "value"},
            scope="session"
        )
        
        assert context.context_id == "test-context"
        assert context.content == {"key": "value"}
        assert context.scope == "session"
        assert isinstance(context.created_at, datetime)
        assert isinstance(context.updated_at, datetime)
        assert context.expires_at is None
        assert context.metadata == {}
    
    def test_context_expiration(self):
        """コンテキストの有効期限テスト"""
        context = MCPContext(
            context_id="test-context",
            content={"key": "value"}
        )
        
        # 有効期限なしの場合
        assert not context.is_expired()
        
        # 有効期限切れの場合
        context.expires_at = datetime.utcnow() - timedelta(seconds=1)
        assert context.is_expired()
        
        # 有効期限内の場合
        context.expires_at = datetime.utcnow() + timedelta(seconds=60)
        assert not context.is_expired()
    
    def test_update_context(self):
        """コンテキストの更新テスト"""
        context = MCPContext(
            context_id="test-context",
            content={"key": "value"}
        )
        original_created_at = context.created_at
        original_updated_at = context.updated_at
        
        # 更新前の確認
        assert context.content == {"key": "value"}
        
        # コンテキストの更新
        new_content = {"key": "new-value"}
        context.update(new_content, ttl=60)
        
        # 更新後の確認
        assert context.content == new_content
        assert context.created_at == original_created_at
        assert context.updated_at > original_updated_at
        assert context.expires_at > datetime.utcnow()

@pytest.mark.unit
class TestContextStore:
    """ContextStoreクラスのテスト"""
    
    def test_set_and_get_context(self):
        """コンテキストの設定と取得テスト"""
        store = ContextStore()
        context = MCPContext(
            context_id="test-context",
            content={"key": "value"}
        )
        
        # コンテキストの設定
        store.set(context)
        
        # コンテキストの取得
        retrieved = store.get("test-context")
        assert retrieved is not None
        assert retrieved.context_id == context.context_id
        assert retrieved.content == context.content
    
    def test_get_nonexistent_context(self):
        """存在しないコンテキストの取得テスト"""
        store = ContextStore()
        assert store.get("nonexistent") is None
    
    def test_delete_context(self):
        """コンテキストの削除テスト"""
        store = ContextStore()
        context = MCPContext(
            context_id="test-context",
            content={"key": "value"}
        )
        
        # コンテキストの設定と削除
        store.set(context)
        assert store.delete("test-context")
        
        # 削除後の確認
        assert store.get("test-context") is None
        assert not store.delete("test-context")
    
    def test_cleanup_expired(self):
        """期限切れコンテキストのクリーンアップテスト"""
        store = ContextStore()
        
        # 期限切れのコンテキスト
        expired = MCPContext(
            context_id="expired",
            content={"key": "value"}
        )
        expired.expires_at = datetime.utcnow() - timedelta(seconds=1)
        
        # 有効なコンテキスト
        valid = MCPContext(
            context_id="valid",
            content={"key": "value"}
        )
        valid.expires_at = datetime.utcnow() + timedelta(seconds=60)
        
        # コンテキストの設定
        store.set(expired)
        store.set(valid)
        
        # クリーンアップの実行
        cleaned = store.cleanup_expired()
        
        # クリーンアップ結果の確認
        assert "expired" in cleaned
        assert "valid" not in cleaned
        assert store.get("expired") is None
        assert store.get("valid") is not None 