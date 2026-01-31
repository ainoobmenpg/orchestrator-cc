# API仕様

## CLI API

### コマンド一覧

| コマンド | 説明 |
|---------|------|
| `cluster init` | 設定ファイルの初期化 |
| `cluster start` | クラスタの起動 |
| `cluster stop` | クラスタの停止 |
| `cluster restart` | クラスタの再起動 |
| `cluster status` | クラスタの状態確認 |
| `cluster logs` | ログの表示 |
| `cluster send` | メッセージの送信 |

---

## cluster init

設定ファイルを初期化します。

### 使用方法

```bash
orchestrator-cc cluster init [OPTIONS]
```

### オプション

| オプション | 説明 | デフォルト |
|-----------|------|----------|
| `--name, -n <name>` | クラスタ名 | "default" |
| `--work-dir <path>` | 作業ディレクトリ | "/tmp/orchestrator-cc" |
| `--log-dir <path>` | ログディレクトリ | "/tmp/orchestrator-cc/logs" |
| `--output, -o <path>` | 出力ファイルパス | "config/cc-cluster.yaml" |

### 例

```bash
# デフォルト設定で初期化
orchestrator-cc cluster init

# カスタム設定で初期化
orchestrator-cc cluster init \
  --name my-cluster \
  --work-dir ./work \
  --log-dir ./logs \
  --output config/my-cluster.yaml
```

---

## cluster start

クラスタを起動します。

### 使用方法

```bash
orchestrator-cc cluster start [OPTIONS]
```

### オプション

| オプション | 説明 | デフォルト |
|-----------|------|----------|
| `--config, -c <path>` | 設定ファイルパス | "config/cc-cluster.yaml" |
| `--agents, -a <agents>` | 起動するエージェント（カンマ区切り） | 全エージェント |
| `--detach, -d` | デタッチモードで起動 | false |
| `--no-logs` | ログを表示しない | false |

### 例

```bash
# デフォルト設定で起動
orchestrator-cc cluster start

# カスタム設定で起動
orchestrator-cc cluster start --config config/my-cluster.yaml

# 特定のエージェントのみ起動
orchestrator-cc cluster start --agents grand_boss,middle_manager

# デタッチモードで起動
orchestrator-cc cluster start --detach
```

---

## cluster stop

クラスタを停止します。

### 使用方法

```bash
orchestrator-cc cluster stop [OPTIONS]
```

### オプション

| オプション | 説明 | デフォルト |
|-----------|------|----------|
| `--config, -c <path>` | 設定ファイルパス | "config/cc-cluster.yaml" |
| `--force, -f` | 強制停止（SIGKILL） | false |
| `--timeout <seconds>` | グレースフルシャットダウンのタイムアウト | 30 |

### 例

```bash
# グレースフルシャットダウン
orchestrator-cc cluster stop

# 強制停止
orchestrator-cc cluster stop --force

# タイムアウト指定
orchestrator-cc cluster stop --timeout 60
```

---

## cluster restart

クラスタを再起動します。

### 使用方法

```bash
orchestrator-cc cluster restart [OPTIONS]
```

### オプション

| オプション | 説明 | デフォルト |
|-----------|------|----------|
| `--config, -c <path>` | 設定ファイルパス | "config/cc-cluster.yaml" |
| `--agents, -a <agents>` | 再起動するエージェント（カンマ区切り） | 全エージェント |

### 例

```bash
# 全エージェントを再起動
orchestrator-cc cluster restart

# 特定のエージェントのみ再起動
orchestrator-cc cluster restart --agents middle_manager
```

---

## cluster status

クラスタの状態を確認します。

### 使用方法

```bash
orchestrator-cc cluster status [OPTIONS]
```

### オプション

| オプション | 説明 | デフォルト |
|-----------|------|----------|
| `--config, -c <path>` | 設定ファイルパス | "config/cc-cluster.yaml" |
| `--json` | JSON形式で出力 | false |
| `--watch, -w` | 状態を監視（1秒間隔） | false |

### 出力例

```
Cluster: default
Status: Running

Processes:
  NAME               ROLE                  STATUS    PID    UPTIME
  grand_boss         grand_boss            Running   1234   00:05:23
  middle_manager     middle_manager        Running   1235   00:05:22
  coding_specialist  specialist_coding     Running   1236   00:05:21
  research_specialist specialist_research  Running   1237   00:05:20

Messages:
  Total: 156
  Pending: 0
  Completed: 156
  Failed: 0
```

---

## cluster logs

ログを表示します。

### 使用方法

```bash
orchestrator-cc cluster logs [OPTIONS] [AGENT]
```

### オプション

| オプション | 説明 | デフォルト |
|-----------|------|----------|
| `--config, -c <path>` | 設定ファイルパス | "config/cc-cluster.yaml" |
| `--follow, -f` | ログを追従（tail -f） | false |
| `--tail, -n <lines>` | 最後のN行を表示 | 50 |
| `--since <time>` | 指定時刻以降のログを表示 | - |
| `--level <level>` | ログレベルでフィルタ | - |

### 例

```bash
# 全エージェントのログを表示
orchestrator-cc cluster logs

# 特定のエージェントのログを表示
orchestrator-cc cluster logs grand_boss

# ログを追従
orchestrator-cc cluster logs --follow

# 最後の100行を表示
orchestrator-cc cluster logs --tail 100

# ERRORレベル以上のログのみ表示
orchestrator-cc cluster logs --level ERROR
```

---

## cluster send

メッセージを送信します。

### 使用方法

```bash
orchestrator-cc cluster send [OPTIONS] MESSAGE
```

### オプション

| オプション | 説明 | デフォルト |
|-----------|------|----------|
| `--config, -c <path>` | 設定ファイルパス | "config/cc-cluster.yaml" |
| `--to, -t <agent>` | 送信先エージェント | "grand_boss" |
| `--from, -f <agent>` | 送信元エージェント（省略時は"system"） | "system" |

### 例

```bash
# Grand Bossにメッセージを送信
echo "Webアプリを作って" | orchestrator-cc cluster send

# Middle Managerに直接メッセージを送信
echo "進捗を報告して" | orchestrator-cc cluster send --to middle_manager

# ファイルからメッセージを送信
orchestrator-cc cluster send --to grand_boss < task.txt
```

---

## Python API

### CCClusterManager

クラスタを管理するメインクラスです。

```python
from orchestrator.core.cluster_manager import CCClusterManager

class CCClusterManager:
    async def start(self) -> None:
        """クラスタを起動"""

    async def stop(self, force: bool = False) -> None:
        """クラスタを停止"""

    async def restart(self, agents: list[str] | None = None) -> None:
        """クラスタを再起動"""

    async def status(self) -> ClusterStatus:
        """クラスタの状態を取得"""

    async def send_message(
        self,
        to_agent: str,
        content: str,
        thinking: str | None = None,
    ) -> None:
        """メッセージを送信"""
```

### CCProcessLauncher

プロセスを起動・管理するクラスです。

```python
from orchestrator.core.cc_process_launcher import CCProcessLauncher

class CCProcessLauncher:
    async def start(self) -> None:
        """プロセスを起動"""

    async def stop(self, force: bool = False) -> None:
        """プロセスを停止"""

    async def is_running(self) -> bool:
        """プロセスが実行中か確認"""

    def get_status(self) -> ProcessStatus:
        """プロセスの状態を取得"""
```

### MCPMessageBridge

メッセージブリッジクラスです。

```python
from orchestrator.core.mcp_message_bridge import MCPMessageBridge

class MCPMessageBridge:
    async def send_message(self, message: CCMessage) -> None:
        """メッセージを送信"""

    async def receive_message(self, agent_id: str) -> CCMessage | None:
        """メッセージを受信"""

    async def broadcast(self, message: CCMessage) -> None:
        """ブロードキャスト送信"""
```

---

## Web API（Phase 4）

### エンドポイント

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/` | ダッシュボード |
| GET | `/api/status` | クラスタの状態 |
| GET | `/api/agents` | エージェント一覧 |
| GET | `/api/agents/{id}` | エージェント詳細 |
| GET | `/api/messages` | メッセージ一覧 |
| POST | `/api/messages` | メッセージ送信 |
| GET | `/api/logs` | ログ取得 |
| WS | `/ws` | WebSocketエンドポイント |

### WebSocket API

#### 接続

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
```

#### メッセージ形式

```json
{
  "type": "message",
  "data": {
    "id": "msg-123",
    "from_agent": "grand_boss",
    "to_agent": "middle_manager",
    "content": "タスクの分解をお願い",
    "thinking": "これは複雑なタスクだな...",
    "timestamp": "2026-02-01T14:32:10Z"
  }
}
```

#### イベントタイプ

| タイプ | 説明 |
|-------|------|
| `message` | メッセージ送受信 |
| `status` | エージェントの状態変化 |
| `log` | ログ出力 |
| `error` | エラー発生 |

---

## 設定ファイル

### cc-cluster.yaml

```yaml
cc_cluster:
  name: "default"
  work_dir: "/tmp/orchestrator-cc"
  log_dir: "/tmp/orchestrator-cc/logs"
  personalities_dir: "config/personalities"

  thinking_log:
    enabled: true
    detail_level: "detailed"

  processes:
    - name: "grand_boss"
      role: "grand_boss"
      claude_path: "claude"
      mcp_host: "localhost"
      mcp_port: 9000
      personality_prompt_path: "config/personalities/grand_boss.txt"
      thinking_log_enabled: true
      thinking_log_detail: "detailed"
      auto_restart: true
      max_restarts: 5
      restart_delay: 5.0

    - name: "middle_manager"
      role: "middle_manager"
      # ... 同様の設定
```

---

## エラーコード

| コード | 説明 |
|-------|------|
| 0 | 成功 |
| 1 | 一般的なエラー |
| 2 | 設定ファイルが見つからない |
| 3 | 設定ファイルが無効 |
| 4 | プロセスの起動に失敗 |
| 5 | プロセスが実行中 |
| 6 | プロセスが停止中 |
| 7 | エージェントが見つからない |
| 8 | メッセージの送信に失敗 |
| 9 | タイムアウト |

---

## バージョン

```bash
$ orchestrator-cc --version
orchestrator-cc 0.1.0
```
