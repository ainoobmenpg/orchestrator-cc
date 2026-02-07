# 通信方式の設計（tmux方式）

## 更新履歴

- **2026-02-01**: MCP方式からtmux方式へ全面切り替え

---

## 決定したアーキテクチャ

### エージェント構成（5エージェント）

```
┌─────────────────────┐
│    Grand Boss       │
│  (ユーザーとの窓口)  │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  Middle Manager     │
│  (タスク分解・進捗管理) │
└──────────┬──────────┘
           │
    ┌──────┴──────┬──────────────┬─────────────┐
    │             │              │             │
┌───▼────┐  ┌────▼──────┐  ┌────▼──────┐  ┌──▼─────────┐
│Coding & │  │Research & │  │Testing    │  │(将来拡張用) │
│Writing  │  │Analysis   │  │Specialist  │  │            │
│Specialist│  │Specialist  │  │          │  │            │
└────────┘  └───────────┘  └───────────┘  └────────────┘
```

| エージェント | 役割 | 応答キーワード | プロンプトファイル |
|-------------|------|--------------|-------------------|
| Grand Boss | ユーザーとの窓口、最終責任者 | GRAND BOSS OK | `config/personalities/grand_boss.txt` |
| Middle Manager | タスク分解、Specialistの取りまとめ、進捗管理 | MIDDLE MANAGER OK | `config/personalities/middle_manager.txt` |
| Coding & Writing Specialist | コーディング + ドキュメント作成 | CODING OK | `config/personalities/coding_writing_specialist.txt` |
| Research & Analysis Specialist | 調査・分析 | RESEARCH OK | `config/personalities/research_analysis_specialist.txt` |
| Testing Specialist | テスト・品質保証 | TESTING OK | `config/personalities/testing_specialist.txt` |

---

## 通信方式：エージェント同士の直接通信

### 採用方式：直接通信

エージェント同士が直接通信を行う方式を採用します。

```
Grand Boss ─────直接────→ Middle Manager
                           │
                           ├────直接────→ Coding & Writing Specialist
                           ├────直接────→ Research & Analysis Specialist
                           └────直接────→ Testing Specialist
```

### 実装イメージ

```python
# 共通ロガー
class MessageLogger:
    """メッセージログを記録する共通クラス"""
    def log(self, from_agent: str, to_agent: str, content: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {from_agent} → {to_agent}: {content}")

# エージェントの基底クラス
class CCAgentBase:
    def __init__(self, agent_id: str, cluster_manager: CCClusterManager):
        self._agent_id = agent_id
        self._cluster = cluster_manager
        self._logger = MessageLogger()  # 共通ロガーを使用
        self._pane_io = PaneIO(cluster_manager.tmux)

    async def send_to(self, to_agent: str, content: str) -> None:
        """他エージェントに直接メッセージを送信"""
        # ログ記録
        self._logger.log(self._agent_id, to_agent, content)

        # 宛先のペインを取得して直接送信
        target_pane = self._cluster.get_pane(to_agent)
        self._pane_io.send_message(target_pane, content)
```

### メリット

| メリット | 説明 |
|---------|------|
| **シンプルな実装** | 宛先のペインに直接メッセージを送るだけ |
| **通常のClaude Codeに近い** | ユーザーがClaude Codeを使うときの直接対話に近い |
| **追従性が高い** | Claude Codeに新機能が追加されたとき、そのまま使える |
| **エージェントの独立性** | 各エージェントが自律的に動作できる |
| **ログは共通クラスで対応** | MessageLoggerクラスを全エージェントが使い回せる |

### 通信フロー例

```
1. Grand BossからMiddle Managerへの送信
   ┌─────────────────────────────────────────────┐
   │ Grand Boss Agent                           │
   │  └─> send_to("middle_manager", "タスク分解して") │
   │      └─> logger.log("grand_boss", "middle_manager", ...) │
   │      └─> pane_io.send_message(pane1, "タスク分解して") │
   └─────────────────────────────────────────────┘

2. tmuxペイン1（Middle Manager）にコマンド送信
   ┌─────────────────────────────────────────────┐
   │ tmux send-keys -t session:0.1 "タスク分解して" Enter │
   └─────────────────────────────────────────────┘

3. Middle Managerが応答
   ┌─────────────────────────────────────────────┐
   │ Middle Manager Agent                        │
   │  └─> 応答生成（MIDDLE MANAGER OKを含む）      │
   └─────────────────────────────────────────────┘

4. orchestrator-ccが応答をキャプチャ
   ┌─────────────────────────────────────────────┐
   │ tmux capture-pane -t session:0.1 -p         │
   │  └─> パースして応答を抽出                     │
   └─────────────────────────────────────────────┘
```

---

## 非同期通信の方式：マーカー検出方式

### 採用方式：応答完了マーカー（合言葉）検出

各エージェントの応答キーワードを「合言葉」として使用し、それが検出された時点で応答完了と判定します。

### 合言葉（マーカー）一覧

| エージェント | 合言葉 | 用途 |
|-------------|--------|------|
| Grand Boss | `GRAND BOSS OK` | Grand Bossの応答完了検出 |
| Middle Manager | `MIDDLE MANAGER OK` | Middle Managerの応答完了検出 |
| Coding & Writing Specialist | `CODING OK` | Coding & Writingの応答完了検出 |
| Research & Analysis Specialist | `RESEARCH OK` | Research & Analysisの応答完了検出 |
| Testing Specialist | `TESTING OK` | Testingの応答完了検出 |

### 実装イメージ

```python
class PaneIO:
    async def get_response(self, pane_index: int,
                          expected_marker: str,
                          timeout: float = 30.0) -> str:
        """合言葉（マーカー）を検出して応答を取得"""
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

        raise TimeoutError(f"合言葉 '{expected_marker}' がタイムアウトまでに検出されませんでした")

    def _extract_response(self, output: str, marker: str) -> str:
        """合言葉までの応答部分を抽出"""
        # 合言葉以降を除去
        lines = output.split('\n')
        response_lines = []

        for line in lines:
            response_lines.append(line)
            # 合言葉が見つかったらそこまで
            if marker in line:
                break

        # プロンプト行を除去して返す
        return self._remove_prompts('\n'.join(response_lines))

# 使用例
class CCAgentBase:
    async def send_to(self, to_agent: str, content: str) -> str:
        """他エージェントにメッセージを送信して応答を取得"""
        # ログ記録
        self._logger.log(self._agent_id, to_agent, content)

        # 宛先のペインを取得
        target_pane = self._cluster.get_pane(to_agent)

        # 送信
        self._pane_io.send_message(target_pane, content)

        # 合言葉を使って応答を取得
        expected_marker = self._cluster.get_marker(to_agent)
        response = await self._pane_io.get_response(target_pane, expected_marker)

        return response
```

### フロー図

```
送信 ──────────────────────────────────────────────→
                                                          │
┌─────────────────────────────────────────────────────┐ │
│ 0.5秒ごとにペイン出力をチェック（tmux capture-pane）  │ │
│  └─> 合言葉が含まれているか確認                       │ │
│      └─> 含まれていれば応答完了                        │ │
│      └─> 含まれていなければ継続                        │ │
└─────────────────────────────────────────────────────┘ │
                                                          │
                                                          ▼
合言葉検出 → 応答を抽出 → 返す
```

### メリット

| メリット | 説明 |
|---------|------|
| **正確な検出** | 応答の完了を確実に判定できる |
| **無駄のない待機** | 応答が完了した時点で即座に取得 |
| **柔軟性** | 合言葉は各エージェントの性格プロンプトで定義済み |
| **タイムアウト付き** | 無限に待たずにタイムアウトでエラー処理 |

### 合言葉のルール

- 各エージェントの性格プロンプトに「返信には必ず「XXX OK」を含めてください」と記載
- 合言葉は応答のどこに含まれていても良い（先頭、途中、末尾）
- 合言葉が複数回含まれる場合、最初の検出で完了とみなす
- タイムアウトデフォルト値は30秒（状況に応じて調整可能）

### エラーハンドリング

```python
try:
    response = await agent.send_to("middle_manager", "タスク分解して")
except TimeoutError as e:
    # 合言葉が検出されなかった場合の処理
    print(f"エラー: {e}")
    # リトライまたはエラー通知
```

---

## データモデル設計

### 基本方針

- **メッセージ**: シンプルに（tmuxで送る最小限の情報のみ）
- **ログ**: 裏で別途記録（タイムスタンプ、ID、タイプ等のデバッグ情報）

### メッセージモデル

```python
@dataclass
class CCMessage:
    """エージェント間のメッセージ（シンプル版）"""
    from_agent: str      # 送信元エージェント（例: "grand_boss"）
    to_agent: str        # 送信先エージェント（例: "middle_manager"）
    content: str         # メッセージ内容
```

**設計思想**: メッセージはtmuxで送るための最小限の情報のみ持つ。デバッグ用のメタデータはログシステムで別途管理する。

### ログモデル

```python
@dataclass
class MessageLogEntry:
    """メッセージログエントリ（裏で記録）"""
    timestamp: str       # タイムスタンプ（ISO 8601形式）
    id: str              # メッセージID（UUID）
    from_agent: str      # 送信元エージェント
    to_agent: str        # 送信先エージェント
    type: str            # メッセージタイプ（task, info, result, error等）
    content: str         # メッセージ内容
```

### ログシステム

```python
class MessageLogger:
    """メッセージログを記録するクラス"""

    def __init__(self, log_file: str = "logs/messages.jsonl"):
        self._log_file = log_file
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

    def log(self, message: CCMessage, msg_type: str) -> str:
        """メッセージをログに記録"""
        entry = MessageLogEntry(
            timestamp=datetime.now().isoformat(),
            id=str(uuid4()),
            from_agent=message.from_agent,
            to_agent=message.to_agent,
            type=msg_type,
            content=message.content
        )

        # コンソールに出力
        print(f"[{entry.timestamp}] {entry.from_agent} → {entry.to_agent} ({entry.type}): {entry.content}")

        # JSONL形式でファイルに保存
        with open(self._log_file, "a") as f:
            f.write(json.dumps(asdict(entry)) + "\n")

        return entry.id
```

### ログファイル形式

**JSONL形式**:
```json
{"timestamp":"2026-02-01T10:30:00.123456","id":"msg-001","from":"grand_boss","to":"middle_manager","type":"task","content":"タスク分解して"}
{"timestamp":"2026-02-01T10:30:15.234567","id":"msg-002","from":"middle_manager","to":"coding_writing_specialist","type":"task","content":"実装して"}
{"timestamp":"2026-02-01T10:31:00.345678","id":"msg-003","from":"coding_writing_specialist","to":"middle_manager","type":"result","content":"CODING OK\n実装完了しました。"}
```

### メッセージタイプ

| タイプ | 説明 | 使用例 |
|--------|------|--------|
| `task` | タスク依頼 | Grand Boss → Middle Manager |
| `info` | 情報通知 | 進捗報告、ステータス更新 |
| `result` | 結果報告 | Specialist → Middle Manager |
| `error` | エラー通知 | 例外発生時 |

### エージェント設定モデル

```python
class CCProcessRole(str, Enum):
    """エージェントの役割"""
    GRAND_BOSS = "grand_boss"
    MIDDLE_MANAGER = "middle_manager"
    SPECIALIST_CODING_WRITING = "specialist_coding_writing"
    SPECIALIST_RESEARCH_ANALYSIS = "specialist_research_analysis"
    SPECIALIST_TESTING = "specialist_testing"

@dataclass
class CCProcessConfig:
    """エージェントの設定情報"""
    name: str                        # エージェント名
    role: CCProcessRole              # 役割
    personality_prompt_path: str     # 性格プロンプトファイルのパス
    marker: str                      # 応答完了マーカー（合言葉）
    pane_index: int                  # tmuxペイン番号
```

### YAML設定ファイル

```yaml
# config/cc-cluster.yaml
cluster:
  name: "orchestrator-cc"
  session_name: "orchestrator-cc"
  work_dir: ".>"

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

  - name: "coding_writing_specialist"
    role: "specialist_coding_writing"
    personality_prompt_path: "config/personalities/coding_writing_specialist.txt"
    marker: "CODING OK"
    pane_index: 2

  - name: "research_analysis_specialist"
    role: "specialist_research_analysis"
    personality_prompt_path: "config/personalities/research_analysis_specialist.txt"
    marker: "RESEARCH OK"
    pane_index: 3

  - name: "testing_specialist"
    role: "specialist_testing"
    personality_prompt_path: "config/personalities/testing_specialist.txt"
    marker: "TESTING OK"
    pane_index: 4
```
