# orchestrator-cc

## 概要

複数のClaude Codeインスタンスを実際に走らせて、それらに生のやり取りをさせるシステム。

## 目的

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

**アーキテクチャ変更**: 設定ファイル分離アプローチから**tmux方式**へ切り替え（2026-02-01）

**次のフェーズ**: Phase 1（tmux方式でのプロセス起動・管理機能）

### Phase 1 で作成するファイル

| ファイル | 役割 |
|---------|------|
| `orchestrator/core/tmux_session_manager.py` | tmuxセッションの作成・管理クラス |
| `orchestrator/core/cc_process_launcher.py` | Claude Codeプロセスの起動・監視 |
| `orchestrator/core/pane_io.py` | ペインへの入力・出力処理 |
| `config/personalities/*.txt` | 各エージェントの性格プロンプトテキスト |
| `config/cc-cluster.yaml` | クラスタ全体の設定ファイル |

### エージェント構成（確定）

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

### 各エージェントの詳細

#### Grand Boss（最高責任者）
- **性格**: 厳格だが公平、戦略的思考、明確なコミュニケーション
- **役割**: ユーザーからのタスクを受領、Middle Managerに委任、最終成果を提示
- **プロンプト**: `config/personalities/grand_boss.txt`

#### Middle Manager（中間管理職）
- **性格**: 柔軟だが着実、部下の能力を活かす、状況を正確に上司に伝える
- **役割**: タスクの分解、Specialistへの割り振り、進捗管理、結果の集約
- **プロンプト**: `config/personalities/middle_manager.txt`

#### Coding & Writing Specialist（コーディング・ドキュメント専門家）
- **性格**: 丁寧、実用的、文脈を理解する
- **役割**: 実装、ドキュメント作成、コードとドキュメントの整合性維持
- **プロンプト**: `config/personalities/coding_writing_specialist.txt`

#### Research & Analysis Specialist（調査・分析専門家）
- **性格**: 好奇心が強い、論理的、客観的
- **役割**: 情報収集、分析、調査レポート作成
- **プロンプト**: `config/personalities/research_analysis_specialist.txt`

#### Testing Specialist（テスト・品質保証専門家）
- **性格**: 厳格、詳細、再現性を重視
- **役割**: テスト設計・実行、バグ報告、品質保証
- **プロンプト**: `config/personalities/testing_specialist.txt`

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
│   │   └── message_logger.py
│   ├── agents/                  # エージェント実装
│   │   ├── cc_agent_base.py
│   │   ├── grand_boss.py
│   │   ├── middle_manager.py
│   │   └── ...
│   └── cli/                    # CLIコマンド
│
├── tests/                       # テスト
│   ├── test_core/
│   ├── test_agents/
│   └── test_integration/
│
└── docs/                        # ドキュメント
    ├── roadmap.md
    ├── validation.md
    └── specs/
        ├── communication.md
        └── directory-structure.md
```

### 採用アプローチ: tmux方式

tmuxセッション内の各ペインでClaude Codeを起動し、プログラムから制御します。

```
tmuxセッション (orchestrator-cc)
├── ペイン0: Grand Boss
│   └── claude --system-prompt "あなたはGrand Bossです..."
├── ペイン1: Middle Manager
│   └── claude --system-prompt "あなたはMiddle Managerです..."
└── ペイン2: Coding Specialist
    └── claude --system-prompt "あなたはCoding Specialistです..."
```

**制御方法**:
- `tmux send-keys -t session:0.0 "コマンド" Enter` → ペインにコマンド送信
- `tmux capture-pane -t session:0.0 -p` → ペインの出力を取得
- 出力をパースしてClaude Codeの応答を抽出

## 開発

詳細な開発ガイドラインは [CLAUDE.md](CLAUDE.md) を参照してください。
