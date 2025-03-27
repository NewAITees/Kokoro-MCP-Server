"""
設定モジュール
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# .envファイルの読み込み
load_dotenv()

class ServerConfig(BaseModel):
    """サーバー設定モデル"""
    host: str = Field(
        default=os.getenv("MCP_HOST", "localhost"),
        description="サーバーのホスト名"
    )
    port: int = Field(
        default=int(os.getenv("MCP_PORT", "8000")),
        description="サーバーのポート番号"
    )
    debug: bool = Field(
        default=os.getenv("MCP_DEBUG", "false").lower() == "true",
        description="デバッグモードの有効/無効"
    )
    workers: int = Field(
        default=int(os.getenv("MCP_WORKERS", "1")),
        description="ワーカープロセス数"
    )
    log_dir: Optional[Path] = Field(
        default=Path(os.getenv("MCP_LOG_DIR", "logs")) if os.getenv("MCP_LOG_DIR") else None,
        description="ログファイルのディレクトリ"
    )
    ssl_cert: Optional[Path] = Field(
        default=Path(os.getenv("MCP_SSL_CERT")) if os.getenv("MCP_SSL_CERT") else None,
        description="SSLサーバー証明書のパス"
    )
    ssl_key: Optional[Path] = Field(
        default=Path(os.getenv("MCP_SSL_KEY")) if os.getenv("MCP_SSL_KEY") else None,
        description="SSLサーバー秘密鍵のパス"
    )
    
    @property
    def use_ssl(self) -> bool:
        """SSLの使用有無"""
        return self.ssl_cert is not None and self.ssl_key is not None

class Config:
    """アプリケーション設定"""
    server: ServerConfig = ServerConfig()
    
    @classmethod
    def load(cls) -> "Config":
        """
        設定の読み込み
        
        Returns:
            Config: 設定インスタンス
        """
        return cls() 