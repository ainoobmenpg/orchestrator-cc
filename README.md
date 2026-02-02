# orchestrator-cc

## 概要

複数のClaude Codeインスタンスを実際に走らせて、それらに生のやり取りをさせるシステム。

## 目的

現在の `orchestrator` プロジェクトは、Pythonオブジェクトとして実装されたエージェントがLLMを呼び出すアーキテクチャです。これは「マルチLLM調整システム」としては機能しますが、本来の目的とは異なります。

**orchestrator-cc** は、本来の目的である以下を実現します：

```
Claude Code A (プロセス1)
  ↓ YAMLファイルで通信
Claude Code B (プロセス2)
  ↓ 処理してYAMLファイルに結果を書き込み
Claude Code C (上司、プロセス3)
  ↓ YAMLファイルを監視して通知
```

## 主な特徴

- **プロセスベースのアーキテクチャ**: 各Claude Codeインスタンスは独立したプロセス
- **tmux方式**: tmuxセッション内の各ペインでClaude Codeを起動・管理
- **YAML通信**: エージェント間通信はYAMLファイルベース（`queue/*.yaml`）
- **ファイル監視**: `watchdog` によるYAML変更の自動検知
- **性格設定**: `--system-prompt`で各エージェントに異なる役割・性格を設定
- **LLM分散**: 各インスタンスが独立してLLMを呼び出し（レートリミット回避）

## 現在の状態

**Phase 0**: ✅ 検証完了（2026-02-01）

| 検証項目 | 結果 |
|---------|------|
| V-001: `claude mcp serve` の基本動作 | ✅ 成功 |
| V-002: `--system-prompt` の動作確認 | ❌ MCPサーバーモードでは利用不可 |
| V-003: Pythonからのプログラム制御 | ✅ 成功 |

**Phase 0.5**: ✅ 検証完了（2026-02-01）

| 検証項目 | 結果 |
|---------|------|
| V-101: tmuxで複数プロセス起動 | ✅ 成功 |
| V-102: Pythonからtmux制御 | ✅ 成功 |
| V-103: 出力のキャプチャ・パース | ✅ 成功（条件付き） |

**Phase 1**: ✅ 完了（2026-02-02）

tmux方式でのプロセス起動・管理機能が実装されました。

**Phase 2**: ✅ 完了（2026-02-02）

YAMLベースのエージェント間通信が実装されました。

### アーキテクチャ変更履歴

- **2026-02-01**: 設定ファイル分離アプローチから**tmux方式**へ切り替え
- **2026-02-02**: Phase 2完了 - **YAML通信方式**の実装

---

## YAML通信方式のアーキテクチャ

### 通信フロー図

```
┌──────────────────────────────────────────────────────────────────────┐
│                         orchestrator-cc クラスタ                       │
├──────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌────────────────┐      queue/       ┌────────────────┐             │
│  │  Grand Boss    │ ─────────────────▶│ Middle Manager  │             │
│  │  (Pane 0)      │  YAMLで通信       │  (Pane 1)       │             │
│  └────────────────┘                   └────────────────┘             │
│                                                │                       │
│         queue/                                  │ queue/              │
│         *.yaml                                  │ *.yaml             │
│                                                ▼                       │
│         ┌──────────────────────────────────────────────────┐          │
│         │                  Specialists                     │          │
│         │  ┌──────────────┬──────────────┬──────────────┐ │          │
│         │  │ Coding &     │ Research &   │ Testing      │ │          │
│         │  │ Writing      │ Analysis     │ Specialist   │ │          │
│         │  │ (Pane 2)     │ (Pane 3)     │ (Pane 4)     │ │          │
│         │  └──────────────┴──────────────┴──────────────┘ │          │
│         └──────────────────────────────────────────────────┘          │
│                                                                        │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │                  YAMLMonitor (watchdog)                      │     │
│  │         queue/ ディレクトリをリアルタイム監視                 │     │
│  └─────────────────────────────────────────────────────────────┘     │
│                                                                        │
└──────────────────────────────────────────────────────────────────────┘
```

### YAMLメッセージ形式

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

#### メッセージタイプ

| タイプ | 説明 | 使用例 |
|--------|------|--------|
| `task` | タスク依頼 | Grand Boss → Middle Manager |
| `info` | 情報通知 | 進捗報告、ステータス更新 |
| `result` | 結果報告 | Specialist → Middle Manager |
| `error` | エラー通知 | 例外発生時 |

### 通信フロー詳細

```
1. Grand Boss → Middle Manager
   ┌─────────────────────────────────────────────┐
   │ Grand Boss Agent                            │
   │  └─> _write_yaml_message()                  │
   │      └─> queue/grand_boss_to_middle_*.yaml  │
   └─────────────────────────────────────────────┘
                        ↓
   ┌─────────────────────────────────────────────┐
   │ YAMLMonitor が変更を検知                     │
   │  └─> NotificationService.notify_agent()    │
   │      └─> tmux send-keys (Pane 1)           │
   └─────────────────────────────────────────────┘
                        ↓
   ┌─────────────────────────────────────────────┐
   │ Middle Manager Agent                         │
   │  └─> _read_yaml_message()                   │
   │      └─> handle_task() で処理               │
   └─────────────────────────────────────────────┘

2. Middle Manager → Specialists (並列)
   ┌─────────────────────────────────────────────┐
   │ Middle Manager Agent                         │
   │  └─> タスク分解                             │
   │  └─> 各SpecialistにYAML書き込み             │
   │      ├─> queue/middle_manager_to_specialist_*.yaml │
   │      ├─> queue/middle_manager_to_specialist_*.yaml │
   │      └─> queue/middle_manager_to_specialist_*.yaml │
   └─────────────────────────────────────────────┘
                        ↓
   ┌─────────────────────────────────────────────┐
   │ 各SpecialistがYAMLを読み込んで処理           │
   │  └─> 結果をYAMLで返却                       │
   └─────────────────────────────────────────────┘
```

### エージェント構成

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

---

## クイックスタート

### 前提条件

- Python 3.10+
- tmux (ターミナルマルチプレクサー)
- watchdog (`pip install watchdog`)

### インストール

```bash
# リポジトリのクローン
git clone https://github.com/your-org/orchestrator-cc.git
cd orchestrator-cc

# 依存関係のインストール
pip install -e .
pip install -r requirements-dev.txt
```

### クラスタの起動

```bash
# クラスタを起動（5つのエージェントがtmuxペインで起動）
python -m orchestrator.cli start

# 設定ファイルを指定する場合
python -m orchestrator.cli start --config config/cc-cluster.yaml
```

tmuxセッション `orchestrator-cc` が作成され、以下のペイン構成で各エージェントが起動します：

```
┌─────┬─────┐
│  0  │  1  │  ← Grand Boss | Middle Manager
├─────┼─────┤
│  2  │  3  │  ← Coding & Writing | Research & Analysis
├─────┴─────┤
│     4      │  ← Testing
└───────────┘
```

### タスクの実行

```bash
# Grand Bossにタスクを送信
python -m orchestrator.cli execute "新しい機能を実装してください"

# 結果はMiddle Managerが集約してGrand Bossに返します
```

### tmuxセッションへの接続

```bash
# セッションにアタッチして各エージェントの状態を確認
tmux attach -t orchestrator-cc

# デタッチ: Ctrl+B, D
```

### ステータス確認

```bash
# クラスタの状態を表示
python -m orchestrator.cli status
```

### クラスタの停止

```bash
# クラスタを停止
python -m orchestrator.cli stop
```

### E2Eテストの実行

```bash
# Phase 2のE2Eテストを実行
bash scripts/test-e2e-phase2.sh
```

---

## cc-cluster.yaml 設定ファイル

クラスタの設定は `config/cc-cluster.yaml` で管理します。

### 設定ファイル構造

```yaml
# config/cc-cluster.yaml

# クラスタ全体の設定
cluster:
  name: "orchestrator-cc"              # クラスタ名
  session_name: "orchestrator-cc"      # tmuxセッション名
  work_dir: "/path/to/orchestrator-cc" # 作業ディレクトリ

# エージェント設定
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

### 設定項目の説明

#### cluster セクション

| 項目 | 説明 | 必須 |
|------|------|------|
| `name` | クラスタ名 | ✅ |
| `session_name` | tmuxセッション名 | ✅ |
| `work_dir` | 作業ディレクトリの絶対パス | ✅ |

#### agents セクション

| 項目 | 説明 | 必須 |
|------|------|------|
| `name` | エージェントの一意な名前 | ✅ |
| `role` | エージェントの役割 | ✅ |
| `personality_prompt_path` | 性格プロンプトファイルのパス | ✅ |
| `marker` | 応答完了検出用のキーワード | ✅ |
| `pane_index` | tmuxペイン番号（0-4） | ✅ |
| `wait_time` | 初期化待機時間（秒、デフォルト5.0） | ❌ |
| `poll_interval` | ポーリング間隔（秒、デフォルト0.5） | ❌ |

### エージェントの役割（role）

| 役割 | 説明 |
|------|------|
| `grand_boss` | 最高責任者、ユーザーとの窓口 |
| `middle_manager` | 中間管理職、タスク分解・進捗管理 |
| `specialist_coding_writing` | コーディング・ドキュメント専門家 |
| `specialist_research_analysis` | 調査・分析専門家 |
| `specialist_testing` | テスト・品質保証専門家 |

---

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
├── queue/                       # YAML通信メッセージ
│   ├── grand_boss_to_middle_manager.yaml
│   ├── middle_manager_to_specialist_*.yaml
│   └── specialist_*_to_middle_manager.yaml
│
├── status/                      # エージェントステータス
│   └── agents/                  # エージェント状態YAML
│       ├── grand_boss.yaml
│       └── ...
│
├── orchestrator/                # メインパッケージ
│   ├── core/                    # コア機能
│   │   ├── yaml_protocol.py     # YAML通信プロトコル
│   │   ├── yaml_monitor.py      # YAMLファイル監視
│   │   ├── notification_service.py  # 通知サービス
│   │   ├── tmux_session_manager.py
│   │   ├── cc_process_models.py
│   │   ├── cc_process_launcher.py
│   │   ├── cc_cluster_manager.py
│   │   └── message_logger.py
│   ├── agents/                  # エージェント実装
│   │   ├── cc_agent_base.py
│   │   ├── grand_boss.py
│   │   ├── middle_manager.py
│   │   └── specialists.py
│   └── cli/                    # CLIコマンド
│       └── main.py
│
├── scripts/                     # ユーティリティスクリプト
│   └── test-e2e-phase2.sh       # E2Eテストスクリプト
│
├── tests/                       # テスト
│   ├── test_core/
│   ├── test_agents/
│   └── test_integration/
│       ├── test_phase1.py
│       ├── test_phase2_minimum.py
│       └── test_phase2.py
│
├── docs/                        # ドキュメント
│   ├── roadmap.md
│   ├── validation.md
│   ├── 011-phase2-minimum.md    # Phase2設計書
│   └── specs/
│       ├── communication.md     # 通信方式仕様
│       └── directory-structure.md
│
├── Makefile                     # 開発コマンド
├── CLAUDE.md                    # Claude Code用ガイド
└── README.md                    # このファイル
```

---

## 既知の制限

### 現在の制約事項

| 制限 | 説明 | 対策・予定 |
|------|------|----------|
| **watchdog 依存** | YAMLファイル監視に watchdog ライブラリが必要 | `pip install watchdog` でインストール |
| **ファイル競合の可能性** | 複数プロセスが同時にYAMLファイルに書き込む可能性 | 将来的にロック機構を検討 |
| **tmux への依存** | tmux がインストールされている必要がある | macOS/Linux では標準的、WSLでも動作 |
| **タイミング問題** | ファイル監視の検知遅延により通信が遅れる場合がある | ポーリング間隔の調整で対応 |
| **スケーラビリティ** | 現在のアーキテクチャは小規模クラスタ向け | エージェント増加時はアーキテクチャ再検討 |
| **エラーハンドリング** | タイムアウトや異常終了時のリカバリーが不完全 | Phase 3以降で改善予定 |

### 今後の検討事項

1. **スケーラビリティ**: エージェント数が増えた場合のアーキテクチャ変更
2. **パフォーマンス**: 通信遅延の計測と最適化
3. **エラーハンドリング**: タイムアウトや異常終了時のリカバリー戦略
4. **ログ管理**: 通信ログの保存期間・フォーマット
5. **Webダッシュボード**: エージェント状態の可視化（Phase 3）

---

## 開発

### 開発コマンド (Makefile)

```bash
make help           # ヘルプを表示
make check          # 全品質チェック（型+リント+フォーマット+単体テスト）
make check-all      # 全チェック+統合テスト
make fmt            # コードの自動フォーマットとリント修正
make lint           # リントチェックのみ
make type-check     # 型チェックのみ
make test           # 単体テストのみ
make test-all       # 全テスト（統合テスト含む、並列実行）
make coverage       # カバレッジレポート生成
make clean          # キャッシュファイルを削除
make install-dev    # 開発依存関係をインストール
make pre-commit     # プリコミットチェック（フォーマット+全チェック）
```

### 詳細な開発ガイドライン

詳細な開発ガイドラインは [CLAUDE.md](CLAUDE.md) を参照してください。

---

## 関連ドキュメント

- [CLAUDE.md](CLAUDE.md) - 開発ガイドライン
- [docs/roadmap.md](docs/roadmap.md) - ロードマップ
- [docs/validation.md](docs/validation.md) - 検証結果
- [docs/architecture.md](docs/architecture.md) - アーキテクチャ詳細
- [docs/technical-decisions.md](docs/technical-decisions.md) - 技術的決定事項
- [docs/specs/communication.md](docs/specs/communication.md) - 通信方式の仕様
- [docs/011-phase2-minimum.md](docs/011-phase2-minimum.md) - Phase 2 設計書
