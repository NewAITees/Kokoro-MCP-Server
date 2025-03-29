#!/usr/bin/env python
"""
Kokoro MCP Server のメインエントリーポイント
"""

import sys
import os

# パッケージのルートディレクトリをPythonパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from kokoro_mcp_server import main

if __name__ == "__main__":
    sys.exit(main()) 