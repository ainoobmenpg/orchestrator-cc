# orchestrator-cc

複数のClaude Codeインスタンスを実際に走らせて、それらに生のやり取りをさせるシステムです。

## 概要

**orchestrator-cc** は、tmuxで複数のClaude Codeプロセスを起動し、YAMLファイルベースの通信で連携させるシステムです。

### アーキテクチャ

```
[ユーザー]
    ↓ tmux attach
[Grand Boss (Claude Code)]
    ↓ YAML作成
[queue/grand_boss_to_middle_manager.yaml]
    ↓ Python監視 (YAMLMonitor)
[NotificationService] → tmux send-keys
[Middle Manager (Claude Code)]
    ↓ YAML読み込み & タスク分解
[queue/middle_manager_to_*.yaml] (x3)
    ↓ Python監視 & 自動通知
[Specialists (Claude Code)]
    ↓ YAML作成
[queue/*_to_middle_manager.yaml]
    ↓ Python監視 & ダッシュボード更新
[status/dashboard.md]
```

## 主な特徴

- **プロセスベースのアーキテクチャ**: 各Claude Codeインスタンスは独立したプロセス
- **tmux方式**: tmuxセッション内の各ペインでClaude Codeを起動・管理
- **YAML通信**: エージェント間通信はYAMLファイルを通じて行われる
- **Python完全自動化**: YAMLファイル監視、自動通知、ダッシュボード更新
- **性格設定**: `--system-prompt`で各エージェントに異なる役割・性格を設定
- **LLM分散**: 各インスタンスが独立してLLMを呼び出し（レートリミット回避）

## 現在の状態

| フェーズ | 状態 | 説明 |
|---------|------|------|
| Phase 0 | ✅ 完了 | Claude Code制御の検証 |
| Phase 0.5 | ✅ 完了 | tmux方式の検証 |
| Phase 1 | ✅ 完了 | プロセス起動・管理機能 |
| Phase 2 | ✅ 完了 | エージェントクラス方式（Phase 3で削除） |
| Phase 3 | ✅ 完了 | YAML通信方式への移行 |

## エージェント構成

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

| エージェント | 役割 | 応答キーワード |
|-------------|------|--------------|
| Grand Boss | ユーザーとの窓口、最終責任者 | GRAND BOSS OK |
| Middle Manager | タスク分解、Specialistの取りまとめ、進捗管理 | MIDDLE MANAGER OK |
| Coding & Writing Specialist | コーディング + ドキュメント作成 | CODING OK |
| Research & Analysis Specialist | 調査・分析 | RESEARCH OK |
| Testing Specialist | テスト・品質保証 | TESTING OK |

## 使い方

### 1. クラスタを起動する

```bash
python3 -m orchestrator.cli start --config config/cc-cluster.yaml
```

### 2. Grand Bossにタスクを送信する

```bash
tmux attach-session -t orchestrator-cc
```

ペイン0（Grand Boss）でタスクを入力します。

### 3. 進捗を確認する

```bash
cat status/dashboard.md
```

## ディレクトリ構成

```
orchestrator-cc/
├── config/                      # 設定ファイル
│   ├── cc-cluster.yaml          # クラスタ設定
│   └── personalities/           # 性格プロンプト
│       ├── grand_boss.txt
│       ├── middle_manager.txt
│       ├── coding_writing_specialist.txt
│       ├── research_analysis_specialist.txt
│       └── testing_specialist.txt
│
├── orchestrator/                # メインパッケージ
│   └── core/                    # コア機能
│       ├── tmux_session_manager.py
│       ├── cc_process_models.py
│       ├── cc_process_launcher.py
│       ├── cc_cluster_manager.py
│       ├── pane_io.py
│       ├── yaml_protocol.py      # YAML通信プロトコル
│       ├── yaml_monitor.py       # YAMLファイル監視
│       ├── notification_service.py # 通知サービス
│       └── dashboard_manager.py   # ダッシュボード管理
│
├── queue/                       # 通信YAMLファイル（自動生成・監視）
│   ├── grand_boss_to_middle_manager.yaml
│   ├── middle_manager_to_coding.yaml
│   ├── middle_manager_to_research.yaml
│   ├── middle_manager_to_testing.yaml
│   ├── coding_to_middle_manager.yaml
│   ├── research_to_middle_manager.yaml
│   ├── testing_to_middle_manager.yaml
│   └── middle_manager_to_grand_boss.yaml
│
├── status/                      # ステータスファイル
│   ├── agents/                  # 各エージェントのステータスYAML
│   │   ├── grand_boss.yaml
│   │   ├── middle_manager.yaml
│   │   ├── coding_writing_specialist.yaml
│   │   ├── research_analysis_specialist.yaml
│   │   └── testing_specialist.yaml
│   └── dashboard.md             # ダッシュボード（自動更新）
│
├── tests/                       # テスト
│   └── test_core/
│
└── docs/                        # ドキュメント
    ├── roadmap.md
    ├── validation.md
    └── specs/
        ├── yaml-communication.md  # YAML通信プロトコル詳細
        └── agent-behavior.md      # エージェント動作仕様
```

## YAML通信方式

詳細は [docs/specs/yaml-communication.md](docs/specs/yaml-communication.md) を参照してください。

### 通信YAMLフォーマット

```yaml
id: "msg-001"
from: "grand_boss"
to: "middle_manager"
type: "task"  # task, info, result, error
status: "pending"  # pending, in_progress, completed, failed
content: |
  タスク内容
timestamp: "2026-02-01T10:00:00"
metadata:  # オプション
  key: value
```

### ステータスYAMLフォーマット

```yaml
agent_name: "grand_boss"
state: "idle"  # idle, working, completed, error
current_task: null
last_updated: "2026-02-01T10:00:00"
statistics:
  tasks_completed: 0
```

## 開発

詳細な開発ガイドラインは [CLAUDE.md](CLAUDE.md) を参照してください。

### 依存関係

```bash
pip install -e '.[dev]'
```

### テスト実行

```bash
pytest tests/ -v
```

### リントチェック

```bash
ruff check .
```

## ライセンス

MIT License
