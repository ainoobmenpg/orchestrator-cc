# ディレクトリ構成

## 最終的なディレクトリ構造

```
orchestrator-cc/
├── README.md                          # プロジェクト概要
├── LICENSE                            # ライセンス
├── CLAUDE.md                          # Claude Code用開発ガイド
├── pyproject.toml                     # プロジェクト設定
├── .gitignore                         # Git除外設定
│
├── config/                            # 設定ファイル
│   ├── cc-cluster.yaml                # クラスタ設定
│   └── personalities/                 # 性格プロンプト
│       ├── grand_boss.txt
│       ├── middle_manager.txt
│       ├── coding_writing_specialist.txt
│       ├── research_analysis_specialist.txt
│       └── testing_specialist.txt
│
├── orchestrator/                      # メインパッケージ
│   ├── __init__.py
│   │
│   ├── core/                          # コア機能
│   │   ├── __init__.py
│   │   ├── tmux_session_manager.py    # tmuxセッション管理
│   │   ├── cc_process_models.py       # データモデル
│   │   ├── cc_process_launcher.py     # プロセス起動・管理
│   │   ├── pane_io.py                 # ペイン入出力
│   │   ├── cc_cluster_manager.py      # クラスタ管理
│   │   ├── yaml_protocol.py           # YAML通信プロトコル
│   │   ├── yaml_monitor.py            # YAMLファイル監視
│   │   ├── task_tracker.py            # タスク追跡
│   │   ├── notification_service.py    # 通知サービス
│   │   ├── cluster_logger.py          # クラスタログ
│   │   ├── message_logger.py          # メッセージログ
│   │   ├── message_models.py          # メッセージデータモデル
│   │   └── cluster_monitor.py         # クラスタ監視
│   │
│   ├── agents/                        # エージェント実装
│   │   ├── __init__.py
│   │   ├── cc_agent_base.py           # エージェント基底クラス
│   │   ├── grand_boss.py              # Grand Boss実装
│   │   ├── middle_manager.py          # Middle Manager実装
│   │   ├── coding_writing_specialist.py    # Coding & Writing実装
│   │   ├── research_analysis_specialist.py # Research & Analysis実装
│   │   └── testing_specialist.py      # Testing実装
│   │
│   └── cli/                           # CLIコマンド
│       ├── __init__.py
│       ├── cc_cluster.py              # クラスタ管理CLI
│       └── cc_agent.py                # エージェント操作CLI
│
│   ├── web/                           # Webダッシュボード
│   │   ├── __init__.py
│   │   ├── dashboard.py               # FastAPIアプリケーション
│   │   ├── message_handler.py         # WebSocketメッセージハンドラー
│   │   ├── monitor.py                 # ダッシュボード監視統合
│   │   ├── static/
│   │   │   ├── main.js                # フロントエンドJavaScript
│   │   │   └── style.css              # スタイルシート
│   │   └── templates/
│   │       └── index.html             # HTMLテンプレート
│       ├── __init__.py
│       ├── cc_cluster.py              # クラスタ管理CLI
│       └── cc_agent.py                # エージェント操作CLI
│
├── tests/                             # テスト
│   ├── __init__.py
│   ├── conftest.py                    # pytest設定
│   │
│   ├── test_core/                     # コア機能テスト
│   │   ├── __init__.py
│   │   ├── test_tmux_session_manager.py
│   │   ├── test_cc_process_models.py
│   │   ├── test_cc_process_launcher.py
│   │   ├── test_pane_io.py
│   │   └── test_message_logger.py
│   │
│   ├── test_agents/                   # エージェントテスト
│   │   ├── __init__.py
│   │   ├── test_cc_agent_base.py
│   │   └── test_*.py                  # 各エージェントのテスト
│   │
│   └── test_integration/              # 統合テスト
│       ├── __init__.py
│       ├── test_cluster_startup.py   # クラスタ起動テスト
│       └── test_agent_communication.py # エージェント間通信テスト
│
│   ├── test_web/                      # Webダッシュボードテスト
│   │   ├── __init__.py
│   │   └── test_dashboard.py          # ダッシュボードテスト
│       ├── __init__.py
│       ├── test_cluster_startup.py   # クラスタ起動テスト
│       └── test_agent_communication.py # エージェント間通信テスト
│
├── docs/                              # ドキュメント
│   ├── overview.md                    # プロジェクト概要
│   ├── roadmap.md                     # 実装ロードマップ
│   ├── validation.md                  # 検証結果
│   └── specs/                         # 仕様書
│       ├── communication.md           # 通信方式仕様
│       └── data-models.md             # データモデル仕様
│
├── logs/                              # ログ出力先（実行時生成）
│   └── messages.jsonl                 # メッセージログ
│
└── scripts/                           # ユーティリティスクリプト
    ├── setup.sh                       # 初期設定スクリプト
    └── cleanup.sh                     # クリーンアップスクリプト
```

## 各ディレクトリの説明

### `/config`

設定ファイルを配置します。

| ファイル | 説明 |
|---------|------|
| `cc-cluster.yaml` | クラスタ全体の設定（エージェント名、役割、ペイン番号等） |
| `personalities/*.txt` | 各エージェントの性格プロンプト |

### `/orchestrator/core`

コア機能を実装します。

| ファイル | 説明 | 主なクラス/関数 |
|---------|------|---------------|
| `tmux_session_manager.py` | tmuxセッションの作成・管理 | `TmuxSessionManager` |
| `cc_process_models.py` | データモデル定義 | `CCMessage`, `CCProcessConfig`, `CCProcessRole` |
| `cc_process_launcher.py` | Claude Codeプロセスの起動・監視 | `CCProcessLauncher` |
| `pane_io.py` | ペインへの入出力処理 | `PaneIO` |
| `cc_cluster_manager.py` | クラスタ全体の管理 | `CCClusterManager` |
| `message_logger.py` | メッセージログの記録 | `MessageLogger` |

### `/orchestrator/agents`

各エージェントを実装します。

| ファイル | 説明 | 主なクラス |
|---------|------|----------|
| `cc_agent_base.py` | エージェント基底クラス | `CCAgentBase` |
| `grand_boss.py` | Grand Boss実装 | `GrandBossAgent` |
| `middle_manager.py` | Middle Manager実装 | `MiddleManagerAgent` |
| `coding_writing_specialist.py` | Coding & Writing実装 | `CodingWritingSpecialist` |
| `research_analysis_specialist.py` | Research & Analysis実装 | `ResearchAnalysisSpecialist` |
| `testing_specialist.py` | Testing実装 | `TestingSpecialist` |

### `/orchestrator/cli`

CLIコマンドを実装します。

| ファイル | 説明 | コマンド例 |
|---------|------|----------|
| `cc_cluster.py` | クラスタ管理CLI | `python -m orchestrator.cli.cc_cluster start` |
| `cc_agent.py` | エージェント操作CLI | `python -m orchestrator.cli.cc_agent send` |

### `/tests`

テストコードを配置します。

| ディレクトリ | 説明 |
|-----------|------|
| `test_core/` | コア機能の単体テスト |
| `test_agents/` | 各エージェントの単体テスト |
| `test_integration/` | 複数コンポーネントを組み合わせた統合テスト |

### `/logs`

実行時に生成されるログを保存します。

| ファイル | 説明 |
|---------|------|
| `messages.jsonl` | メッセージログ（JSONL形式） |

## Phase 1 で作成するファイル

| 優先度 | ファイル | 行数見積 |
|--------|---------|----------|
| P0 | `orchestrator/core/cc_process_models.py` | 150 |
| P0 | `orchestrator/core/tmux_session_manager.py` | 200 |
| P0 | `orchestrator/core/pane_io.py` | 200 |
| P0 | `orchestrator/core/cc_process_launcher.py` | 250 |
| P0 | `orchestrator/core/message_logger.py` | 100 |
| P0 | `orchestrator/core/cc_cluster_manager.py` | 250 |
| P1 | `orchestrator/agents/cc_agent_base.py` | 200 |
| P1 | `tests/test_core/test_tmux_session_manager.py` | 150 |
| P1 | `tests/test_core/test_pane_io.py` | 150 |

合計：約1,650行

## 依存関係

```
cc_process_models.py（データモデル）
    ↓
tmux_session_manager.py（tmux管理）
    ↓
pane_io.py（ペイン入出力）
    ↓
cc_process_launcher.py（プロセス起動）
    ↓
message_logger.py（ログ）
    ↓
cc_cluster_manager.py（クラスタ管理）
    ↓
cc_agent_base.py（エージェント基底）
    ↓
各エージェント実装
```
