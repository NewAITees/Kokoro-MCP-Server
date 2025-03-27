このドキュメントでは、VoiceCraft-MCP-Serverが実装するAPIとModel Context Protocol（MCP）の仕様について詳細に解説します。

## MCPプロトコル概要

Model Context Protocol（MCP）は、AIアシスタント（Claude等）が外部ツールを呼び出してその機能を利用するためのオープンプロトコルです。VoiceCraft-MCP-Serverは、このプロトコルを実装して音声合成機能を提供します。

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

## VoiceCraft-MCP-Server固有のコマンド

VoiceCraft-MCP-Serverは、MCPプロトコルの基本機能に加えて、以下の音声合成特化コマンドを提供します：

### 1. text_to_speech

単一のテキストを音声に変換します。

#### リクエスト

```json
{
  "command": "text_to_speech",
  "request_id": "abc123",
  "params": {
    "text": "音声に変換するテキスト",
    "language": "japanese",  // オプション
    "options": {
      "speed": 1.0,          // 再生速度
      "pitch": 0.0,          // 音程調整
      "voice_id": "default"  // 音声タイプ
    }
  }
}
```

#### パラメータ詳細

| パラメータ | 型 | 必須 | 説明 |
|----------|------|--------|-------------|
| text | string | はい | 音声に変換するテキスト（最大5,000文字） |
| language | string | いいえ | 言語コード。未指定の場合は自動検出（"japanese"または"english"） |
| options | object | いいえ | 音声オプション |

##### オプションパラメータ

| オプション | 型 | デフォルト | 説明 |
|----------|------|---------|-------------|
| speed | float | 1.0 | 音声の速度。範囲: 0.5（遅い）〜2.0（速い） |
| pitch | float | 0.0 | 音声のピッチ調整。範囲: -10.0（低い）〜10.0（高い） |
| voice_id | string | "default" | 使用する音声のID。Kokoroエンジンがサポートする音声IDを指定 |

#### レスポンス

```json
{
  "status": "success",
  "request_id": "abc123",
  "data": {
    "audio_data": "data:audio/mp3;base64,AUDIO_DATA_BASE64",
    "format": "mp3",
    "duration": 2.5,  // 音声の長さ（秒）
    "language": "japanese"  // 使用された言語
  }
}
```

#### エラーレスポンス

```json
{
  "status": "error",
  "request_id": "abc123",
  "error": {
    "code": "invalid_parameter",
    "message": "テキストが空です"
  }
}
```

#### 使用例

```javascript
// クライアント側コード例（JavaScript）
const ws = new WebSocket("ws://localhost:8080");

ws.onopen = () => {
  const request = {
    command: "text_to_speech",
    request_id: "abc123",
    params: {
      text: "こんにちは、世界",
      language: "japanese",
      options: {
        speed: 1.2
      }
    }
  };
  
  ws.send(JSON.stringify(request));
};

ws.onmessage = (event) => {
  const response = JSON.parse(event.data);
  if (response.status === "success") {
    // audio_dataからBase64データを抽出
    const audioData = response.data.audio_data.split(',')[1];
    // Base64データをバイナリに変換
    const audioBuffer = Uint8Array.from(atob(audioData), c => c.charCodeAt(0));
    // 音声再生処理
    playAudio(audioBuffer);
  } else {
    console.error("エラー:", response.error.message);
  }
};
```

### 2. conversation_audio

会話形式のテキストを音声に変換します。複数の話者が含まれる場合に適しています。

#### リクエスト

```json
{
  "command": "conversation_audio",
  "request_id": "def456",
  "params": {
    "text": "A: こんにちは\nB: お元気ですか？",
    "language": "japanese",
    "speakers": [
      {
        "name": "A",
        "voice_id": "female_1"
      },
      {
        "name": "B",
        "voice_id": "male_1"
      }
    ],
    "options": {
      "speed": 1.0,
      "include_speaker_labels": true
    }
  }
}
```

#### パラメータ詳細

| パラメータ | 型 | 必須 | 説明 |
|----------|------|--------|-------------|
| text | string | はい | 会話テキスト（最大10,000文字） |
| language | string | いいえ | 言語コード（未指定の場合は自動検出） |
| speakers | array | いいえ | 話者情報の配列 |
| options | object | いいえ | 音声オプション |

##### 話者情報

| フィールド | 型 | 必須 | 説明 |
|----------|------|--------|-------------|
| name | string | はい | 話者の識別子（テキスト内で使用） |
| voice_id | string | はい | 使用する音声ID |

##### オプションパラメータ

| オプション | 型 | デフォルト | 説明 |
|----------|------|---------|-------------|
| speed | float | 1.0 | 音声の速度 |
| include_speaker_labels | boolean | false | 話者ラベルを音声に含めるかどうか |

#### レスポンス

```json
{
  "status": "success",
  "request_id": "def456",
  "data": {
    "audio_data": "data:audio/mp3;base64,AUDIO_DATA_BASE64",
    "format": "mp3",
    "duration": 10.2,
    "language": "japanese",
    "speakers": ["A", "B"]
  }
}
```

#### 使用例

```javascript
// クライアント側コード例（JavaScript）
const ws = new WebSocket("ws://localhost:8080");

ws.onopen = () => {
  const request = {
    command: "conversation_audio",
    request_id: "def456",
    params: {
      text: "User: What's the weather like?\nAssistant: It's sunny today.",
      language: "english",
      speakers: [
        { name: "User", voice_id: "male_1" },
        { name: "Assistant", voice_id: "female_1" }
      ]
    }
  };
  
  ws.send(JSON.stringify(request));
};
```

### 3. get_capabilities

サーバーの機能と設定を取得します。

```json
{
  "command": "get_capabilities",
  "request_id": "ghi789"
}
```

レスポンス例：
```json
{
  "status": "success",
  "request_id": "ghi789",
  "data": {
    "supported_languages": ["japanese", "english"],
    "available_voices": {
      "japanese": ["default", "female_1", "male_1"],
      "english": ["default", "female_1", "male_1"]
    },
    "max_text_length": 5000,
    "speed_range": {
      "min": 0.5,
      "max": 2.0
    },
    "pitch_range": {
      "min": -10.0,
      "max": 10.0
    }
  }
}
```

#### パラメータ詳細

| フィールド | 型 | 説明 |
|----------|------|-------------|
| supported_languages | array | サポートされている言語のリスト |
| available_voices | object | 言語ごとの利用可能な音声IDのマップ |
| max_text_length | number | 一度に処理可能な最大テキスト長 |
| speed_range | object | 音声速度の調整可能範囲 |
| pitch_range | object | 音声ピッチの調整可能範囲 |

## エラーコード

サーバーから返されるエラーコードと意味は以下の通りです：

| エラーコード | 説明 |
|------------|-------------|
| invalid_command | 不明なコマンド |
| invalid_parameter | 無効なパラメータ |
| missing_parameter | 必須パラメータの欠落 |
| text_too_long | テキストが長すぎる |
| unsupported_language | サポートされていない言語 |
| unsupported_format | サポートされていない形式 |
| speech_generation_failed | 音声生成に失敗 |
| rate_limit_exceeded | レート制限超過 |
| server_error | サーバー内部エラー |

## レート制限

サーバーには以下のレート制限が設定されています：

- 1分あたり最大60リクエスト
- 1日あたり最大1,000リクエスト

制限を超えた場合、`rate_limit_exceeded` エラーが返されます。

## 認証（オプション）

認証が必要な環境では、WebSocket接続時にクエリパラメータで認証情報を提供できます：

```
ws://localhost:8080?api_key=YOUR_API_KEY
```

または、リクエストヘッダーで認証情報を提供することも可能です：

```javascript
const ws = new WebSocket("ws://localhost:8080");
ws.onopen = () => {
  ws.send(JSON.stringify({
    command: "authenticate",
    params: {
      api_key: "YOUR_API_KEY"
    }
  }));
};
```

## HTTPインターフェース

WebSocketに加えて、シンプルなHTTPインターフェースも提供しています：

### テキスト読み上げ（HTTP）

```
POST /api/tts
Content-Type: application/json

{
  "text": "こんにちは、世界",
  "language": "japanese",
  "options": {
    "speed": 1.0
  }
}
```

レスポンス：

```
HTTP/1.1 200 OK
Content-Type: audio/mp3

[音声データ]
```

または：

```
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "success",
  "data": {
    "audio_url": "data:audio/mp3;base64,...\"
  }
}
```

## クライアント実装例

### Pythonクライアント

```python
import json
import websocket

# WebSocket接続を作成
ws = websocket.create_connection("ws://localhost:8080")

# リクエストを送信
request = {
    "command": "text_to_speech",
    "request_id": "python-client-1",
    "params": {
        "text": "こんにちは、世界",
        "language": "japanese"
    }
}
ws.send(json.dumps(request))

# レスポンスを受信
response = json.loads(ws.recv())
if response["status"] == "success":
    # 音声データを保存
    audio_data = response["data"]["audio_data"].split(",")[1]
    import base64
    with open("output.mp3", "wb") as f:
        f.write(base64.b64decode(audio_data))
    print("音声ファイルを保存しました: output.mp3")
else:
    print("エラー:", response["error"]["message"])

# 接続を閉じる
ws.close()
```

### Node.jsクライアント

```javascript
const WebSocket = require('ws');
const fs = require('fs');

// WebSocket接続を作成
const ws = new WebSocket('ws://localhost:8080');

ws.on('open', function open() {
  // リクエストを送信
  const request = {
    command: "text_to_speech",
    request_id: "node-client-1",
    params: {
      text: "こんにちは、世界",
      language: "japanese"
    }
  };
  ws.send(JSON.stringify(request));
});

ws.on('message', function incoming(data) {
  const response = JSON.parse(data);
  if (response.status === "success") {
    // 音声データを保存
    const audioData = response.data.audio_data.split(',')[1];
    const buffer = Buffer.from(audioData, 'base64');
    fs.writeFileSync('output.mp3', buffer);
    console.log("音声ファイルを保存しました: output.mp3");
  } else {
    console.error("エラー:", response.error.message);
  }
  ws.close();
});
```

## テスト用ツール

開発とテストのために、コマンドラインツールが提供されています：

```bash
# テキスト読み上げのテスト
python tools/test_tts.py --text "こんにちは、世界" --language japanese

# 会話音声のテスト
python tools/test_conversation.py --file conversation.txt
```

## 推奨使用方法

1. 起動時に `get_capabilities` を呼び出して、サポートされる機能と音声を確認
2. ユーザー入力に基づいて適切なコマンドを選択
3. 言語の自動検出機能を活用（特に多言語テキストの場合）
4. 大きなテキストは適切なチャンクに分割して送信

## 将来の拡張

このAPIは将来、以下の機能で拡張される予定です：

1. スピーチマークのサポート（字幕やアニメーション同期用）
2. ストリーミング音声出力
3. 感情パラメータ
4. 音声認識との統合

最新の機能と変更については、プロジェクトのGitHubリポジトリを参照してください。
