# src/kokoro_mcp_server/__main__.py に作成
"""
Entry point module for running the Kokoro MCP Server as a module.
"""

from . import main

if __name__ == "__main__":
    import sys
    sys.exit(main())