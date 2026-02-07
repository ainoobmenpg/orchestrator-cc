# アーキテクチャ詳細

## システム全体図

```
┌─────────────────────────────────────────────────────────────────────┐
│                         orchestrator-cc                              │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Core Modules                               │  │
│  │                                                               │  │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌────────────┐  │  │
│  │  │ Agent Teams      │  │ Agent Health     │  │ Thinking   │  │  │
│  │  │ Manager          │  │ Monitor          │  │ Log Handler│  │  │
│  │  │                  │  │                  │  │            │  │
│  │  │ - チーム作成/削除 │  │ - ヘルスチェック  │  │ - 思考ログ │  │  │
│  │  │ - 設定管理       │  │ - タイムアウト検知│  │   監視      │  │
│  │  │ - タスク管理     │  │ - イベント通知    │  │ - ファイル │  │  │
│  │  └──────────────────┘  └──────────────────┘  │   ベース    │  │  │
│  │                                         │  └────────────┘  │  │
│  │  ┌──────────────────┐  ┌──────────────┐                   │  │
│  │  │ Teams Monitor    │  │ Team File     │                   │  │
│  │  │                  │  │ Observer      │                   │  │
│  │  │ - チーム監視     │  │               │                   │  │
│  │  │ - 変更検知       │  │ - ファイル    │                   │  │
│  │  │ - WebSocket配信  │  │   監視        │                   │  │
│  │  └──────────────────┘  └──────────────┘                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                    │                               │
│                                    ▼                               │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              ~/.claude/teams/ (チームデータ)                   │  │
│  │                                                              │  │
│  │   {team-name}/                                              │  │
│  │   ├── config.json    (チーム設定)                            │  │
│  │   ├── inbox/        (メッセージ履歴)                         │  │
│  │   └── messages/     (送信メッセージ)                         │  │
│  │                                                              │  │
│  │   ~/.claude/tasks/{team-name}/                              │  │
│  │   └── *.json       (タスクデータ)                            │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Web Dashboard (FastAPI)                    │  │
│  │                                                               │  │
│  │  REST API: /api/teams, /api/health, /api/teams/{name}/...   │  │
│  │  WebSocket: /ws                                              │  │
│  │  Static: /static/main.js, /static/style.css                  │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## コンポーネント構成

### 1. AgentTeamsManager

チームの作成・削除・管理を行うクラス。

**責務**:
- チーム設定ファイルの作成・削除
- チームメンバーのヘルスモニターへの登録
- チームタスクリストの取得
- チーム状態の取得

**主要メソッド**:
```python
class AgentTeamsManager:
    def __init__(self, teams_dir: Path | None = None, tasks_dir: Path | None = None):
        self._health_monitor = get_agent_health_monitor()
        self._teams_dir = Path(teams_dir or Path.home() / ".claude" / "teams")
        self._tasks_dir = Path(tasks_dir or Path.home() / ".claude" / "tasks")

    def create_team(self, config: TeamConfig) -> str:
        """チームを作成します。"""

    def delete_team(self, team_name: str) -> bool:
        """チームを削除します。"""

    def get_team_tasks(self, team_name: str) -> list[dict[str, Any]]:
        """チームのタスクリストを取得します。"""

    def get_team_status(self, team_name: str) -> dict[str, Any]:
        """チームの状態を取得します。"""

    def update_agent_activity(self, team_name: str, agent_name: str) -> None:
        """エージェントのアクティビティを更新します。"""
```

### 2. AgentHealthMonitor

エージェントのヘルス状態を監視するクラス。

**責務**:
- エージェントのアクティビティ監視
- タイムアウト検知
- ヘルスイベントの通知

**主要メソッド**:
```python
class AgentHealthMonitor:
    def __init__(self):
        self._agents: dict[str, dict[str, AgentHealthInfo]] = defaultdict(dict)

    def register_agent(self, team_name: str, agent_name: str, timeout_threshold: float = 300.0) -> None:
        """エージェントを監視に登録します。"""

    def update_activity(self, team_name: str, agent_name: str) -> None:
        """エージェントのアクティビティを更新します。"""

    def get_health_status(self) -> dict[str, dict[str, dict[str, Any]]]:
        """全エージェントのヘルス状態を取得します。"""

    def register_callback(self, callback: Callable[[HealthCheckEvent], None]) -> None:
        """ヘルスチェックイベントのコールバックを登録します。"""

    def start_monitoring(self) -> None:
        """監視を開始します。"""

    def stop_monitoring(self) -> None:
        """監視を停止します。"""
```

### 3. TeamsMonitor

Webダッシュボード用のチーム監視クラス。

**責務**:
- チームの状態、メッセージ、タスク、思考ログの監視
- WebSocketを通じたクライアントへの配信
- ファイル監視による変更検知

**主要メソッド**:
```python
class TeamsMonitor:
    def __init__(self, tmux_session_name: str | None = None):
        self._teams: dict[str, TeamInfo] = {}
        self._messages: dict[str, list[TeamMessage]] = defaultdict(list)
        self._tasks: dict[str, list[TaskInfo]] = defaultdict(list)
        self._thinking_logs: dict[str, list[ThinkingLog]] = defaultdict(list)
        self._file_observer = TeamFileObserver()
        self._task_observer = TaskFileObserver()
        self._update_callbacks: list[Callable[[dict[str, Any]], None]] = []

    def register_update_callback(self, callback: Callable[[dict[str, Any]], None]) -> None:
        """更新コールバックを登録します。"""

    def start_monitoring(self) -> None:
        """監視を開始します。"""

    def stop_monitoring(self) -> None:
        """監視を停止します。"""

    def get_teams(self) -> list[dict[str, Any]]:
        """チーム一覧を取得します。"""

    def get_team_messages(self, team_name: str) -> list[dict[str, Any]]:
        """チームのメッセージを取得します。"""

    def get_team_tasks(self, team_name: str) -> list[dict[str, Any]]:
        """チームのタスクを取得します。"""

    def get_team_thinking(self, team_name: str) -> list[dict[str, Any]]:
        """チームの思考ログを取得します。"""
```

### 4. ThinkingLogHandler

思考ログの処理を行うクラス。

**責務**:
- 思考ログのファイル監視
- ログの読み込み・検索
- 新しいログのコールバック通知

**主要メソッド**:
```python
class ThinkingLogHandler:
    def __init__(self, logs_dir: Path | None = None):
        self._logs_dir = Path(logs_dir or Path.home() / ".claude" / "thinking-logs")
        self._callbacks: list[Callable[[dict[str, Any]], None]] = []

    def register_callback(self, callback: Callable[[dict[str, Any]], None]) -> None:
        """コールバックを登録します。"""

    def start_monitoring(self) -> None:
        """監視を開始します。"""

    def stop_monitoring(self) -> None:
        """監視を停止します。"""

    def get_logs(self, team_name: str) -> list[dict[str, Any]]:
        """チームの思考ログを取得します。"""

    def save_log(self, team_name: str, agent_name: str, content: str, category: str = "thinking") -> str:
        """思考ログを保存します。"""
```

### 5. TeamFileObserver

チームファイルの監視を行うクラス。

**責務**:
- チーム設定ファイル(config.json)の監視
- メッセージファイル(inbox)の監視
- チーム作成・削除の監視

**主要メソッド**:
```python
class TeamFileObserver:
    def __init__(self):
        self._callbacks: dict[str, list[Callable]] = defaultdict(list)
        self._observer: Observer | None = None

    def register_callback(self, event_type: str, callback: Callable) -> None:
        """コールバックを登録します。"""

    def start(self) -> None:
        """監視を開始します。"""

    def stop(self) -> None:
        """監視を停止します."""

    def is_running(self) -> bool:
        """監視中かどうかを返します。"""
```

### 6. Team Models

データモデル定義。

**主要クラス**:
```python
@dataclass
class TeamInfo:
    """チーム情報"""
    name: str
    description: str
    created_at: int
    lead_agent_id: str
    members: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]: ...

@dataclass
class TeamMessage:
    """チームメッセージ"""
    id: str
    timestamp: str
    sender: str
    content: str
    message_type: str

    def to_dict(self) -> dict[str, Any]: ...

@dataclass
class TaskInfo:
    """タスク情報"""
    id: str
    subject: str
    description: str
    status: str
    owner: str | None
    active_form: str

    def to_dict(self) -> dict[str, Any]: ...

@dataclass
class ThinkingLog:
    """思考ログ"""
    id: str
    timestamp: str
    agent_name: str
    content: str
    category: str

    def to_dict(self) -> dict[str, Any]: ...
```

### 7. FastAPIアプリケーション

Webダッシュボードのバックエンド。

**エンドポイント**:
- `GET /` - ダッシュボードHTML
- `GET /api/teams` - チーム一覧API
- `GET /api/teams/{team_name}/messages` - チームメッセージAPI
- `GET /api/teams/{team_name}/tasks` - チームタスクAPI
- `GET /api/teams/{team_name}/thinking` - チーム思考ログAPI
- `GET /api/teams/{team_name}/status` - チーム状態API
- `GET /api/health` - ヘルス状態API
- `POST /api/health/start` - ヘルスモニタリング開始API
- `POST /api/health/stop` - ヘルスモニタリング停止API
- `WebSocket /ws` - WebSocketエンドポイント

## データフロー

### 1. チーム作成フロー

```
1. ユーザーがCLIからチーム作成コマンドを実行
   └─> python -m orchestrator.cli create-team my-team

2. AgentTeamsManager.create_team() が呼ばれる
   └─> ~/.claude/teams/my-team/ ディレクトリ作成
   └─> config.json ファイル作成

3. メンバーをヘルスモニターに登録
   └─> AgentHealthMonitor.register_agent()

4. TeamFileObserver が新しいチームを検知
   └─> TeamsMonitor に通知
   └─> WebSocketクライアントにブロードキャスト
```

### 2. エージェント間通信フロー

```
1. Team Lead が Specialist にメッセージ送信
   └─> SendMessage ツールを使用

2. Claude Code が ~/.claude/teams/{team}/messages/ にメッセージ保存

3. TeamFileObserver がファイル変更を検知
   └─> TeamsMonitor._on_inbox_changed()

4. WebSocketクライアントにメッセージを配信
   └─> _broadcast({"type": "team_message", ...})
```

### 3. タスク実行フロー

```
1. ユーザーがチームにタスクを依頼
   └─> タスク: "Webアプリを作って"

2. Team Lead がタスクを作成
   └─> TaskCreate ツールでタスク作成

3. Specialist がタスクを引き受けて実行
   └─> TaskUpdate ツールで状態更新

4. タスク完了時に Team Lead に結果を送信
   └─> SendMessage で通知

5. TeamFileObserver が変更を検知してダッシュボードに反映
```

## 通信プロトコル

### Agent Teams 通信方式

Claude Codeのネイティブ機能を使用した通信方式です。

| ツール | 説明 |
|--------|------|
| `TeamCreate` | 新しいチームを作成 |
| `SendMessage` | チームメンバー間のメッセージ送信 |
| `TaskUpdate` | タスク状態の更新 |

### ファイルベース監視

`~/.claude/teams/` ディレクトリ以下のファイルを監視して、リアルタイムに状態を追跡します。

| ディレクトリ/ファイル | 説明 |
|---------------------|------|
| `~/.claude/teams/{team}/config.json` | チーム設定 |
| `~/.claude/teams/{team}/inbox/` | 受信メッセージ |
| `~/.claude/teams/{team}/messages/` | 送信メッセージ |
| `~/.claude/tasks/{team}/*.json` | タスクデータ |
| `~/.claude/thinking-logs/{team}/` | 思考ログ |

## 設定ファイル

### config.json

チーム設定ファイルです。

```json
{
  "name": "my-team",
  "description": "My first team",
  "createdAt": 1737892800000,
  "leadAgentId": "team-lead@my-team",
  "leadSessionId": "session-my-team",
  "members": [
    {
      "agentId": "team-lead@my-team",
      "name": "team-lead",
      "agentType": "general-purpose",
      "model": "claude-sonnet-4-5-20250929",
      "joinedAt": 1737892800000,
      "tmuxPaneId": "",
      "cwd": "/path/to/project",
      "subscriptions": [],
      "planModeRequired": false
    }
  ]
}
```

## エラーハンドリング

### タイムアウト処理

```python
# ヘルスモニターによるタイムアウト検知
if not health_info["isHealthy"]:
    logger.warning(f"Agent timeout: {team_name}/{agent_name}")
    # TODO: 自動再起動ロジックを実装
```

### ファイル監視エラー

```python
# TeamFileObserver によるエラーハンドリング
try:
    self._observer.start()
except Exception as e:
    logger.error(f"File observer error: {e}")
    # 再起動ロジック
```

## 関連ドキュメント

- [README.md](../README.md) - プロジェクト概要
- [technical-decisions.md](technical-decisions.md) - 技術的決定事項
- [validation.md](validation.md) - 検証結果の記録
