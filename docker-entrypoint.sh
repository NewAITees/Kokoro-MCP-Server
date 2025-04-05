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

# 設定ファイルの確認と作成
echo "Checking configuration files..."
CONFIG_PATHS=(
    "/app/src/kokoro_mcp_server/config.json"
    "/app/config.json"
)

for config_path in "${CONFIG_PATHS[@]}"; do
    if [ -f "$config_path" ]; then
        echo "Found configuration file: $config_path"
        echo "Configuration contents:"
        cat "$config_path"
        break
    fi
done

if [ ! -f "/app/src/kokoro_mcp_server/config.json" ] && [ ! -f "/app/config.json" ]; then
    echo "Warning: Configuration file not found, creating default..."
    mkdir -p /app/src/kokoro_mcp_server
    cat > /app/src/kokoro_mcp_server/config.json << EOF
{
    "name": "kokoro-mcp-server",
    "version": "0.1.0",
    "description": "AI アシスタントと連携し、テキストを高品質な音声に変換する MCP サーバー",
    "capabilities": {
        "textToSpeech": {
            "supportedVoices": ["jf_alpha"],
            "supportedFormats": ["wav"],
            "supportedLanguages": ["ja"]
        }
    }
}
EOF
    echo "Created default configuration file at /app/src/kokoro_mcp_server/config.json"
fi

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