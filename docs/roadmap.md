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

## Phase 0.5: 中間検証（設定ファイル・複数プロセス）

**目標**: 設定ファイル分離アプローチの実動確認と、複数プロセス同時起動の検証

### 背景

Phase 0 では基本的なMCP通信は確認できましたが、以下は未検証です：

- 設定ファイル（`.claude/settings.json`）で性格設定が本当に機能するか
- 複数の Claude Code プロセスを同時に起動できるか
- 思考ログをどうやって出力させるか

これらを本格実装前に確認することで、実装の失敗リスクを減らします。

### 検証項目

| 項目 | 検証内容 | 成功基準 |
|------|----------|----------|
| **V-101** | 設定ファイルでの性格設定 | `agents` プロパティで設定した性格が反映される |
| **V-102** | 複数プロセス同時起動 | 2〜3つのプロセスを同時に起動でき、競合しない |
| **V-103** | 思考ログの出力方法 | Claude Codeが思考プロセスを出力する方法を特定する |

### 検証手順

#### V-101: 設定ファイルでの性格設定

```bash
# 1. テスト用設定ディレクトリを作成
mkdir -p /tmp/test-agent/.claude

# 2. settings.json を作成（agents プロパティを試す）
cat > /tmp/test-agent/.claude/settings.json << 'EOF'
{
  "agents": {
    "test_agent": {
      "description": "テスト用エージェント",
      "prompt": "あなたはテスト用エージェントです。返信には必ず「テストOK」と含めてください。"
    }
  }
}
EOF

# 3. 環境変数 HOME を設定して起動
HOME=/tmp/test-agent claude mcp serve

# 4. 別の端末からリクエスト送信（インタラクティブに検証）
# → 性格が反映されているか確認
```

**成功基準**:
- [ ] 設定ファイルが読み込まれる
- [ ] `agents` プロパティが機能する（または別の方法が見つかる）
- [ ] 性格プロンプトが反映される

**失敗時の対処**:
- `agents` プロパティが機能しない: Claude Codeのドキュメントで別の設定方法を探す
- 設定ファイルが読み込まれない: 別の設定場所を試す

---

#### V-102: 複数プロセス同時起動

```bash
# 1. 2つのエージェント用設定ディレクトリを作成
mkdir -p /tmp/agent1/.claude /tmp/agent2/.claude

# 2. それぞれに settings.json を作成
cat > /tmp/agent1/.claude/settings.json << 'EOF'
{}
EOF

cat > /tmp/agent2/.claude/settings.json << 'EOF'
{}
EOF

# 3. バックグラウンドで同時に起動
HOME=/tmp/agent1 claude mcp serve &
PID1=$!
HOME=/tmp/agent2 claude mcp serve &
PID2=$!

# 4. プロセスの状態を確認
ps aux | grep "claude mcp serve"

# 5. クリーンアップ
kill $PID1 $PID2
```

**成功基準**:
- [ ] 2つのプロセスが同時に起動できる
- [ ] ポート競合などのエラーが発生しない
- [ ] 各プロセスが独立して動作する

**失敗時の対処**:
- ポート競合: ポート番号を明示的に指定する方法を探す
- 起動失敗: 起動順序を変える or 遅延を入れる

---

#### V-103: 思考ログの出力方法

```bash
# 1. Claude Codeのドキュメントで思考ログに関する設定を探す
claude --help | grep -i think
claude --help | grep -i reason
claude --help | grep -i verbose

# 2. 設定ファイルでの思考ログ設定を確認
# → settings.json に思考ログ関連のプロパティがあるか

# 3. 実際に試して確認
```

**成功基準**:
- [ ] 思考ログを出力する方法を特定できる
- [ ] 出力形式（stdout, ファイル, etc.）を確認できる

**失敗時の対処**:
- 思考ログ機能がない: メッセージ内にカスタムフィールドを追加する方式を検討
- 出力先が不明: 複数の出力先を試す

---

### 完了条件

- [ ] V-101: 設定ファイルでの性格設定方法を確立
- [ ] V-102: 複数プロセス同時起動が可能であることを確認
- [ ] V-103: 思考ログの出力方法を特定

### リスク対応

| リスク | 対処方法 |
|-------|----------|
| `agents` プロパティが機能しない | Claude Codeのドキュメントで別の設定方法を探す |
| 複数プロセスでリソース不足 | メモリ使用量を監視、必要に応じて制限を設ける |
| 思考ログ機能がない | メッセージ内にカスタムフィールドを追加する方式を採用 |

---

## Phase 1: 基礎プロセス起動・管理機能

**目標**: Claude Codeプロセスを起動し、MCPサーバーとして動作させる

### 実装ファイル

| ファイル | 内容 | 行数見積 | 新規/再利用 |
|---------|------|----------|-------------|
| `orchestrator/core/cc_process_models.py` | Claude Codeプロセス設定モデル | 150 | 新規 |
| `orchestrator/core/cc_process_launcher.py` | Claude Codeプロセス起動・管理 | 200 | 新規（ProcessLauncher継承） |
| `config/cc-cluster.yaml` | Claude Codeクラスタ設定 | 50 | 新規 |
| `config/personalities/grand_boss.txt` | Grand Boss性格プロンプト | 100 | 新規 |
| `config/personalities/middle_manager.txt` | Middle Manager性格プロンプト | 100 | 新規 |
| `config/personalities/coding_specialist.txt` | Coding Specialist性格プロンプト | 100 | 新規 |
| `tests/test_core/test_cc_process_models.py` | プロセスモデルテスト | 100 | 新規 |
| `tests/test_core/test_cc_process_launcher.py` | プロセス起動テスト | 150 | 新規 |

### 主要実装項目

#### 1. CCProcessRole（列挙型）

```python
class CCProcessRole(str, Enum):
    GRAND_BOSS = "grand_boss"
    MIDDLE_MANAGER = "middle_manager"
    SPECIALIST_CODING = "specialist_coding"
    SPECIALIST_RESEARCH = "specialist_research"
    SPECIALIST_WRITING = "specialist_writing"
    SPECIALIST_ANALYSIS = "specialist_analysis"
    SPECIALIST_TESTING = "specialist_testing"
```

#### 2. CCProcessConfig（データモデル）

```python
@dataclass
class CCProcessConfig:
    name: str
    role: CCProcessRole
    claude_path: str = "claude"
    mcp_host: str = "localhost"
    mcp_port: int = 0
    work_dir: str | None = None
    log_dir: str | None = None
    personality_prompt_path: str | None = None
    auto_restart: bool = True
    max_restarts: int = 5
    restart_delay: float = 5.0
    thinking_log_enabled: bool = True
    thinking_log_detail: str = "detailed"
```

#### 3. CCProcessLauncher（プロセス起動）

```python
class CCProcessLauncher(ProcessLauncher):
    def __init__(self, config: CCProcessConfig, **kwargs):
        super().__init__(config, **kwargs)
        self._personality_prompt: str | None = None

    async def _load_personality_prompt(self) -> str | None:
        if self._config.personality_prompt_path:
            with open(self._config.personality_prompt_path) as f:
                return f.read()
        return None

    def _build_command(self) -> list[str]:
        cmd = [
            self._config.claude_path,
            "mcp",
            "serve",
        ]
        if self._personality_prompt:
            cmd.extend(["--system-prompt", self._personality_prompt])
        return cmd
```

#### 4. クラスタ設定（YAML）

```yaml
cc_cluster:
  name: "default"
  work_dir: "/tmp/orchestrator-cc"
  log_dir: "/tmp/orchestrator-cc/logs"
  personalities_dir: "config/personalities"

  processes:
    - name: "grand_boss"
      role: "grand_boss"
      mcp_port: 9000
      personality_prompt_path: "config/personalities/grand_boss.txt"
      thinking_log_enabled: true
      thinking_log_detail: "detailed"

    - name: "middle_manager"
      role: "middle_manager"
      mcp_port: 9001
      personality_prompt_path: "config/personalities/middle_manager.txt"
      thinking_log_enabled: true
      thinking_log_detail: "detailed"
```

### 完了条件

- [ ] Claude Codeプロセスが起動できる
- [ ] MCPサーバーポートで接続確認できる
- [ ] 複数プロセスを一括起動できる
- [ ] プロセス停止・再起動ができる
- [ ] 性格プロンプトが読み込まれる
- [ ] テストがパスする

### 検証方法

```bash
# 単体テスト
pytest tests/test_core/test_cc_process_models.py -v
pytest tests/test_core/test_cc_process_launcher.py -v

# 手動テスト
python -m orchestrator.cli.cc_cluster start --config config/cc-cluster.yaml
```

---

## Phase 2: MCPブリッジの実装

**目標**: OrchestratorメッセージとMCPリクエストの双方向変換 + 思考ログ

### 実装ファイル

| ファイル | 内容 | 行数見積 | 新規/再利用 |
|---------|------|----------|-------------|
| `orchestrator/core/mcp_message_bridge.py` | Message↔MCP変換ブリッジ | 250 | 新規 |
| `orchestrator/core/cc_agent_registry.py` | エージェント登録・発見 | 150 | 新規 |
| `tests/test_core/test_mcp_message_bridge.py` | メッセージブリッジテスト | 150 | 新規 |
| `tests/test_core/test_cc_agent_registry.py` | エージェント登録テスト | 100 | 新規 |

### 主要実装項目

#### 1. CCMessage（メッセージモデル）

```python
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

#### 2. MCPMessageBridge（ブリッジ）

```python
class MCPMessageBridge:
    async def send_message(self, message: CCMessage) -> None:
        # CCMessage → MCPRequest
        mcp_request = self._to_mcp_request(message)
        await self._send_to_agent(message.to_agent, mcp_request)

    async def receive_message(self, agent_id: str) -> CCMessage | None:
        # MCPResponse → CCMessage
        mcp_response = await self._receive_from_agent(agent_id)
        return self._from_mcp_response(mcp_response)

    def _to_mcp_request(self, message: CCMessage) -> dict:
        return {
            "jsonrpc": "2.0",
            "id": message.id,
            "method": "tools/call",
            "params": {
                "name": "send_message",
                "arguments": {
                    "from": message.from_agent,
                    "to": message.to_agent,
                    "type": message.type,
                    "content": message.content,
                    "thinking": message.thinking,
                    "metadata": message.metadata,
                }
            }
        }
```

#### 3. CCAgentRegistry（エージェント登録）

```python
class CCAgentRegistry:
    def __init__(self):
        self._agents: dict[str, CCProcessInfo] = {}
        self._connections: dict[str, asyncio.StreamReaderWriter] = {}

    def register(self, agent_id: str, process_info: CCProcessInfo) -> None:
        self._agents[agent_id] = process_info

    def get_connection(self, agent_id: str) -> asyncio.StreamReaderWriter:
        return self._connections[agent_id]
```

### 完了条件

- [ ] Message→MCPRequest変換ができる
- [ ] MCPResponse→Message変換ができる
- [ ] 思考ログを含むメッセージを送受信できる
- [ ] 複数のClaude Codeプロセスと通信できる
- [ ] エージェントの登録・発見ができる
- [ ] テストがパスする

### 検証方法

```bash
# 単体テスト
pytest tests/test_core/test_mcp_message_bridge.py -v
pytest tests/test_core/test_cc_agent_registry.py -v

# 統合テスト
pytest tests/test_integration/test_cc_mcp_communication.py -v -s
```

---

## Phase 3: エージェント間通信

**目標**: Grand Boss ↔ Middle Manager ↔ Specialists で通信 + 思考ログ出力

### 実装ファイル

| ファイル | 内容 | 行数見積 | 新規/再利用 |
|---------|------|----------|-------------|
| `orchestrator/agents/cc_grand_boss.py` | Grand Boss CCエージェント | 200 | 新規 |
| `orchestrator/agents/cc_middle_manager.py` | Middle Manager CCエージェント | 250 | 新規 |
| `orchestrator/agents/cc_specialists.py` | Specialists CCエージェント | 150 | 新規 |
| `tests/test_integration/test_cc_agent_communication.py` | エージェント間通信テスト | 200 | 新規 |

### 主要実装項目

#### 1. CCAgentBase（基底クラス）

```python
class CCAgentBase:
    def __init__(
        self,
        agent_id: str,
        bridge: MCPMessageBridge,
        registry: CCAgentRegistry,
    ):
        self._agent_id = agent_id
        self._bridge = bridge
        self._registry = registry

    async def send(
        self,
        to_agent: str,
        content: str,
        thinking: str | None = None,
    ) -> None:
        message = CCMessage(
            id=str(uuid4()),
            from_agent=self._agent_id,
            to_agent=to_agent,
            type=MessageType.MESSAGE,
            content=content,
            thinking=thinking,
        )
        await self._bridge.send_message(message)
        self._log_send(message)

    async def receive(self) -> CCMessage:
        message = await self._bridge.receive_message(self._agent_id)
        self._log_receive(message)
        return message

    def _log_send(self, message: CCMessage) -> None:
        timestamp = message.timestamp.strftime("%H:%M:%S")
        print(f"[{timestamp}] > {message.to_agent}へ送信: {message.content}")
        if message.thinking:
            for line in message.thinking.split("\n"):
                print(f"[{timestamp}] [思考] {line}")

    def _log_receive(self, message: CCMessage) -> None:
        timestamp = message.timestamp.strftime("%H:%M:%S")
        print(f"[{timestamp}] > {message.from_agent}から受信: {message.content}")
```

#### 2. GrandBossAgent

```python
class GrandBossAgent(CCAgentBase):
    async def handle_user_task(self, task: str) -> None:
        # 思考ログ
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

    async def aggregate_results(self, results: list[str]) -> str:
        # 結果を集約
        aggregated = "\n".join(results)
        return aggregated
```

### 完了条件

- [ ] Grand Boss→Middle Manager通信
- [ ] Middle Manager→Specialists通信
- [ ] 各インスタンスが思考ログを出力
- [ ] エンドツーエンドのタスク実行
- [ ] 会話の様子がターミナルで観察できる
- [ ] テストがパスする

### 検証方法

```bash
# 統合テスト
pytest tests/test_integration/test_cc_agent_communication.py -v -s

# 手動テスト
python -m orchestrator.cli.cc_cluster start --config config/cc-cluster.yaml
# 別ターミナルからタスクを送信
echo "Webアプリを作って" | python -m orchestrator.cli.cc_cluster send
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
Phase 0 (事前検証)
    │
    ▼
Phase 1 (プロセス起動)
    │
    ▼
Phase 2 (MCPブリッジ)
    │
    ▼
Phase 3 (エージェント間通信)
    │
    ▼
Phase 4 (Webダッシュボード)
```

---

## マイルストーン

| マイルストーン | 期限 | 成果物 |
|---------------|------|--------|
| **MS-0** | Day 1 | Phase 0完了、実装可能性確認 |
| **MS-1** | Day 5 | Phase 1完了、プロセス起動可能 |
| **MS-2** | Day 10 | Phase 2完了、MCP通信可能 |
| **MS-3** | Day 17 | Phase 3完了、エージェント間通信可能 |
| **MS-4** | Day 24 | Phase 4完了、Webダッシュボード完成 |

---

## 優先度

| フェーズ | 優先度 | 説明 |
|---------|--------|------|
| **Phase 0** | P0 | 実装の可能性を確認するため必須 |
| **Phase 1** | P0 | プロセス起動はシステムの基盤 |
| **Phase 2** | P0 | MCP通信はシステムの中核 |
| **Phase 3** | P0 | エージェント間通信はシステムの目的 |
| **Phase 4** | P1 | Webダッシュボードは便利だが必須ではない |
