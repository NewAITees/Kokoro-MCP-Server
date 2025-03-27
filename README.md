VoiceCraft-MCP-Server は、Claude などの AI アシスタントと連携し、テキストを高品質な音声に変換する MCP (Model Context Protocol) サーバーです。Kokoro の音声合成技術を活用して、自然で表現豊かな音声を生成します。

## 主な機能

- 🎯 AI アシスタントからのテキスト読み上げリクエストを処理
- 🌏 日本語と英語の自然な音声合成をサポート
- 🔊 テキスト読み上げと会話形式の音声生成
- ⚙️ 音声の速度やピッチなどのカスタマイズオプション
- 🧠 自動言語検出機能

## 背景

AI アシスタントとの対話をより自然で豊かなものにするために、テキスト応答を音声に変換する機能は重要です。VoiceCraft-MCP-Server は、Claude などの AI アシスタントと Kokoro 音声合成エンジンを橋渡しし、シームレスな音声体験を提供します。

## 仕組み

VoiceCraft-MCP-Server は以下のように動作します：

1. Claude などの AI アシスタントから MCP プロトコルを通じてテキスト読み上げリクエストを受信
2. リクエストを解析し、必要に応じて言語を自動検出
3. ローカルにインストールされた Kokoro 音声合成エンジンを呼び出し
4. 生成された音声データを AI アシスタントに返送
5. AI アシスタントが音声をユーザーに再生

## クイックスタート

### 前提条件

- Python 3.8 以上
- Kokoro 音声合成エンジン（ローカルにインストール済み）

### インストール

```bash
# リポジトリのクローン
git clone https://github.com/yourusername/VoiceCraft-MCP-Server.git
cd VoiceCraft-MCP-Server

# uvのインストール（macOS/Linux）
curl -sSf https://astral.sh/uv/install.sh | sh
# または（Windows）
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 仮想環境の作成と依存パッケージのインストール
uv venv
source .venv/bin/activate  # または .venv\Scripts\activate（Windows）
uv pip install -r requirements.txt

# 環境変数の設定
cp .env.example .env
# .env ファイルを編集して Kokoro の設定を追加
```

### サーバーの起動

```bash
# 基本的な起動
python src/main.py

# または特定のホスト/ポートを指定
python src/main.py --host 127.0.0.1 --port 8080
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

## 謝辞

- Kokoro の優れた音声合成技術
- MCP (Model Context Protocol) の開発者の皆様
- オープンソースコミュニティの貢献者の皆様
