Kokoro-MCP-Server は、Claude などの AI アシスタントと連携し、テキストを高品質な音声に変換する MCP (Model Context Protocol) サーバーです。Kokoro の音声合成技術を活用して、自然で表現豊かな音声を生成します。

## 主な機能

- 🎯 AI アシスタントからのテキスト読み上げリクエストを処理
- 🌏 日本語と英語の自然な音声合成をサポート
- 🔊 テキスト読み上げと会話形式の音声生成
- ⚙️ 音声の速度やピッチなどのカスタマイズオプション
- 🧠 自動言語検出機能

## 背景

AI アシスタントとの対話をより自然で豊かなものにするために、テキスト応答を音声に変換する機能は重要です。Kokoro-MCP-Server は、Claude などの AI アシスタントと Kokoro 音声合成エンジンを橋渡しし、シームレスな音声体験を提供します。

## クイックスタート

### 前提条件

- Python 3.8 以上
- uv パッケージマネージャー
- Kokoro 音声合成エンジン（実モードで使用する場合）

### インストール

```bash
# リポジトリのクローン
git clone https://github.com/NewAITeesKokoro-MCP-Server.git
cd Kokoro-MCP-Server

# uvのインストール（まだインストールしていない場合）
# macOS/Linux
curl -sSf https://astral.sh/uv/install.sh | sh
# または Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# まず、仮想環境を作成
uv venv .venv

# 仮想環境をアクティベート
# Windowsの場合
.\.venv\Scripts\activate


# Hugging Face CLIをインストールして認証
pip install huggingface_hub
huggingface-cli login

# 環境変数の設定


cp .env.example .env

# Linux系のコマンド
CMAKE_POLICY_VERSION_MINIMUM=3.5 uv add pyopenjtalk

# windows系でインストールするときのコマンド
$env:CMAKE_POLICY_VERSION_MINIMUM = "3.5"; uv add pyopenjtalk

# .env ファイルをエディタで編集して必要な設定を追加

uv run src/main.py

```

### サーバーの起動

```bash
# モックモードで実行（Kokoroパッケージがインストールされていない環境向け）
MOCK_TTS=true python -m kokoro_mcp_server

# または
MOCK_TTS=true python src/main.py

# 実モードで実行（Kokoroパッケージがインストールされている環境向け）
python -m kokoro_mcp_server

# または
python src/main.py
```

### 開発者向けコマンド

```bash
# テストの実行
make test

# コードのフォーマット
make format

# リントチェック
make lint

# キャッシュとビルドファイルのクリーンアップ
make clean
```

## 使用方法

Claude などの AI アシスタントから、以下のようなプロンプトを送信できます：

- 「この内容を日本語で読んで」
- 「英語で会話して」
- 「次のテキストを音声に変換して: こんにちは、世界」

AI アシスタントがこれらのリクエストを認識すると、MCP プロトコルを通じて VoiceCraft-MCP-Server にリクエストが送信され、音声が生成されます。

## 機能と設定

### サポートされている言語

- 日本語
- 英語

※ 将来的に他の言語も追加予定です。

### 音声カスタマイズオプション

以下のオプションをサポートしています：

- 速度調整 (0.5 - 2.0)
- ピッチ調整 (-10.0 - 10.0)
- 音声タイプ選択 (利用可能な Kokoro の音声モデルに依存)

## MCP プロトコルの統合

VoiceCraft-MCP-Server は、Model Context Protocol (MCP) を実装しており、Claude などの AI アシスタントと簡単に連携できます。MCP は AI システムが外部ツールやサービスと通信するための標準プロトコルです。

AI アシスタントの設定から、MCP サーバーとして VoiceCraft-MCP-Server を追加することで、テキスト読み上げ機能を有効化できます。

## 開発情報

### プロジェクト構造

```
VoiceCraft-MCP-Server/
├── src/
│   ├── main.py               # エントリーポイント
│   ├── mcp/                  # MCP プロトコル実装
│   ├── kokoro/               # Kokoro 連携モジュール
│   ├── language/             # 言語処理モジュール
│   └── audio/                # 音声処理モジュール
├── tests/                    # テストコード
├── docs/                     # ドキュメント
├── examples/                 # 使用例
├── requirements.txt          # 依存パッケージ
└── README.md                 # このファイル
```

### 貢献

バグレポートや機能リクエスト、プルリクエストなど、あらゆる形での貢献を歓迎します。詳細は [CONTRIBUTING.md](docs/CONTRIBUTING.md) を参照してください。

## ライセンス


このプロジェクトは [MIT ライセンス](LICENSE) の下で公開されています。

## サードパーティライセンス

このプロジェクトで使用しているサードパーティライブラリのライセンス情報については、[THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md) を参照してください。


## トラブルシューティング

### よくある問題と解決策

#### インストール関連の問題

1. **`error: アクセスが拒否されました。(os error 5)`**
   - **原因**: パッケージのインストール時に権限の問題が発生
   - **解決策**: 
     ```bash
     # 管理者権限でコマンドプロンプトかPowerShellを実行するか、
     # 以下のようにインストールを試みる
     uv pip install --user fugashi[unidic]
     
     # または一旦仮想環境を削除して再作成
     rm -rf .venv
     uv venv .venv
     .\.venv\Scripts\activate
     ```

2. **PyOpenJTalkのインストールエラー**
   - **原因**: プラットフォームの互換性やビルド環境の問題
   - **解決策**:
     ```bash
     # Windowsの場合は環境変数を設定してから
     $env:CMAKE_POLICY_VERSION_MINIMUM = "3.5"
     uv pip install pyopenjtalk
     
     # 上記が失敗する場合はprebuiltホイールを試す
     uv pip install https://github.com/r9y9/pyopenjtalk/releases/download/v0.3.0/pyopenjtalk-0.3.0-cp39-cp39-win_amd64.whl
     
     # それでも失敗する場合はモックモードでの実行を検討
     MOCK_TTS=true uv run src/main.py
     ```

#### 依存関係のエラー

1. **`ImportError: cannot import name 'table' from 'wasabi'`**
   - **原因**: wasabiパッケージのバージョンが互換性のないものになっている
   - **解決策**:
     ```bash
     # 依存関係パッケージの適切なバージョンをインストール
     uv pip install 'wasabi>=0.10.0' 'spacy>=3.5.0' 'thinc>=8.1.0'
     
     # または依存関係を一括でアップグレード
     uv pip install --upgrade wasabi spacy thinc
     ```

2. **`ERROR:kokoro-mcp-server:Kokoro package is not installed`**
   - **原因**: Kokoroパッケージがインストールされていないか、アクセスできない
   - **解決策**:
     ```bash
     # Kokoroパッケージをインストールするか、
     # モックモードで実行して代替の音声合成を使用
     MOCK_TTS=true uv run src/main.py
     ```

#### サーバー起動の問題

1. **タイムアウトやコネクション関連のエラー**
   - **原因**: 起動プロセスが完了する前にクライアントからの要求があった
   - **解決策**:
     ```bash
     # ログを詳細に確認
     uv run src/main.py --log-level DEBUG
     
     # クライアント側でタイムアウト設定を調整
     # または、システムリソースの使用状況を確認
     ```

### サーバーの動作モード

1. **実モード** - Kokoroパッケージを使用して高品質な音声を生成
   ```bash
   uv run src/main.py
   ```

2. **モックモード** - Kokoroパッケージなしでもサーバーをテスト実行可能
   ```bash
   MOCK_TTS=true uv run src/main.py
   ```

### バージョン互換性

- Python: 3.8以上必須
- 依存ライブラリのバージョン要件:
  - wasabi >= 0.10.0
  - spacy >= 3.5.0 
  - thinc >= 8.1.0
  - fugashi + unidic

### ログの確認

問題診断には詳細なログを確認することをお勧めします:

```bash
# 詳細ログの有効化
uv run src/main.py --log-level DEBUG

# ログファイルへの出力
uv run src/main.py --log-file kokoro-mcp-server.log
```

より詳細なトラブルシューティングが必要な場合は、[Issue](https://github.com/NewAITees/Kokoro-MCP-Server/issues)を作成してください。


## 謝辞

- Kokoro の優れた音声合成技術
- MCP (Model Context Protocol) の開発者の皆様
- オープンソースコミュニティの貢献者の皆様
