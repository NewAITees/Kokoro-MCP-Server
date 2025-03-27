"""
ロギング設定モジュール
"""

import sys
from pathlib import Path
from loguru import logger

def setup_logging(log_dir: Path = None, debug: bool = False) -> None:
    """
    ロギングの設定
    
    Args:
        log_dir (Path, optional): ログファイルのディレクトリ
        debug (bool, optional): デバッグモードの有効/無効
    """
    # デフォルトのロガーを削除
    logger.remove()
    
    # ログレベルの設定
    log_level = "DEBUG" if debug else "INFO"
    
    # 標準出力へのロギング設定
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        level=log_level,
        colorize=True
    )
    
    # ファイルへのロギング設定（指定された場合）
    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "mcp_server.log"
        
        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | "
                   "{level: <8} | "
                   "{name}:{function}:{line} | "
                   "{message}",
            level=log_level,
            rotation="1 day",
            retention="7 days",
            compression="zip"
        ) 