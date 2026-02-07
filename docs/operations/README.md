# orchestrator-cc 運用ドキュメント

このディレクトリには、orchestrator-cc システムの運用に関するドキュメントが含まれています。

---

## 概要

orchestrator-cc は、Claude CodeのAgent Teams機能を使用したマルチエージェント協調システムです。運用ドキュメントでは、システムの本番運用に必要な手順、設定、監視、トラブルシューティングについて説明します。

**注意**: 2026-02-07をもって、tmux方式からAgent Teams方式へ完全移行しました。古いtmux方式のドキュメントは `docs/archive/` にアーカイブされています。

---

## 対象読者

このドキュメントは、以下の役割の方々を対象としています。

- **システム管理者**: orchestrator-cc のインストール、設定、管理を担当する方
- **運用エンジニア**: 日々の運用、監視、トラブル対応を担当する方
- **DevOps エンジニア**: デプロイ、CI/CD、インフラ管理を担当する方

---

## ドキュメント構成

| ドキュメント | 説明 | 優先度 |
|-------------|------|--------|
| [configuration.md](configuration.md) | 設定管理 | P0 |
| [troubleshooting.md](troubleshooting.md) | トラブルシューティング | P0 |
| [deployment.md](deployment.md) | デプロイ手順 | P1 |
| [security.md](security.md) | セキュリティ設定 | P1 |
| [monitoring.md](monitoring.md) | 監視とアラート | P1 |
| [backup-recovery.md](backup-recovery.md) | バックアップと復旧 | P1 |
| [runbook.md](runbook.md) | 運用マニュアル | P1 |

---

## 用語集

| 用語 | 説明 |
|------|------|
| **Agent Teams** | Claude Codeの機能で、複数のAIエージェントをチームとして協調動作させる仕組み |
| **チーム（Team）** | orchestrator-cc で管理されるエージェント群 |
| **エージェント（Agent）** | チーム内で動作する個別の Claude Code プロセス |
| **ダッシュボード** | Web ベースのチーム管理インターフェース（FastAPI + React） |
| **ヘルスチェック** | エージェントの状態を監視する機能 |
| ** SendMessage** | Claude Codeのツールで、エージェント間でメッセージを送信する機能 |
| **TaskUpdate** | Claude Codeのツールで、タスク状態を更新する機能 |

---

## クイックリファレンス

### チーム操作コマンド

```bash
# チーム一覧を表示
python -m orchestrator.cli list-teams

# チームの状態を確認
python -m orchestrator.cli team-status <team-name>

# チームのメッセージを表示
python -m orchestrator.cli team-messages <team-name>

# チームのタスクを表示
python -m orchestrator.cli team-tasks <team-name>

# チームの思考ログを表示
python -m orchestrator.cli show-logs <team-name>

# 新しいチームを作成
python -m orchestrator.cli create-team <team-name> \
  --description "チームの説明" \
  --members members.json

# チームを削除
python -m orchestrator.cli delete-team <team-name>

# ヘルスステータスを表示
python -m orchestrator.cli health
```

### ダッシュボード操作

```bash
# ダッシュボードを起動
python -m orchestrator.web.dashboard

# ブラウザでアクセス
open http://localhost:8000
```

---

## システム要件

### 最小要件

| 項目 | 要件 |
|------|------|
| OS | macOS 12+, Ubuntu 20.04+, WSL2 |
| Python | 3.10+ |
| メモリ | 4GB+ |
| ディスク | 1GB+ |
| Claude Code | Agent Teams機能をサポートするバージョン |

### 推奨要件

| 項目 | 要件 |
|------|------|
| メモリ | 8GB+ |
| ディスク | SSD |
| CPU | 4コア以上 |

---

## ディレクトリ構成

```
~/.claude/
├── teams/                      # チームデータ
│   └── {team-name}/
│       ├── config.json         # チーム設定
│       ├── inbox/              # 受信メッセージ
│       └── messages/           # 送信メッセージ
└── tasks/                      # タスクデータ
    └── {team-name}/
        └── *.json              # タスクデータ

orchestrator-cc/
├── orchestrator/               # メインパッケージ
│   ├── core/                   # コア機能
│   ├── web/                    # Webダッシュボード
│   └── cli/                    # CLIツール
└── docs/                       # ドキュメント
```

---

## 関連ドキュメント

### プロジェクト内ドキュメント

- [../README.md](../README.md) - プロジェクト概要
- [../architecture.md](../architecture.md) - アーキテクチャ詳細
- [CLAUDE.md](../../CLAUDE.md) - Claude Code用ガイド

### ワークフロードキュメント

- [../workflows/development-process.md](../workflows/development-process.md) - 開発ワークフロー
- [../workflows/review-process.md](../workflows/review-process.md) - レビュー運用フロー

### 品質管理ドキュメント

- [../quality/quality-management.md](../quality/quality-management.md) - コード品質管理

---

## 運用に関するよくある質問

### Q: チームが作成できない場合はどうすればよいですか？

A: [troubleshooting.md](troubleshooting.md) の「チーム作成エラー」セクションを参照してください。

### Q: エージェントが応答しない場合はどうすればよいですか？

A: [troubleshooting.md](troubleshooting.md) の「エージェント応答なし」セクションを参照してください。

### Q: 監視やアラートはどのように設定しますか？

A: [monitoring.md](monitoring.md) で監視の設定とアラート通知について説明しています。

### Q: バックアップはどのように作成しますか？

A: [backup-recovery.md](backup-recovery.md) でバックアップと復旧の手順について説明しています。

---

## サポート

問題や質問がある場合は、以下の手順で対応してください。

1. まず [troubleshooting.md](troubleshooting.md) を参照
2. 解決しない場合は GitHub Issues を検索
3. 該当する Issue がない場合は新規作成

---

## ドキュメントの更新履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|----------|
| 2026-02-07 | 2.0.0 | Agent Teams移行に伴う全面改訂 |
| 2026-02-04 | 1.0.0 | 初版作成 |
