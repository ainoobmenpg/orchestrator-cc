# YAML通信プロトコル仕様

## 概要

orchestrator-ccでは、エージェント間通信にYAMLファイルベースのプロトコルを使用します。各エージェントはYAMLファイルを読み書きすることで通信を行い、Python側の監視プロセスが自動で通知を行います。

## 通信フロー

```
┌─────────────────┐
│   Grand Boss    │
│  (Claude Code)  │
└────────┬────────┘
         │ YAML書き込み
         ▼
┌─────────────────────────────────────┐
│ queue/grand_boss_to_middle_manager  │
│             .yaml                    │
└────────┬────────────────────────────┘
         │ 変更検知 (watchdog)
         ▼
┌─────────────────────────────────────┐
│      YAMLMonitor (Python)            │
│  ────────────────────────────────   │
│  • ファイル変更を監視                │
│  • TaskMessageとしてパース           │
│  • NotificationService呼び出し       │
└────────┬────────────────────────────┘
         │ tmux send-keys
         ▼
┌─────────────────┐
│ Middle Manager  │
│  (Claude Code)  │
└─────────────────┘
```

## YAMLフォーマット

### 通信メッセージ (queue/*.yaml)

エージェント間のメッセージ伝達に使用します。

```yaml
# 必須フィールド
id: "msg-001"              # メッセージID（一意な値）
from: "grand_boss"         # 送信元エージェント名
to: "middle_manager"       # 送信先エージェント名
type: "task"               # メッセージタイプ
status: "pending"          # タスク状態
content: |                 # メッセージ内容（複数行可）
  タスクの詳細説明
  複数行で記述可能

# 必須フィールド
timestamp: "2026-02-01T10:00:00"  # ISO 8601形式のタイムスタンプ

# オプションフィールド
metadata:                 # 追加メタデータ
  priority: "high"
  estimated_time: 30
```

#### メッセージタイプ (type)

| 値 | 説明 |
|---|------|
| `task` | タスク依頼 |
| `info` | 情報通知 |
| `result` | 結果報告 |
| `error` | エラー通知 |

#### タスク状態 (status)

| 値 | 説明 |
|---|------|
| `pending` | 待機中 |
| `in_progress` | 実行中 |
| `completed` | 完了 |
| `failed` | 失敗 |

### エージェントステータス (status/agents/*.yaml)

各エージェントの現在の状態を表します。

```yaml
# 必須フィールド
agent_name: "grand_boss"            # エージェント名
state: "idle"                       # エージェント状態
last_updated: "2026-02-01T10:00:00"  # 最終更新時刻
statistics:                         # 統計情報
  tasks_completed: 5

# オプションフィールド
current_task: "タスク分解中"         # 現在のタスク
```

#### エージェント状態 (state)

| 値 | 説明 | 絵文字 |
|---|------|--------|
| `idle` | アイドル中 | 💤 |
| `working` | 作業中 | ⚙️ |
| `completed` | 完了 | ✅ |
| `error` | エラー | ❌ |

## 通信ファイルのマッピング

### ユーザー -> Grand Boss

tmuxセッションに直接アタッチして入力します。

### Grand Boss -> Middle Manager

- **ファイル**: `queue/grand_boss_to_middle_manager.yaml`
- **タイプ**: 通常は `task`

### Middle Manager -> Specialists

| Specialist | ファイル |
|------------|----------|
| Coding & Writing | `queue/middle_manager_to_coding.yaml` |
| Research & Analysis | `queue/middle_manager_to_research.yaml` |
| Testing | `queue/middle_manager_to_testing.yaml` |

### Specialists -> Middle Manager

| Specialist | ファイル |
|------------|----------|
| Coding & Writing | `queue/coding_to_middle_manager.yaml` |
| Research & Analysis | `queue/research_to_middle_manager.yaml` |
| Testing | `queue/testing_to_middle_manager.yaml` |

### Middle Manager -> Grand Boss

- **ファイル**: `queue/middle_manager_to_grand_boss.yaml`
- **タイプ**: 通常は `result`

## Python監視プロセス

### YAMLMonitor

`queue/` ディレクトリを監視し、YAMLファイルの変更を検知します。

```python
from orchestrator.core.yaml_monitor import YAMLMonitor
from orchestrator.core.notification_service import NotificationService

def on_message(message, file_path):
    service = NotificationService(tmux_manager)
    service.notify_agent(message, file_path)

monitor = YAMLMonitor(
    queue_dir=Path("queue"),
    notification_callback=on_message,
)
monitor.start()
```

### NotificationService

エージェントにtmux経由で通知します。

```python
from orchestrator.core.notification_service import NotificationService

service = NotificationService(tmux_manager)
service.notify_agent(message, queue_file)
```

### DashboardManager

`status/agents/` ディレクトリを監視し、ダッシュボードを更新します。

```python
from orchestrator.core.dashboard_manager import DashboardManager

manager = DashboardManager(
    status_dir=Path("status/agents"),
    dashboard_path=Path("status/dashboard.md"),
)
await manager.update_dashboard()
```

## エージェントの動作

### タスク送信時

1. 送信元エージェントが対応するYAMLファイルを編集
2. YAMLMonitorが変更を検知
3. NotificationServiceが宛先エージェントに通知
4. 宛先エージェントがYAMLファイルを読み込む

### タスク完了時

1. エージェントが対応するYAMLファイルの `status` を `completed` に更新
2. 必要に応じて `status/agents/*.yaml` を更新
3. DashboardManagerがダッシュボードを更新

## エラーハンドリング

### 無効なYAML

YAMLフォーマットが無効な場合、監視プロセスはエラーログを出力し、通知を行いません。

### 不明なエージェント

宛先エージェントが不明な場合、`ValueError` が発生します。

### ファイルアクセスエラー

ファイルが存在しない場合、`FileNotFoundError` が発生します。

## 実装クラス

### TaskMessage

```python
from orchestrator.core.yaml_protocol import TaskMessage, MessageType, TaskStatus

message = TaskMessage(
    id="msg-001",
    from_agent="grand_boss",
    to_agent="middle_manager",
    type=MessageType.TASK,
    content="タスク内容",
    status=TaskStatus.PENDING,
)

# YAMLに保存
message.to_file(Path("queue/grand_boss_to_middle_manager.yaml"))

# YAMLから読み込み
loaded = TaskMessage.from_file(Path("queue/grand_boss_to_middle_manager.yaml"))
```

### AgentStatus

```python
from orchestrator.core.yaml_protocol import AgentStatus

status = AgentStatus(
    agent_name="grand_boss",
    state="working",
    current_task="タスク管理中",
)

# YAMLに保存
status.to_file(Path("status/agents/grand_boss.yaml"))

# YAMLから読み込み
loaded = AgentStatus.from_file(Path("status/agents/grand_boss.yaml"))
```
