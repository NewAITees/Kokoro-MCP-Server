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
git clone https://github.com/yourusername/Kokoro-MCP-Server.git
cd Kokoro-MCP-Server

# uvのインストール（まだインストールしていない場合）
# macOS/Linux
curl -sSf https://astral.sh/uv/install.sh | sh
# または Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 仮想環境の作成とパッケージのインストール
make setup

# 環境変数の設定
cp .env.example .env
# .env ファイルをエディタで編集して必要な設定を追加
```

### サーバーの起動

```bash

# または引数付きで起動
uv run kokoro-MCP-server
# 開発モード（モック）での起動
MOCK_TTS=true make run
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

## 謝辞

- Kokoro の優れた音声合成技術
- MCP (Model Context Protocol) の開発者の皆様
- オープンソースコミュニティの貢献者の皆様
