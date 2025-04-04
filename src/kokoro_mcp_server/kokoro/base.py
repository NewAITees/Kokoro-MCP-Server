"""
TTSサービスのベースクラス
"""

from dataclasses import dataclass
from typing import Optional, Tuple, Union, Dict, Any, cast

@dataclass
class TTSRequest:
    """TTSリクエストのデータクラス"""
    text: str
    voice: Optional[str] = None
    speed: Optional[float] = None
    
    def __getitem__(self, key: str) -> Any:
        """辞書風アクセスをサポート"""
        if key == "text":
            return self.text
        elif key == "voice":
            return self.voice
        elif key == "speed":
            return self.speed
        raise KeyError(f"TTSRequest has no attribute '{key}'")

class BaseTTSService:
    """TTSサービスのベースクラス"""
    
    def generate(self, request: TTSRequest) -> Tuple[bool, Optional[str]]:
        """
        音声を生成する
        
        Args:
            request: TTSリクエスト
            
        Returns:
            tuple[bool, Optional[str]]: 成功したかどうかとファイルパス
        """
        raise NotImplementedError 