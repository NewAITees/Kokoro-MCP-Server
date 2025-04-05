# src/kokoro_mcp_server/__main__.py (新規作成)

# __init__.pyからmain関数をインポート
from . import server

if __name__ == "__main__":
    import sys
    sys.exit(server.main())