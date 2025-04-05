# src/kokoro_mcp_server/__main__.py
"""Kokoro MCP Server main entry point"""

from . import server
import asyncio

def main():
    """Main entry point for the package."""
    asyncio.run(server.main())