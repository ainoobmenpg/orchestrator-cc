# Phase2ミニマム版設計書: YAML通信方式の実装

**作成日**: 2026-02-02
**作成者**: eng1
**タスクID**: task-20260202080440-wu8w (Phase2)

---

## 1. 概要

orchestrator-ccのエージェント間通信をYAMLファイルベースで実装する。

### 1.1 背景

現在の実装では、エージェントが直接 `send_to()` メソッドで通信しているが、これは「プロセスベースのアーキテクチャ」の目的に合致しない。本来は各Claude Codeプロセスが自律的にYAMLファイルを読み書きして通信する必要がある。

### 1.2 目標

1. **YAML通信プロトコル**: queue/*.yaml でのメッセージ交換
2. **ファイル監視**: YAML変更を自動検知して通知
3. **エージェント対応**: YAMLベースの非同期通信
4. **CLI統合**: `python -m orchestrator.cli start` で動作
5. **統合テスト**: エンドツーエンドの動作確認

---

## 2. 現状のアーキテクチャ

### 2.1 既存実装

```
orchestrator/
├── cli/
│   └── main.py           # ✅ CLI実装済
├── core/
│   ├── cc_cluster_manager.py   # ✅ クラスタ管理
│   ├── cc_process_launcher.py  # ✅ プロセス起動
│   └── pane_io.py              # ✅ ペイン入出力
├── agents/
│   ├── cc_agent_base.py        # ✅ エージェント基底
│   ├── grand_boss.py           # ✅ Grand Boss
│   ├── middle_manager.py       # ✅ Middle Manager
│   └── specialists.py          # ✅ Specialists
```

### 2.2 問題点

| 問題 | 説明 | 影響 |
|------|------|------|
| YAML通信未実装 | queue/ ディレクトリがない | エージェント間通信が動かない |
| ファイル監視未実装 | yaml_monitor.py がない | 自動通知が動かない |
| 通知サービス未実装 | notification_service.py がない | プロセス間連携が動かない |

---

## 3. Phase2ミニマム版の設計

### 3.1 アーキテクチャ図

```
[Grand Boss (Claude Code)]
    ↓ YAML書き込み
[queue/grand_boss_to_middle_manager.yaml]
    ↓ Python監視 (YAMLMonitor)
[NotificationService] → tmux send-keys
[Middle Manager (Claude Code)]
    ↓ YAML読み込み & タスク分解
[queue/middle_manager_to_specialist_coding_writing.yaml]
    ↓ Python監視 & 自動通知
[Coding Specialist (Claude Code)]
    ↓ YAML書き込み
[queue/specialist_coding_writing_to_middle_manager.yaml]
    ↓ Python監視 & ダッシュボード更新
[status/dashboard.md]
```

### 3.2 新規実装コンポーネント

| コンポーネント | 説明 | 優先度 |
|---------------|------|--------|
| `orchestrator/core/yaml_protocol.py` | YAML通信プロトコル（TaskMessage, AgentStatus） | 高 |
| `orchestrator/core/yaml_monitor.py` | YAMLファイル監視（watchdog使用） | 高 |
| `orchestrator/core/notification_service.py` | エージェント通知サービス | 高 |
| `queue/*.yaml` | 通信YAMLテンプレート | 高 |
| `status/agents/*.yaml` | ステータステンプレート | 中 |
| `tests/test_integration/test_phase2_minimum.py` | 統合テスト | 中 |

### 3.3 YAML通信プロトコル

#### TaskMessage フォーマット

```yaml
id: "msg-001"
from: "grand_boss"
to: "middle_manager"
type: "task"  # task, info, result, error
status: "pending"  # pending, in_progress, completed, failed
content: |
  タスク内容
timestamp: "2026-02-02T10:00:00"
metadata:
  priority: "high"
```

#### AgentStatus フォーマット

```yaml
agent_name: "grand_boss"
state: "idle"  # idle, working, completed, error
current_task: null
last_updated: "2026-02-02T10:00:00"
statistics:
  tasks_completed: 0
```

---

## 4. 実装計画

### Phase 2-A: 基盤実装（30分）

1. **yaml_protocol.py**: データモデル定義
   - `TaskMessage` クラス
   - `AgentStatus` クラス
   - YAML読み書き関数

2. **yaml_monitor.py**: ファイル監視
   - `YAMLMonitor` クラス（watchdog使用）
   - 変更検知時のコールバック

3. **notification_service.py**: 通知サービス
   - `NotificationService` クラス
   - tmux send-keys による通知

4. **queue/ テンプレート**: YAMLファイル作成
   - grand_boss_to_middle_manager.yaml
   - middle_manager_to_specialist_*.yaml
   - specialist_*_to_middle_manager.yaml

### Phase 2-B: エージェント統合（45分）

1. **CCAgentBase拡張**: YAML対応
   - `_read_yaml_message()` メソッド
   - `_write_yaml_message()` メソッド
   - `_check_and_process_messages()` メソッド

2. **各エージェント実装**: YAML処理
   - `handle_task()` でYAML対応
   - 非同期メッセージループ

3. **CLI統合**: 監視プロセス起動
   - `start_cluster()` でYAMLMonitor起動
   - 複数プロセスの管理

### Phase 2-C: テスト（45分）

1. **統合テスト**: エンドツーエンド
   - クラスタ起動
   - Grand Boss → Middle Manager → Specialist
   - 結果返却の確認

2. **エージェント間通信テスト**:
   - タスク分解
   - 並列実行
   - 結果集約

---

## 5. 技術的詳細

### 5.1 yaml_protocol.py

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
import yaml

class MessageType(str, Enum):
    TASK = "task"
    INFO = "info"
    RESULT = "result"
    ERROR = "error"

class MessageStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class TaskMessage:
    id: str
    from: str
    to: str
    type: MessageType
    status: MessageStatus
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict = field(default_factory=dict)

    def to_yaml(self, path: Path) -> None:
        with open(path, "w") as f:
            yaml.dump(self.__dict__, f)

    @classmethod
    def from_yaml(cls, path: Path) -> "TaskMessage":
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)
```

### 5.2 yaml_monitor.py

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import asyncio

class YAMLFileHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback

    def on_modified(self, event):
        if event.src_path.endswith('.yaml'):
            self.callback(event.src_path)

class YAMLMonitor:
    def __init__(self, queue_dir: str):
        self.queue_dir = queue_dir
        self.observer = Observer()

    async def watch(self, callback):
        handler = YAMLFileHandler(callback)
        self.observer.schedule(handler, self.queue_dir, recursive=False)
        self.observer.start()
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()
```

### 5.3 notification_service.py

```python
from orchestrator.core.tmux_session_manager import TmuxSessionManager

class NotificationService:
    def __init__(self, session_name: str):
        self.tmux = TmuxSessionManager(session_name)

    def notify_agent(self, pane_index: int, message: str) -> None:
        # プロンプトにメッセージを送信
        self.tmux.send_keys(pane_index, f"echo '{message}'")
        self.tmux.send_keys(pane_index, "Enter")
```

---

## 6. 実装手順

### Step 1: 基盤実装

```bash
# 1. ディレクトリ作成
mkdir -p queue status/agents

# 2. ファイル作成
touch orchestrator/core/yaml_protocol.py
touch orchestrator/core/yaml_monitor.py
touch orchestrator/core/notification_service.py

# 3. YAMLテンプレート作成
touch queue/grand_boss_to_middle_manager.yaml
touch queue/middle_manager_to_specialist_coding_writing.yaml
# ... etc
```

### Step 2: 実装とテスト

```bash
# 1. ユニットテスト実行
pytest tests/test_core/test_yaml_protocol.py
pytest tests/test_core/test_yaml_monitor.py

# 2. 統合テスト実行
pytest tests/test_integration/test_phase2_minimum.py

# 3. 手動テスト
python -m orchestrator.cli start --config config/cc-cluster.yaml
```

---

## 7. リスク評価

| リスク | 影響 | 緩和策 |
|--------|------|--------|
| watchdog依存 | 中 | pip install watchdog を明示 |
| ファイル競合 | 中 | ロック機構または再試行ロジック |
| タイミング問題 | 中 | ポーリング間隔の調整 |
| プロセス管理 | 低 | asyncioで適切に管理 |

---

## 8. 成功基準

1. ✅ `python -m orchestrator.cli start` でクラスタ起動
2. ✅ Grand Boss にタスク送信で自動伝達
3. ✅ Middle Manager がタスクを分解してSpecialistに振り分け
4. ✅ Specialist が結果を返して集約される
5. ✅ 統合テストが全てパス

---

## 9. 参考資料

- [docs/specs/yaml-communication.md](../specs/yaml-communication.md)
- [docs/architecture.md](../architecture.md)
- watchdog ドキュメント: https://python-watchdog.readthedocs.io/
