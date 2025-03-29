"""
TTSサービスのベースクラス
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class TTSRequest:
    """TTSリクエストのデータクラス"""
    text: str
    voice: Optional[str] = None
    speed: Optional[float] = None

class BaseTTSService:
    """TTSサービスのベースクラス"""
    
    def generate(self, request: TTSRequest) -> tuple[bool, str | None]:
        """
        音声を生成する
        
        Args:
            request: TTSリクエスト
            
        Returns:
            tuple[bool, Optional[str]]: 成功したかどうかとファイルパス
        """
        raise NotImplementedError 