#!/bin/bash
set -e

# コンテナが起動したときに表示するメッセージ
echo "=================================="
echo "  Kokoro MCP Server"
echo "=================================="
echo "Mode: ${MOCK_TTS:=false}"
echo "Log Level: ${LOG_LEVEL:=INFO}"
echo "=================================="

# 出力ディレクトリの作成
mkdir -p /app/output/audio

# 依存関係の確認
echo "Checking dependencies..."
if [ ! -f "/usr/local/etc/mecabrc" ]; then
    echo "Creating mecabrc symlink..."
    mkdir -p /usr/local/etc
    if [ -f "/etc/mecabrc" ]; then
        ln -sf /etc/mecabrc /usr/local/etc/mecabrc
    else
        echo "Warning: mecabrc not found"
    fi
fi

# 仮想環境のアクティベート
. /app/.venv/bin/activate

# Pythonパスの設定
export PYTHONPATH=/app:${PYTHONPATH}

# サーバー起動
echo "Starting Kokoro MCP Server..."

# uvコマンドの存在とrunサブコマンドの確認
if command -v uv &> /dev/null && uv --help | grep -q "run"; then
    echo "Using uv run command..."
    exec uv run kokoro_mcp_server "$@"
else
    echo "uv run command not available, using python directly..."
    exec python -m kokoro_mcp_server "$@"
fi 