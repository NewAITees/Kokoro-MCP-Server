"""
Kokoro MCP Server
"""

import sys
from typing import Optional

def main() -> int:
    """
    メインエントリーポイント。サーバーの起動と実行を管理します。
    
    Returns:
        int: 終了コード（0: 成功, 1: エラー）
    """
    # 起動メッセージを表示
    print("=" * 50)
    print("Kokoro MCP Server 起動開始")
    print("=" * 50)
    
    try:
        from . import server
        import asyncio
        
        print("モジュールのインポートに成功しました")
        
        # server.pyからmcpを受け取り、実行する
        try:
            print("server.main()を実行します")
            mcp = asyncio.run(server.main())
            print(f"server.main()の実行完了: {'成功' if mcp else '失敗'}")
            if mcp:
                print("mcp.run()を実行します")
                result = mcp.run()
                print(f"mcp.run()の結果: {result}")
                return result
            print("エラー: MCPサーバーの初期化に失敗しました")
            return 1
        except KeyboardInterrupt:
            print("ユーザーによる中断を検知しました")
            return 0
        except Exception as e:
            print(f"サーバー実行エラー: {e}")
            print(f"詳細なエラー情報: {sys.exc_info()}")
            return 1
            
    except ImportError as e:
        print(f"モジュールのインポートに失敗しました: {e}")
        return 1
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")
        return 1

__all__ = ['main', 'server']

# No imports at the top level that could cause circularity

