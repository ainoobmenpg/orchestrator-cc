# 監視とアラート

このドキュメントでは、orchestrator-cc の監視とアラートについて説明します。

**注意**: 2026-02-07をもって、tmux方式からAgent Teams方式へ完全移行しました。古いtmux方式に関する監視ドキュメントは `docs/archive/` にアーカイブされています。

---

## 現在の状況

### 実装済みの機能

orchestrator-cc には `AgentHealthMonitor` クラスによる監視機能が実装されています。

**機能**:
- エージェントのアクティビティ監視
- タイムアウト検知
- ヘルスイベントの通知
- Webダッシュボードでのリアルタイム表示

**監視項目**:
| 項目 | 説明 |
|------|------|
| エージェント状態 | アクティブ、アイドル、タイムアウト |
| 最終アクティビティ時刻 | 最後の活動時刻の追跡 |
| タイムアウト検知 | 設定された閾値を超えたエージェントの検知 |

### 現在の制約事項

| 項目 | 現状 |
|------|------|
| **外部監視システム連携** | 未対応（Prometheus, Datadog等） |
| **アラート通知** | ログ出力のみ（Email, Slack Webhook未対応） |
| **ログ集約** | 未対応（ELK, Loki等） |

---

## 監視の設定

### AgentHealthMonitor の初期化

```python
from orchestrator.core.agent_health_monitor import get_agent_health_monitor

# ヘルスモニターの取得
monitor = get_agent_health_monitor()

# エージェントの登録
monitor.register_agent(
    team_name="my-team",
    agent_name="team-lead",
    timeout_threshold=300.0  # 5分
)

# 監視の開始
monitor.start_monitoring()

# 監視の停止
monitor.stop_monitoring()
```

### コールバックの登録

```python
def health_callback(event: HealthCheckEvent):
    """ヘルスチェックイベントのコールバック"""
    if event.event_type == HealthEventType.TIMEOUT:
        print(f"Timeout: {event.team_name}/{event.agent_name}")
    elif event.event_type == HealthEventType.RECOVERED:
        print(f"Recovered: {event.team_name}/{event.agent_name}")

# コールバックの登録
monitor.register_callback(health_callback)
```

---

## ヘルスステータスの確認

### CLI からの確認

```bash
# ヘルスステータスを表示
python -m orchestrator.cli health

# 出力例
# Health Status:
#   my-team/team-lead: active (last_activity: 2s ago)
#   my-team/researcher: active (last_activity: 15s ago)
#   my-team/coder: timeout (last_activity: 320s ago)
```

### API からの確認

```bash
# ヘルスステータスを取得
curl http://localhost:8000/api/health

# 出力例
# {
#   "status": "healthy",
#   "teams": {
#     "my-team": {
#       "team-lead": {"status": "active", "last_activity": "2026-02-07T12:00:00"},
#       "researcher": {"status": "active", "last_activity": "2026-02-07T11:59:45"},
#       "coder": {"status": "timeout", "last_activity": "2026-02-07T11:55:00"}
#     }
#   }
# }
```

### ダッシュボードでの確認

```bash
# ダッシュボードを起動
python -m orchestrator.web.dashboard

# ブラウザでアクセス
open http://localhost:8000
```

---

## アラートレベル

| レベル | 説明 | 使用例 |
|--------|------|--------|
| INFO | 情報 | エージェント参加、離脱 |
| WARNING | 警告 | タイムアウト予告 |
| ERROR | エラー | エージェントタイムアウト |
| CRITICAL | 重大 | チーム全体の障害 |

---

## 推奨される改善策

### 1. Prometheus 連携

**提案**: `/metrics` エンドポイントを追加

```python
# orchestrator/web/prometheus.py
from prometheus_client import Counter, Gauge, generate_latest

# メトリクスの定義
agent_up = Gauge('orchestrator_agent_up', 'Agent status', ['team_name', 'agent_name'])
agent_idle_time = Gauge('orchestrator_agent_idle_time_seconds', 'Agent idle time', ['team_name', 'agent_name'])
agent_timeouts = Counter('orchestrator_agent_timeouts_total', 'Agent timeouts', ['team_name', 'agent_name'])

@app.get("/metrics")
async def metrics():
    """Prometheus メトリクスエンドポイント"""
    # メトリクスの更新
    for team_name, agents in health_status.items():
        for agent_name, status in agents.items():
            agent_up.labels(team_name=team_name, agent_name=agent_name).set(
                1 if status["isHealthy"] else 0
            )
            agent_idle_time.labels(team_name=team_name, agent_name=agent_name).set(
                status["idleTime"]
            )
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

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

async def send_slack_alert(event: HealthCheckEvent):
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
            "color": color_map.get(event.event_type.value, "#cccccc"),
            "title": f"[{event.event_type.value.upper()}] {event.team_name}/{event.agent_name}",
            "text": event.message,
            "ts": int(event.timestamp.timestamp()),
        }]
    }

    async with httpx.AsyncClient() as client:
        await client.post(SLACK_WEBHOOK_URL, json=payload)

# コールバックとして設定
monitor.register_callback(lambda e: send_slack_alert(e))
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

def send_email_alert(event: HealthCheckEvent):
    """Email にアラートを送信"""
    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = ALERT_EMAIL_TO
    msg["Subject"] = f"[{event.event_type.value.upper()}] orchestrator-cc Alert"

    body = f"""
    Team: {event.team_name}
    Agent: {event.agent_name}
    Level: {event.event_type.value}
    Message: {event.message}
    Timestamp: {event.timestamp}
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
logger.log("info", "Agent started", team_name="my-team", agent_name="team-lead")
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
        "title": "Agent Idle Time",
        "targets": [{
          "expr": "orchestrator_agent_idle_time_seconds"
        }]
      },
      {
        "title": "Agent Timeouts",
        "targets": [{
          "expr": "rate(orchestrator_agent_timeouts_total[5m])"
        }]
      }
    ]
  }
}
```

---

## 監視のベストプラクティス

### 1. 監視間隔の設定

| 環境 | 推奨間隔 |
|------|----------|
| 開発 | 10-30 秒 |
| ステージング | 5-10 秒 |
| 本番 | 5 秒 |

### 2. タイムアウトの閾値

| エージェントタイプ | 推奨タイムアウト |
|------------------|-----------------|
| Team Lead | 300 秒 (5分) |
| Specialist | 300 秒 (5分) |
| Monitor Only | 600 秒 (10分) |

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
- [../architecture.md](../architecture.md) - アーキテクチャ詳細
