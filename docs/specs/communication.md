# 通信プロトコル仕様

## 概要

orchestrator-cc は、MCP（Model Context Protocol）を使用してClaude Codeインスタンス間の通信を実現します。

## プロトコルスタック

```
┌─────────────────────────────────────────────────────────┐
│  アプリケーション層    │  orchestrator-cc メッセージ   │
├─────────────────────────────────────────────────────────┤
│  プレゼンテーション層  │  MCP (Model Context Protocol) │
├─────────────────────────────────────────────────────────┤
│  RPC層               │  JSON-RPC 2.0                  │
├─────────────────────────────────────────────────────────┤
│  トランスポート層     │  stdio (標準入出力)           │
└─────────────────────────────────────────────────────────┘
```

## JSON-RPC 2.0

### 基本形式

```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "method": "method_name",
  "params": { ... }
}
```

### レスポンス形式

```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "result": { ... }
}
```

### エラー形式

```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "error": {
    "code": -32601,
    "message": "Method not found",
    "data": { ... }
  }
}
```

## MCP メソッド

### tools/list

利用可能なツールの一覧を取得します。

**リクエスト**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}
```

**レスポンス**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "send_message",
        "description": "別のエージェントにメッセージを送信します",
        "inputSchema": {
          "type": "object",
          "properties": {
            "to": { "type": "string" },
            "content": { "type": "string" },
            "thinking": { "type": "string" }
          },
          "required": ["to", "content"]
        }
      }
    ]
  }
}
```

### tools/call

ツールを実行します。

**リクエスト**:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "send_message",
    "arguments": {
      "from": "grand_boss",
      "to": "middle_manager",
      "type": "task_request",
      "content": "タスクの分解をお願い",
      "thinking": "これは複雑なタスクだな...",
      "metadata": {
        "timestamp": "2026-02-01T14:32:10Z",
        "priority": "normal"
      }
    }
  }
}
```

**レスポンス**:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": "タスクを受信しました。分解を開始します。",
    "thinking": "了解。まず要件を整理しよう...",
    "isError": false
  }
}
```

## orchestrator-cc メッセージ形式

### メッセージ構造

```python
@dataclass
class CCMessage:
    """orchestrator-cc メッセージ"""
    # 基本フィールド
    id: str                    # 一意なID
    from_agent: str            # 送信元エージェントID
    to_agent: str              # 送信先エージェントID
    type: MessageType          # メッセージタイプ
    content: str               # メッセージ内容

    # オプションフィールド
    thinking: str | None = None           # 思考ログ
    metadata: dict[str, Any] = field(default_factory=dict)  # メタデータ
    timestamp: datetime = field(default_factory=datetime.now)  # タイムスタンプ
    reply_to: str | None = None          # 返信元メッセージID
```

### メッセージタイプ

```python
class MessageType(str, Enum):
    """メッセージタイプ"""
    # タスク関連
    TASK_REQUEST = "task_request"      # タスク依頼
    TASK_RESPONSE = "task_response"    # タスク応答
    TASK_COMPLETE = "task_complete"    # タスク完了
    TASK_FAILED = "task_failed"        # タスク失敗

    # 情報通知
    INFO = "info"                     # 一般情報
    PROGRESS = "progress"             # 進捗報告
    ERROR = "error"                   # エラー通知

    # 制御
    PING = "ping"                     # 死活監視
    PONG = "pong"                     # 死活監視応答
    SHUTDOWN = "shutdown"             # シャットダウン
```

### メタデータ

```python
@dataclass
class MessageMetadata:
    """メッセージメタデータ"""
    timestamp: datetime              # タイムスタンプ
    priority: Priority               # 優先度
    task_id: str | None = None       # タスクID
    correlation_id: str | None = None # 相関ID
    retry_count: int = 0             # リトライ回数
    ttl: int | None = None           # Time-To-Live

class Priority(str, Enum):
    """優先度"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
```

## 通信フロー

### 1. 初期化フロー（設定ファイル分離アプローチ）

```
orchestrator-cc                  Claude Code (Grand Boss)
      │                                  │
      │ 1. 設定ファイル作成                │
      │ /tmp/orchestrator-cc/agents/     │
      │   grand_boss/.claude/settings.json
      │                                  │
      │ 2. HOME環境変数設定                │
      │ HOME=/tmp/.../grand_boss         │
      │                                  │
      │ 3. プロセス起動                    │
      │─────────────────────────────────>│
      │                                  │
      │ 4. Claude Codeが設定ファイル読み込み│
      │    (性格プロンプト適用)            │
      │                                  │
      │ 5. tools/list                     │
      │─────────────────────────────────>│
      │                                  │
      │ 6. tools/list レスポンス          │
      │<─────────────────────────────────│
      │                                  │
      │ 7. 初期メッセージ（役割確認）      │
      │─────────────────────────────────>│
      │                                  │
      │ 8. レスポンス（性格が反映されている）│
      │<─────────────────────────────────│
```

**設定ファイル分離アプローチの詳細**:

各エージェント専用のHOMEディレクトリを作成し、その中に `.claude/settings.json` を配置して性格設定を管理します。

```json
{
  "agents": {
    "grand_boss": {
      "description": "Grand Boss - 組織のトップ",
      "prompt": "あなたはGrand Bossです。組織のトップとして、穏やかですが決定力を持って行動してください。常に大局的な視点を持ち、部下を信頼して任せるスタイルです。思考プロセスを常に詳細に出力してください。"
    }
  }
}
```

**起動コマンド例**:
```bash
# Grand Boss
HOME=/tmp/orchestrator-cc/agents/grand_boss claude mcp serve

# Middle Manager
HOME=/tmp/orchestrator-cc/agents/middle_manager claude mcp serve

# Coding Specialist
HOME=/tmp/orchestrator-cc/agents/coding_specialist claude mcp serve
```

**メリット**:
- ✅ 永続性: settings.jsonに保存される
- ✅ プロンプト追従性: Claude Codeがネイティブに読み込む
- ✅ 分離: 各エージェントが独立した設定を持てる
- ✅ 再現性: プロセス再起動で設定が維持される

### 2. メッセージ送信フロー

```
Grand Boss                    Middle Manager           orchestrator-cc
     │                               │                        │
     │ 1. メッセージ作成                │                        │
     │────────────────────────────────>│                        │
     │                               │                        │
     │ 2. JSON-RPCリクエスト          │                        │
     │────────────────────────────────>│                        │
     │                               │                        │
     │                               │ 3. 受信・ルーティング       │
     │                               │───────────────────────>│
     │                               │                        │
     │                               │ 4. 処理                 │
     │                               │<───────────────────────│
     │                               │                        │
     │ 5. JSON-RPCレスポンス         │                        │
     │<───────────────────────────────│                        │
     │                               │                        │
     │ 6. メッセージ完了               │                        │
     │<─────────────────────────────────│                        │
```

### 3. タスク実行フロー

```
ユーザー    Grand Boss    Middle Manager  Specialist
  │           │              │              │
  │ タスク入力  │              │              │
  │──────────>│              │              │
  │           │              │              │
  │           │ タスク分解依頼  │              │
  │           │─────────────>│              │
  │           │              │              │
  │           │              │ サブタスク割り振り│
  │           │              │─────────────>│
  │           │              │              │
  │           │              │              │ 実行
  │           │              │              │
  │           │              │ 結果         │
  │           │              │<─────────────│
  │           │              │              │
  │           │ 集約結果     │              │
  │           │<─────────────│              │
  │           │              │              │
  │ 最終結果  │              │              │
  │<──────────│              │              │
```

## エラーハンドリング

### エラーコード

| コード | 名前 | 説明 |
|-------|------|------|
| -32700 | Parse error | JSONパースエラー |
| -32600 | Invalid Request | 無効なリクエスト |
| -32601 | Method not found | メソッドが見つからない |
| -32602 | Invalid params | 無効なパラメータ |
| -32603 | Internal error | 内部エラー |
| -32000 | Agent not found | エージェントが見つからない |
| -32001 | Timeout | タイムアウト |
| -32002 | Rate limit | レートリミット |

### エラーレスポンス例

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "error": {
    "code": -32001,
    "message": "Timeout",
    "data": {
      "timeout_seconds": 30,
      "agent_id": "middle_manager"
    }
  }
}
```

## タイムアウト

| 操作 | デフォルトタイムアウト | 説明 |
|------|---------------------|------|
| **プロセス起動** | 30秒 | プロセスが起動してreadyになるまで |
| **メッセージ送信** | 10秒 | メッセージの送信が完了するまで |
| **メッセージ受信** | 60秒 | レスポンスを受信するまで |
| **タスク実行** | 300秒 | タスクが完了するまで |
| **アイドル** | 120秒 | 通信がない場合の接続タイムアウト |

## 再接続

### 再接続ポリシー

```python
class ReconnectPolicy:
    max_retries: int = 5              # 最大リトライ回数
    initial_delay: float = 1.0        # 初期待機時間（秒）
    max_delay: float = 60.0           # 最大待機時間（秒）
    backoff_factor: float = 2.0       # 指数バックオフ係数
```

### 再接続フロー

```
orchestrator-cc             Claude Code
      │                            │
      │ 1. 通信試行                  │
      │──────────────────────────>│
      │                            │
      │ 2. エラー（接続失敗）        │
      │<──────────────────────────│
      │                            │
      │ 3. 1秒待機                  │
      │                            │
      │ 4. 再接続試行                │
      │──────────────────────────>│
      │                            │
      │ 5. 成功                     │
      │<──────────────────────────│
```

## セキュリティ

### 認証

現時点では認証は実装しません（ローカルプロセス間通信のため）。

### データ検証

- 受信メッセージのスキーマ検証
- 不正なデータの拒否
- メッセージサイズの制限

### 権限

- 各エージェントは通信相手を制限できます
- Grand Bossのみがユーザーと通信できます

## パフォーマンス

### メッセージサイズ

- 最大メッセージサイズ: 1MB
- 思考ログの最大サイズ: 100KB

### スループット

- 目標スループット: 100メッセージ/秒
- 実測値: （検証後に更新）

### レイテンシ

- 目標レイテンシ: < 100ms (P50)
- 目標レイテンシ: < 500ms (P99)

## ログ

### 通信ログ

```python
@dataclass
class CommunicationLog:
    timestamp: datetime
    from_agent: str
    to_agent: str
    message_type: MessageType
    message_size: int
    duration_ms: float | None
    success: bool
    error: str | None
```

### ログレベル

| レベル | 説明 |
|-------|------|
| DEBUG | すべての通信ログ |
| INFO | 送受信メッセージのサマリー |
| WARN | 再接続、タイムアウト等 |
| ERROR | 通信エラー |
```

## 今後の拡張

1. **圧縮**: 大きいメッセージの圧縮
2. **バッチ処理**: 複数メッセージの一括送信
3. **ストリーミング**: 大きなデータのストリーミング転送
4. **暗号化**: 通信の暗号化（必要な場合）
5. **リモート通信**: ネットワーク経由の通信
