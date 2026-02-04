# orchestrator-cc 運用ドキュメント

このディレクトリには、orchestrator-cc システムの運用に関するドキュメントが含まれています。

---

## 概要

orchestrator-cc は、複数の Claude Code インスタンスを実際に走らせて、それらに生のやり取りをさせるシステムです。運用ドキュメントでは、システムの本番運用に必要な手順、設定、監視、トラブルシューティングについて説明します。

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
| [deployment.md](deployment.md) | デプロイ手順 | P0 |
| [security.md](security.md) | セキュリティ設定 | P0 |
| [configuration.md](configuration.md) | 設定管理 | P0 |
| [troubleshooting.md](troubleshooting.md) | トラブルシューティング | P0 |
| [monitoring.md](monitoring.md) | 監視とアラート | P1 |
| [backup-recovery.md](backup-recovery.md) | バックアップと復旧 | P1 |
| [runbook.md](runbook.md) | 運用マニュアル | P1 |

---

## 用語集

| 用語 | 説明 |
|------|------|
| **クラスタ** | orchestrator-cc で管理される Claude Code インスタンス群 |
| **エージェント** | 各ペインで動作する Claude Code プロセス |
| **tmux セッション** | エージェントを動作させるターミナルマルチプレクサーのセッション |
| **ペイン** | tmux セッション内の分割された端末画面 |
| **ダッシュボード** | Web ベースのクラスタ管理インターフェース |
| **監視（Monitoring）** | クラスタの状態を監視する機能 |
| **アラート** | 異常検知時に発行される通知 |
| **再起動（Restart）** | エージェントを再起動する操作 |
| **シャットダウン（Shutdown）** | クラスタ全体を停止し、tmux セッションを削除する操作 |

---

## クイックリファレンス

### クラスタ操作コマンド

```bash
# クラスタ起動
python -m orchestrator.cli start

# クラスタ停止
python -m orchestrator.cli stop

# クラスタ再起動
python -m orchestrator.cli restart

# クラスタシャットダウン
python -m orchestrator.cli shutdown

# ステータス確認
python -m orchestrator.cli status

# ダッシュボード起動
python -m orchestrator.cli dashboard
```

### tmux 操作

```bash
# セッションにアタッチ
tmux attach -t orchestrator-cc

# デタッチ
Ctrl+B, D

# セッション一覧
tmux ls

# セッション強制終了
tmux kill-session -t orchestrator-cc
```

---

## システム要件

### 最小要件

| 項目 | 要件 |
|------|------|
| OS | macOS 12+, Ubuntu 20.04+, WSL2 |
| Python | 3.10+ |
| tmux | 3.0+ |
| メモリ | 4GB+ |
| ディスク | 1GB+ |

### 推奨要件

| 項目 | 要件 |
|------|------|
| メモリ | 8GB+ |
| ディスク | SSD |
| CPU | 4コア以上 |

---

## 関連ドキュメント

### プロジェクト内ドキュメント

- [../README.md](../README.md) - プロジェクト概要
- [../architecture.md](../architecture.md) - アーキテクチャ詳細
- [../web-dashboard.md](../web-dashboard.md) - Webダッシュボード仕様
- [../api/web-api.md](../api/web-api.md) - Web API 仕様

### ワークフロードキュメント

- [../workflows/development-process.md](../workflows/development-process.md) - 開発ワークフロー
- [../workflows/review-process.md](../workflows/review-process.md) - レビュー運用フロー

### 品質管理ドキュメント

- [../quality/quality-management.md](../quality/quality-management.md) - コード品質管理

---

## 運用に関するよくある質問

### Q: クラスタが起動しない場合はどうすればよいですか？

A: [troubleshooting.md](troubleshooting.md) の「エージェントが起動しない」セクションを参照してください。

### Q: 本番環境でどのようにデプロイすべきですか？

A: [deployment.md](deployment.md) で推奨されるデプロイ方法を説明しています。

### Q: セキュリティ対策は何が必要ですか？

A: [security.md](security.md) で認証、HTTPS、シークレット管理について説明しています。

### Q: 監視やアラートはどのように設定しますか？

A: [monitoring.md](monitoring.md) で監視の設定とアラート通知について説明しています。

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
| 2026-02-04 | 1.0.0 | 初版作成 |
