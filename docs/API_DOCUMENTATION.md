このドキュメントでは、VoiceCraft-MCP-Serverが実装するAPIとModel Context Protocol（MCP）の仕様について詳細に解説します。

## MCPプロトコル概要

Model Context Protocol（MCP）は、AIアシスタント（Claude等）が外部サービスやツールと通信するための標準プロトコルです。VoiceCraft-MCP-Serverは、このプロトコルを実装して音声合成機能を提供します。

### 通信方式

MCPプロトコルはWebSocketベースの双方向通信を使用します。メッセージの形式はJSONで、UTF-8エンコーディングを使用します。

### 基本的なリクエスト/レスポンス形式

```json
// リクエスト
{
  \"command\": \"コマンド名\",
  \"request_id\": \"リクエストID\",
  \"params\": {
    // コマンド固有のパラメータ
  }
}

// レスポンス
{
  \"status\": \"success\",  // または \"error\"
  \"request_id\": \"リクエストID\",
  \"data\": {
    // レスポンスデータ
  }
}
```

## コマンド一覧

VoiceCraft-MCP-Serverは以下のコマンドをサポートしています：

1. `text_to_speech` - テキストを音声に変換
2. `conversation_audio` - 会話形式のテキストを音声に変換
3. `get_capabilities` - サーバーの機能と設定を取得

## コマンド詳細

### 1. text_to_speech

テキストを音声に変換します。

#### リクエスト

```json
{
  \"command\": \"text_to_speech\",
  \"request_id\": \"abc123\",
  \"params\": {
    \"text\": \"音声に変換するテキスト\",
    \"language\": \"japanese\",  // オプション：\"japanese\" または \"english\"
    \"options\": {
      \"speed\": 1.0,          // 再生速度（0.5-2.0）
      \"pitch\": 0.0,          // 音程調整（-10.0-10.0）
      \"voice_id\": \"default\"  // 音声タイプ
    }
  }
}
```

#### パラメータ詳細

| パラメータ | 型 | 必須 | 説明 |
|----------|------|--------|-------------|
| text | string | はい | 音声に変換するテキスト（最大5,000文字） |
| language | string | いいえ | 言語コード。未指定の場合は自動検出（\"japanese\"または\"english\"） |
| options | object | いいえ | 音声オプション |

##### オプションパラメータ

| オプション | 型 | デフォルト | 説明 |
|----------|------|---------|-------------|
| speed | float | 1.0 | 音声の速度。範囲: 0.5（遅い）〜2.0（速い） |
| pitch | float | 0.0 | 音声のピッチ調整。範囲: -10.0（低い）〜10.0（高い） |
| voice_id | string | \"default\" | 使用する音声のID。Kokoroエンジンがサポートする音声IDを指定 |

#### レスポンス

```json
{
  \"status\": \"success\",
  \"request_id\": \"abc123\",
  \"data\": {
    \"audio_data\": \"data:audio/mp3;base64,AUDIO_DATA_BASE64\",
    \"format\": \"mp3\",
    \"duration\": 2.5,  // 音声の長さ（秒）
    \"language\": \"japanese\"  // 使用された言語
  }
}
```

#### エラーレスポンス

```json
{
  \"status\": \"error\",
  \"request_id\": \"abc123\",
  \"error\": {
    \"code\": \"invalid_parameter\",
    \"message\": \"テキストが空です\"
  }
}
```

#### 使用例

```javascript
// クライアント側コード例（JavaScript）
const ws = new WebSocket(\"ws://localhost:8080\");

ws.onopen = () => {
  const request = {
    command: \"text_to_speech\",
    request_id: \"abc123\",
    params: {
      text: \"こんにちは、世界\",
      language: \"japanese\",
      options: {
        speed: 1.2
      }
    }
  };
  
  ws.send(JSON.stringify(request));
};

ws.onmessage = (event) => {
  const response = JSON.parse(event.data);
  if (response.status === \"success\") {
    // audio_dataからBase64データを抽出
    const audioData = response.data.audio_data.split(',')[1];
    // Base64データをバイナリに変換
    const audioBuffer = Uint8Array.from(atob(audioData), c => c.charCodeAt(0));
    // 音声再生処理
    playAudio(audioBuffer);
  } else {
    console.error(\"エラー:\", response.error.message);
  }
};
```

### 2. conversation_audio

会話形式のテキストを音声に変換します。複数の話者が含まれる場合に適しています。

#### リクエスト

```json
{
  \"command\": \"conversation_audio\",
  \"request_id\": \"def456\",
  \"params\": {
    \"text\": \"A: こんにちは\
B: お元気ですか？\
A: はい、元気です\",
    \"language\": \"japanese\",
    \"speakers\": [
      {
        \"name\": \"A\",
        \"voice_id\": \"female_1\"
      },
      {
        \"name\": \"B\",
        \"voice_id\": \"male_1\"
      }
    ],
    \"options\": {
      \"speed\": 1.0,
      \"include_speaker_labels\": true
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
  \"status\": \"success\",
  \"request_id\": \"def456\",
  \"data\": {
    \"audio_data\": \"data:audio/mp3;base64,AUDIO_DATA_BASE64\",
    \"format\": \"mp3\",
    \"duration\": 10.2,
    \"language\": \"japanese\",
    \"speakers\": [\"A\", \"B\"]
  }
}
```

#### 使用例

```javascript
// クライアント側コード例（JavaScript）
const ws = new WebSocket(\"ws://localhost:8080\");

ws.onopen = () => {
  const request = {
    command: \"conversation_audio\",
    request_id: \"def456\",
    params: {
      text: \"User: What's the weather like?\
Assistant: It's sunny today.\",
      language: \"english\",
      speakers: [
        { name: \"User\", voice_id: \"male_1\" },
        { name: \"Assistant\", voice_id: \"female_1\" }
      ]
    }
  };
  
  ws.send(JSON.stringify(request));
};
```

### 3. get_capabilities

サーバーがサポートする機能と設定を取得します。

#### リクエスト

```json
{
  \"command\": \"get_capabilities\",
  \"request_id\": \"ghi789\"
}
```

#### レスポンス

```json
{
  \"status\": \"success\",
  \"request_id\": \"ghi789\",
  \"data\": {
    \"name\": \"VoiceCraft-MCP-Server\",
    \"version\": \"1.0.0\",
    \"supported_languages\": [\"japanese\", \"english\"],
    \"supported_features\": [\"text_to_speech\", \"conversation_audio\"],
    \"voices\": [
      {
        \"id\": \"default\",
        \"name\": \"デフォルト\",
        \"language\": \"japanese\"
      },
      {
        \"id\": \"female_1\",
        \"name\": \"女性 1\",
        \"language\": \"japanese\"
      },
      {
        \"id\": \"male_1\",
        \"name\": \"男性 1\",
        \"language\": \"japanese\"
      },
      {
        \"id\": \"female_en_1\",
        \"name\": \"Female 1\",
        \"language\": \"english\"
      },
      {
        \"id\": \"male_en_1\",
        \"name\": \"Male 1\",
        \"language\": \"english\"
      }
    ],
    \"limits\": {
      \"max_text_length\": 5000,
      \"max_conversation_length\": 10000
    }
  }
}
```

#### 使用例

```javascript
// クライアント側コード例（JavaScript）
const ws = new WebSocket(\"ws://localhost:8080\");

ws.onopen = () => {
  const request = {
    command: \"get_capabilities\",
    request_id: \"ghi789\"
  };
  
  ws.send(JSON.stringify(request));
};

ws.onmessage = (event) => {
  const response = JSON.parse(event.data);
  if (response.status === \"success\") {
    console.log(\"サポートされている言語:\", response.data.supported_languages);
    console.log(\"利用可能な音声:\", response.data.voices);
  }
};
```

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
const ws = new WebSocket(\"ws://localhost:8080\");
ws.onopen = () => {
  ws.send(JSON.stringify({
    command: \"authenticate\",
    params: {
      api_key: \"YOUR_API_KEY\"
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
  \"text\": \"こんにちは、世界\",
  \"language\": \"japanese\",
  \"options\": {
    \"speed\": 1.0
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
  \"status\": \"success\",
  \"data\": {
    \"audio_url\": \"data:audio/mp3;base64,...\"
  }
}
```

## クライアント実装例

### Pythonクライアント

```python
import json
import websocket

# WebSocket接続を作成
ws = websocket.create_connection(\"ws://localhost:8080\")

# リクエストを送信
request = {
    \"command\": \"text_to_speech\",
    \"request_id\": \"python-client-1\",
    \"params\": {
        \"text\": \"こんにちは、世界\",
        \"language\": \"japanese\"
    }
}
ws.send(json.dumps(request))

# レスポンスを受信
response = json.loads(ws.recv())
if response[\"status\"] == \"success\":
    # 音声データを保存
    audio_data = response[\"data\"][\"audio_data\"].split(\",\")[1]
    import base64
    with open(\"output.mp3\", \"wb\") as f:
        f.write(base64.b64decode(audio_data))
    print(\"音声ファイルを保存しました: output.mp3\")
else:
    print(\"エラー:\", response[\"error\"][\"message\"])

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
    command: \"text_to_speech\",
    request_id: \"node-client-1\",
    params: {
      text: \"こんにちは、世界\",
      language: \"japanese\"
    }
  };
  ws.send(JSON.stringify(request));
});

ws.on('message', function incoming(data) {
  const response = JSON.parse(data);
  if (response.status === \"success\") {
    // 音声データを保存
    const audioData = response.data.audio_data.split(',')[1];
    const buffer = Buffer.from(audioData, 'base64');
    fs.writeFileSync('output.mp3', buffer);
    console.log(\"音声ファイルを保存しました: output.mp3\");
  } else {
    console.error(\"エラー:\", response.error.message);
  }
  ws.close();
});
```

## テスト用ツール

開発とテストのために、コマンドラインツールが提供されています：

```bash
# テキスト読み上げのテスト
python tools/test_tts.py --text \"こんにちは、世界\" --language japanese

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
