# Kokoro MCP Server

Kokoro MCP ServerはModel Context Protocol (MCP)を使用して、高品質な日本語音声合成を提供するサーバーです。

## 機能

- 高品質な日本語音声合成
- MCPプロトコル対応（Claude Desktopなどと連携可能）
- 日本語テキスト処理（MeCab, fugashi）
- 音声速度の調整
- モックモードサポート（開発用）

## 必要条件

- Docker と Docker Compose
- Claude Desktop（オプション）

## インストール方法

### Dockerを使用した実行

1. リポジトリのクローン:
```bash
git clone https://github.com/yourusername/Kokoro-MCP-Server.git
cd Kokoro-MCP-Server
```

2. Dockerイメージのビルドと実行:
```bash
# ビルド
make build

# 起動
make up

# ログの確認
make logs
```

### 環境変数の設定

`.env`ファイルを作成して環境変数をカスタマイズできます：

```bash
# .envファイルの例
MOCK_TTS=false    # モックモードの有効/無効
LOG_LEVEL=INFO    # ログレベル（DEBUG/INFO/WARNING/ERROR）
```

## Claude Desktopとの連携

1. Claude Desktop設定ファイルのインストール:
```bash
make setup-claude
```

2. 設定ファイルの編集:
設定ファイルの場所:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

3. パスの設定:
設定ファイル内の`/path/to/your/Kokoro-MCP-Server`を実際のパスに変更してください。

## 開発者向け情報

### 開発環境の起動

モックモードでの開発:
```bash
make dev
```

### テストの実行

```bash
make test
```

### マルチアーキテクチャビルド

x86_64とarm64の両方のアーキテクチャ用のイメージをビルド:
```bash
# DockerHubユーザー名を設定
export DOCKER_HUB_USERNAME=yourusername

# ビルドの実行
make multi-arch-build
```

## コマンドリファレンス

Makefileで提供される主なコマンド:

- `make build`: Dockerイメージのビルド
- `make up`: コンテナの起動
- `make down`: コンテナの停止
- `make logs`: ログの表示
- `make shell`: コンテナ内でシェルを起動
- `make clean`: コンテナとイメージの削除
- `make dev`: 開発モードでの起動
- `make test`: テストの実行
- `make multi-arch-build`: マルチアーキテクチャビルド

## トラブルシューティング

### よくある問題と解決方法

1. MeCabの初期化エラー:
```bash
# コンテナ内でMeCabの設定を確認
make shell
ls -l /usr/local/etc/mecabrc
```

2. 音声出力エラー:
- 出力ディレクトリのパーミッションを確認
- ログレベルをDEBUGに設定して詳細を確認

3. Claude Desktopとの接続エラー:
- 設定ファイルのパスが正しいか確認
- Dockerコンテナが起動しているか確認

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 貢献

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. Pull Requestを作成

## 謝辞

このプロジェクトは以下のオープンソースプロジェクトを使用しています：

- [MeCab](https://taku910.github.io/mecab/)
- [fugashi](https://github.com/polm/fugashi)
- [PyOpenJTalk](https://github.com/r9y9/pyopenjtalk)

詳細は[THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md)を参照してください。
