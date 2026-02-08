# 実装ロードマップ

## フェーズ概要

| フェーズ | 目標 | 期間 | 状態 | 完了日 |
|---------|------|------|------|--------|
| **Phase 0** | 事前検証 | 1日 | ✅ 完了 | 2026-02-01 |
| **Phase 0.5** | 中間検証（設定ファイル・複数プロセス） | 1日 | ✅ 完了 | 2026-02-01 |
| **Phase 1** | 基礎プロセス起動・管理機能 | 3-5日 | ✅ 完了 | 2026-02-02 |
| **Phase 2** | YAML通信方式の実装 | 3-5日 | ✅ 完了 | 2026-02-02 |
| **Phase 3** | クラスタ管理・CLI拡張 | 5-7日 | ✅ 完了 | 2026-02-02 |
| **Phase 4** | Webダッシュボード | 5-7日 | ✅ 完了 | 2026-02-03 |

---

## Phase 0: 事前検証 ✅ 完了 (2026-02-01)

**目標**: Claude Codeの`mcp serve`機能を検証し、実装の可能性を確認する

### 検証項目

| 項目 | 検証内容 | 結果 |
|------|----------|------|
| **V-001** | `claude mcp serve` の基本動作 | ✅ 成功 |
| **V-002** | `--system-prompt` の動作 | ❌ MCPサーバーモードでは利用不可 |
| **V-003** | プログラム制御の可否 | ✅ 成功 |
| **V-004** | 思考ログの出力方法 | ⚠️ 検証保留 |

### 完了条件

- [x] V-001: `tools/list` が正しいJSON-RPCレスポンスを返す
- [ ] V-002: `--system-prompt` で設定した性格が反映される
- [x] V-003: Pythonからstdin/stdout経由で制御できる
- [ ] V-004: 思考ログを含むメッセージを処理できる

### 結果

`--system-prompt` がMCPサーバーモードで利用できないことが判明したため、**tmux方式**への切り替えを決定。

---

## Phase 0.5: 中間検証（tmux方式への切り替え） ✅ 完了 (2026-02-01)

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

---

## Phase 1: 基礎プロセス起動・管理機能（tmux方式） ✅ 完了 (2026-02-02)

**目標**: tmuxセッションで複数のClaude Codeプロセスを起動・管理する

### 実装ファイル

| ファイル | 内容 | 状態 |
|---------|------|------|
| `orchestrator/core/tmux_session_manager.py` | tmuxセッションの作成・管理 | ✅ 実装済 |
| `orchestrator/core/cc_process_models.py` | エージェント設定データモデル | ✅ 実装済 |
| `orchestrator/core/cc_process_launcher.py` | Claude Codeプロセス起動・監視 | ✅ 実装済 |
| `orchestrator/core/pane_io.py` | ペインへの入出力処理 | ✅ 実装済 |
| `config/cc-cluster.yaml` | クラスタ設定ファイル | ✅ 作成済 |
| `config/personalities/*.txt` | 各エージェントの性格プロンプト | ✅ 作成済 |
| `tests/test_core/test_tmux_session_manager.py` | tmuxセッションマネージャーテスト | ✅ 作成済 |
| `tests/test_core/test_pane_io.py` | ペイン入出力テスト | ✅ 作成済 |

### 完了条件

- [x] tmuxセッションを作成できる
- [x] 複数のペインを分割できる
- [x] 各ペインでClaude Codeを起動できる
- [x] 性格プロンプトが反映される
- [x] メッセージを送信・応答を取得できる
- [x] 出力のパース処理が動作する
- [x] テストがパスする

### 検証方法

```bash
# 単体テスト
pytest tests/test_core/test_tmux_session_manager.py -v
pytest tests/test_core/test_pane_io.py -v

# 統合テスト
pytest tests/test_integration/test_phase1.py -v
```

---

## Phase 2: YAML通信方式の実装 ✅ 完了 (2026-02-02)

**目標**: エージェント間通信をYAMLファイルベースで実装する

### 実装ファイル

| ファイル | 内容 | 状態 |
|---------|------|------|
| `orchestrator/core/yaml_protocol.py` | YAML通信プロトコル（TaskMessage, AgentStatus） | ✅ 実装済 |
| `orchestrator/core/yaml_monitor.py` | YAMLファイル監視（watchdog使用） | ✅ 実装済 |
| `orchestrator/core/notification_service.py` | エージェント通知サービス | ✅ 実装済 |
| `queue/*.yaml` | 通信YAMLテンプレート | ✅ 作成済 |
| `status/agents/*.yaml` | ステータステンプレート | ✅ 作成済 |
| `tests/test_integration/test_phase2_minimum.py` | 統合テスト | ✅ 作成済 |
| `tests/test_integration/test_phase2.py` | 完全版統合テスト | ✅ 作成済 |

### 主要実装項目

#### 1. YAML通信プロトコル

```python
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
    from_agent: str
    to: str
    type: MessageType
    status: MessageStatus
    content: str
    timestamp: str
    metadata: dict[str, Any]
```

#### 2. YAMLメッセージ形式

```yaml
id: "msg-001"
from: "grand_boss"
to: "middle_manager"
type: "task"
status: "pending"
content: |
  タスク内容
timestamp: "2026-02-02T10:00:00"
metadata:
  priority: "high"
```

#### 3. ファイル監視

`watchdog` ライブラリを使用して、`queue/` ディレクトリのYAMLファイル変更をリアルタイムで監視します。

### 完了条件

- [x] YAML通信プロトコルが実装されている
- [x] ファイル監視が動作する
- [x] エージェント間でYAMLメッセージを送受信できる
- [x] 通知サービスが動作する
- [x] E2Eテストがパスする

### 検証方法

```bash
# E2Eテスト
bash scripts/test-e2e-phase2.sh

# 統合テスト
pytest tests/test_integration/test_phase2.py -v
```

---

## Phase 3: クラスタ管理・CLI拡張 ✅ 完了 (2026-02-02)

**目標**: クラスタ全体の管理とCLIコマンドの拡張

### 実装ファイル

| ファイル | 内容 | 状態 |
|---------|------|------|
| `orchestrator/core/cc_cluster_manager.py` | クラスタ全体の管理 | ✅ 実装済 |
| `orchestrator/agents/cc_agent_base.py` | エージェント基底クラス | ✅ 実装済 |
| `orchestrator/agents/grand_boss.py` | Grand Boss実装 | ✅ 実装済 |
| `orchestrator/agents/middle_manager.py` | Middle Manager実装 | ✅ 実装済 |
| `orchestrator/agents/specialists.py` | Specialists実装 | ✅ 実装済 |
| `orchestrator/cli/main.py` | CLIコマンド | ✅ 実装済 |
| `tests/test_integration/test_phase2.py` | エージェント間通信テスト | ✅ 作成済 |

### CLIコマンド

```bash
# クラスタ起動
python -m orchestrator.cli start

# タスク実行
python -m orchestrator.cli execute "タスク内容"

# ステータス確認
python -m orchestrator.cli status

# クラスタ停止
python -m orchestrator.cli stop
```

### 完了条件

- [x] クラスタ全体の起動・停止ができる
- [x] CLIからタスクを実行できる
- [x] エージェント間通信が動作する
- [x] ステータス確認ができる
- [x] テストがパスする

### 検証方法

```bash
# クラスタ起動
python -m orchestrator.cli start --config config/cc-cluster.yaml

# タスク実行
python -m orchestrator.cli execute "新しい機能を実装してください"

# ステータス確認
python -m orchestrator.cli status
```

---

## Phase 4: Webダッシュボード ✅ 完了 (2026-02-03)

**目標**: Webブラウザ上で会話を観察できるようにする

### 実装ファイル

| ファイル | 内容 | 状態 |
|---------|------|------|
| `orchestrator/core/cluster_monitor.py` | クラスタ監視 | ✅ 実装済 |
| `orchestrator/web/dashboard.py` | Webダッシュボード（FastAPI） | ✅ 実装済 |
| `orchestrator/web/message_handler.py` | WebSocketメッセージハンドラー | ✅ 実装済 |
| `orchestrator/web/monitor.py` | ダッシュボード監視統合 | ✅ 実装済 |
| `orchestrator/web/static/main.js` | フロントエンドJavaScript | ✅ 実装済 |
| `orchestrator/web/static/style.css` | スタイルシート | ✅ 実装済 |
| `orchestrator/web/templates/index.html` | HTMLテンプレート | ✅ 実装済 |

### 主要実装項目

#### 1. ClusterMonitor（クラスタ監視）

クラスタ全体の状態を監視するクラス。

```python
class ClusterMonitor:
    def __init__(self, cluster_manager: CCClusterManager):
        self._cluster = cluster_manager

    async def start(self) -> None:
        """監視を開始"""

    async def stop(self) -> None:
        """監視を停止"""

    def get_metrics(self) -> ClusterMetrics:
        """クラスタメトリクスを取得"""

    def get_alerts(self) -> list[Alert]:
        """アラート履歴を取得"""
```

#### 2. FastAPIアプリケーション

```python
app = FastAPI()

class WebSocketManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def broadcast(self, message: dict) -> None:
        for connection in self.active_connections:
            await connection.send_json(message)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    manager.active_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await handler.handle_message(data, websocket)
    finally:
        manager.active_connections.remove(websocket)

@app.get("/")
async def get_dashboard():
    return FileResponse("orchestrator/web/templates/index.html")

@app.get("/api/status")
async def get_status():
    return dashboard_monitor.get_cluster_status()
```

#### 3. フロントエンド（JavaScript）

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

- [x] Webダッシュボードが起動できる
- [x] 複数インスタンスの会話がリアルタイムで見える
- [x] 思考ログの表示/非表示が切り替えられる
- [x] 過去ログを閲覧できる
- [x] テストがパスする

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
Phase 0 (事前検証) + Phase 0.5 (tmux方式検証) ✅
    │
    ▼
Phase 1 (tmuxプロセス起動・管理) ✅
    │
    ▼
Phase 2 (YAML通信方式) ✅
    │
    ▼
Phase 3 (クラスタ管理・CLI拡張) ✅
    │
    ▼
Phase 4 (Webダッシュボード) ✅
```

---

## マイルストーン

| マイルストーン | 期限 | 状態 | 完了日 |
|---------------|------|------|--------|
| **MS-0** | Day 1 | ✅ 完了 | 2026-02-01 |
| **MS-1** | Day 5 | ✅ 完了 | 2026-02-02 |
| **MS-2** | Day 10 | ✅ 完了 | 2026-02-02 |
| **MS-3** | Day 17 | ✅ 完了 | 2026-02-02 |
| **MS-4** | Day 24 | ✅ 完了 | 2026-02-03 |

---

## 優先度

| フェーズ | 優先度 | 説明 | 状態 |
|---------|--------|------|------|
| **Phase 0** | P0 | 実装の可能性を確認するため必須 | ✅ 完了 |
| **Phase 0.5** | P0 | tmux方式の実現可能性を確認するため必須 | ✅ 完了 |
| **Phase 1** | P0 | tmuxプロセス起動はシステムの基盤 | ✅ 完了 |
| **Phase 2** | P0 | YAML通信はシステムの中核 | ✅ 完了 |
| **Phase 3** | P0 | クラスタ管理・CLI拡張はシステムの目的 | ✅ 完了 |
| **Phase 4** | P1 | Webダッシュボードは便利だが必須ではない | ✅ 完了 |

---

## Issue完了履歴

| Issue | タイトル | 完了日 | 関連フェーズ |
|-------|---------|--------|-------------|
| #37 | Issue #37確認のみで実装なし | 2026-02-02 | - |
| #38 | Phase 2関連（詳細不明） | 2026-02-02 | Phase 2 |
| #39 | README更新（Phase 2完了後の現状に合わせた文書作成） | 2026-02-02 | Phase 2 |
| #40 | Phase 2/3関連（詳細不明） | 2026-02-02 | Phase 2, 3 |
| #42 | Phase 4 Webダッシュボード実装 | 2026-02-03 | Phase 4 |

---

---

## 「人間臭いAgent Teams体験」への移行 ✅ 完了 (2026-02-08)

**目標**: 「便利に使うツール」から「体験・学習できるツール」への方向転換

### コンテキスト

**ユーザーのビジョン**: Agent Teamsを便利に、楽しく使うためのツール」から「Agent Teamsを体験・学習できるツール」へ

**新たな方向性**:
1. **お手本コード集** - よく使うAgent Teamsパターンの例
2. **人間臭さの可視化** - 会議室、Slack風のやり取り、思考ログ、愚痴、独り言
3. **フェーズ分け** - ①体験ツール → ②利便性・監視機能

### 実装フェーズ

| フェーズ | 目標 | 期間 | 状態 | 完了日 |
|---------|------|------|------|--------|
| **フェーズ1** | CLAUDE.mdのルール緩和 | 1日 | ✅ 完了 | 2026-02-08 |
| **フェーズ2** | ダッシュボードの簡素化 | 2〜3日 | ✅ 完了 | 2026-02-08 |
| **フェーズ3** | 「人間臭さ」体験の実装 | 5〜7日 | ✅ 完了 | 2026-02-08 |

### フェーズ1: CLAUDE.mdのルール緩和 ✅ 完了

**目的**: 「お手本コード集」としての教育効果を向上させる

**変更内容**:
- 「常にAgent Teamsを使用する」→「Agent Teamsの活用（推奨）」に変更
- タスク複雑度に応じたガイドライン表を追加

| 複雑度 | ステップ数 | エージェント使用 |
|--------|-----------|----------------|
| 小さなタスク | 1〜2 | 単独で実行してもOK |
| 中程度のタスク | 3〜5 | Agent Teamsの使用を推奨 |
| 複雑なタスク | 6+ | Agent Teamsの使用を強く推奨 |

### フェーズ2: ダッシュボードの簡素化 ✅ 完了

**目的**: ダッシュボードを「監視ツール」から「体験ツール」へ簡素化

**変更内容**:
- 不要なコンポーネントを削除（Tutorial、Timeline、SystemLog）
- タブ構造を簡素化（会議室、タスクボード）

### フェーズ3: 「人間臭さ」体験の実装 ✅ 完了

**目的**: 「会議室」「Slack風」の人間臭い体験を実現

**実装機能**:
- Slack風チャットUI（ChatInput、ChatMessage、ChatMessageList、ThinkingMessage、TypingIndicator）
- カスタムフック: useThinkingLog（思考ログのリアルタイム取得）
- 会議室ページ: ConferenceRoomPage.tsx（Slack風UI）

### 実行計画

詳しくは以下の計画を参照：

## コンテキスト

**ユーザーのビジョン**: 「Agent Teamsを便利に、楽しく使うためのツール」から「Agent Teamsを体験・学習できるツール」へ

**新たな方向性**:
1. **お手本コード集** - よく使うAgent Teamsパターンの例
2. **人間臭さの可視化** - 会議室、Slack風のやり取り、思考ログ、愚痴、独り言
3. **フェーズ分け** - ①体験ツール → ②利便性・監視機能

---

## 今後の予定

1. **Phase 4: Webダッシュボード** - エージェント間通信の可視化
2. **機能拡張** - タスク管理、ログ管理、エラーハンドリングの改善
3. **パフォーマンス最適化** - 通信遅延の計測と改善
4. **ドキュメント整備** - APIドキュメント、ユーザーガイドの充実
