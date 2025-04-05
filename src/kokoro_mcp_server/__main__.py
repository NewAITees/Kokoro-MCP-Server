# src/kokoro_mcp_server/__main__.py
"""Kokoro MCP Server main entry point"""

import asyncio
from . import server

def main():
    """Main entry point for the package."""
    print("=" * 50)
    print("Kokoro MCP Server をメインエントリーポイントから起動します")
    print("=" * 50)
    
    mcp = asyncio.run(server.main())
    if mcp:
        print("MCPサーバーが正常に初期化されました。サーバーを実行します...")
        mcp()
    
    print("MCPサーバーの初期化に失敗しました。終了します。")
    return 1

if __name__ == "__main__":
    main()