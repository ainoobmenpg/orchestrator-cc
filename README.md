# orchestrator-cc

## 概要

**orchestrator-cc** は、Claude CodeのAgent Teams機能を使用したマルチエージェント協調システムです。複数のClaude Codeインスタンスを実際に走らせて、それらに生のやり取りをさせることができます。

## 目的

このプロジェクトは、Claude CodeのTeamCreate、SendMessage、TaskUpdateツールを使用して、複数のAIエージェントが協調してタスクを完遂するシステムを実現します。

```
┌─────────────────────────────────────────────────────────┐
│                    Claude Code Desktop                   │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │         Team: orchestrator-cc (example)          │  │
│  │                                                    │  │
│  │  ┌──────────────┐  ┌──────────────┐              │  │
│  │  │ Team Lead    │  │ Specialist 1 │  ...         │  │
│  │  │ (Process)    │  │ (Process)    │              │  │
│  │  └──────┬───────┘  └──────┬───────┘              │  │
│  │         │                  │                       │  │
│  │         └────────┬─────────┘                       │  │
│  │                  │                                 │  │
│  │           SendMessage                              │  │
│  │           TaskUpdate                               │  │
│  │                                                  │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ~/.claude/teams/{team-name}/                          │
│    ├── config.json                                      │
│    ├── tasks/                                          │
│    └── messages/                                       │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              Web Dashboard (localhost:8000)              │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Teams Monitor  │  Thinking Logs  │  Health      │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 主な特徴

- **Agent Teams アーキテクチャ**: Claude CodeのTeamCreate機能を使用したネイティブなマルチエージェントシステム
- **SendMessage ツール**: エージェント間の直接通信
- **TaskUpdate ツール**: タスク状態の共有と管理
- **Webダッシュボード**: FastAPIベースのリアルタイム監視ダッシュボード
- **ヘルスモニタリング**: エージェントの健全性を監視・通知
- **思考ログ**: エージェントの思考プロセスを可視化
- **ファイルベース監視**: `~/.claude/teams/` のファイル監視による状態追跡

## 現在の状態

**Agent Teams移行**: ✅ 完了（コミット `76a5341`）

tmux方式からAgent Teamsへ完全移行しました（13,562行削除）。

| 機能 | 状態 |
|------|------|
| Agent Teams管理 | ✅ 実装完了 |
| Webダッシュボード | ✅ 実装完了 |
| ヘルスモニタリング | ✅ 実装完了 |
| 思考ログ | ✅ 実装完了 |
| CLIツール | ✅ 実装完了 |

### アーキテクチャ変更履歴

- **2026-02-01**: 設定ファイル分離アプローチから **tmux方式** へ切り替え
- **2026-02-02**: Phase 2完了 - **YAML通信方式**の実装
- **2026-02-07**: **Agent Teamsへ完全移行** - tmux方式、YAML通信方式を廃止

---

## Agent Teams アーキテクチャ

### システム構成図

```
┌─────────────────────────────────────────────────────────────────────┐
│                         orchestrator-cc                              │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Core Modules                               │  │
│  │                                                               │  │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌────────────┐  │  │
│  │  │ Agent Teams      │  │ Agent Health     │  │ Thinking   │  │  │
│  │  │ Manager          │  │ Monitor          │  │ Log Handler│  │  │
│  │  │                  │  │                  │  │            │  │  │
│  │  │ - チーム作成/削除 │  │ - ヘルスチェック  │  │ - 思考ログ │  │  │
│  │  │ - 設定管理       │  │ - タイムアウト検知│  │   監視      │  │  │
│  │  │ - タスク管理     │  │ - イベント通知    │  │ - ファイル │  │  │
│  │  └──────────────────┘  └──────────────────┘  │   ベース    │  │  │
│  │                                         │  └────────────┘  │  │
│  │  ┌──────────────────┐  ┌──────────────┐                   │  │
│  │  │ Teams Monitor    │  │ Team File     │                   │  │
│  │  │                  │  │ Observer      │                   │  │
│  │  │ - チーム監視     │  │               │                   │  │
│  │  │ - 変更検知       │  │ - ファイル    │                   │  │
│  │  │ - WebSocket配信  │  │   監視        │                   │  │
│  │  └──────────────────┘  └──────────────┘                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                    │                               │
│                                    ▼                               │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              ~/.claude/teams/ (チームデータ)                   │  │
│  │                                                              │  │
│  │   {team-name}/                                              │  │
│  │   ├── config.json    (チーム設定)                            │  │
│  │   ├── inbox/        (メッセージ履歴)                         │  │
│  │   └── messages/     (送信メッセージ)                         │  │
│  │                                                              │  │
│  │   ~/.claude/tasks/{team-name}/                              │  │
│  │   └── *.json       (タスクデータ)                            │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Web Dashboard (FastAPI)                    │  │
│  │                                                               │  │
│  │  REST API: /api/teams, /api/health, /api/teams/{name}/...   │  │
│  │  WebSocket: /ws                                              │  │
│  │  Static: /static/main.js, /static/style.css                  │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 主要モジュール

| モジュール | ファイル | 役割 |
|-----------|---------|------|
| Agent Teams Manager | `agent_teams_manager.py` | チームの作成・削除・管理 |
| Health Monitor | `agent_health_monitor.py` | エージェントのヘルスチェック |
| Teams Monitor | `teams_monitor.py` | Webダッシュボード用データ提供 |
| Team Models | `team_models.py` | チーム・タスク・メッセージのデータモデル |
| Thinking Log Handler | `thinking_log_handler.py` | 思考ログの保存・検索 |
| Team File Observer | `team_file_observer.py` | チーム設定ファイルの監視 |

---

## クイックスタート

### 前提条件

- Python 3.10+
- Claude Code (Agent Teams機能をサポートするバージョン)

### インストール

```bash
# リポジトリのクローン
git clone https://github.com/your-org/orchestrator-cc.git
cd orchestrator-cc

# 依存関係のインストール
pip install -e .
pip install -r requirements-dev.txt
```

### Webダッシュボードの起動

```bash
# ダッシュボードを起動
python -m orchestrator.web.dashboard

# ブラウザでアクセス
open http://localhost:8000
```

### CLIツールの使用

```bash
# チーム一覧を表示
python -m orchestrator.cli list-teams

# チームの状態を確認
python -m orchestrator.cli team-status <team-name>

# チームのメッセージを表示
python -m orchestrator.cli team-messages <team-name>

# チームのタスクを表示
python -m orchestrator.cli team-tasks <team-name>

# ヘルスステータスを表示
python -m orchestrator.cli health

# 思考ログを表示
python -m orchestrator.cli show-logs <team-name>
```

### カスタムスキルの使用（/team）

このプロジェクトでは、すべての作業でAgent Teamsを自動的に使用するカスタムスキル `/team` を提供しています。

```bash
# シンプルなタスク
/team バグを修正して

# 標準的なタスク
/team 新しい機能を実装して

# 複雑なタスク
/team ドキュメントを全面更新して
```

`/team` スキルを使用すると、タスクの複雑度に応じて自動的に適切なチーム構成が作成されます：

- **シンプルなタスク**: Team Lead + 1スペシャリスト
- **標準的なタスク**: Team Lead + Coding + Testing
- **複雑なタスク**: Team Lead + Research + Coding + Testing

### 新しいチームの作成

```bash
# チームを作成
python -m orchestrator.cli create-team my-team \
  --description "My first team" \
  --agent-type general-purpose

# メンバー定義ファイルから作成
python -m orchestrator.cli create-team my-team \
  --description "My team" \
  --members members.json
```

`members.json` の例:
```json
{
  "members": [
    {
      "name": "team-lead",
      "agentType": "general-purpose",
      "timeoutThreshold": 300.0
    },
    {
      "name": "researcher",
      "agentType": "general-purpose",
      "timeoutThreshold": 300.0
    },
    {
      "name": "coder",
      "agentType": "general-purpose",
      "timeoutThreshold": 300.0
    }
  ]
}
```

---

## チーム設定ファイル

チームの設定は `~/.claude/teams/{team-name}/config.json` で管理されます。

### 設定ファイル構造

```json
{
  "name": "my-team",
  "description": "My first team",
  "createdAt": 1737892800000,
  "leadAgentId": "team-lead@my-team",
  "leadSessionId": "session-my-team",
  "members": [
    {
      "agentId": "team-lead@my-team",
      "name": "team-lead",
      "agentType": "general-purpose",
      "model": "claude-sonnet-4-5-20250929",
      "joinedAt": 1737892800000,
      "cwd": "/path/to/project",
      "subscriptions": [],
      "planModeRequired": false
    }
  ]
}
```

### 設定項目の説明

| 項目 | 説明 |
|------|------|
| `name` | チーム名 |
| `description` | チームの説明 |
| `createdAt` | 作成日時（Unixタイムスタンプミリ秒） |
| `leadAgentId` | チームリードのエージェントID |
| `members[].name` | メンバー名 |
| `members[].agentType` | エージェントタイプ |
| `members[].model` | 使用するモデル |
| `members[].planModeRequired` | プランモード必須フラグ |

---

## ディレクトリ構成

```
orchestrator-cc/
├── orchestrator/                # メインパッケージ
│   ├── core/                    # コア機能
│   │   ├── agent_teams_manager.py  # Agent Teams管理
│   │   └── agent_health_monitor.py # ヘルスモニタリング
│   ├── web/                     # Webダッシュボード
│   │   ├── dashboard.py         # FastAPIアプリケーション
│   │   ├── teams_monitor.py     # チーム監視
│   │   ├── thinking_log_handler.py # 思考ログ処理
│   │   ├── team_file_observer.py  # ファイル監視
│   │   ├── team_models.py       # データモデル
│   │   ├── message_handler.py   # WebSocketメッセージ処理
│   │   ├── templates/           # HTMLテンプレート
│   │   └── static/              # 静的ファイル
│   └── cli/                     # CLIツール
│       └── main.py              # メインCLI
│
├── tests/                       # テスト
│   ├── test_core/
│   ├── test_web/
│   └── test_integration/
│
├── docs/                        # ドキュメント
│   ├── workflows/               # ワークフロー関連
│   ├── quality/                 # 品質管理関連
│   └── archive/                 # アーカイブ（古いドキュメント）
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
| **Claude Code依存** | Claude CodeのAgent Teams機能に依存 | 最新のClaude Codeを使用する |
| **ファイル監視遅延** | ファイルシステム監視の検知遅延 | ポーリング間隔の調整で対応 |
| **エージェント再起動** | エージェントの異常終了時の自動再起動は未実装 | 将来実装予定 |

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
- [docs/architecture.md](docs/architecture.md) - アーキテクチャ詳細
- [docs/technical-decisions.md](docs/technical-decisions.md) - 技術的決定事項
