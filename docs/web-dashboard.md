# Webダッシュボード

## 概要

Webブラウザ上でクラスタの状態をリアルタイムに監視するダッシュボード。

## アーキテクチャ

### バックエンド（FastAPI）

- `orchestrator/web/dashboard.py` - FastAPIアプリケーション
- `orchestrator/web/message_handler.py` - WebSocketメッセージハンドラー
- `orchestrator/web/monitor.py` - ダッシュボード監視統合
- `orchestrator/core/cluster_monitor.py` - クラスタ監視

### フロントエンド

- `static/main.js` - メインのJavaScriptコード
- `static/style.css` - スタイルシート
- `templates/index.html` - HTMLテンプレート

## APIエンドポイント

### REST API

#### GET /

ダッシュボードのHTMLを返します。

**レスポンス**: HTMLファイル

#### GET /api

API情報を返します。

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

#### GET /api/status

クラスタの状態を返します。

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

#### GET /api/metrics

現在のメトリクスを返します。

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

#### GET /api/alerts

アラート履歴を返します。

**クエリパラメータ**:
- `level` - アラートレベルでフィルタ（オプション）
- `resolved` - 解決状況でフィルタ（オプション）
- `limit` - 最大取得件数（デフォルト: 100）

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

#### POST /api/alerts/{alert_index}/resolve

アラートを解決済みにマークします。

**レスポンス**:
```json
{
  "message": "Alert 0 resolved"
}
```

#### DELETE /api/alerts

全てのアラートをクリアします。

**レスポンス**:
```json
{
  "message": "All alerts cleared"
}
```

#### GET /api/agents

エージェント一覧を返します。

**レスポンス**:
```json
{
  "agents": [
    {
      "name": "grand_boss",
      "running": true,
      "last_activity": 1738555200.0,
      "restart_count": 0
    }
  ]
}
```

#### POST /api/monitoring/start

監視を開始します。

**レスポンス**:
```json
{
  "message": "Monitoring started"
}
```

#### POST /api/monitoring/stop

監視を停止します。

**レスポンス**:
```json
{
  "message": "Monitoring stopped"
}
```

### WebSocket

#### /ws

リアルタイム状態更新を受け取ります。

**メッセージ形式（サーバー→クライアント）**:
```json
{
  "type": "metrics" | "alert" | "status" | "agent" | "connected" | "pong",
  "data": {...},
  "timestamp": 1738555200.0
}
```

**タイプ**:
- `metrics` - メトリクス更新
- `alert` - アラート通知
- `status` - 状態更新
- `agent` - エージェント固有のイベント
- `connected` - 接続確立
- `pong` - pingへの応答

**メッセージ形式（クライアント→サーバー）**:
```json
{
  "type": "ping" | "subscribe" | "unsubscribe" | "get_status",
  ...
}
```

## 使用方法

### Webサーバー起動

```bash
# クラスタを起動
python -m orchestrator.cli start --config config/cc-cluster.yaml

# Webサーバーを起動
python -m orchestrator.web.dashboard
```

### ブラウザでアクセス

```
open http://localhost:8000
```

## 機能

- リアルタイムのエージェント状態監視
- メッセージの表示
- 思考ログの表示/非表示切り替え
- 過去ログの閲覧
- アラート通知
- メトリクス表示

## 関連ドキュメント

- [architecture.md](architecture.md) - システム全体のアーキテクチャ
- [api/web-api.md](api/web-api.md) - API仕様書
