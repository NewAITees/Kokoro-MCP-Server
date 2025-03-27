
このガイドでは、VoiceCraft-MCP-Server プロジェクトの開発環境をセットアップする方法を詳しく説明します。

## 前提条件

VoiceCraft-MCP-Server の開発には以下のソフトウェアが必要です：

- Python 3.8 以上
- pip (最新版)
- Git
- Kokoro 音声合成エンジン

## 基本セットアップ

### 1. リポジトリのクローン

```bash
# リポジトリのクローン
git clone https://github.com/yourusername/VoiceCraft-MCP-Server.git
cd VoiceCraft-MCP-Server
```

### 2. 仮想環境の作成と有効化

プロジェクト専用の Python 仮想環境を作成することをお勧めします。

```bash
# 仮想環境の作成
python -m venv venv

# 仮想環境の有効化（Windows）
venv\\Scripts\\activate

# 仮想環境の有効化（macOS/Linux）
source venv/bin/activate
```

### 3. 依存パッケージのインストール

```bash
# 依存パッケージのインストール
pip install -r requirements.txt

# 開発用パッケージのインストール
pip install -r requirements-dev.txt
```

## Kokoro 音声合成エンジンのセットアップ

Kokoro は、ローカルで動作する高品質な音声合成エンジンです。以下の手順でインストールします。

### 1. Kokoro のダウンロードとインストール

公式サイトから Kokoro をダウンロードし、インストールします。

```bash
# Kokoro モデルをダウンロードするディレクトリを作成
mkdir -p models/kokoro

# モデルのダウンロード（以下は例です）
# 実際のダウンロード URL やインストール手順は Kokoro の公式ドキュメントを参照してください
cd models/kokoro
# ここに日本語モデルと英語モデルをダウンロードします
```

### 2. モデルの配置

ダウンロードしたモデルファイルを適切なディレクトリに配置します。

```bash
# モデルファイルの配置例
models/
├── kokoro/
│   ├── japanese/
│   │   └── model_files...
│   └── english/
│       └── model_files...
```

### 3. 環境変数の設定

Kokoro の設定を環境変数に追加します。

```bash
# .env ファイルをサンプルからコピー
cp .env.example .env

# .env ファイルをエディタで開いて編集
# KOKORO_MODEL_PATH=./models/kokoro
# KOKORO_JAPANESE_MODEL=japanese
# KOKORO_ENGLISH_MODEL=english
```

## 開発用設定

### 1. 開発モードの有効化

開発モードでは、デバッグログが有効になり、変更が自動的に反映されます。

```bash
# 開発モードで実行
python src/main.py --dev
```

### 2. ログ設定

ログレベルを調整することで、詳細なデバッグ情報を表示できます。

```bash
# デバッグログを有効にして実行
python src/main.py --log-level debug
```

### 3. ポートの設定

デフォルトでは、サーバーは `8080` ポートで起動しますが、変更も可能です。

```bash
# カスタムポートで実行
python src/main.py --port 9000
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

### 2. モック環境の使用

Kokoro 音声合成エンジンが利用できない環境でも開発を行えるよう、モック機能が用意されています。

```bash
# モックモードで実行
python src/main.py --mock
```

モックモードでは、実際の音声合成の代わりにサンプル音声ファイルが返されます。

### 3. テスト用クライアント

MCP サーバーの動作をテストするためのクライアントツールが提供されています。

```bash
# テストクライアントの実行
python tools/test_client.py --text \"こんにちは、世界\" --language \"japanese\"
```

## デバッグ手法

### 1. デバッグログの有効化

詳細なデバッグ情報を確認するには、ログレベルを調整します。

```bash
# デバッグログを有効にして実行
python src/main.py --log-level debug
```

### 2. 対話的デバッグ

Python の `pdb` またはより高度な `ipdb` を使用して、対話的にコードをデバッグできます。

```python
# コード内でデバッグポイントを設定
import pdb; pdb.set_trace()
# または
import ipdb; ipdb.set_trace()
```

### 3. リクエスト/レスポンスの記録

開発中は、すべてのリクエストとレスポンスを記録して後で分析することができます。

```bash
# リクエスト/レスポンスの記録を有効にして実行
python src/main.py --record-requests
```

記録されたリクエストとレスポンスは `logs/requests/` ディレクトリに保存されます。

## コードスタイルとリンター

### 1. コードスタイルのチェック

このプロジェクトでは、PEP 8 スタイルガイドとプロジェクト固有のルールに従ったコードスタイルを採用しています。

```bash
# コードスタイルのチェック
flake8 src/ tests/

# 自動整形
black src/ tests/

# インポートの整理
isort src/ tests/
```

### 2. 型チェック

静的型チェックには mypy を使用しています。

```bash
# 型チェックの実行
mypy src/
```

## 一般的なワークフロー

開発作業の一般的なワークフローは以下の通りです：

1. 機能ブランチを作成する
   ```bash
   git checkout -b feature/new-feature
   ```

2. コードを変更し、テストを追加する

3. テストを実行して変更が機能することを確認する
   ```bash
   pytest
   ```

4. コードスタイルをチェックし、必要に応じて修正する
   ```bash
   flake8 src/ tests/
   black src/ tests/
   ```

5. 変更をコミットする
   ```bash
   git add .
   git commit -m \"Add new feature: description\"
   ```

6. プルリクエストを作成する

## トラブルシューティング

### 1. 仮想環境の問題

仮想環境の問題が発生した場合は、環境を再作成してください。

```bash
# 仮想環境を削除して再作成
rm -rf venv
python -m venv venv
source venv/bin/activate  # または venv\\Scripts\\activate (Windows)
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Kokoro エンジンの接続問題

Kokoro 音声合成エンジンに接続できない場合：

- `.env` ファイルのパス設定を確認
- モデルファイルが正しくダウンロードされているか確認
- `--mock` モードで実行して、サーバー自体の動作を確認

### 3. ポートの競合

指定したポートが既に使用されている場合：

```bash
# 別のポートで実行
python src/main.py --port 8081
```

または：

```bash
# 現在ポートを使用しているプロセスを確認（Linux/macOS）
lsof -i :8080

# 現在ポートを使用しているプロセスを確認（Windows）
netstat -ano | findstr :8080
```

## パフォーマンスプロファイリング

アプリケーションのパフォーマンスをプロファイリングするツールも提供されています。

```bash
# プロファイリングを有効にして実行
python -m cProfile -o profile.stats src/main.py

# 結果の分析
python -m pstats profile.stats
# または
snakeviz profile.stats  # snakeviz がインストールされている場合
```

## 開発者ツール

### 1. 開発者ダッシュボード

開発中にサーバーの状態を監視するためのダッシュボードがあります。

```bash
# ダッシュボードを有効にして実行
python src/main.py --dashboard
```

ダッシュボードには `http://localhost:8081` でアクセスできます（デフォルト）。

### 2. API ドキュメントの生成

API ドキュメントは自動的に生成されます。

```bash
# API ドキュメントの生成
python tools/generate_api_docs.py
```

生成されたドキュメントは `docs/api/` ディレクトリに保存されます。

## CI/CD パイプライン

このプロジェクトでは CI/CD パイプラインを使用して、コードの品質と一貫性を確保しています。

- プルリクエスト時に自動的にテストが実行されます
- マージ前にコードスタイルと型チェックが行われます
- リリースブランチへのマージ時に自動的にバージョンがタグ付けされます

## ヘルプの取得

開発中に問題が発生した場合：

- GitHub Issues でバグを報告する
- プロジェクトの Wiki を参照する
- コードのドキュメンテーションを確認する

---

これで VoiceCraft-MCP-Server の開発環境が整いました。楽しいコーディングを！
