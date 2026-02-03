# 運用マニュアル

このドキュメントでは、orchestrator-cc の運用マニュアルについて説明します。

---

## 日次運用タスク

### 毎日の確認事項

| タスク | 頻度 | コマンド/手順 |
|--------|------|---------------|
| クラスタステータス確認 | 毎日 | `python -m orchestrator.cli status` |
| エージェント動作確認 | 毎日 | ダッシュボードで確認 |
| エラーログ確認 | 毎日 | `grep ERROR logs/orchestrator.log` |
| ディスク容量確認 | 毎日 | `df -h` |
| アラート確認 | 毎日 | `curl http://localhost:8000/api/alerts` |

### 日次チェックリスト

```bash
#!/bin/bash
# scripts/daily-check.sh

echo "=== orchestrator-cc 日次チェック ==="

# 1. クラスタステータス
echo "[1] クラスタステータス"
python -m orchestrator.cli status

# 2. ディスク容量
echo "[2] ディスク容量"
df -h | grep -E "(Filesystem|/opt/orchestrator-cc)"

# 3. エラーログ（過去24時間）
echo "[3] エラーログ（過去24時間）"
since yesterday --format="%Y-%m-%d %H:%M:%S" | xargs -I {} grep -A 5 ERROR logs/orchestrator.log | grep "{}" || echo "エラーなし"

# 4. アラート確認
echo "[4] アラート確認"
curl -s http://localhost:8000/api/alerts | jq '.alerts[] | select(.resolved == false)'

# 5. プロセス確認
echo "[5] プロセス確認"
ps aux | grep -E "(orchestrator|dashboard)" | grep -v grep

echo "=== チェック完了 ==="
```

---

## 週次運用タスク

### 毎週の確認事項

| タスク | 頻度 | 説明 |
|--------|------|------|
| ログローテーション確認 | 毎週 | ログファイルの肥大化チェック |
| バックアップ確認 | 毎週 | バックアップが正常に作成されているか確認 |
| パフォーマンス確認 | 毎週 | 応答時間、リソース使用状況の確認 |
| セキュリティ更新 | 毎週 | 依存パッケージの更新確認 |

### 週次チェックリスト

```bash
#!/bin/bash
# scripts/weekly-check.sh

echo "=== orchestrator-cc 週次チェック ==="

# 1. ログサイズ確認
echo "[1] ログファイルサイズ"
du -sh logs/*

# 2. バックアップ確認
echo "[2] 最新のバックアップ"
ls -lth /backup/orchestrator-cc/*.tar.gz | head -5

# 3. 依存パッケージの更新確認
echo "[3] 依存パッケージの更新"
pip list --outdated

# 4. メトリクスサマリー
echo "[4] 今週のメトリクス"
curl -s http://localhost:8000/api/metrics | jq '.'

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
find logs/ -name "*.log" -mtime +30 -exec gzip {} \;
mv logs/*.gz logs/archive/

# 2. バックアップの検証
echo "[2] バックアップの検証"
LATEST_BACKUP=$(ls -t /backup/orchestrator-cc/*.tar.gz | head -1)
./scripts/verify-backup.sh "$LATEST_BACKUP"

# 3. ディスク使用状況のレポート
echo "[3] ディスク使用状況"
du -sh /opt/orchestrator-cc/* | sort -hr

# 4. 今月のアラートサマリー
echo "[4] 今月のアラートサマリー"
curl -s "http://localhost:8000/api/alerts?limit=1000" | \
  jq '.alerts | group_by(.level) | map({level: .[0].level, count: length})'

echo "=== 月次チェック完了 ==="
```

---

## 緊急対応手順

### クラスタ障害時の対応

#### レベル1: 軽微な障害

**症状**: 一部のエージェントが応答しない

**対応手順**:

```bash
# 1. ステータス確認
python -m orchestrator.cli status

# 2. 問題のエージェントを特定
tmux attach -t orchestrator-cc

# 3. 必要に応じて再起動
python -m orchestrator.cli restart
```

#### レベル2: 中程度の障害

**症状**: 複数のエージェントが停止している、または tmux セッションが異常

**対応手順**:

```bash
# 1. クラスタの停止
python -m orchestrator.cli shutdown

# 2. tmux セッションの強制終了
tmux kill-session -t orchestrator-cc

# 3. プロセスの確認とクリーンアップ
ps aux | grep orchestrator
kill <pid>

# 4. クラスタの再起動
python -m orchestrator.cli start

# 5. ステータス確認
python -m orchestrator.cli status
```

#### レベル3: 重大な障害

**症状**: システム全体が応答しない、またはデータ破損の疑い

**対応手順**:

```bash
# 1. システムの完全停止
python -m orchestrator.cli shutdown
tmux kill-session -t orchestrator-cc

# 2. バックアップから復旧
./scripts/restore.sh /backup/orchestrator-cc/orchestrator-cc-latest.tar.gz

# 3. 依存関係の再インストール
pip install -e .

# 4. クラスタの起動
python -m orchestrator.cli start

# 5. 動作確認
python -m orchestrator.cli status
curl http://localhost:8000/api/status
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
- 影響範囲: 全体/一部エージェント/ダッシュボード

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

### ローリングアップデート

```bash
# 1. 設定ファイルの更新
cp config/cc-cluster.yaml config/cc-cluster.yaml.bak
vi config/cc-cluster.yaml

# 2. エージェントごとの再起動
for agent in grand_boss middle_manager coding_writing_specialist; do
  # 個別エージェントの再起動（実装必要）
  echo "Restarting $agent..."
done

# 3. 動作確認
python -m orchestrator.cli status
```

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
