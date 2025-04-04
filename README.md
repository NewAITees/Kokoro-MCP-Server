# Kokoro MCP Server 開発環境セットアップガイド

このガイドでは、Kokoro MCP Server プロジェクトの開発環境をセットアップする方法を詳しく説明します。

## 前提条件

Kokoro MCP Server の開発には以下のソフトウェアが必要です：

- Python 3.10 以上
- uv パッケージマネージャー
- Git
- Docker と Docker Compose
- Kokoro 音声合成エンジン（実モードで使用する場合）

## 基本セットアップ

### 1. リポジトリのクローン

```bash
# リポジトリのクローン
git clone https://github.com/yourusername/Kokoro-MCP-Server.git
cd Kokoro-MCP-Server
```

### 2. uvのインストールと仮想環境の作成

```bash
# uvのインストール（macOS/Linux）
curl -sSf https://astral.sh/uv/install.sh | sh
# または（Windows）
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 仮想環境の作成
uv venv

# 仮想環境の有効化（Windows）
.venv\Scripts\activate

# 仮想環境の有効化（macOS/Linux）
source .venv/bin/activate
```

### 3. 依存パッケージのインストール

```bash
# 依存パッケージのインストール
uv pip install -r requirements.txt

# 開発用パッケージのインストール
uv pip install -r requirements-dev.txt
```

### 4. PyOpenJTalkのインストール

PyOpenJTalkはWindowsでのインストールに追加設定が必要な場合があります：

```bash
# Linuxの場合
CMAKE_POLICY_VERSION_MINIMUM=3.5 uv pip install pyopenjtalk

# Windowsの場合
$env:CMAKE_POLICY_VERSION_MINIMUM = "3.5"; uv pip install pyopenjtalk

# インストールに問題がある場合は、ビルド済みホイールを試す
uv pip install https://github.com/r9y9/pyopenjtalk/releases/download/v0.3.0/pyopenjtalk-0.3.0-cp39-cp39-win_amd64.whl
```

## MeCabとfugashiのセットアップ

### 1. MeCabのインストール（Linuxの場合）

```bash
sudo apt-get update
sudo apt-get install -y mecab libmecab-dev mecab-ipadic-utf8
```

### 2. fugashiとunidic-liteのインストール

```bash
uv pip install fugashi[unidic] unidic-lite ipadic
```

### 3. Windows特有の設定

Windowsでは、MeCabの設定ファイルのパスを手動で設定する必要がある場合があります：

```bash
# mecab_windows_setup.pyを実行
python mecab_windows_setup.py
```

## 開発用設定

### 1. 開発モードの有効化

開発モードでは、デバッグログが有効になり、変更が自動的に反映されます。

```bash
# 開発モードで実行
MOCK_TTS=true python src/main.py --dev
```

### 2. ログ設定

ログレベルを調整することで、詳細なデバッグ情報を表示できます。

```bash
# デバッグログを有効にして実行
python src/main.py --log-level debug
```

### 3. モックモードの使用

Kokoro音声合成エンジンがない環境でも開発できるように、モックモードを使用できます：

```bash
# モックモードで実行
MOCK_TTS=true python src/main.py
```

## テスト環境

### 1. テストの実行

プロジェクトには、自動テストスイートが含まれています。

```bash
# すべてのテストを実行
pytest

# 特定のテストモジュールを実行
pytest tests/test_mcp_server.py

# カバレッジレポートを生成
pytest --cov=src
```

### 2. テスト用クライアント

MCP サーバーの動作をテストするためのクライアントツールが提供されています。

```bash
# テストクライアントの実行
python tools/test_client.py --text "こんにちは、世界" --language "japanese"
```

## Docker環境

### 1. Dockerコンテナのビルドと実行

```bash
# イメージをビルド
make build

# コンテナを起動
make up

# ログを確認
make logs

# コンテナ内でシェルを実行
make shell
```

### 2. マルチアーキテクチャビルド

複数のアーキテクチャ（amd64, arm64）向けにイメージをビルドできます：

```bash
# Docker Hub ユーザー名を設定
export DOCKER_HUB_USERNAME="your-username"

# マルチアーキテクチャビルドを実行
./build-multi-arch.sh
```

### 3. 本番環境へのデプロイ

本番環境へのデプロイは以下の手順で行います：

1. 設定ファイルの準備：
```bash
# 設定ファイルをコピーして編集
cp claude_desktop_config.json.example claude_desktop_config.json
```

2. 設定ファイルの編集：
- API キーの設定
- ボリュームパスの設定
- リソース制限の設定

3. デプロイの実行：
```bash
# デプロイスクリプトを実行
./deploy.sh
```

### 4. 開発モードでのDocker実行

```bash
# 開発モードでコンテナを起動（モックTTSを使用）
make dev
```

## デバッグ手法

### 1. デバッグログの有効化

詳細なデバッグ情報を確認するには、ログレベルを調整します。

```bash
# デバッグログを有効にして実行
python src/main.py --log-level debug
```

### 2. Python Debuggerの使用

Pythonのデバッガーを使用して、対話的にコードをデバッグできます：

```python
# コード内でデバッグポイントを設定
import pdb; pdb.set_trace()
```

### 3. リクエスト/レスポンスのロギング

MCPリクエストとレスポンスをログに記録して確認できます：

```bash
# リクエスト/レスポンスのロギングを有効化
python src/main.py --log-level debug --log-requests
```

## コード品質ツール

### 1. Blackによるコードフォーマット

```bash
# コードのフォーマット
black src/ tests/
```

### 2. isortによるインポートの整理

```bash
# インポートの整理
isort src/ tests/
```

### 3. flake8によるリント

```bash
# コードのリント
flake8 src/ tests/
```

### 4. mypyによる型チェック

```bash
# 型チェック
mypy src/
```

## よくある問題と解決方法

### 1. MeCab関連のエラー

MeCabが見つからない場合やmecabrcファイルにアクセスできない場合は、以下の解決方法を試してください：

```bash
# MeCabの設定ファイルを探す
find / -name mecabrc 2>/dev/null

# 環境変数の設定
export MECABRC=/path/to/mecabrc

# または、シンボリックリンクの作成
sudo ln -sf /path/to/mecabrc /usr/local/etc/mecabrc
```

### 2. fugashiとunidic関連のエラー

```bash
# まず、既存のパッケージをアンインストール
uv pip uninstall fugashi ipadic unidic-lite

# インストールし直す
uv pip install fugashi[unidic] unidic-lite ipadic
```

### 3. PyTorch関連のエラー

```bash
# PyTorchの再インストール
uv pip uninstall torch
uv pip install torch
```

## MCP開発のベストプラクティス

1. **ツール定義の明確化**: MCPツールの引数と戻り値を明確に定義してください
2. **エラーハンドリング**: すべてのMCPリクエストを適切にエラーハンドリングしてください
3. **テスト駆動開発**: 新機能を追加する前にテストを作成してください
4. **ドキュメント**: すべてのAPIとツールを適切にドキュメント化してください

## ヘルプの取得

開発中に問題が発生した場合：

- GitHub Issues でバグを報告する
- プロジェクトの Wiki を参照する
- README.md や ARCHITECTURE.md などのドキュメントを確認する

## 環境変数

以下の環境変数を使用して、サーバーの動作をカスタマイズできます：

- `OPENAI_API_KEY`: OpenAI APIキー
- `CLAUDE_API_KEY`: Claude APIキー
- `LOG_LEVEL`: ログレベル（DEBUG, INFO, WARNING, ERROR）
- `MOCK_TTS`: モックモードの有効化（true/false）
- `PORT`: サーバーのポート番号（デフォルト: 8080）

## トラブルシューティング

### 1. Docker関連の問題

- イメージのビルドに失敗する場合：
  ```bash
  # キャッシュを使用せずにビルド
  make build-no-cache
  ```

- コンテナが起動しない場合：
  ```bash
  # ログを確認
  docker logs kokoro-mcp-server
  ```

### 2. PyOpenJTalk関連の問題

CMakeのバージョンに関するエラーが発生する場合：
```bash
# 環境変数を設定してインストール
CMAKE_POLICY_VERSION_MINIMUM=3.5 uv pip install pyopenjtalk
```

これで Kokoro MCP Server の開発環境が整いました。楽しいコーディングを！