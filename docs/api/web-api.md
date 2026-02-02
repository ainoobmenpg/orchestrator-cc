# Web API仕様書

## REST API

### GET /

ダッシュボードのHTMLを返します。

**エンドポイント**: `GET /`

**認証**: 不要

**レスポンス**:
- ステータスコード: `200 OK`
- Content-Type: `text/html`
- Body: HTMLファイル

---

### GET /api

API情報を返します。

**エンドポイント**: `GET /api`

**認証**: 不要

**レスポンス**:
```json
{
  "message": "Orchestrator CC Dashboard API",
  "version": "0.1.0",
  "endpoints": {
    "status": "/api/status",
    "metrics": "/api/metrics",
    "alerts": "/api/alerts",
    "agents": "/api/agents",
    "websocket": "/ws"
  }
}
```

---

### GET /api/status

クラスタの状態を返します。

**エンドポイント**: `GET /api/status`

**認証**: 不要

**レスポンス**:
```json
{
  "monitoring": true,
  "check_interval": 5.0,
  "agent_timeout": 60.0,
  "max_idle_time": 300.0,
  "total_alerts": 0,
  "unresolved_alerts": 0,
  "last_metrics": {
    "total_agents": 5,
    "running_agents": 5,
    "idle_agents": 0,
    "unhealthy_agents": 0,
    "total_restarts": 0
  }
}
```

**フィールド説明**:
| フィールド | 型 | 説明 |
|-----------|------|------|
| `monitoring` | boolean | 監視が有効かどうか |
| `check_interval` | number | 監視間隔（秒） |
| `agent_timeout` | number | エージェント応答タイムアウト（秒） |
| `max_idle_time` | number | 最大アイドル時間（秒） |
| `total_alerts` | number | 総アラート数 |
| `unresolved_alerts` | number | 未解決のアラート数 |
| `last_metrics` | object | 最後のメトリクス（監視未実行の場合はnull） |

---

### GET /api/metrics

現在のメトリクスを返します。

**エンドポイント**: `GET /api/metrics`

**認証**: 不要

**レスポンス**:
```json
{
  "metrics": {
    "total_agents": 5,
    "running_agents": 5,
    "idle_agents": 0,
    "unhealthy_agents": 0,
    "total_restarts": 0,
    "timestamp": 1738555200.0
  }
}
```

**フィールド説明**:
| フィールド | 型 | 説明 |
|-----------|------|------|
| `total_agents` | number | エージェント総数 |
| `running_agents` | number | 実行中のエージェント数 |
| `idle_agents` | number | アイドル状態のエージェント数 |
| `unhealthy_agents` | number | 異常状態のエージェント数 |
| `total_restarts` | number | 総再起動回数 |
| `timestamp` | number | 計測時刻（Unixタイムスタンプ） |

---

### GET /api/alerts

アラート履歴を返します。

**エンドポイント**: `GET /api/alerts`

**認証**: 不要

**クエリパラメータ**:
| パラメータ | 型 | 必須 | 説明 |
|-----------|------|------|------|
| `level` | string | いいえ | アラートレベルでフィルタ（`info`, `warning`, `error`, `critical`） |
| `resolved` | boolean | いいえ | 解決状況でフィルタ |
| `limit` | number | いいえ | 最大取得件数（デフォルト: 100、最大: 1000） |

**レスポンス**:
```json
{
  "alerts": [
    {
      "level": "warning",
      "agent_name": "grand_boss",
      "message": "エージェントが長時間アイドル状態です（300秒）",
      "timestamp": 1738555200.0,
      "resolved": false
    }
  ]
}
```

**アラートフィールド説明**:
| フィールド | 型 | 説明 |
|-----------|------|------|
| `level` | string | アラートレベル（`info`, `warning`, `error`, `critical`） |
| `agent_name` | string | 対象エージェント名 |
| `message` | string | アラートメッセージ |
| `timestamp` | number | 発生時刻（Unixタイムスタンプ） |
| `resolved` | boolean | 解決済みかどうか |

---

### POST /api/alerts/{alert_index}/resolve

アラートを解決済みにマークします。

**エンドポイント**: `POST /api/alerts/{alert_index}/resolve`

**認証**: 不要

**パスパラメータ**:
| パラメータ | 型 | 説明 |
|-----------|------|------|
| `alert_index` | number | アラートのインデックス（`GET /api/alerts`で取得したリストのインデックス） |

**レスポンス（成功時）**:
```json
{
  "message": "Alert 0 resolved"
}
```

**レスポンス（エラー時）**:
```json
{
  "error": "Invalid alert index"
}
```

---

### DELETE /api/alerts

全てのアラートをクリアします。

**エンドポイント**: `DELETE /api/alerts`

**認証**: 不要

**レスポンス（成功時）**:
```json
{
  "message": "All alerts cleared"
}
```

**レスポンス（エラー時）**:
```json
{
  "error": "Dashboard not initialized"
}
```

---

### GET /api/agents

エージェント一覧を返します。

**エンドポイント**: `GET /api/agents`

**認証**: 不要

**レスポンス**:
```json
{
  "agents": [
    {
      "name": "grand_boss",
      "running": true,
      "last_activity": 1738555200.0,
      "restart_count": 0
    },
    {
      "name": "middle_manager",
      "running": true,
      "last_activity": 1738555190.0,
      "restart_count": 0
    }
  ]
}
```

**エージェントフィールド説明**:
| フィールド | 型 | 説明 |
|-----------|------|------|
| `name` | string | エージェント名 |
| `running` | boolean | 実行中かどうか |
| `last_activity` | number | 最終アクティビティ時刻（Unixタイムスタンプ） |
| `restart_count` | number | 再起動回数 |

---

### POST /api/monitoring/start

監視を開始します。

**エンドポイント**: `POST /api/monitoring/start`

**認証**: 不要

**レスポンス（成功時）**:
```json
{
  "message": "Monitoring started"
}
```

**レスポンス（既に実行中）**:
```json
{
  "message": "Monitoring already running"
}
```

---

### POST /api/monitoring/stop

監視を停止します。

**エンドポイント**: `POST /api/monitoring/stop`

**認証**: 不要

**レスポンス（成功時）**:
```json
{
  "message": "Monitoring stopped"
}
```

**レスポンス（未実行時）**:
```json
{
  "message": "Monitoring not running"
}
```

---

## WebSocket

### /ws

リアルタイム状態更新を受け取ります。

**エンドポイント**: `WS /ws`

**認証**: なし（将来的にはトークン認証を追加予定）

**接続例**:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  console.log('Connected to dashboard');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected from dashboard');
};
```

---

### サーバー→クライアント メッセージ

#### 接続確立メッセージ

```json
{
  "type": "connected",
  "message": "Connected to Orchestrator CC Dashboard"
}
```

#### メトリクス更新

```json
{
  "type": "metrics",
  "data": {
    "total_agents": 5,
    "running_agents": 5,
    "idle_agents": 0,
    "unhealthy_agents": 0,
    "total_restarts": 0
  },
  "timestamp": 1738555200.0
}
```

#### アラート通知

```json
{
  "type": "alert",
  "data": {
    "level": "warning",
    "agent_name": "grand_boss",
    "message": "エージェントが長時間アイドル状態です（300秒）",
    "resolved": false
  },
  "timestamp": 1738555200.0
}
```

#### 状態更新

```json
{
  "type": "status",
  "data": {
    "monitoring": true,
    "check_interval": 5.0,
    "total_alerts": 1,
    "unresolved_alerts": 1
  },
  "timestamp": 1738555200.0
}
```

#### エージェントイベント

```json
{
  "type": "agent",
  "data": {
    "name": "grand_boss",
    "event": "status_changed",
    "running": true
  },
  "timestamp": 1738555200.0
}
```

#### Pong（pingへの応答）

```json
{
  "type": "pong",
  "timestamp": 1738555200.0
}
```

#### エラーレスポンス

```json
{
  "type": "error",
  "message": "Unknown message type: invalid_type"
}
```

---

### クライアント→サーバー メッセージ

#### Ping（接続確認）

```json
{
  "type": "ping",
  "timestamp": 1738555200.0
}
```

**サーバーレスポンス**: `pong` メッセージ

#### ストリークス（チャンネル購読）

```json
{
  "type": "subscribe",
  "channels": ["metrics", "alerts"]
}
```

**サーバーレスポンス**:
```json
{
  "type": "subscribed",
  "channels": ["metrics", "alerts"]
}
```

#### アンストリークス（チャンネル購読解除）

```json
{
  "type": "unsubscribe",
  "channels": ["alerts"]
}
```

**サーバーレスポンス**:
```json
{
  "type": "unsubscribed",
  "channels": ["alerts"]
}
```

#### ステータス取得

```json
{
  "type": "get_status"
}
```

**サーバーレスポンス**: `status` メッセージ

---

## エラーレスポンス

### REST API エラー

全てのエンドポイントで以下のエラーレスポンスが返される可能性があります。

**ダッシュボード未初期化エラー**:
```json
{
  "error": "Dashboard not initialized"
}
```

**無効なリクエストエラー**:
```json
{
  "error": "Invalid request",
  "details": "..."
}
```

### WebSocket エラー

WebSocket接続でエラーが発生した場合、以下の形式でエラーメッセージが送信されます。

```json
{
  "type": "error",
  "message": "Error description"
}
```

**クローズコード**:
| コード | 説明 |
|-------|------|
| 1000 | 正常終了 |
| 1011 | サーバーエラー |

---

## レート制限

現在、レート制限は実装されていません。

将来的には以下の制限を追加予定：
- REST API: 100リクエスト/分
- WebSocket: 10メッセージ/秒

---

## 関連ドキュメント

- [web-dashboard.md](../web-dashboard.md) - Webダッシュボードの概要
- [architecture.md](../architecture.md) - システム全体のアーキテクチャ
