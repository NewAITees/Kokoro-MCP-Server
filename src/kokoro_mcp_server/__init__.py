"""
Kokoro MCP Server
"""

import logging
import sys
from typing import Optional

def main() -> int:
    """
    メインエントリーポイント。サーバーの起動と実行を管理します。
    
    Returns:
        int: 終了コード（0: 成功, 1: エラー）
    """
    # ロギングの設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("kokoro-mcp-server")
    
    try:
        from . import server
        import asyncio
        
        # server.pyからmcpを受け取り、実行する
        try:
            mcp = asyncio.run(server.main())
            if mcp:
                return mcp.run()
            logger.error("MCPサーバーの初期化に失敗しました")
            return 1
        except KeyboardInterrupt:
            logger.info("ユーザーによる中断を検知しました")
            return 0
        except Exception as e:
            logger.error(f"サーバー実行エラー: {e}", exc_info=True)
            return 1
            
    except ImportError as e:
        logger.error(f"モジュールのインポートに失敗しました: {e}", exc_info=True)
        return 1
    except Exception as e:
        logger.error(f"予期せぬエラーが発生しました: {e}", exc_info=True)
        return 1

__all__ = ['main', 'server']

# No imports at the top level that could cause circularity

