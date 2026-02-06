# Agent Teams監視ダッシュボード設計書

## 概要

既存のorchestrator-cc Webダッシュボードを拡張し、Claude CodeのAgent Teams機能を監視・可視化するシステムを設計する。

**作成日**: 2026-02-06
**ステータス**: 設計中

---

## 1. 目的

Agent Teams上で動作するエージェントの以下を可視化する：

1. **行動**: どのエージェントが誰にメッセージを送ったか
2. **思考**: タスクの進捗、依存関係の変化
3. **感情**: メッセージ内容から推定されるエージェントの状態

---

## 2. アーキテクチャ

### 2.1 システム構成図

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          orchestrator/web/                                  │
│                        (既存Webダッシュボード)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  [既存] dashboard.py (FastAPI)                                      │   │
│  │  [新規] APIエンドポイント追加                                        │   │
│  │    - GET /api/teams - チーム一覧                                     │   │
│  │    - GET /api/teams/{name} - チーム詳細                              │   │
│  │    - GET /api/teams/{name}/messages - メッセージ履歴                 │   │
│  │    - GET /api/teams/{name}/tasks - タスクリスト                       │   │
│  │    - GET /api/teams/{name}/members - メンバー一覧                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  [新規] teams_monitor.py                                            │   │
│  │  TeamsMonitor クラス:                                                │   │
│  │    - __init__() - 初期化、監視開始                                    │   │
│  │    - start() - 監視ループ開始                                        │   │
│  │    - stop() - 監視ループ停止                                         │   │
│  │    - _watch_team_configs() - ~/.claude/teams/*/config.json監視       │   │
│  │    - _watch_inboxes() - ~/.claude/teams/*/inboxes/*.json監視         │   │
│  │    - _watch_tasks() - ~/.claude/tasks/*/監視                         │   │
│  │    - _get_teams() - チーム一覧取得                                   │   │
│  │    - _get_team_info() - 特定チームの情報取得                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  [新規] team_models.py                                              │   │
│  │  データクラス:                                                        │   │
│  │    - TeamInfo - チーム基本情報                                       │   │
│  │    - TeamMember - メンバー情報                                       │   │
│  │    - TeamMessage - メッセージ情報                                    │   │
│  │    - TeamTask - タスク情報                                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  [既存] message_handler.py                                         │   │
│  │  [拡張] チーム用メッセージタイプ追加                                  │   │
│  │    - UpdateType.TEAM_ADDED - チーム追加                             │   │
│  │    - UpdateType.TEAM_MESSAGE - メッセージ追加                        │   │
│  │    - UpdateType.TEAM_TASK - タスク更新                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            フロントエンド (拡張)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  [既存 + 拡張] main.js                                              │   │
│  │    - handleTeamMessage() - チームメッセージ処理                      │   │
│  │    - handleTeamTask() - タスク更新処理                               │   │
│  │    - renderTeamList() - チーム一覧表示                               │   │
│  │    - renderTeamDetail() - チーム詳細表示                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  [既存 + 拡張] style.css                                            │   │
│  │    - .team-selector - チーム選択スタイル                            │   │
│  │    - .team-message - メッセージスタイル                             │   │
│  │    - .task-card - タスクカードスタイル                              │   │
│  │    - .status-badge - ステータスバッジ                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  [既存 + 拡張] index.html                                           │   │
│  │    - チーム選択ドロップダウン                                        │   │
│  │    - タスクボード                                                   │   │
│  │    - メッセージフロー                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      監視対象: Agent Teamsファイル構造                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  ~/.claude/teams/<team-name>/                                               │
│  ├── config.json          - チーム設定・メンバー情報                         │
│  └── inboxes/<agent-name>.json - メッセージinbox                            │
│  ~/.claude/tasks/<team-name>/<task-id>.json - タスク情報                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 データフロー

```
1. チーム検出
   TeamsMonitor._watch_team_configs()
   ~/.claude/teams/*/config.json を監視
   ↓
   新しいチームを検出 → TeamInfoを作成 → WebSocketでクライアントに通知

2. メッセージ検出
   TeamsMonitor._watch_inboxes()
   ~/.claude/teams/<team-name>/inboxes/*.json を監視
   ↓
   新しいメッセージを検出 → TeamMessageを作成 → WebSocketで通知

3. タスク検出
   TeamsMonitor._watch_tasks()
   ~/.claude/tasks/<team-name>/*.json を監視
   ↓
   タスク更新を検出 → TeamTaskを作成 → WebSocketで通知
```

---

## 3. データモデル

### 3.1 TeamInfo（チーム情報）

```python
@dataclass
class TeamInfo:
    """チームの基本情報"""
    name: str                    # チーム名
    description: str             # 説明
    created_at: datetime         # 作成日時
    lead_agent_id: str           # リーダーエージェントID
    member_count: int            # メンバー数
    members: list[TeamMember]    # メンバー一覧
```

### 3.2 TeamMember（メンバー情報）

```python
@dataclass
class TeamMember:
    """チームメンバーの情報"""
    agent_id: str                # エージェントID
    name: str                    # 表示名
    agent_type: str              # エージェントタイプ
    model: str                   # 使用モデル
    joined_at: datetime          # 参加日時
    backend_type: str            # バックエンドタイプ (in-process/tmux)
```

### 3.3 TeamMessage（メッセージ情報）

```python
@dataclass
class TeamMessage:
    """チーム内のメッセージ"""
    team_name: str               # チーム名
    from_agent: str              # 送信者
    to_agent: str | None         # 受信者 (None=broadcast)
    text: str                    # メッセージ本文
    summary: str                 # 要約
    timestamp: datetime          # タイムスタンプ
    color: str | None            # カラー
    read: bool                   # 既読フラグ
    message_type: MessageType    # メッセージタイプ
```

```python
class MessageType(Enum):
    """メッセージの種類"""
    DIRECT = "direct"            # 個別メッセージ
    BROADCAST = "broadcast"      # ブロードキャスト
    SHUTDOWN_REQUEST = "shutdown_request"
    SHUTDOWN_RESPONSE = "shutdown_response"
    PLAN_APPROVAL = "plan_approval"
    IDLE_NOTIFICATION = "idle_notification"
```

### 3.4 TeamTask（タスク情報）

```python
@dataclass
class TeamTask:
    """チームのタスク情報"""
    team_name: str               # チーム名
    task_id: str                 # タスクID
    subject: str                 # 件名
    description: str             # 説明
    active_form: str             # 進行中のアクティブフォーム
    status: TaskStatus           # ステータス
    owner: str | None            # 担当者
    blocks: list[str]            # このタスクがブロックするタスクID
    blocked_by: list[str]        # このタスクをブロックしているタスクID
```

```python
class TaskStatus(Enum):
    """タスクのステータス"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELETED = "deleted"
```

---

## 4. APIエンドポイント

### 4.1 チーム関連

| エンドポイント | メソッド | 説明 | レスポンス |
|---------------|----------|------|-----------|
| `/api/teams` | GET | チーム一覧取得 | `list[TeamInfo]` |
| `/api/teams/{name}` | GET | チーム詳細取得 | `TeamDetail` |
| `/api/teams/{name}/members` | GET | メンバー一覧取得 | `list[TeamMember]` |

### 4.2 メッセージ関連

| エンドポイント | メソッド | 説明 | レスポンス |
|---------------|----------|------|-----------|
| `/api/teams/{name}/messages` | GET | メッセージ履歴取得 | `list[TeamMessage]` |
| `/api/teams/{name}/messages/latest` | GET | 最新メッセージ取得 | `TeamMessage` |

### 4.3 タスク関連

| エンドポイント | メソッド | 説明 | レスポンス |
|---------------|----------|------|-----------|
| `/api/teams/{name}/tasks` | GET | タスクリスト取得 | `list[TeamTask]` |
| `/api/teams/{name}/tasks/{task_id}` | GET | タスク詳細取得 | `TeamTask` |

---

## 5. WebSocketメッセージ

### 5.1 メッセージ形式

```json
{
  "type": "team_message" | "team_task" | "team_added" | "team_removed",
  "data": {
    "team_name": "チーム名",
    // ... 各タイプ固有のデータ
  },
  "timestamp": 1704525600.0
}
```

### 5.2 メッセージタイプ

| タイプ | データ内容 | 発生タイミング |
|--------|-----------|---------------|
| `team_added` | `TeamInfo` | 新しいチームを検出 |
| `team_message` | `TeamMessage` | 新しいメッセージ到着 |
| `team_task` | `TeamTask` | タスク状態変更 |
| `team_member_added` | `TeamMember` | メンバー追加 |
| `team_member_removed` | `str` (agent_id) | メンバー削除 |

---

## 6. フロントエンド拡張

### 6.1 UI構成

```
┌─────────────────────────────────────────────────────────────────┐
│ [ヘッダー] 接続状態 | チーム選択ドロップダウン                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ [チーム概要パネル]                                            │ │
│ │  チーム名: test-team                                          │ │
│ │  メンバー数: 3                                                │ │
│ │  アクティブタスク: 2                                           │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ ┌───────────────────────┬─────────────────────────────────────┐ │
│ │ [タスクリスト]          │ [メッセージログ]                    │ │
│ │                        │                                     │ │
│ │ □ タスク1 (pending)     │ [Agent A → Agent B]                │ │
│ │ □ タスク2 (in_progress) │ メッセージ内容...                   │ │
│ │ ☑ タスク3 (completed)   │                                     │ │
│ │                        │ [Agent C → All]                     │ │
│ │                        │ ブロードキャスト...                  │ │
│ └───────────────────────┴─────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 新規CSSクラス

```css
/* チームセレクタ */
.team-selector {
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background: var(--bg-primary);
}

/* チームカード */
.team-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: 8px;
  margin-bottom: 16px;
}

/* タスクカード */
.task-card {
  padding: 12px;
  border-left: 3px solid var(--border-color);
  border-radius: 4px;
  background: var(--bg-tertiary);
}

.task-card.status-pending { border-left-color: #6c757d; }
.task-card.status-in_progress { border-left-color: #ffc107; }
.task-card.status-completed { border-left-color: #28a745; }

/* メッセージ */
.team-message {
  display: flex;
  gap: 8px;
  padding: 8px 12px;
  margin-bottom: 8px;
  border-radius: 6px;
  background: var(--bg-tertiary);
}

.team-message.direct { border-left: 3px solid #007bff; }
.team-message.broadcast { border-left: 3px solid #6f42c1; }
```

---

## 7. 実装フェーズ

### Phase 1: 基本監視機能（MVP）

**目標**: チームとメッセージを監視・表示する

1. **データモデル** (`team_models.py`)
   - `TeamInfo`, `TeamMember`, `TeamMessage` クラス
   - JSONパース関数

2. **ファイル監視** (`teams_monitor.py`)
   - `~/.claude/teams/` ディレクトリ監視
   - config.jsonの監視
   - inboxの監視
   - WebSocketブロードキャスト

3. **API** (`dashboard.py`拡張)
   - `/api/teams`
   - `/api/teams/{name}/messages`

4. **フロントエンド**
   - チーム選択UI
   - メッセージ表示

### Phase 2: タスク監視

**目標**: タスクの状態を追跡する

1. `TeamTask` モデル追加
2. `~/.claude/tasks/` 監視
3. タスクボードUI
4. 依存関係表示

### Phase 3: 高度な可視化

**目標**: エージェント間の相互作用を理解しやすく

1. メッセージフロー図
2. アクティビティタイムライン
3. 感情推定（オプション）

---

## 8. 既存コードの流用

### 8.1 流用する既存コンポーネント

| 既存ファイル | 流用箇所 | 用途 |
|-------------|---------|------|
| `message_handler.py` WebSocketManager | `teams_monitor.py` | 更新通知のブロードキャスト |
| `monitor.py` DashboardMonitor | `teams_monitor.py` | コールバック登録パターン |
| `main.js` handleAgentMessage() | `main.js` handleTeamMessage() | メッセージ処理パターン |
| `style.css` メッセージスタイル | `style.css` チームメッセージ | スタイル定義 |

### 8.2 新規作成ファイル

| ファイル | 役割 | 推定行数 |
|---------|------|----------|
| `orchestrator/web/team_models.py` | データモデル | ~150行 |
| `orchestrator/web/teams_monitor.py` | 監視ロジック | ~300行 |

---

## 9. 技術的詳細

### 9.1 ファイル監視方式

Pythonの`watchdog`ライブラリを使用して、ファイルシステムの変更を監視する。

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class TeamFileHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self._callback = callback

    def on_modified(self, event):
        if event.src_path.endswith('config.json'):
            self._callback('team_config', event.src_path)
        elif 'inbox' in event.src_path and event.src_path.endswith('.json'):
            self._callback('inbox', event.src_path)
```

### 9.2 JSONパース

Agent Teamsのファイル形式に対応したパーサーを実装する。

```python
def parse_team_config(path: str) -> TeamInfo:
    with open(path) as f:
        data = json.load(f)
    return TeamInfo(
        name=data['name'],
        description=data.get('description', ''),
        created_at=datetime.fromtimestamp(data['createdAt'] / 1000),
        lead_agent_id=data['leadAgentId'],
        member_count=len(data['members']),
        members=[parse_member(m) for m in data['members']],
    )
```

---

## 10. 検証計画

1. **テストチーム作成**: `Teammate`ツールでテームを作成
2. **監視動作確認**: ファイル変更が正しく検知されるか
3. **表示確認**: ブラウザでリアルタイム更新が見えるか
4. **負荷テスト**: 大量のメッセージ・タスクでも安定動作するか

---

## 11. 制約と留意点

1. **Agent Teamsのバックエンド依存**: `in-process`バックエンドの場合、tmuxペインが存在しない
2. **ファイルアクセス権**: `~/.claude/` ディレクトリへの読み取り権限が必要
3. **並列処理**: 複数のチームを同時に監視する場合の効率性
4. **データ永続化**: ダッシュボード再起動時の状態復帰

---

## 12. 将来の拡張

1. **思考ログ取得**: tmuxペインまたはdebugログの監視（オプション）
2. **録画・再生機能**: チーム活動の記録と再生
3. **エクスポート**: メッセージ・タスクのCSV/JSONエクスポート
4. **分析ダッシュボード**: アクティビティ統計、貢献度分析
