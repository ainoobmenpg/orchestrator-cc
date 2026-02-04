# バックアップと復旧

このドキュメントでは、orchestrator-cc のバックアップと復旧手順について説明します。

---

## バックアップ対象

### 必要なバックアップ項目

| ディレクトリ/ファイル | 説明 | 重要度 |
|---------------------|------|--------|
| `config/` | 設定ファイル | 高 |
| `config/personalities/` | 性格プロンプト | 高 |
| `queue/` | 通信メッセージ（YAML） | 中 |
| `status/` | エージェントステータス | 中 |
| `logs/` | ログファイル | 低 |
| `.env` | 環境変数（シークレット含む） | 高 |

### 推奨バックアップ頻度

| データ | 頻度 |
|--------|------|
| 設定ファイル | 変更時 |
| 通信メッセージ | 毎時 |
| エージェントステータス | 毎時 |
| ログファイル | 毎日 |

---

## バックアップ手順

### 方法1: 手動バックアップ

```bash
#!/bin/bash
# scripts/backup.sh

# バックアップ先ディレクトリ
BACKUP_DIR="/backup/orchestrator-cc"
DATE=$(date +%Y%m%d_%H%M%S)

# バックアップディレクトリの作成
mkdir -p "$BACKUP_DIR/$DATE"

# バックアップの実行
cp -r config/ "$BACKUP_DIR/$DATE/"
cp -r queue/ "$BACKUP_DIR/$DATE/" 2>/dev/null || true
cp -r status/ "$BACKUP_DIR/$DATE/" 2>/dev/null || true
cp -r logs/ "$BACKUP_DIR/$DATE/" 2>/dev/null || true
cp .env "$BACKUP_DIR/$DATE/" 2>/dev/null || true

# アーカイブの作成
tar czf "$BACKUP_DIR/orchestrator-cc-$DATE.tar.gz" -C "$BACKUP_DIR/$DATE" .

# 一時ディレクトリの削除
rm -rf "$BACKUP_DIR/$DATE"

echo "Backup completed: orchestrator-cc-$DATE.tar.gz"
```

### 方法2: rsync による同期バックアップ

```bash
#!/bin/bash
# scripts/backup-rsync.sh

SOURCE_DIR="/opt/orchestrator-cc"
BACKUP_HOST="backup.example.com"
BACKUP_DIR="/backup/orchestrator-cc"

# rsync によるバックアップ
rsync -avz --delete \
  --exclude="venv/" \
  --exclude="__pycache__/" \
  --exclude="*.pyc" \
  "$SOURCE_DIR/" \
  "$BACKUP_HOST:$BACKUP_DIR/"

echo "Rsync backup completed"
```

### 方法3: cron による定期バックアップ

```bash
# /etc/cron.d/orchestrator-cc-backup

# 毎日午前2時にバックアップを実行
0 2 * * * root /opt/orchestrator-cc/scripts/backup.sh

# 毎時0分に設定ファイルのみバックアップ
0 * * * * root /opt/orchestrator-cc/scripts/backup-config.sh
```

---

## 復旧手順

### 方法1: アーカイブからの復旧

```bash
#!/bin/bash
# scripts/restore.sh

BACKUP_FILE="$1"
RESTORE_DIR="/opt/orchestrator-cc"

if [ -z "$BACKUP_FILE" ]; then
  echo "Usage: restore.sh <backup-file.tar.gz>"
  exit 1
fi

# クラスタの停止
python -m orchestrator.cli shutdown

# アーカイブの展開
tar xzf "$BACKUP_FILE" -C /tmp/

# ファイルの復元
cp -r /tmp/config/* "$RESTORE_DIR/config/"
cp -r /tmp/queue/* "$RESTORE_DIR/queue/" 2>/dev/null || true
cp -r /tmp/status/* "$RESTORE_DIR/status/" 2>/dev/null || true
cp -tmp/.env "$RESTORE_DIR/" 2>/dev/null || true

# 一時ファイルの削除
rm -rf /tmp/config /tmp/queue /tmp/status /tmp/.env

# クラスタの再起動
python -m orchestrator.cli start

echo "Restore completed"
```

### 方法2: rsync からの復旧

```bash
#!/bin/bash
# scripts/restore-rsync.sh

BACKUP_HOST="backup.example.com"
BACKUP_DIR="/backup/orchestrator-cc"
RESTORE_DIR="/opt/orchestrator-cc"

# クラスタの停止
python -m orchestrator.cli shutdown

# rsync による復元
rsync -avz "$BACKUP_HOST:$BACKUP_DIR/" "$RESTORE_DIR/"

# クラスタの再起動
python -m orchestrator.cli start

echo "Rsync restore completed"
```

---

## 緊急復旧手順

### 完全なシステム復旧

```bash
# 1. orchestrator-cc の停止
python -m orchestrator.cli shutdown

# 2. tmux セッションの削除
tmux kill-session -t orchestrator-cc

# 3. バックアップからの復元
./scripts/restore.sh /backup/orchestrator-cc/orchestrator-cc-20260204_020000.tar.gz

# 4. 依存関係の再インストール（必要な場合）
pip install -e .

# 5. クラスタの起動
python -m orchestrator.cli start

# 6. ステータス確認
python -m orchestrator.cli status
```

---

## バックアップの検証

### バックアップ整合性の確認

```bash
#!/bin/bash
# scripts/verify-backup.sh

BACKUP_FILE="$1"

# アーカイブのテスト展開
TEMP_DIR=$(mktemp -d)
tar xzf "$BACKUP_FILE" -C "$TEMP_DIR"

# 必要ファイルの存在確認
REQUIRED_FILES=(
  "config/cc-cluster.yaml"
  "config/personalities/grand_boss.txt"
  "config/personalities/middle_manager.txt"
)

for file in "${REQUIRED_FILES[@]}"; do
  if [ ! -f "$TEMP_DIR/$file" ]; then
    echo "Missing required file: $file"
    rm -rf "$TEMP_DIR"
    exit 1
  fi
done

rm -rf "$TEMP_DIR"
echo "Backup verification passed"
```

---

## バックアップ戦略

### 推奨されるバックアップスケジュール

| スケジュール | 内容 | 保存期間 |
|-------------|------|----------|
| 毎時 | 通信メッセージ、ステータス | 24 時間 |
| 毎日 | 全バックアップ | 30 日 |
| 毎週 | 全バックアップ | 90 日 |
| 毎月 | 全バックアップ | 365 日 |

### リテンションポリシー

| データ種類 | 保存期間 |
|-----------|----------|
| 設定ファイル | 永久 |
| 通信メッセージ | 30 日 |
| エージェントステータス | 30 日 |
| ログファイル | 90 日 |

---

## 災害 recovery

### サーバー障害時の対応

1. **代替サーバーの準備**
   - 新しいサーバーに orchestrator-cc をデプロイ
   - 依存関係をインストール

2. **バックアップからの復旧**
   - 最新のバックアップを取得
   - 復元スクリプトを実行

3. **動作確認**
   - クラスタの起動
   - ステータス確認
   - ダッシュボードの動作確認

---

## 関連ドキュメント

- [deployment.md](deployment.md) - デプロイ手順
- [troubleshooting.md](troubleshooting.md) - トラブルシューティング
- [configuration.md](configuration.md) - 設定管理
