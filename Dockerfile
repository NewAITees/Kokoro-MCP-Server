# ベースイメージとしてPython 3.10のスリムバージョンを使用
FROM python:3.10-slim

# 環境変数の設定
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    MECABRC=/etc/mecabrc \
    FUGASHI_ENABLE_FALLBACK=1

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
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Pythonパッケージのインストール
COPY requirements.txt pyproject.toml ./

# uvのインストールと依存関係のインストール
RUN pip install --upgrade pip \
    && pip install 'uv==0.1.4' \
    && uv pip install -r requirements.txt

# 必要なPython依存関係のインストール
RUN uv pip install fugashi[unidic] unidic-lite ipadic \
    && uv pip install pyopenjtalk

# mecabrcのシンボリックリンク作成
RUN if [ ! -f "/usr/local/etc/mecabrc" ] && [ -f "/etc/mecabrc" ]; then \
        mkdir -p /usr/local/etc && \
        ln -sf /etc/mecabrc /usr/local/etc/mecabrc; \
    fi

# ソースコードのコピー
COPY . .

# 出力ディレクトリの作成
RUN mkdir -p output/audio

# エントリーポイントスクリプトの作成
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"] 