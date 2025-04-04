# Kokoro MCP Server API ドキュメント

このドキュメントでは、Kokoro MCP Serverが実装するAPIとModel Context Protocol（MCP）の仕様について詳細に解説します。

## MCPプロトコル概要

Model Context Protocol（MCP）は、AIアシスタント（Claude等）が外部ツールを呼び出してその機能を利用するためのオープンプロトコルです。Kokoro MCP Serverは、このプロトコルを実装して音声合成機能を提供します。

### プロトコルの特徴

MCPプロトコルは以下の主要な要素で構成されています：

1. **Resources**: ファイルや情報などのリソースをLLMに提供
2. **Tools**: LLMが呼び出せる機能（関数）
3. **Prompts**: 再利用可能なプロンプトテンプレート
4. **Roots**: サーバーが操作できる境界を定義
5. **Sampling**: サーバーがLLMからの応答を要求する機能

### 通信アーキテクチャ

MCPでは、以下のようなフローで通信が行われます：

1. ユーザーがAIアシスタントにリクエスト（例：「この文章を音声に変換して」）
2. AIアシスタントがMCPサーバーに必要な機能（ツール等）を確認
3. AIアシスタントが適切なツールを選び、必要なパラメータと共に呼び出し
4. MCPサーバーがリクエストを処理し、結果を返す
5. AIアシスタントがその結果を元にユーザーに応答

### 通信方式

MCPは以下の通信方式をサポートしています：

1. **WebSocket**: 双方向リアルタイム通信（推奨）
2. **HTTP/SSE**: HTTPベースの通信とServer-Sent Events
3. **STDIO**: 標準入出力を使用したローカルプロセス間通信

メッセージの形式はJSONで、UTF-8エンコーディングを使用します。また、JSON-RPC 2.0の仕様に基づくメッセージングフォーマットを採用しています。

## Kokoro MCP Serverが提供するツール

Kokoro MCP Serverは、MCPプロトコルに準拠し、以下のツールとリソースを提供します：

### ツール

#### 1. text_to_speech

テキストを音声に変換するツールです。

**パラメータ**:

| パラメータ | タイプ | 必須 | 説明 |
|----------|------|-----|-------------|
| text | string | はい | 音声に変換するテキスト |
| voice | string | いいえ | 使用する音声ID（デフォルト: "jf_alpha"） |
| speed | float | いいえ | 音声の速度（範囲: 0.5-2.0, デフォルト: 1.0） |

**戻り値**:
- 成功時: 生成された音声データ（.wav形式）
- 失敗時: エラーメッセージ

**使用例**:
```python
# MCP クライアント側の例
response = mcp_client.call_tool("text_to_speech", {
    "text": "こんにちは、世界",
    "voice": "jf_alpha",
    "speed": 1.0
})
```

#### 2. list_voices

利用可能な音声の一覧を取得するツールです。

**パラメータ**: なし

**戻り値**:
- 利用可能な音声IDのリストを含む文字列

**使用例**:
```python
# MCP クライアント側の例
response = mcp_client.call_tool("list_voices")
```

### リソース

#### 1. voices://available

利用可能な音声の一覧を提供するリソースです。

**戻り値**:
- 利用可能な音声IDの配列を含むJSON文字列

```json
{
  "voices": ["jf_alpha", "jf_beta", "jf_gamma"]
}
```

#### 2. audio://recent

最近生成された音声ファイルの一覧を提供するリソースです。

**戻り値**:
- 最近生成された音声ファイルの情報を含むJSON文字列

```json
{
  "audio_files": [
    {
      "name": "jf_alpha_20250405_120000.wav",
      "path": "output/audio/jf_alpha_20250405_120000.wav",
      "created": 1712312400
    },
    ...
  ]
}
```

## エラーコード

サーバーから返されるエラーメッセージは以下のカテゴリに分類されます：

1. **入力検証エラー**: テキストが空、速度が範囲外など
2. **音声生成エラー**: 音声合成エンジンが失敗した場合
3. **システムエラー**: サーバー内部で発生した予期せぬエラー

## 実装詳細

### TTSエンジン

Kokoro MCP Serverは内部で以下のTTSエンジンを使用しています：

1. **Kokoro TTS**: 高品質な日本語音声合成エンジン
2. **Mock TTS**: 開発・テスト用のモックエンジン（環境変数 `MOCK_TTS=true` で有効化）

### 音声特性

生成される音声ファイルは以下の特性を持ちます：

- **フォーマット**: WAV
- **サンプルレート**: 44100Hz
- **チャンネル**: モノラル
- **速度調整範囲**: 0.5倍（遅い）〜2.0倍（速い）

## テストと開発

### クライアント側テストコード例（Python）

```python
import json
import requests

# HTTPインターフェースを使用する場合
def test_http_tts():
    response = requests.post(
        "http://localhost:8080/api/tts",
        json={
            "text": "こんにちは、世界",
            "voice": "jf_alpha",
            "speed": 1.0
        }
    )
    
    # 音声データを保存
    if response.status_code == 200:
        with open("output.wav", "wb") as f:
            f.write(response.content)
        print("音声ファイルを保存しました: output.wav")
    else:
        print(f"エラー: {response.text}")

# MCPクライアントを使用する場合
from mcp.client import MCPClient

def test_mcp_tts():
    client = MCPClient("localhost:8080")
    result = client.call_tool("text_to_speech", {
        "text": "こんにちは、世界",
        "voice": "jf_alpha",
        "speed": 1.0
    })
    
    # 結果を処理
    # ...

if __name__ == "__main__":
    test_http_tts()
```

### Claude Desktopとの統合

Claude Desktopの設定ファイル例（`claude_desktop_config.json`）:

```json
{
  "mcpServers": {
    "kokoro-tts": {
      "command": "docker",
      "args": ["compose", "-f", "/path/to/your/Kokoro-MCP-Server/docker-compose.yml", "run", "--rm", "-T", "kokoro-mcp-server"]
    }
  }
}
```

## セキュリティと制限

1. **ローカル実行**: Kokoro MCP Serverはローカル環境での実行を前提としており、外部からのアクセスを想定していません
2. **テキスト長**: 処理可能なテキストの長さに実質的な制限はありませんが、非常に長いテキストは処理に時間がかかります

## 今後の開発予定

以下の機能拡張を計画しています：

1. **多言語サポート**: 英語など他の言語への対応強化
2. **感情表現**: 感情を持った音声合成の実現
3. **音声スタイル**: より多様な音声スタイルのサポート
4. **ストリーミング出力**: 大きなテキストの処理効率化

## APIの変更と下位互換性

APIの変更があった場合は、CHANGELOG.mdに記録します。下位互換性を保つよう努めますが、大きな変更が必要な場合はメジャーバージョンを更新します。

## 関連リソース

- [MCP プロトコル仕様](https://github.com/mcp-dev/mcp-spec)
- [Claude Developer Platform](https://docs.anthropic.com/claude/docs)

---

このドキュメントは継続的に更新されます。最新版は常にリポジトリを参照してください。