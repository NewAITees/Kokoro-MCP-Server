"""
設定管理モジュール
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

class ServerConfig(BaseModel):
    """サーバー設定"""
    host: str = Field(default="127.0.0.1", description="サーバーのホストアドレス")
    port: int = Field(default=8080, description="サーバーのポート番号")
    debug: bool = Field(default=False, description="デバッグモードの有効/無効")

class LogConfig(BaseModel):
    """ログ設定"""
    level: str = Field(default="INFO", description="ログレベル")
    file_path: Path = Field(default=Path("logs/voicestudio-mcp.log"), description="ログファイルのパス")
    rotation: str = Field(default="1 day", description="ログローテーション期間")
    retention: str = Field(default="7 days", description="ログ保持期間")

class Config(BaseModel):
    """アプリケーション全体の設定"""
    server: ServerConfig = Field(default_factory=ServerConfig, description="サーバー設定")
    log: LogConfig = Field(default_factory=LogConfig, description="ログ設定")
    
    @classmethod
    def from_env(cls) -> 'Config':
        """
        環境変数から設定を読み込む
        
        Returns:
            Config: 設定オブジェクト
        """
        return cls(
            server=ServerConfig(
                host=os.getenv("MCP_SERVER_HOST", "127.0.0.1"),
                port=int(os.getenv("MCP_SERVER_PORT", "8080")),
                debug=os.getenv("MCP_DEBUG", "false").lower() == "true"
            ),
            log=LogConfig(
                level=os.getenv("MCP_LOG_LEVEL", "INFO"),
                file_path=Path(os.getenv("MCP_LOG_FILE", "logs/voicestudio-mcp.log")),
                rotation=os.getenv("MCP_LOG_ROTATION", "1 day"),
                retention=os.getenv("MCP_LOG_RETENTION", "7 days")
            )
        )