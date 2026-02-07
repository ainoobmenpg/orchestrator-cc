# 運用マニュアル

このドキュメントでは、orchestrator-cc の運用マニュアルについて説明します。

**注意**: 2026-02-07をもって、tmux方式からAgent Teams方式へ完全移行しました。古いtmux方式に関する運用マニュアルは `docs/archive/` にアーカイブされています。

---

## 日次運用タスク

### 毎日の確認事項

| タスク | 頻度 | コマンド/手順 |
|--------|------|---------------|
| チームステータス確認 | 毎日 | `python -m orchestrator.cli list-teams` |
| ヘルスステータス確認 | 毎日 | `python -m orchestrator.cli health` |
| エラーログ確認 | 毎日 | `grep ERROR logs/orchestrator.log` |
| ディスク容量確認 | 毎日 | `df -h` |
| ダッシュボード動作確認 | 毎日 | `curl http://localhost:8000/api/health` |

### 日次チェックリスト

```bash
#!/bin/bash
# scripts/daily-check.sh

echo "=== orchestrator-cc 日次チェック ==="

# 1. チームステータス
echo "[1] チームステータス"
python -m orchestrator.cli list-teams

# 2. ヘルスステータス
echo "[2] ヘルスステータス"
python -m orchestrator.cli health

# 3. ディスク容量
echo "[3] ディスク容量"
df -h | grep -E "(Filesystem|/$|/home)"

# 4. エラーログ（過去24時間）
echo "[4] エラーログ（過去24時間）"
since yesterday --format="%Y-%m-%d %H:%M:%S" 2>/dev/null || date -v-1d +"%Y-%m-%d %H:%M:%S" | \
  xargs -I {} grep -A 5 ERROR logs/orchestrator.log | grep "{}" || echo "エラーなし"

# 5. APIヘルスチェック
echo "[5] APIヘルスチェック"
curl -s http://localhost:8000/api/health | jq '.'

# 6. ダッシュボードプロセス確認
echo "[6] ダッシュボードプロセス"
ps aux | grep -E "(orchestrator.*dashboard)" | grep -v grep || echo "ダッシュボードは起動していません"

echo "=== チェック完了 ==="
```

---

## 週次運用タスク

### 毎週の確認事項

| タスク | 頻度 | 説明 |
|--------|------|------|
| ログローテーション確認 | 毎週 | ログファイルの肥大化チェック |
| バックアップ確認 | 毎週 | `~/.claude/teams/` のバックアップ確認 |
| パフォーマンス確認 | 毎週 | 応答時間、リソース使用状況の確認 |
| 依存パッケージの更新確認 | 毎週 | Pythonパッケージの更新確認 |

### 週次チェックリスト

```bash
#!/bin/bash
# scripts/weekly-check.sh

echo "=== orchestrator-cc 週次チェック ==="

# 1. ログサイズ確認
echo "[1] ログファイルサイズ"
du -sh logs/* 2>/dev/null || echo "ログディレクトリがありません"

# 2. チームデータのバックアップ確認
echo "[2] チームデータバックアップ"
if [ -d "$HOME/.claude/teams" ]; then
  echo "チームデータ: $HOME/.claude/teams/"
  du -sh ~/.claude/teams/* 2>/dev/null
else
  echo "チームデータがありません"
fi

# 3. 依存パッケージの更新確認
echo "[3] 依存パッケージの更新"
pip list --outdated

# 4. ヘルスサマリー
echo "[4] 今週のヘルスサマリー"
python -m orchestrator.cli health

echo "=== 週次チェック完了 ==="
```

---

## 月次運用タスク

### 毎月の実行事項

| タスク | 頻度 | 説明 |
|--------|------|------|
| 古いログのアーカイブ | 毎月 | 30日以上前のログをアーカイブ |
| バックアップの検証 | 毎月 | バックアップからの復元テスト |
| 設定ファイルの見直し | 毎月 | 設定の最適化チェック |
| パフォーマンスレビュー | 毎月 | 今月のパフォーマンス状況のレビュー |

### 月次チェックリスト

```bash
#!/bin/bash
# scripts/monthly-check.sh

echo "=== orchestrator-cc 月次チェック ==="

# 1. 古いログのアーカイブ
echo "[1] 古いログのアーカイブ"
find logs/ -name "*.log" -mtime +30 -exec gzip {} \; 2>/dev/null
mkdir -p logs/archive
mv logs/*.gz logs/archive/ 2>/dev/null || echo "アーカイブ対象のログがありません"

# 2. チームデータのバックアップ
echo "[2] チームデータのバックアップ"
BACKUP_DIR="$HOME/backups/orchestrator-cc"
mkdir -p "$BACKUP_DIR"
tar -czf "$BACKUP_DIR/teams-$(date +%Y%m%d).tar.gz" -C ~/.claude teams 2>/dev/null
echo "バックアップ作成: $BACKUP_DIR/teams-$(date +%Y%m%d).tar.gz"

# 3. ディスク使用状況のレポート
echo "[3] ディスク使用状況"
du -sh ~/orchestrator-cc ~/.claude/teams 2>/dev/null

# 4. 今月のアラートサマリー
echo "[4] 今月のアラートサマリー"
grep -c "ERROR" logs/orchestrator.log 2>/dev/null || echo "0"

echo "=== 月次チェック完了 ==="
```

---

## 緊急対応手順

### ダッシュボード障害時の対応

#### レベル1: 軽微な障害

**症状**: ダッシュボードへの接続が遅い、一部の機能が動作しない

**対応手順**:

```bash
# 1. APIヘルスチェック
curl http://localhost:8000/api/health

# 2. ダッシュボードの再起動
pkill -f "orchestrator.web.dashboard"
python -m orchestrator.web.dashboard

# 3. ログ確認
tail -f logs/dashboard.log
```

#### レベル2: 中程度の障害

**症状**: ダッシュボードに接続できない、WebSocket接続が切断される

**対応手順**:

```bash
# 1. ポート使用状況の確認
lsof -i :8000

# 2. プロセスの強制終了
pkill -9 -f "orchestrator.web.dashboard"

# 3. ポートのクリア待機
sleep 2

# 4. ダッシュボードの再起動
python -m orchestrator.web.dashboard
```

#### レベル3: 重大な障害

**症状**: システム全体が応答しない、データ破損の疑い

**対応手順**:

```bash
# 1. 全プロセスの停止
pkill -9 -f orchestrator

# 2. バックアップから復旧
cp -r ~/backups/orchestrator-cc/teams-latest.tar.gz ~/tmp/
tar -xzf ~/tmp/teams-latest.tar.gz -C ~/.claude/

# 3. 依存関係の再インストール
pip install -e .

# 4. ダッシュボードの起動
python -m orchestrator.web.dashboard

# 5. 動作確認
curl http://localhost:8000/api/health
```

---

## エージェント障害時の対応

### エージェントタイムアウト

**症状**: エージェントがタイムアウト状態になる

**対応手順**:

```bash
# 1. ヘルスステータス確認
python -m orchestrator.cli health

# 2. チームの状態確認
python -m orchestrator.cli team-status my-team

# 3. Claude Code Desktopを再起動
# （手動操作）

# 4. チームの再作成（必要な場合）
python -m orchestrator.cli delete-team my-team
python -m orchestrator.cli create-team my-team \
  --description "My team" \
  --members members.json
```

---

## インシデント対応フロー

### インシデント発生時の手順

1. **検知**: アラートまたはユーザー報告
2. **評価**: 影響範囲と重要度の判定
3. **対応**: 障害レベルに応じた対応手順の実行
4. **復旧**: サービスの正常化確認
5. **報告**: インシデントレポートの作成
6. **改善**: 再発防止策の検討

### インシデント報告テンプレート

```markdown
# インシデントレポート

## 概要
- 発生日時: YYYY-MM-DD HH:MM:SS
- 検知方法: アラート/ユーザー報告/その他
- 影響範囲: 全体/一部チーム/ダッシュボード

## 症状
- （具体的な症状を記述）

## 原因
- （根本原因を記述）

## 対応
- （実施した対応手順を記述）

## 復旧時間
- 検知: HH:MM
- 復旧: HH:MM
- 所要時間: X分

## 再発防止策
- （改善策を記述）
```

---

## メンテナンス手順

### 計画メンテナンス

1. **事前通知**: ユーザーへのメンテナンス通知
2. **バックアップ作成**: メンテナンス前のバックアップ
3. **メンテナンス実施**: システムの更新や変更
4. **動作確認**: 全機能の動作確認
5. **完了通知**: メンテナンス完了の通知

---

## パフォーマンス監視

### 監視指標

| 指標 | 目標値 | 警告閾値 |
|------|--------|----------|
| エージェント稼働率 | 99%+ | 95% |
| 平均応答時間 | < 5秒 | > 10秒 |
| CPU 使用率 | < 70% | > 90% |
| メモリ使用率 | < 70% | > 85% |
| ディスク使用率 | < 80% | > 90% |

---

## 関連ドキュメント

- [deployment.md](deployment.md) - デプロイ手順
- [troubleshooting.md](troubleshooting.md) - トラブルシューティング
- [monitoring.md](monitoring.md) - 監視とアラート
- [backup-recovery.md](backup-recovery.md) - バックアップと復旧
