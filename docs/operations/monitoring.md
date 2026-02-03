# 監視とアラート

このドキュメントでは、orchestrator-cc の監視とアラートについて説明します。

---

## 現在の状況

### 実装済みの機能

orchestrator-cc には `ClusterMonitor` クラスによる監視機能が実装されています。

**機能**:
- エージェントの状態監視（実行中、アイドル、エラーなど）
- メトリクス収集
- アラート通知

**監視項目**:
| 項目 | 説明 |
|------|------|
| エージェント状態 | 実行中/停止、最終アクティビティ時刻、再起動回数 |
| メトリクス | 総エージェント数、実行中数、アイドル数、異常数 |
| アラート | 異常検知時の通知 |

### 現在の制約事項

| 項目 | 現状 |
|------|------|
| **外部監視システム連携** | 未対応（Prometheus, Datadog等） |
| **アラート通知** | ログ出力のみ（Email, Slack Webhook未対応） |
| **ログ集約** | 未対応（ELK, Loki等） |

---

## 監視の設定

### ClusterMonitor の初期化

```python
from orchestrator.core.cluster_monitor import ClusterMonitor

# 監視間隔: 5秒
# エージェント応答タイムアウト: 60秒
# 最大アイドル時間: 300秒
monitor = ClusterMonitor(
    cluster_manager,
    check_interval=5.0,
    agent_timeout=60.0,
    max_idle_time=300.0,
    alert_callback=alert_handler  # オプション
)
```

### 監視の開始と停止

```python
# 監視の開始
monitor.start()

# 監視の停止
monitor.stop()
```

---

## アラートレベル

| レベル | 説明 | 使用例 |
|--------|------|--------|
| INFO | 情報 | 状態変化通知 |
| WARNING | 警告 | アイドル状態、再起動回数増加 |
| ERROR | エラー | エージェント停止 |
| CRITICAL | 重大 | クラスタ全体の障害 |

---

## 推奨される改善策

### 1. Prometheus 連携

**提案**: `/metrics` エンドポイントを追加

```python
# orchestrator/web/prometheus.py
from prometheus_client import Counter, Gauge, Histogram, generate_latest

# メトリクスの定inition
agent_up = Gauge('orchestrator_agent_up', 'Agent status', ['agent_name'])
agent_idle_time = Gauge('orchestrator_agent_idle_time_seconds', 'Agent idle time', ['agent_name'])
agent_restarts = Counter('orchestrator_agent_restarts_total', 'Agent restarts', ['agent_name'])
cluster_alerts = Counter('orchestrator_cluster_alerts_total', 'Cluster alerts', ['level'])

@app.get("/metrics")
async def metrics():
    """Prometheus メトリクスエンドポイント"""
    # メトリクスの更新
    for agent in status["agents"]:
        agent_up.labels(agent_name=agent["name"]).set(1 if agent["running"] else 0)
        agent_restarts.labels(agent_name=agent["name"]).inc(agent["restart_count"])

    return Response(content=generate_latest(), media_type="text/plain")
```

**Prometheus 設定例**:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'orchestrator-cc'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8000']
```

---

### 2. アラート通知

#### Slack Webhook

**提案**: Slack へのアラート通知を実装

```python
# orchestrator/web/notifications.py
import os
import httpx
from orchestrator.core.cluster_monitor import Alert

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

async def send_slack_alert(alert: Alert):
    """Slack にアラートを送信"""
    if not SLACK_WEBHOOK_URL:
        return

    color_map = {
        "info": "#36a64f",
        "warning": "#ff9900",
        "error": "#ff0000",
        "critical": "#990000",
    }

    payload = {
        "attachments": [{
            "color": color_map.get(alert.level, "#cccccc"),
            "title": f"[{alert.level.value.upper()}] {alert.agent_name}",
            "text": alert.message,
            "ts": int(alert.timestamp),
        }]
    }

    async with httpx.AsyncClient() as client:
        await client.post(SLACK_WEBHOOK_URL, json=payload)

# コールバックとして設定
monitor = ClusterMonitor(
    cluster_manager,
    alert_callback=lambda alert: send_slack_alert(alert)
)
```

**環境変数設定**:

```bash
# .env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

---

#### Email 通知

**提案**: SMTP 経由のメール通知を実装

```python
# orchestrator/web/notifications.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO", "admin@example.com")

def send_email_alert(alert: Alert):
    """Email にアラートを送信"""
    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = ALERT_EMAIL_TO
    msg["Subject"] = f"[{alert.level.value.upper()}] orchestrator-cc Alert"

    body = f"""
    Agent: {alert.agent_name}
    Level: {alert.level.value}
    Message: {alert.message}
    Timestamp: {alert.timestamp}
    """

    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
```

---

### 3. 構造化ログ

**提案**: JSON 形式の構造化ログを実装

```python
# orchestrator/core/structured_logger.py
import json
import logging
from datetime import datetime

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def log(self, level: str, message: str, **kwargs):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            **kwargs
        }
        self.logger.log(getattr(logging, level.upper()), json.dumps(log_entry))

# 使用例
logger = StructuredLogger("orchestrator")
logger.log("info", "Agent started", agent_name="grand_boss", pane_index=0)
```

---

### 4. Grafana ダッシュボード

**提案**: Grafana 用ダッシュボード設定

```json
{
  "dashboard": {
    "title": "orchestrator-cc Dashboard",
    "panels": [
      {
        "title": "Agent Status",
        "targets": [{
          "expr": "orchestrator_agent_up"
        }]
      },
      {
        "title": "Agent Restarts",
        "targets": [{
          "expr": "rate(orchestrator_agent_restarts_total[5m])"
        }]
      },
      {
        "title": "Cluster Alerts",
        "targets": [{
          "expr": "rate(orchestrator_cluster_alerts_total[5m])"
        }]
      }
    ]
  }
}
```

---

## Web ダッシュボードでの監視

### ダッシュボードの起動

```bash
python -m orchestrator.cli dashboard
```

### 監視機能の使用

```bash
# 監視の開始
curl -X POST http://localhost:8000/api/monitoring/start

# 監視の停止
curl -X POST http://localhost:8000/api/monitoring/stop

# メトリクスの取得
curl http://localhost:8000/api/metrics

# アラートの取得
curl http://localhost:8000/api/alerts
```

---

## 監視のベストプラクティス

### 1. 監視間隔の設定

| 環境 | 推奨間隔 |
|------|----------|
| 開発 | 10-30 秒 |
| ステージング | 5-10 秒 |
| 本番 | 5 秒 |

### 2. アラートの閾値

| 項目 | WARNING | ERROR | CRITICAL |
|------|---------|-------|----------|
| アイドル時間 | 300 秒 | 600 秒 | 900 秒 |
| 再起動回数 | 3 回 | 5 回 | 10 回 |
| 停止エージェント数 | 1 | 2 | 3 |

### 3. ログの保存期間

| 環境 | 保存期間 |
|------|----------|
| 開発 | 7 日 |
| ステージング | 30 日 |
| 本番 | 90 日 |

---

## 関連ドキュメント

- [deployment.md](deployment.md) - デプロイ手順
- [troubleshooting.md](troubleshooting.md) - トラブルシューティング
- [backup-recovery.md](backup-recovery.md) - バックアップと復旧
