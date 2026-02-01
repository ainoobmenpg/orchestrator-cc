# 実装ロードマップ

## フェーズ概要

| フェーズ | 目標 | 期間 | 優先度 |
|---------|------|------|--------|
| **Phase 0** | 事前検証 | 1日 | P0 |
| **Phase 0.5** | 中間検証（設定ファイル・複数プロセス） | 1日 | P0 |
| **Phase 1** | 基礎プロセス起動・管理機能 | 3-5日 | P0 |
| **Phase 2** | MCPブリッジの実装 | 3-5日 | P0 |
| **Phase 3** | エージェント間通信 | 5-7日 | P0 |
| **Phase 4** | Webダッシュボード | 5-7日 | P1 |

---

## Phase 0: 事前検証

**目標**: Claude Codeの`mcp serve`機能を検証し、実装の可能性を確認する

### 検証項目

| 項目 | 検証内容 | 成功基準 |
|------|----------|----------|
| **V-001** | `claude mcp serve` の基本動作 | JSON-RPCリクエストに正しく応答する |
| **V-002** | `--system-prompt` の動作 | プロンプトが反映される |
| **V-003** | プログラム制御の可否 | stdin/stdoutでの制御が可能 |
| **V-004** | 思考ログの出力方法 | 思考ログを含むメッセージを送信可能 |

### 検証手順

```bash
# V-001: 基本動作確認
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | claude mcp serve

# V-002: system-prompt確認
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | \
  claude mcp serve --system-prompt "あなたはテスト用エージェントです"

# V-003: プログラム制御確認
python3 -c "
import subprocess
import json

proc = subprocess.Popen(
    ['claude', 'mcp', 'serve'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True
)

request = json.dumps({
    'jsonrpc': '2.0',
    'id': 1,
    'method': 'tools/list'
})

proc.stdin.write(request + '\n')
proc.stdin.flush()
response = proc.stdout.readline()
print('Response:', response)

proc.terminate()
"

# V-004: 思考ログ確認
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"send_message","arguments":{"content":"テスト","thinking":"これは思考ログです"}}}' | \
  claude mcp serve
```

### 完了条件

- [ ] V-001: `tools/list` が正しいJSON-RPCレスポンスを返す
- [ ] V-002: `--system-prompt` で設定した性格が反映される
- [ ] V-003: Pythonからstdin/stdout経由で制御できる
- [ ] V-004: 思考ログを含むメッセージを処理できる

### リスク対応

| リスク | 対処方法 |
|-------|----------|
| `mcp serve` が対話モードを要求する | 別の通信方法を検討（ファイルベース等） |
| `--system-prompt` が機能しない | 最初のメッセージでプロンプトを送信 |
| 思考ログが出力されない | メッセージ内にカスタムフィールドを追加 |

---

## Phase 0.5: 中間検証（tmux方式への切り替え）

**目標**: tmux方式によるClaude Codeプロセス管理の実動確認

### 背景

Phase 0 でMCPサーバーモードの基本動作は確認できましたが、以下の課題が判明しました：

- `--system-prompt` オプションがMCPサーバーモードでは利用できない
- 設定ファイル分離アプローチ（`.claude/settings.json`）でも性格設定が機能しない

代替案として、**tmux方式**を採用することにしました。

### 検証項目

| 項目 | 検証内容 | 結果 |
|------|----------|------|
| **V-101** | tmuxで複数プロセス起動 | ✅ 成功（2026-02-01） |
| **V-102** | Pythonからtmux制御 | ✅ 成功（2026-02-01） |
| **V-103** | 出力のキャプチャ・パース | ✅ 成功（2026-02-01） |

### 検証結果

#### V-101: tmuxで複数プロセス起動

tmuxセッションを作成し、複数のペインで異なる`--system-prompt`を持つClaude Codeを起動できることを確認しました。

```bash
# tmuxセッション作成とペイン分割
tmux new-session -d -s test-orchestrator-cc
tmux split-window -h -t test-orchestrator-cc

# 各ペインでClaude Code起動
tmux send-keys -t test-orchestrator-cc:0.0 \
  'claude --system-prompt "あなたはGrand Bossです..."' Enter

tmux send-keys -t test-orchestrator-cc:0.1 \
  'claude --system-prompt "あなたはMiddle Managerです..."' Enter
```

#### V-102: Pythonからtmux制御

Pythonからsubprocess経由でtmuxコマンドを実行し、ペインにコマンドを送信・出力を取得できることを確認しました。

```python
import subprocess

# コマンド送信
subprocess.run([
    "tmux", "send-keys", "-t", "session:0.0",
    "echo 'test'", "Enter"
])

# 出力キャプチャ
result = subprocess.run([
    "tmux", "capture-pane", "-t", "session:0.0", "-p"
], capture_output=True, text=True)
```

#### V-103: 出力のキャプチャ・パース

tmux capture-paneでペインの出力を取得し、プロンプト行を除去して応答を抽出できることを確認しました（パース処理の改善が必要）。

### アーキテクチャ変更の決定

設定ファイル分離アプローチを破棄し、**tmux方式**を採用することにしました。

| 項目 | 旧方式（設定ファイル分離） | 新方式（tmux方式） |
|------|--------------------------|-------------------|
| 性格設定 | ❌ settings.jsonでは機能しない | ✅ `--system-prompt`で機能する |
| 複数プロセス起動 | ⚠️ 検証未完了 | ✅ tmuxペインで同時起動可能 |
| プログラム制御 | ✅ stdin/stdoutで可能 | ✅ tmuxコマンドで可能 |
| 出力取得 | ✅ stdoutから取得 | ✅ capture-paneで取得 |

### 完了条件

- [x] V-101: tmuxで複数プロセス起動が可能であることを確認（2026-02-01）
- [x] V-102: Pythonからtmux制御が可能であることを確認（2026-02-01）
- [x] V-103: 出力のキャプチャ・パースが可能であることを確認（2026-02-01）

### リスク対応

| リスク | 対処方法 |
|-------|----------|
| パース処理が不完全 | 正規表現でプロンプト行をより厳密に検出、または応答開始マーカーを使用 |
| tmuxがインストールされていない環境 | インストール手順をドキュメント化、またはDockerコンテナ化 |

---

## Phase 1: 基礎プロセス起動・管理機能（tmux方式）

**目標**: tmuxセッションで複数のClaude Codeプロセスを起動・管理する

### 実装ファイル

| ファイル | 内容 | 行数見積 | 新規/再利用 |
|---------|------|----------|-------------|
| `orchestrator/core/tmux_session_manager.py` | tmuxセッションの作成・管理 | 200 | 新規 |
| `orchestrator/core/cc_process_models.py` | エージェント設定データモデル | 150 | 新規 |
| `orchestrator/core/cc_process_launcher.py` | Claude Codeプロセス起動・監視 | 250 | 新規 |
| `orchestrator/core/pane_io.py` | ペインへの入出力処理 | 200 | 新規 |
| `config/cc-cluster.yaml` | クラスタ設定ファイル | 50 | 新規 |
| `config/personalities/*.txt` | 各エージェントの性格プロンプト | 100x6 | 新規 |
| `tests/test_core/test_tmux_session_manager.py` | tmuxセッションマネージャーテスト | 150 | 新規 |
| `tests/test_core/test_pane_io.py` | ペイン入出力テスト | 150 | 新規 |

### 主要実装項目

#### 1. CCProcessRole（列挙型）

```python
class CCProcessRole(str, Enum):
    GRAND_BOSS = "grand_boss"
    MIDDLE_MANAGER = "middle_manager"
    SPECIALIST_CODING_WRITING = "specialist_coding_writing"
    SPECIALIST_RESEARCH_ANALYSIS = "specialist_research_analysis"
    SPECIALIST_TESTING = "specialist_testing"
```

#### 2. CCProcessConfig（データモデル）

```python
@dataclass
class CCProcessConfig:
    name: str
    role: CCProcessRole
    personality_prompt_path: str | None = None
    work_dir: str = "/tmp/orchestrator-cc"
    claude_path: str = "claude"
    auto_restart: bool = True
    max_restarts: int = 3
```

#### 3. TmuxSessionManager（tmuxセッション管理）

```python
class TmuxSessionManager:
    def __init__(self, session_name: str):
        self._session_name = session_name

    def create_session(self) -> None:
        """tmuxセッションを作成"""
        subprocess.run([
            "tmux", "new-session", "-d", "-s", self._session_name
        ])

    def split_pane(self, direction: str = "h") -> None:
        """ペインを分割"""
        subprocess.run([
            "tmux", "split-window", f"-{direction}", "-t", self._session_name
        ])

    def send_keys(self, pane_index: int, command: str) -> None:
        """ペインにコマンドを送信"""
        subprocess.run([
            "tmux", "send-keys", "-t",
            f"{self._session_name}:0.{pane_index}",
            command, "Enter"
        ])

    def capture_pane(self, pane_index: int) -> str:
        """ペインの出力を取得"""
        result = subprocess.run([
            "tmux", "capture-pane", "-t",
            f"{self._session_name}:0.{pane_index}", "-p"
        ], capture_output=True, text=True)
        return result.stdout

    def kill_session(self) -> None:
        """セッションを終了"""
        subprocess.run([
            "tmux", "kill-session", "-t", self._session_name
        ])
```

#### 4. PaneIO（ペイン入出力処理）

```python
class PaneIO:
    def __init__(self, session_manager: TmuxSessionManager):
        self._tmux = session_manager

    def send_message(self, pane_index: int, message: str) -> None:
        """メッセージを送信（エスケープ処理付き）"""
        escaped = self._escape_message(message)
        self._tmux.send_keys(pane_index, escaped)

    def get_response(self, pane_index: int, timeout: float = 30.0) -> str:
        """応答を取得（パース処理付き）"""
        time.sleep(timeout)
        raw_output = self._tmux.capture_pane(pane_index)
        return self._parse_response(raw_output)

    def _parse_response(self, raw_output: str) -> str:
        """プロンプト行を除去して応答のみ抽出"""
        lines = raw_output.split('\n')
        response_lines = []
        in_response = False

        for line in lines:
            # プロンプト行を検出してスキップ
            if '@' in line and '%' in line:
                in_response = False
                continue
            # 応答部分を抽出
            if in_response or self._is_response_start(line):
                in_response = True
                response_lines.append(line)

        return '\n'.join(response_lines).strip()

    def _is_response_start(self, line: str) -> bool:
        """応答の開始を判定"""
        # Claude Codeの出力開始パターンを検出
        return any(marker in line for marker in ['# ', '## ', 'GRAND BOSS', 'MIDDLE MANAGER'])
```

#### 5. CCProcessLauncher（プロセス起動・監視）

```python
class CCProcessLauncher:
    def __init__(self, config: CCProcessConfig, pane_index: int,
                 tmux_manager: TmuxSessionManager):
        self._config = config
        self._pane_index = pane_index
        self._tmux = tmux_manager
        self._pane_io = PaneIO(tmux_manager)
        self._restart_count = 0

    async def start(self) -> None:
        """Claude Codeプロセスを起動"""
        # 性格プロンプトを読み込み
        personality = self._load_personality_prompt()

        # Claude Codeを起動
        cmd = f'cd {self._config.work_dir} && claude --system-prompt "{personality}"'
        self._tmux.send_keys(self._pane_index, cmd)

        # 起動完了を待機
        await self._wait_for_ready()

    async def send_message(self, message: str) -> str:
        """メッセージを送信して応答を取得"""
        self._pane_io.send_message(self._pane_index, message)
        response = await self._pane_io.get_response(self._pane_index)
        return response

    def _load_personality_prompt(self) -> str:
        """性格プロンプトを読み込み"""
        if self._config.personality_prompt_path:
            with open(self._config.personality_prompt_path) as f:
                return f.read()
        return "あなたは有帮助なアシスタントです。"
```

#### 6. クラスタ設定（YAML）

```yaml
cc_cluster:
  name: "orchestrator-cc"
  work_dir: ".>"
  session_name: "orchestrator-cc"

  personalities_dir: "config/personalities"

  agents:
    - name: "grand_boss"
      role: "grand_boss"
      personality_prompt_path: "config/personalities/grand_boss.txt"
      pane_index: 0

    - name: "middle_manager"
      role: "middle_manager"
      personality_prompt_path: "config/personalities/middle_manager.txt"
      pane_index: 1

    - name: "coding_writing_specialist"
      role: "specialist_coding_writing"
      personality_prompt_path: "config/personalities/coding_writing_specialist.txt"
      pane_index: 2

    - name: "research_analysis_specialist"
      role: "specialist_research_analysis"
      personality_prompt_path: "config/personalities/research_analysis_specialist.txt"
      pane_index: 3

    - name: "testing_specialist"
      role: "specialist_testing"
      personality_prompt_path: "config/personalities/testing_specialist.txt"
      pane_index: 4
```

### 完了条件

- [ ] tmuxセッションを作成できる
- [ ] 複数のペインを分割できる
- [ ] 各ペインでClaude Codeを起動できる
- [ ] 性格プロンプトが反映される
- [ ] メッセージを送信・応答を取得できる
- [ ] 出力のパース処理が動作する
- [ ] テストがパスする

### 検証方法

```bash
# 単体テスト
pytest tests/test_core/test_tmux_session_manager.py -v
pytest tests/test_core/test_pane_io.py -v

# 手動テスト
python -m orchestrator.cli.cc_cluster start --config config/cc-cluster.yaml

# 別ターミナルからメッセージ送信
python -m orchestrator.cli.cc_cluster send --to grand_boss "テストメッセージ"
```

---

## Phase 2: エージェント間通信（tmux方式）

**目標**: 各エージェント間でメッセージを送受信できるようにする

### 実装ファイル

| ファイル | 内容 | 行数見積 | 新規/再利用 |
|---------|------|----------|-------------|
| `orchestrator/core/cc_message.py` | メッセージデータモデル | 100 | 新規 |
| `orchestrator/core/cc_cluster_manager.py` | クラスタ全体の管理 | 250 | 新規 |
| `orchestrator/agents/cc_agent_base.py` | エージェント基底クラス | 200 | 新規 |
| `tests/test_core/test_cc_message.py` | メッセージモデルテスト | 100 | 新規 |
| `tests/test_integration/test_cc_agent_communication.py` | エージェント間通信テスト | 200 | 新規 |

### 主要実装項目

#### 1. CCMessage（メッセージモデル）

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class MessageType(str, Enum):
    TASK = "task"           # タスク依頼
    INFO = "info"           # 情報通知
    RESULT = "result"       # 結果報告
    ERROR = "error"         # エラー通知

@dataclass
class CCMessage:
    id: str
    from_agent: str
    to_agent: str
    type: MessageType
    content: str
    thinking: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
```

#### 2. CCAgentBase（エージェント基底クラス）

```python
class CCAgentBase:
    def __init__(
        self,
        agent_id: str,
        config: CCProcessConfig,
        pane_index: int,
        tmux_manager: TmuxSessionManager,
    ):
        self._agent_id = agent_id
        self._config = config
        self._pane_index = pane_index
        self._tmux = tmux_manager
        self._launcher = CCProcessLauncher(config, pane_index, tmux_manager)
        self._message_queue: asyncio.Queue[CCMessage] = asyncio.Queue()

    async def start(self) -> None:
        """エージェントを起動"""
        await self._launcher.start()

    async def send(self, to_agent: str, content: str,
                   thinking: str | None = None) -> None:
        """他エージェントにメッセージを送信"""
        message = CCMessage(
            id=str(uuid4()),
            from_agent=self._agent_id,
            to_agent=to_agent,
            type=MessageType.MESSAGE,
            content=content,
            thinking=thinking,
        )
        # クラスタマネージャー経由で送信
        await self._cluster.send_message(message)

    async def receive(self) -> CCMessage:
        """メッセージを受信"""
        return await self._message_queue.get()

    def _print_thinking(self, thinking: str) -> None:
        """思考ログを出力"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{self._agent_id}] [思考] {thinking}")
```

#### 3. CCClusterManager（クラスタ管理）

```python
class CCClusterManager:
    def __init__(self, config_path: str):
        self._config = self._load_config(config_path)
        self._tmux = TmuxSessionManager(self._config.session_name)
        self._agents: dict[str, CCAgentBase] = {}

    async def start(self) -> None:
        """クラスタを起動"""
        # tmuxセッション作成
        self._tmux.create_session()

        # 各エージェント用のペインを作成
        for i in range(len(self._config.agents) - 1):
            self._tmux.split_pane()

        # 各エージェントを起動
        for agent_config in self._config.agents:
            agent = self._create_agent(agent_config)
            await agent.start()
            self._agents[agent_config.name] = agent

    async def send_message(self, message: CCMessage) -> None:
        """メッセージを指定エージェントに送信"""
        to_agent = self._agents.get(message.to_agent)
        if to_agent:
            # 宛先エージェントのペインにメッセージを送信
            await to_agent._launcher.send_message(message.content)
            # メッセージキューに追加
            await to_agent._message_queue.put(message)

    def get_agent(self, agent_id: str) -> CCAgentBase:
        """エージェントを取得"""
        return self._agents[agent_id]

    async def shutdown(self) -> None:
        """クラスタをシャットダウン"""
        self._tmux.kill_session()
```

#### 4. 具体的なエージェント実装

```python
class GrandBossAgent(CCAgentBase):
    async def handle_user_task(self, task: str) -> None:
        """ユーザータスクを処理"""
        thinking = (
            f"ユーザーからタスクを受信: {task}\n"
            "これは複雑なタスクだな。Middle Managerに分解してもらおう。"
        )
        self._print_thinking(thinking)

        # Middle Managerに送信
        await self.send(
            "middle_manager",
            f"タスクの分解をお願い: {task}",
            thinking,
        )

class MiddleManagerAgent(CCAgentBase):
    async def handle_task_decomposition(self, task: str) -> None:
        """タスクを分解して Specialists に割り振る"""
        thinking = (
            f"タスクを受信: {task}\n"
            "これをサブタスクに分解して、各Specialistに割り振ろう。"
        )
        self._print_thinking(thinking)

        # タスクを分解（LLMに任せる）
        subtasks = await self._decompose_task(task)

        # 各Specialistに割り振り
        for specialist, subtask in subtasks.items():
            await self.send(specialist, subtask)
```

### 完了条件

- [ ] エージェント間でメッセージを送受信できる
- [ ] Grand Boss → Middle Manager → Specialists で通信できる
- [ ] 思考ログが出力される
- [ ] エンドツーエンドのタスク実行ができる
- [ ] テストがパスする

### 検証方法

```bash
# 単体テスト
pytest tests/test_core/test_cc_message.py -v

# 統合テスト
pytest tests/test_integration/test_cc_agent_communication.py -v -s

# 手動テスト
python -m orchestrator.cli.cc_cluster start --config config/cc-cluster.yaml

# 別ターミナルからタスク送信
python -m orchestrator.cli.cc_cluster send --to grand_boss "Webアプリを作って"
```

---

## Phase 3: 高度な機能・運用管理（tmux方式）

**目標**: タスクの分解・集約、進捗管理、ログ出力などの高度な機能を実装

### 実装ファイル

| ファイル | 内容 | 行数見積 | 新規/再利用 |
|---------|------|----------|-------------|
| `orchestrator/agents/cc_grand_boss.py` | Grand Boss実装 | 250 | 新規 |
| `orchestrator/agents/cc_middle_manager.py` | Middle Manager実装 | 300 | 新規 |
| `orchestrator/agents/cc_specialists.py` | Specialists実装 | 200 | 新規 |
| `orchestrator/core/task_orchestrator.py` | タスクの分解・集約 | 250 | 新規 |
| `orchestrator/core/progress_tracker.py` | 進捗管理 | 150 | 新規 |
| `orchestrator/core/logger.py` | ログ出力管理 | 100 | 新規 |
| `tests/test_integration/test_task_execution.py` | タスク実行テスト | 200 | 新規 |

### 主要実装項目

#### 1. TaskOrchestrator（タスクオーケストレーター）

```python
class TaskOrchestrator:
    """タスクの分解・集約を管理"""

    def __init__(self, cluster_manager: CCClusterManager):
        self._cluster = cluster_manager
        self._active_tasks: dict[str, TaskContext] = {}

    async def execute_task(self, task: str) -> str:
        """タスクを実行"""
        task_id = str(uuid4())
        context = TaskContext(
            id=task_id,
            original_task=task,
            status="in_progress",
            subtasks=[],
            results=[],
        )
        self._active_tasks[task_id] = context

        # Grand Bossにタスクを送信
        grand_boss = self._cluster.get_agent("grand_boss")
        await grand_boss.handle_user_task(task)

        # 結果を待機
        result = await self._wait_for_completion(task_id)
        return result

    async def _wait_for_completion(self, task_id: str) -> str:
        """タスク完了を待機"""
        context = self._active_tasks[task_id]

        while context.status == "in_progress":
            await asyncio.sleep(1)
            # 進捗をログ出力
            self._log_progress(context)

        return "\n".join(context.results)

    def _log_progress(self, context: TaskContext) -> None:
        """進捗をログ出力"""
        print(f"[タスク {context.id}] 進捗: {len(context.results)}/{len(context.subtasks)} 完了")
```

#### 2. ProgressTracker（進捗管理）

```python
class ProgressTracker:
    """タスクの進捗を追跡"""

    def __init__(self):
        self._task_status: dict[str, str] = {}
        self._subtask_status: dict[str, dict[str, str]] = {}

    def register_task(self, task_id: str, subtask_ids: list[str]) -> None:
        """タスクを登録"""
        self._task_status[task_id] = "in_progress"
        self._subtask_status[task_id] = {
            subtask_id: "pending" for subtask_id in subtask_ids
        }

    def update_subtask(self, task_id: str, subtask_id: str, status: str) -> None:
        """サブタスクの状態を更新"""
        if task_id in self._subtask_status:
            self._subtask_status[task_id][subtask_id] = status

        # 全サブタスク完了時の処理
        if self._is_all_subtasks_completed(task_id):
            self._task_status[task_id] = "completed"

    def _is_all_subtasks_completed(self, task_id: str) -> bool:
        """全サブタスクが完了しているか確認"""
        if task_id not in self._subtask_status:
            return False
        return all(
            status == "completed"
            for status in self._subtask_status[task_id].values()
        )

    def get_progress(self, task_id: str) -> dict:
        """進捗状況を取得"""
        if task_id not in self._subtask_status:
            return {"progress": 0, "total": 0, "completed": 0}

        subtasks = self._subtask_status[task_id]
        total = len(subtasks)
        completed = sum(1 for s in subtasks.values() if s == "completed")
        progress = (completed / total * 100) if total > 0 else 0

        return {
            "progress": progress,
            "total": total,
            "completed": completed,
            "subtasks": subtasks,
        }
```

#### 3. GrandBossAgent（完全版）

```python
class GrandBossAgent(CCAgentBase):
    """Grand Boss: 最上位管理者"""

    async def handle_user_task(self, task: str) -> None:
        """ユーザータスクを処理"""
        thinking = (
            f"ユーザーからタスクを受信: {task}\n"
            "このタスクの複雑さを評価し、Middle Managerに分解を依頼する必要がある。"
        )
        self._print_thinking(thinking)

        # Middle Managerにタスク分解を依頼
        await self.send(
            "middle_manager",
            f"タスクを分解して各Specialistに割り振ってください: {task}",
            thinking,
        )

    async def aggregate_results(self, results: list[str]) -> str:
        """結果を集約"""
        thinking = (
            f"{len(results)}個の結果を受け取りました。\n"
            "これらを統合して最終的な成果物を作成します。"
        )
        self._print_thinking(thinking)

        # 結果を統合（LLMに任せることも可能）
        aggregated = self._format_results(results)
        return aggregated

    def _format_results(self, results: list[str]) -> str:
        """結果をフォーマット"""
        return "\n\n".join([
            f"## 結果 {i+1}\n{result}"
            for i, result in enumerate(results)
        ])
```

#### 4. MiddleManagerAgent（完全版）

```python
class MiddleManagerAgent(CCAgentBase):
    """Middle Manager: タスク分解・進捗管理"""

    async def handle_task_decomposition(self, task: str) -> None:
        """タスクを分解して Specialists に割り振る"""
        thinking = (
            f"タスクを受信: {task}\n"
            "このタスクを適切なサブタスクに分解し、各Specialistの能力に応じて割り振ります。"
        )
        self._print_thinking(thinking)

        # タスクを分解（LLMに任せる）
        subtasks = await self._decompose_task_with_llm(task)

        # 進捗管理に登録
        self._progress_tracker.register_task(task_id, list(subtasks.keys()))

        # 各Specialistに割り振り
        for specialist, subtask in subtasks.items():
            await self.send(specialist, subtask)
            print(f"[Middle Manager] {specialist} にタスクを割り振りました: {subtask[:50]}...")

    async def collect_results(self, task_id: str) -> list[str]:
        """Specialist からの結果を収集"""
        thinking = "全 Specialist からの結果を待機しています..."
        self._print_thinking(thinking)

        results = []
        subtasks = self._progress_tracker.get_progress(task_id)["subtasks"]

        for subtask_id in subtasks.keys():
            # 結果を待機
            result = await self._wait_for_subtask_result(subtask_id)
            results.append(result)

            # 進捗を更新
            self._progress_tracker.update_subtask(task_id, subtask_id, "completed")

        # Grand Boss に結果を送信
        await self.send("grand_boss", f"タスク完了。結果を集約しました。")

        return results
```

### 完了条件

- [ ] タスクが自動的に分解される
- [ ] 各 Specialist にサブタスクが割り振られる
- [ ] 進捗がリアルタイムで追跡される
- [ ] 結果が適切に集約される
- [ ] 思考ログが出力される
- [ ] エンドツーエンドのタスク実行ができる
- [ ] テストがパスする

### 検証方法

```bash
# 統合テスト
pytest tests/test_integration/test_task_execution.py -v -s

# 手動テスト
python -m orchestrator.cli.cc_cluster start --config config/cc-cluster.yaml

# 別ターミナルからタスク送信
python -m orchestrator.cli.cc_cluster execute "Webアプリを作って"

# 進捗確認
python -m orchestrator.cli.cc_cluster status --task-id <task_id>
```

---

## Phase 4: Webダッシュボード

**目標**: Webブラウザ上で会話を観察できるようにする

### 実装ファイル

| ファイル | 内容 | 行数見積 | 新規/再利用 |
|---------|------|----------|-------------|
| `orchestrator/web/dashboard.py` | Webダッシュボード（FastAPI） | 200 | 新規 |
| `orchestrator/web/static/main.js` | フロントエンドJavaScript | 300 | 新規 |
| `orchestrator/web/static/style.css` | スタイルシート | 150 | 新規 |
| `orchestrator/web/templates/index.html` | HTMLテンプレート | 100 | 新規 |
| `tests/test_web/test_dashboard.py` | ダッシュボードテスト | 100 | 新規 |

### 主要実装項目

#### 1. FastAPIアプリケーション

```python
app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def broadcast(self, message: dict) -> None:
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    manager.active_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # handle message
    finally:
        manager.active_connections.remove(websocket)

@app.get("/")
async def get_dashboard():
    return FileResponse("orchestrator/web/templates/index.html")
```

#### 2. フロントエンド（JavaScript）

```javascript
const ws = new WebSocket(`ws://${host}/ws`);

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    displayMessage(message);
};

function displayMessage(message) {
    const timestamp = formatTime(message.timestamp);
    const agent = message.agent;
    const content = message.content;
    const thinking = message.thinking;

    // メッセージを表示
    addMessageLine(timestamp, agent, content);

    // 思考ログを表示（有効な場合）
    if (showThinking && thinking) {
        addThinkingLine(timestamp, thinking);
    }
}
```

### 完了条件

- [ ] Webダッシュボードが起動できる
- [ ] 複数インスタンスの会話がリアルタイムで見える
- [ ] 思考ログの表示/非表示が切り替えられる
- [ ] 過去ログを閲覧できる
- [ ] テストがパスする

### 検証方法

```bash
# Webサーバー起動
python -m orchestrator.web.dashboard

# ブラウザでアクセス
open http://localhost:8000
```

---

## 依存関係

```
Phase 0 (事前検証) + Phase 0.5 (tmux方式検証)
    │
    ▼
Phase 1 (tmuxプロセス起動・管理)
    │
    ▼
Phase 2 (エージェント間通信)
    │
    ▼
Phase 3 (高度な機能・運用管理)
    │
    ▼
Phase 4 (Webダッシュボード)
```

---

## マイルストーン

| マイルストーン | 期限 | 成果物 |
|---------------|------|--------|
| **MS-0** | Day 1 | Phase 0 + 0.5完了、tmux方式実現可能性確認 |
| **MS-1** | Day 5 | Phase 1完了、tmuxプロセス起動可能 |
| **MS-2** | Day 10 | Phase 2完了、エージェント間通信可能 |
| **MS-3** | Day 17 | Phase 3完了、タスク実行・進捗管理可能 |
| **MS-4** | Day 24 | Phase 4完了、Webダッシュボード完成 |

---

## 優先度

| フェーズ | 優先度 | 説明 |
|---------|--------|------|
| **Phase 0** | P0 | 実装の可能性を確認するため必須 |
| **Phase 0.5** | P0 | tmux方式の実現可能性を確認するため必須 |
| **Phase 1** | P0 | tmuxプロセス起動はシステムの基盤 |
| **Phase 2** | P0 | エージェント間通信はシステムの中核 |
| **Phase 3** | P0 | タスク実行・進捗管理はシステムの目的 |
| **Phase 4** | P1 | Webダッシュボードは便利だが必須ではない |
