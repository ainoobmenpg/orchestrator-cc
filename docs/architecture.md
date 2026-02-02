# アーキテクチャ詳細

## システム全体図

```
┌─────────────────────────────────────────────────────────────────────┐
│                         orchestrator-cc                            │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Orchestrator Core                          │  │
│  │                                                               │  │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌────────────┐  │  │
│  │  │ TmuxSession      │  │ CCProcess        │  │ PaneIO     │  │  │
│  │  │ Manager          │  │ Launcher         │  │            │  │  │
│  │  │                  │  │                  │  │            │  │  │
│  │  │ - セッション作成  │  │ - プロセス起動   │  │ - send-keys│  │  │
│  │  │ - ペイン分割     │  │ - 監視・再起動   │  │ - capture  │  │  │
│  │  │ - セッション管理  │  │                  │  │   -pane    │  │  │
│  │  └──────────────────┘  └──────────────────┘  └────────────┘  │  │
│  │                                                               │  │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌────────────┐  │  │
│  │  │ CC Cluster       │  │ Message          │  │ Config     │  │  │
│  │  │ Manager          │  │ Logger           │  │ Loader     │  │  │
│  │  │                  │  │                  │  │            │  │  │
│  │  │ - エージェント管理│  │ - 通信ログ       │  │ - YAML読み │  │  │
│  │  │ - ペイン割り当て │  │ - JSONL保存      │  │ - プロンプト│  │  │
│  │  └──────────────────┘  └──────────────────┘  └────────────┘  │  │
│  │                                                               │  │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌────────────┐  │  │
│  │  │ Cluster          │  │ Dashboard        │  │ WebSocket  │  │  │
│  │  │ Monitor          │  │ Monitor          │  │ Manager    │  │  │
│  │  │                  │  │                  │  │            │  │  │
│  │  │ - 状態監視       │  │ - 統合監視       │  │ - 接続管理 │  │  │
│  │  │ - メトリクス配信 │  │ - コールバック   │  │ - ブロード│  │  │
│  │  │ - アラート通知   │  │   登録           │  │   キャスト │  │  │
│  │  └──────────────────┘  └──────────────────┘  └────────────┘  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                    │                               │
│                                    ▼                               │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              tmux session: orchestratorcc                    │  │
│  │                                                              │  │
│  │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │  │
│  │   │  ペイン0      │  │  ペイン1      │  │  ペイン2      │      │  │
│  │   │              │  │              │  │              │      │  │
│  │   │ Grand Boss   │  │ Middle       │  │ Coding       │      │  │
│  │   │              │  │ Manager      │  │ Specialist   │      │  │
│  │   │ claude       │  │              │  │              │      │  │
│  │   │ --system-    │  │ claude       │  │ claude       │      │  │
│  │   │ prompt       │  │ --system-    │  │ --system-    │      │  │
│  │   │ "..."        │  │ prompt       │  │ prompt       │      │  │
│  │   │              │  │ "..."        │  │ "..."        │      │  │
│  │   └──────────────┘  └──────────────┘  └──────────────┘      │  │
│  │                                                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Web Dashboard (FastAPI)                    │  │
│  │                                                               │  │
│  │  REST API: /api/status, /api/metrics, /api/alerts            │  │
│  │  WebSocket: /ws                                               │  │
│  │  Static: /static/main.js, /static/style.css                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## コンポーネント構成

### 1. TmuxSessionManager

tmuxセッションの作成・管理を行うクラス。

**責務**:
- tmuxセッションの作成・破棄
- ペインの分割・管理
- セッションの状態確認

**主要メソッド**:
```python
class TmuxSessionManager:
    def __init__(self, session_name: str):
        self._session_name = session_name

    def create_session(self) -> None:
        """新しいtmuxセッションを作成"""

    def create_pane(self, split: str = "h") -> int:
        """新しいペインを作成してペイン番号を返す"""

    def send_keys(self, pane_index: int, keys: str) -> None:
        """指定ペインにキー入力を送信"""

    def capture_pane(self, pane_index: int) -> str:
        """指定ペインの出力をキャプチャ"""

    def kill_session(self) -> None:
        """セッションを破棄"""
```

### 2. CCProcessLauncher

各ペインでClaude Codeプロセスを起動・監視するクラス。

**責務**:
- Claude Codeプロセスの起動
- プロセスの状態監視
- 異常終了時の再起動

**主要メソッド**:
```python
class CCProcessLauncher:
    def __init__(self, config: CCProcessConfig, tmux: TmuxSessionManager):
        self._config = config
        self._tmux = tmux

    async def start(self) -> None:
        """Claude Codeプロセスを起動"""

    def is_running(self) -> bool:
        """プロセスが実行中か確認"""

    async def stop(self) -> None:
        """プロセスを停止"""
```

### 3. PaneIO

ペインへの入出力処理を行うクラス。

**責務**:
- ペインへのメッセージ送信
- ペインからの応答取得
- 合言葉（マーカー）検出

**主要メソッド**:
```python
class PaneIO:
    def __init__(self, tmux: TmuxSessionManager):
        self._tmux = tmux

    def send_message(self, pane_index: int, message: str) -> None:
        """指定ペインにメッセージを送信"""

    async def get_response(self, pane_index: int,
                          expected_marker: str,
                          timeout: float = 30.0) -> str:
        """合言葉を検出して応答を取得"""

    def _extract_response(self, output: str, marker: str) -> str:
        """合言葉までの応答部分を抽出"""
```

### 4. CCClusterManager

クラスタ全体を管理するクラス。

**責務**:
- エージェントの登録・管理
- ペイン番号の割り当て
- エージェント間の通信仲介

**主要メソッド**:
```python
class CCClusterManager:
    def __init__(self, config_path: str):
        self._agents: Dict[str, CCProcessConfig] = {}
        self._tmux = TmuxSessionManager("orchestratorcc")

    async def start(self) -> None:
        """クラスタ全体を起動"""

    def get_agent(self, name: str) -> CCAgentBase:
        """指定エージェントを取得"""

    def get_pane(self, agent_name: str) -> int:
        """指定エージェントのペイン番号を取得"""

    def get_marker(self, agent_name: str) -> str:
        """指定エージェントの合言葉を取得"""

    async def stop(self) -> None:
        """クラスタ全体を停止"""
```

### 5. CCAgentBase

エージェントの基底クラス。

**責務**:
- 他エージェントへのメッセージ送信
- 受信メッセージの処理
- 性格プロンプトに基づいた応答生成

**主要メソッド**:
```python
class CCAgentBase:
    def __init__(self, agent_id: str, cluster: CCClusterManager):
        self._agent_id = agent_id
        self._cluster = cluster
        self._logger = MessageLogger()
        self._pane_io = PaneIO(cluster.tmux)

    async def send_to(self, to_agent: str, content: str) -> str:
        """他エージェントにメッセージを送信して応答を取得"""

    async def receive(self) -> Optional[CCMessage]:
        """メッセージを受信"""
```

### 6. MessageLogger

メッセージログを記録するクラス。

**責務**:
- 通信ログの記録
- JSONL形式でのファイル保存
- コンソール出力

**主要メソッド**:
```python
class MessageLogger:
    def __init__(self, log_file: str = "logs/messages.jsonl"):
        self._log_file = log_file

    def log(self, from_agent: str, to_agent: str,
            content: str, msg_type: str) -> str:
        """メッセージをログに記録"""
```

### 7. ClusterMonitor

クラスタ全体の状態を監視するクラス。

**責務**:
- エージェントの状態監視（実行中、アイドル、エラーなど）
- タスクの進捗監視
- リソース使用状況の監視
- アラート通知（異常検知時）

**主要メソッド**:
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

    def get_status_summary(self) -> dict:
        """監視ステータスのサマリーを取得"""
```

### 8. DashboardMonitor

ダッシュボード用の監視統合クラス。

**責務**:
- ClusterMonitorのラッパー
- 定期ポーリングとイベント検知
- WebSocket接続への状態配信

**主要メソッド**:
```python
class DashboardMonitor:
    def __init__(self, cluster_monitor: ClusterMonitor):
        self._cluster_monitor = cluster_monitor

    async def start_monitoring(self) -> None:
        """監視を開始"""

    async def stop_monitoring(self) -> None:
        """監視を停止"""

    def get_cluster_status(self) -> dict:
        """クラスタのステータスを取得"""

    def register_callback(self, callback) -> None:
        """更新通知コールバックを登録"""
```

### 9. WebSocketManager

WebSocket接続管理クラス。

**責務**:
- 接続の管理
- メッセージのブロードキャスト

**主要メソッド**:
```python
class WebSocketManager:
    def __init__(self) -> None:
        self._active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """新しい接続を受け入れ"""

    async def broadcast(self, message: dict) -> None:
        """全クライアントにメッセージをブロードキャスト"""

    async def send_personal(self, message: dict, websocket: WebSocket) -> None:
        """特定のクライアントにメッセージを送信"""
```

### 10. FastAPIアプリケーション

Webダッシュボードのバックエンド。

**エンドポイント**:
- `GET /` - ダッシュボードHTML
- `GET /api/status` - クラスタ状態API
- `GET /api/metrics` - メトリクスAPI
- `GET /api/alerts` - アラート履歴API
- `GET /api/agents` - エージェント一覧API
- `POST /api/monitoring/start` - 監視開始API
- `POST /api/monitoring/stop` - 監視停止API
- `WebSocket /ws` - WebSocketエンドポイント

## データフロー

### 1. クラスタ起動フロー

```
1. ユーザーがクラスタ起動コマンドを実行
   └─> python -m orchestrator.cli start

2. CCClusterManager.start() が呼ばれる
   └─> TmuxSessionManager.create_session()

3. 各エージェントのプロセスを起動
   └─> CCProcessLauncher.start()
       └─> tmux send-keys "claude --system-prompt '...'" Enter

4. 全プロセスの起動を待機・確認
   └─> tmux capture-pane で各ペインの状態を確認
```

### 2. メッセージ送信フロー

```
1. Grand Boss から Middle Manager への送信
   └─> grand_boss.send_to("middle_manager", "タスク分解して")

2. メッセージログを記録
   └─> MessageLogger.log("grand_boss", "middle_manager", ...)

3. 宛先のペインを取得して送信
   └─> PaneIO.send_message(pane1, "タスク分解して")
       └─> tmux send-keys -t session:0.1 "タスク分解して" Enter

4. 応答を待機（合言葉検出）
   └─> PaneIO.get_response(pane1, "MIDDLE MANAGER OK")
       └─> 0.5秒ごとに tmux capture-pane で出力をチェック
       └─> "MIDDLE MANAGER OK" が検出されたら応答を返す
```

### 3. タスク実行フロー

```
1. ユーザーが Grand Boss にタスクを依頼
   └─> タスク: "Webアプリを作って"

2. Grand Boss が Middle Manager にタスクを委任
   └─> send_to("middle_manager", "タスク分解してください: Webアプリを作って")

3. Middle Manager がタスクを分解して Specialists に割り振り
   └─> send_to("coding_writing_specialist", "バックエンドを実装して")
   └─> send_to("testing_specialist", "テスト計画を作成して")

4. 各 Specialist がサブタスクを実行
   └─> Coding Specialist: 実装完了 → "CODING OK\n実装完了しました。"
   └─> Testing Specialist: テスト計画完了 → "TESTING OK\nテスト計画を作成しました。"

5. Middle Manager が結果を集約して Grand Boss に報告
   └─> send_to("grand_boss", "タスク完了しました。")

6. Grand Boss がユーザーに最終結果を提示
```

## 通信プロトコル

### マーカー検出方式（合言葉方式）

各エージェントの応答キーワードを「合言葉」として使用し、それが検出された時点で応答完了と判定します。

| エージェント | 合言葉 |
|-------------|--------|
| Grand Boss | `GRAND BOSS OK` |
| Middle Manager | `MIDDLE MANAGER OK` |
| Coding & Writing Specialist | `CODING OK` |
| Research & Analysis Specialist | `RESEARCH OK` |
| Testing Specialist | `TESTING OK` |

### 検出アルゴリズム

```python
async def get_response(self, pane_index: int,
                      expected_marker: str,
                      timeout: float = 30.0) -> str:
    start_time = time.time()
    previous_output = ""

    while time.time() - start_time < timeout:
        # ペインの出力を取得
        current_output = self._tmux.capture_pane(pane_index)

        # 出力が変化したか確認
        if current_output != previous_output:
            previous_output = current_output

            # 合言葉を検出
            if expected_marker in current_output:
                return self._extract_response(current_output, expected_marker)

        await asyncio.sleep(0.5)  # 軽い待機

    raise TimeoutError(f"合言葉 '{expected_marker}' がタイムアウト")
```

## 設定ファイル

### cc-cluster.yaml

クラスタ全体の設定を定義するYAMLファイル。

```yaml
cluster:
  name: "orchestrator-cc"
  session_name: "orchestrator-cc"
  work_dir: "/path/to/orchestrator-cc"

agents:
  - name: "grand_boss"
    role: "grand_boss"
    personality_prompt_path: "config/personalities/grand_boss.txt"
    marker: "GRAND BOSS OK"
    pane_index: 0

  - name: "middle_manager"
    role: "middle_manager"
    personality_prompt_path: "config/personalities/middle_manager.txt"
    marker: "MIDDLE MANAGER OK"
    pane_index: 1
```

### personalities/*.txt

各エージェントの性格プロンプトファイル。

```
あなたはGrand Bossです。
...
応答には必ず「GRAND BOSS OK」を含めてください。
```

## エラーハンドリング

### タイムアウト処理

```python
try:
    response = await agent.send_to("middle_manager", "タスク分解して")
except TimeoutError as e:
    # 合言葉が検出されなかった場合の処理
    print(f"エラー: {e}")
    # リトライまたはエラー通知
```

### プロセス異常終了

```python
# プロセス監視スレッドで定期的に状態確認
if not launcher.is_running():
    # 自動再起動
    await launcher.restart()
```

## 関連ドキュメント

- [overview.md](overview.md) - プロジェクト全体の概要
- [specs/communication.md](specs/communication.md) - 通信方式の詳細仕様
- [validation.md](validation.md) - 検証結果の記録
