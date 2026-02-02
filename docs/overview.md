# orchestrator-cc 概要

## プロジェクトの目的

orchestrator-cc は、**複数の Claude Code インスタンスを実際に走らせて、それらに生のやり取りをさせるシステム**です。

現在の `orchestrator` プロジェクトは、Pythonオブジェクトとして実装されたエージェントがLLMを呼び出すアーキテクチャです。これは「マルチLLM調整システム」としては機能しますが、本来の目的とは異なります。

**orchestrator-cc** は、本来の目的である以下を実現します：

```
Claude Code A (プロセス1)
  ↓ Claude Code Bの「入力欄」に文字を入れて送信
Claude Code B (プロセス2)
  ↓ 処理してAに結果を返す + 上司のClaude Codeに通知
Claude Code C (上司、プロセス3)
  ↓ 連絡用ファイルを作って作業完了通知
```

## 主な特徴

- **プロセスベースのアーキテクチャ**: 各Claude Codeインスタンスは独立したプロセス
- **tmux方式**: tmuxセッション内の各ペインでClaude Codeを起動・管理
- **プログラム制御**: `tmux send-keys`でコマンド送信、`tmux capture-pane`で出力取得
- **性格設定**: `--system-prompt`で各エージェントに異なる役割・性格を設定
- **LLM分散**: 各インスタンスが独立してLLMを呼び出し（レートリミット回避）

## アーキテクチャ概要

### tmux方式の構造

```
┌─────────────────────────────────────────────────────────┐
│                  orchestrator-cc コア                    │
│                                                         │
│  ┌─────────────┐         ┌─────────────────┐                  │
│  │Tmuxセッション│         │プロセス管理     │                  │
│  │   管理クラス │         │                 │                  │
│  └──────┬──────┘         └─────────────────┘                  │
│         │                                                │
│         ▼                                                │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  tmux session: orchestratorcc                       │  │
│  │  ├─ ペイン0: Grand Boss      (通常モード + プロンプト設定)│  │
│  │  ├─ ペイン1: Middle Manager  (通常モード + プロンプト設定)│  │
│  │  └─ ペイン2: Coding Specialist (通常モード + プロンプト設定)│  │
│  │                                                     │  │
│  │  orchestrator-cc から各ペインにキー入力・出力取得      │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
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

## Phase構成

### ✅ Phase 0: 事前検証（完了）

Claude CodeのMCPサーバー機能の基本動作確認。

| 検証項目 | 結果 |
|---------|------|
| V-001: `claude mcp serve` の基本動作 | ✅ 成功 |
| V-002: `--system-prompt` の動作確認 | ❌ MCPサーバーモードでは利用不可 |
| V-003: Pythonからのプログラム制御 | ✅ 成功 |

### ✅ Phase 0.5: 中間検証（完了）

tmux方式によるClaude Codeプロセス管理の実動確認。

| 検証項目 | 結果 |
|---------|------|
| V-101: tmuxで複数プロセス起動 | ✅ 成功 |
| V-102: Pythonからtmux制御 | ✅ 成功 |
| V-103: 出力のキャプチャ・パース | ✅ 成功（条件付き） |

**アーキテクチャ変更**: 設定ファイル分離アプローチから**tmux方式**へ切り替え（2026-02-01）

### ✅ Phase 1: tmuxプロセス管理機能（完了）

tmux方式でのプロセス起動・管理機能の実装。

**作成したファイル**:
- `orchestrator/core/tmux_session_manager.py`
- `orchestrator/core/cc_process_launcher.py`
- `orchestrator/core/pane_io.py`
- `config/personalities/*.txt`
- `config/cc-cluster.yaml`

### ✅ Phase 2: エージェント間通信（完了）

Grand Boss, Middle Manager, Specialists の実装。

**実装内容**:
- 各エージェントのtmux経由でのメッセージ送受信
- タスク分解・割り当てロジック
- 合言葉（マーカー）検出方式による応答完了判定

### ✅ Phase 3: クラスタ管理・CLI拡張（完了）

クラスタ全体の管理とCLIコマンドの拡張。

### ✅ Phase 4: Webダッシュボード（完了）

FastAPI + WebSocket によるリアルタイムの思考ログ表示。

**実装したファイル**:
- `orchestrator/core/cluster_monitor.py` - クラスタ監視
- `orchestrator/web/dashboard.py` - FastAPIアプリケーション
- `orchestrator/web/message_handler.py` - WebSocketメッセージハンドラー
- `orchestrator/web/monitor.py` - ダッシュボード監視統合
- `orchestrator/web/static/main.js` - フロントエンドJavaScript
- `orchestrator/web/static/style.css` - スタイルシート
- `orchestrator/web/templates/index.html` - HTMLテンプレート

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
│   ├── core/                    # コア機能
│   │   ├── tmux_session_manager.py
│   │   ├── cc_process_models.py
│   │   ├── cc_process_launcher.py
│   │   ├── pane_io.py
│   │   ├── cc_cluster_manager.py
│   │   ├── cluster_monitor.py   # クラスタ監視
│   │   ├── yaml_protocol.py
│   │   ├── yaml_monitor.py
│   │   ├── message_logger.py
│   │   └── message_models.py
│   ├── agents/                  # エージェント実装
│   │   ├── cc_agent_base.py
│   │   ├── grand_boss.py
│   │   ├── middle_manager.py
│   │   └── ...
│   ├── web/                     # Webダッシュボード
│   │   ├── dashboard.py         # FastAPIアプリケーション
│   │   ├── message_handler.py   # WebSocketメッセージハンドラー
│   │   ├── monitor.py           # ダッシュボード監視統合
│   │   ├── static/
│   │   │   ├── main.js
│   │   │   └── style.css
│   │   └── templates/
│   │       └── index.html
│   └── cli/                     # CLIコマンド
│
├── tests/                       # テスト
│   ├── test_core/
│   ├── test_agents/
│   └── test_integration/
│
└── docs/                        # ドキュメント
    ├── overview.md              # このファイル
    ├── architecture.md          # アーキテクチャ詳細
    ├── roadmap.md               # 実装ロードマップ
    ├── validation.md            # 検証結果の記録
    ├── technical-decisions.md   # 技術的決定事項
    └── specs/                   # 仕様書
        ├── communication.md     # 通信方式の仕様
        └── directory-structure.md # ディレクトリ構成
```

## 関連ドキュメント

- [architecture.md](architecture.md) - 詳細なアーキテクチャ設計
- [roadmap.md](roadmap.md) - 実装ロードマップ
- [validation.md](validation.md) - 検証結果の記録
- [technical-decisions.md](technical-decisions.md) - 技術的決定事項
- [README.md](../README.md) - プロジェクト概要
- [CLAUDE.md](../CLAUDE.md) - 開発者向けガイド
