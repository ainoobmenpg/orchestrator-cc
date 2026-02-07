# 設定管理

このドキュメントでは、orchestrator-cc の設定管理について説明します。

**注意**: 2026-02-07をもって、tmux方式からAgent Teams方式へ完全移行しました。古いtmux方式の設定ファイル（`config/cc-cluster.yaml`）は使用されなくなりました。

---

## 現在の状況

### Agent Teams 設定方式

現在、orchestrator-cc は **Claude CodeのAgent Teams機能**を使用しており、チーム設定は `~/.claude/teams/{team-name}/config.json` で管理されています。

**設定項目**:
- チーム名
- チーム説明
- 作成日時
- チームリードのエージェントID
- メンバー設定（名前、エージェントタイプ、モデル、CWD、プランモード設定）

**設定場所**:
```
~/.claude/teams/{team-name}/config.json
```

**制限事項**:
- 設定ファイルはClaude Codeによって自動生成・管理される
- 手動編集は推奨されません（CLIツールを使用してください）
- 環境変数による設定の上書きはClaude Codeの設定に依存します

---

## 設定ファイル構成

### config.json (自動生成)

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
      "tmuxPaneId": "",
      "cwd": "/path/to/project",
      "subscriptions": [],
      "planModeRequired": false
    }
  ]
}
```

### 設定項目一覧

| 項目 | 型 | 必須 | 説明 |
|------|----|----|------|
| `name` | string | ✅ | チーム名 |
| `description` | string | ✅ | チームの説明 |
| `createdAt` | number | ✅ | 作成日時（Unixタイムスタンプミリ秒） |
| `leadAgentId` | string | ✅ | チームリードのエージェントID |
| `leadSessionId` | string | ✅ | リードのセッションID |
| `members` | array | ✅ | メンバーの配列 |

#### members セクション

| 項目 | 型 | 必須 | 説明 |
|------|----|----|------|
| `agentId` | string | ✅ | エージェントの一意なID |
| `name` | string | ✅ | メンバー名 |
| `agentType` | string | ✅ | エージェントタイプ（general-purpose等） |
| `model` | string | ✅ | 使用するモデル |
| `joinedAt` | number | ✅ | 参加日時（Unixタイムスタンプミリ秒） |
| `cwd` | string | ✅ | 作業ディレクトリ |
| `planModeRequired` | boolean | ❌ | プランモード必須フラグ |

---

## CLI によるチーム作成

### 新しいチームの作成

```bash
# 基本的なチーム作成
python -m orchestrator.cli create-team my-team \
  --description "My first team" \
  --agent-type general-purpose

# メンバー定義ファイルから作成
python -m orchestrator.cli create-team my-team \
  --description "My team" \
  --members members.json
```

### members.json の例

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

## チームの削除

```bash
# チームの削除
python -m orchestrator.cli delete-team my-team
```

**注意**: チームを削除すると、以下のデータも削除されます：
- `~/.claude/teams/{team-name}/` ディレクトリ全体
- チームのメッセージ履歴
- チームのタスクデータ
- チームの思考ログ

---

## ヘルスモニタリング設定

### AgentHealthMonitor の設定

```python
from orchestrator.core.agent_health_monitor import get_agent_health_monitor

# ヘルスモニターの取得
monitor = get_agent_health_monitor()

# エージェントの登録
monitor.register_agent(
    team_name="my-team",
    agent_name="team-lead",
    timeout_threshold=300.0  # 5分
)

# 監視の開始
monitor.start_monitoring()
```

### 環境変数による設定

| 環境変数 | 説明 | デフォルト値 |
|---------|------|-------------|
| `ORCHESTRATOR_LOG_LEVEL` | ログレベル | `INFO` |
| `ORCHESTRATOR_DASHBOARD_PORT` | ダッシュボードポート | `8000` |
| `ORCHESTRATOR_DASHBOARD_HOST` | ダッシュボードホスト | `127.0.0.1` |

---

## 設定のベストプラクティス

### 1. バージョン管理

- CLIツールを使用してチームを作成・管理してください
- 手動で `config.json` を編集しないでください
- 重要なチーム設定のバックアップを取得してください

### 2. ドキュメント化

- チームの目的と役割を説明に記載してください
- 各メンバーの役割を明確に定義してください

### 3. ヘルスモニタリング

- 各エージェントに適切なタイムアウト値を設定してください
- チームの規模に応じて監視間隔を調整してください

### 4. バックアップ

- 定期的に `~/.claude/teams/` をバックアップしてください
- チーム削除前に必要なデータをエクスポートしてください

---

## 関連ドキュメント

- [deployment.md](deployment.md) - デプロイ手順
- [security.md](security.md) - セキュリティ設定
- [troubleshooting.md](troubleshooting.md) - トラブルシューティング
- [../architecture.md](../architecture.md) - アーキテクチャ詳細
