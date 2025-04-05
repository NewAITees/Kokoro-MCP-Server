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

# MeCabの設定確認
echo "Checking MeCab configuration..."
MECAB_CONFIG_DIR="/app/.venv/lib/python3.10/site-packages/unidic/dicdir"
if [ ! -f "${MECAB_CONFIG_DIR}/mecabrc" ]; then
    echo "Creating MeCab configuration..."
    mkdir -p "${MECAB_CONFIG_DIR}"
    cat > "${MECAB_CONFIG_DIR}/mecabrc" << EOF
dicdir = ${MECAB_CONFIG_DIR}
cost-factor = 800
max-grouping-size = 10
EOF
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
    exec uv run --directory ./src -m kokoro_mcp_server "$@"
else
    echo "uv run command not available, using python directly..."
    exec python --directory ./src -m kokoro_mcp_server "$@"
fi 