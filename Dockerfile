# ベースイメージとしてPython 3.10のスリムバージョンを使用
FROM python:3.10-slim

# 環境変数の設定
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    MECABRC=/app/.venv/lib/python3.10/site-packages/unidic/dicdir/mecabrc \
    FUGASHI_ENABLE_FALLBACK=1 \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    CMAKE_POLICY_VERSION_MINIMUM=3.5

# 作業ディレクトリの設定
WORKDIR /app

# 必要なパッケージのインストール
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        mecab \
        libmecab-dev \
        mecab-ipadic-utf8 \
        sudo \
        build-essential \
        cmake \
        git \
        curl \
        espeak-ng \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Pythonパッケージのインストール
COPY requirements.txt pyproject.toml ./

# uvの最新バージョンをインストールして仮想環境を作成
RUN pip install --upgrade pip \
    && pip install --upgrade 'uv>=0.1.4' \
    && uv venv \
    && . .venv/bin/activate \
    && uv pip install -r requirements.txt \
    && CMAKE_POLICY_VERSION_MINIMUM=3.5 uv pip install fugashi[unidic] unidic-lite ipadic pyopenjtalk

# MeCabの設定ファイルを作成
RUN mkdir -p /app/.venv/lib/python3.10/site-packages/unidic/dicdir && \
    echo "dicdir = /app/.venv/lib/python3.10/site-packages/unidic/dicdir" > /app/.venv/lib/python3.10/site-packages/unidic/dicdir/mecabrc && \
    echo "cost-factor = 800" >> /app/.venv/lib/python3.10/site-packages/unidic/dicdir/mecabrc && \
    echo "max-grouping-size = 10" >> /app/.venv/lib/python3.10/site-packages/unidic/dicdir/mecabrc

# ソースコードのコピー
COPY . .

# 設定ファイルのコピー（明示的に）
COPY src/kokoro_mcp_server/config.json /app/src/kokoro_mcp_server/config.json

# バックアップとしてルートディレクトリにもコピー
COPY src/kokoro_mcp_server/config.json /app/config.json

# 出力ディレクトリの作成
RUN mkdir -p output/audio

# エントリーポイントスクリプトの作成
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"] 