# 技術的決定事項

このドキュメントでは、orchestrator-cc プロジェクトで行った技術的決定事項とその背景を記録します。

---

## 決定: Agent Teamsへの移行

### 日付
2026-02-07

### 背景

プロジェクトは最初、tmux方式とYAML通信方式を採用していましたが、以下の課題がありました：

1. **tmuxへの依存**: tmuxのインストールと設定が必要
2. **複雑なプロセス管理**: tmuxセッション、ペイン、プロセスの監視が複雑
3. **YAML通信の制約**: ファイルベースの通信処理が複雑
4. **Claude Codeのネイティブ機能が利用可能**: Agent Teams機能がリリースされ、よりシンプルに実装できるようになった

### 決定内容

**Agent Teams方式を採用**

tmux方式とYAML通信方式を完全に廃止し、Claude CodeのネイティブなAgent Teams機能を使用する方式へ移行しました。

```
旧方式（tmux方式）:
tmuxセッション (orchestrator-cc)
├── ペイン0: Grand Boss (claude --system-prompt "...")
├── ペイン1: Middle Manager (claude --system-prompt "...")
└── ペイン2: Coding Specialist (claude --system-prompt "...")

新方式（Agent Teams）:
┌─────────────────────────────────────────────────────────┐
│                    Claude Code Desktop                   │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │         Team: orchestrator-cc                     │  │
│  │                                                    │  │
│  │  ┌──────────────┐  ┌──────────────┐              │  │
│  │  │ Team Lead    │  │ Specialist 1 │              │  │
│  │  │ (Process)    │  │ (Process)    │              │  │
│  │  └──────┬───────┘  └──────┬───────┘              │  │
│  │         │                  │                       │  │
│  │         └────────┬─────────┘                       │  │
│  │                  │                                 │  │
│  │           SendMessage / TaskUpdate                │  │
│  │                                                  │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ~/.claude/teams/{team-name}/                          │
│    ├── config.json                                      │
│    ├── tasks/                                          │
│    └── messages/                                       │
└─────────────────────────────────────────────────────────┘
```

### メリット

| メリット | 説明 |
|---------|------|
| **tmux不要** | tmuxのインストール・設定が不要 |
| **シンプルな実装** | Claude Codeのネイティブ機能を使用するだけ |
| **高い信頼性** | Claude Code公式の機能を使用 |
| **追従性が高い** | Claude Codeのアップデートに自動対応 |
| **ファイルベース監視** | `~/.claude/teams/` の監視だけで状態追跡可能 |

### 削除されたコード

コミット `76a5341` で13,562行を削除：

| 削除されたモジュール | 説明 |
|---------------------|------|
| `tmux_session_manager.py` | tmuxセッション管理 |
| `cc_process_launcher.py` | プロセス起動・監視 |
| `pane_io.py` | ペイン入出力 |
| `yaml_protocol.py` | YAML通信プロトコル |
| `yaml_monitor.py` | YAMLファイル監視 |
| `notification_service.py` | 通知サービス |
| `cc_cluster_manager.py` | クラスタ管理 |
| `cc_agent_base.py` | エージェント基底クラス |
| `grand_boss.py` | Grand Bossエージェント |
| `middle_manager.py` | Middle Managerエージェント |
| `specialists.py` | Specialistエージェント |

### 新しいモジュール

| 新しいモジュール | 説明 |
|-----------------|------|
| `agent_teams_manager.py` | Agent Teams管理 |
| `agent_health_monitor.py` | エージェントのヘルスモニタリング |
| `teams_monitor.py` | チーム監視・データ提供 |
| `team_models.py` | チーム・タスク・メッセージのデータモデル |
| `thinking_log_handler.py` | 思考ログの保存・検索 |
| `team_file_observer.py` | チーム設定ファイルの監視 |
| `dashboard.py` | FastAPIベースのWebダッシュボード |

### 移行の影響

| 影響 | 説明 |
|------|------|
| **CLIコマンド変更** | `start`、`stop`、`status` → `list-teams`、`team-status`、`team-messages` など |
| **設定ファイル変更** | `config/cc-cluster.yaml` → `~/.claude/teams/{team}/config.json` |
| **通信方式変更** | YAMLファイル通信 → SendMessage/TaskUpdate ツール |
| **監視方式変更** | tmux capture-pane → ファイル監視 |

---

## アーカイブ: tmux方式の採用（2026-02-01）

### 背景

Phase 0でClaude CodeのMCPサーバーモードの基本動作は確認できましたが、以下の課題が判明しました：

1. **`--system-prompt` オプションが利用できない**
   - MCPサーバーモードでは `--system-prompt` オプションが存在しない
   - エラー: `error: unknown option '--system-prompt'`
   - 各エージェントに異なる性格設定ができない

2. **設定ファイル方式でも機能しない**
   - `.claude/settings.json` での `systemPrompt` 設定は機能しない
   - 各エージェント専用のホームディレクトリを作成するアプローチでも解決せず

### 決定内容

**tmux方式（通常モード + ターミナルマルチプレクサー）を採用**

各エージェントをtmuxセッションの別ペインで起動し、プログラムから制御していました。

```
tmuxセッション (orchestrator-cc)
├── ペイン0: Grand Boss (claude --system-prompt "...")
├── ペイン1: Middle Manager (claude --system-prompt "...")
└── ペイン2: Coding Specialist (claude --system-prompt "...")
```

### メリット

| メリット | 説明 |
|---------|------|
| **性格設定が可能** | `--system-prompt`で各エージェントに異なる役割を設定できる |
| **独立性が高い** | 各ペインが独立したClaude Codeプロセスとして動作 |
| **可視性** | tmux attachで各エージェントの状態を直接確認できる |
| **デバッグ容易** | 各ペインの出力を直接見られるのでデバッグが容易 |
| **追従性が高い** | Claude Codeの通常モードの機能をそのまま使える |

### デメリット

| デメリット | 説明 |
|-----------|------|
| tmuxへの依存 | tmuxがインストールされている必要がある |
| 出力パースの複雑さ | 合言葉（マーカー）検出方式で対応 |
| プロセス管理の複雑さ | CCProcessLauncherで監視・再起動を実装 |

---

## アーカイブ: エージェント間通信方式（直接通信）

### 日付
2026-02-01

### 採用方式: 直接通信

エージェント同士が直接通信を行う方式を採用していました。

```
Grand Boss ─────直接────→ Middle Manager
                           │
                           ├────直接────→ Coding & Writing Specialist
                           ├────直接────→ Research & Analysis Specialist
                           └────直接────→ Testing Specialist
```

### メリット

| メリット | 説明 |
|---------|------|
| **シンプルな実装** | 宛先のペインに直接メッセージを送るだけ |
| **通常のClaude Codeに近い** | ユーザーがClaude Codeを使うときの直接対話に近い |
| **追従性が高い** | Claude Codeに新機能が追加されたとき、そのまま使える |
| **エージェントの独立性** | 各エージェントが自律的に動作できる |

### 通信フロー

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

## アーカイブ: 非同期通信の方式（合言葉検出）

### 日付
2026-02-01

### 採用方式: 応答完了マーカー（合言葉）検出

各エージェントの応答キーワードを「合言葉」として使用し、それが検出された時点で応答完了と判定していました。

### 合言葉一覧

| エージェント | 合言葉 |
|-------------|--------|
| Grand Boss | `GRAND BOSS OK` |
| Middle Manager | `MIDDLE MANAGER OK` |
| Coding & Writing Specialist | `CODING OK` |
| Research & Analysis Specialist | `RESEARCH OK` |
| Testing Specialist | `TESTING OK` |

### メリット

| メリット | 説明 |
|---------|------|
| **正確な検出** | 応答の完了を確実に判定できる |
| **無駄のない待機** | 応答が完了した時点で即座に取得 |
| **柔軟性** | 合言葉は各エージェントの性格プロンプトで定義済み |
| **タイムアウト付き** | 無限に待たずにタイムアウトでエラー処理 |

---

## 今後の検討事項

以下の事項は、実装の進捗に応じて再検討する可能性があります：

1. **エージェント自動再起動**: タイムアウトや異常終了時の自動リカバリー
2. **パフォーマンス**: 通信遅延の計測と最適化
3. **スケーラビリティ**: 大規模チームでのパフォーマンス
4. **ログ管理**: 通信ログの保存期間・フォーマット

---

## 関連ドキュメント

- [validation.md](validation.md) - 検証結果の詳細
- [architecture.md](architecture.md) - アーキテクチャ詳細
