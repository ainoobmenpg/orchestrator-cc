# トラブルシューティング

このドキュメントでは、orchestrator-cc で発生する可能性のある問題と、その解決方法について説明します。

---

## よくある問題と解決方法

### エージェントが起動しない

#### 症状

```bash
$ python -m orchestrator.cli start
Error: エージェント 'grand_boss' の起動に失敗しました
```

#### 原因と解決方法

| 原因 | 解決方法 |
|------|----------|
| **tmux がインストールされていない** | `brew install tmux` (macOS) または `apt-get install tmux` (Ubuntu) |
| **設定ファイルが見つからない** | `config/cc-cluster.yaml` の存在を確認 |
| **作業ディレクトリが存在しない** | `work_dir` で指定されたパスが存在するか確認 |
| **既存の tmux セッションが残っている** | `tmux kill-session -t orchestrator-cc` でセッションを削除 |
| **性格プロンプトファイルが見つからない** | `config/personalities/` 以下のファイルを確認 |

#### デバッグ手順

```bash
# 1. tmux セッションの確認
tmux ls

# 既存のセッションがある場合は削除
tmux kill-session -t orchestrator-cc

# 2. 設定ファイルの確認
cat config/cc-cluster.yaml

# 3. 作業ディレクトリの確認
ls -la $(grep work_dir config/cc-cluster.yaml | awk '{print $2}')

# 4. 再起動
python -m orchestrator.cli start
```

---

### tmux セッションが残っている

#### 症状

```bash
$ python -m orchestrator.cli start
Error: セッション 'orchestrator-cc' は既に存在します
```

#### 解決方法

```bash
# セッションの確認
tmux ls

# セッションの削除
tmux kill-session -t orchestrator-cc

# 強制終了（プロセスレベル）
ps aux | grep tmux
kill <pid>
```

---

### ダッシュボードに接続できない

#### 症状

- ブラウザで `http://localhost:8000` にアクセスしても接続できない
- WebSocket 接続が切断される

#### 原因と解決方法

| 原因 | 解決方法 |
|------|----------|
| **ダッシュボードが起動していない** | `python -m orchestrator.cli dashboard` を実行 |
| **ポートが使用中** | `lsof -i :8000` でプロセスを確認 |
| **クラスタが起動していない** | `python -m orchestrator.cli start` を実行 |
| **ファイアウォールがブロックしている** | ポート 8000 を開放 |

#### デバッグ手順

```bash
# 1. ポート使用状況の確認
lsof -i :8000

# 2. ダッシュボードプロセスの確認
ps aux | grep dashboard

# 3. クラスタステータスの確認
python -m orchestrator.cli status

# 4. API エンドポイントの確認
curl http://localhost:8000/api/status
```

---

### エージェントが応答しない

#### 症状

- エージェントが「実行中」と表示されるが応答がない
- メッセージが送信されない

#### 原因と解決方法

| 原因 | 解決方法 |
|------|----------|
| **Claude Code プロセスが停止している** | tmux セッションにアタッチして状態を確認 |
| **プロンプト検出キーワードが間違っている** | `marker` 設定を確認 |
| **メッセージファイルの権限問題** | `queue/` ディレクトリの権限を確認 |

#### デバッグ手順

```bash
# 1. tmux セッションにアタッチ
tmux attach -t orchestrator-cc

# 各ペインを確認して、エージェントが応答しているかチェック

# デタッチ: Ctrl+B, D

# 2. メッセージファイルの確認
ls -la queue/

# 3. エージェントステータスの確認
python -m orchestrator.cli status

# 4. 再起動
python -m orchestrator.cli restart
```

---

### YAML 通信が動作しない

#### 症状

- エージェント間でメッセージが送信されない
- `queue/` ディレクトリにファイルが作成されない

#### 原因と解決方法

| 原因 | 解決方法 |
|------|----------|
| **watchdog がインストールされていない** | `pip install watchdog` |
| **YAML ファイルのパースエラー** | `queue/` 以下の YAML ファイルを確認 |
| **ファイル監視が動作していない** | YAMLMonitor のログを確認 |

#### デバッグ手順

```bash
# 1. watchdog の確認
pip show watchdog

# 2. YAML ファイルの確認
ls -la queue/
cat queue/grand_boss_to_middle_manager.yaml

# 3. ログの確認
tail -f logs/orchestrator.log

# 4. ファイル監視の再起動
python -m orchestrator.cli restart
```

---

### メモリ不足

#### 症状

- エージェントが頻繁にクラッシュする
- システムが重くなる

#### 解決方法

```bash
# 1. メモリ使用状況の確認
ps aux | grep python

# 2. エージェント数の削減
# config/cc-cluster.yaml でエージェント数を減らす

# 3. 再起動
python -m orchestrator.cli restart
```

---

## ログの見方

### ログファイルの場所

```
orchestrator-cc/
├── logs/
│   ├── orchestrator.log        # メインログ
│   ├── dashboard.log           # ダッシュボードログ
│   └── agent_*.log            # エージェントログ
```

### ログレベル

| レベル | 説明 |
|--------|------|
| DEBUG | 詳細なデバッグ情報 |
| INFO | 一般的な情報 |
| WARNING | 警告 |
| ERROR | エラー |
| CRITICAL | 重大なエラー |

### ログの確認

```bash
# リアルタイムでログを監視
tail -f logs/orchestrator.log

# エラーログのみ表示
grep ERROR logs/orchestrator.log

# 特定のエージェントのログを確認
tail -f logs/agent_grand_boss.log

# 過去100行を表示
tail -n 100 logs/orchestrator.log
```

---

## デバッグモード

### 詳細ログの有効化

```bash
# 環境変数でログレベルを設定
export ORCHESTRATOR_LOG_LEVEL=DEBUG
python -m orchestrator.cli start
```

### tmux セッションでの直接確認

```bash
# tmux セッションにアタッチ
tmux attach -t orchestrator-cc

# ペインの切り替え: Ctrl+B, 0-4
# ペインの分割表示: Ctrl+B, q

# デタッチ: Ctrl+B, D
```

---

## 状態確認コマンド

### クラスタステータス

```bash
# CLI からの確認
python -m orchestrator.cli status

# 出力例
# Cluster: orchestrator-cc
# Session: orchestrator-cc (exists)
# Agents:
#   - grand_boss: running
#   - middle_manager: running
#   - coding_writing_specialist: running
#   - research_analysis_specialist: running
#   - testing_specialist: running
```

### API からの確認

```bash
# ステータス確認
curl http://localhost:8000/api/status

# メトリクス確認
curl http://localhost:8000/api/metrics

# アラート確認
curl http://localhost:8000/api/alerts
```

---

## 緊急対応手順

### クラスタの完全再起動

```bash
# 1. シャットダウン
python -m orchestrator.cli shutdown

# 2. tmux セッションの確認と削除
tmux ls
tmux kill-session -t orchestrator-cc

# 3. プロセスの確認と強制終了
ps aux | grep python
kill <pid>

# 4. 再起動
python -m orchestrator.cli start
```

### 設定のリセット

```bash
# 1. バックアップから復元
cp config/cc-cluster.yaml.backup config/cc-cluster.yaml

# 2. 再起動
python -m orchestrator.cli restart
```

---

## サポートへの問い合わせ

上記の手順で問題が解決しない場合は、以下の情報を添えて GitHub Issues に報告してください。

### 必要な情報

1. **OS とバージョン**
   ```bash
   uname -a  # Linux/macOS
   ```

2. **Python バージョン**
   ```bash
   python --version
   ```

3. **tmux バージョン**
   ```bash
   tmux -V
   ```

4. **エラーメッセージ**
   ```bash
   # 実行時の出力をコピー
   ```

5. **ログファイル**
   ```bash
   # logs/ 以下の関連ログを添付
   ```

6. **設定ファイル**
   ```bash
   # シークレットを削除した設定ファイル
   ```

---

## 関連ドキュメント

- [deployment.md](deployment.md) - デプロイ手順
- [configuration.md](configuration.md) - 設定管理
- [monitoring.md](monitoring.md) - 監視とアラート
