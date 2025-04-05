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
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("kokoro-mcp-server")
    
    print("Kokoro MCP Server 起動開始")
    
    try:
        from . import server
        import asyncio
        
        print("モジュールのインポートに成功しました")
        
        # server.pyからmcpを受け取り、実行する
        try:
            print("server.main()を実行します")
            mcp = asyncio.run(server.main())
            print(f"server.main()の結果: {mcp}")
            if mcp:
                print("mcp.run()を実行します")
                result = mcp.run()
                print(f"mcp.run()の結果: {result}")
                return result
            logger.error("MCPサーバーの初期化に失敗しました")
            return 1
        except KeyboardInterrupt:
            logger.info("ユーザーによる中断を検知しました")
            return 0
        except Exception as e:
            logger.error(f"サーバー実行エラー: {e}", exc_info=True)
            print(f"サーバー実行中に例外が発生しました: {e}")
            return 1
            
    except ImportError as e:
        logger.error(f"モジュールのインポートに失敗しました: {e}", exc_info=True)
        print(f"モジュールのインポートに失敗しました: {e}")
        return 1
    except Exception as e:
        logger.error(f"予期せぬエラーが発生しました: {e}", exc_info=True)
        print(f"予期せぬエラーが発生しました: {e}")
        return 1

__all__ = ['main', 'server']

# No imports at the top level that could cause circularity

