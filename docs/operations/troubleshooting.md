# トラブルシューティング

このドキュメントでは、orchestrator-cc で発生する可能性のある問題と、その解決方法について説明します。

**注意**: 2026-02-07をもって、tmux方式からAgent Teams方式へ完全移行しました。古いtmux方式に関するトラブルシューティングは `docs/archive/` にアーカイブされています。

---

## よくある問題と解決方法

### チームが作成できない

#### 症状

```bash
$ python -m orchestrator.cli create-team my-team
Error: チーム 'my-team' の作成に失敗しました
```

#### 原因と解決方法

| 原因 | 解決方法 |
|------|----------|
| **Claude Codeがインストールされていない** | Claude Codeをインストールしてください |
| **`~/.claude/teams/` ディレクトリの権限問題** | `mkdir -p ~/.claude/teams` で作成 |
| **既存のチームが存在する** | 別のチーム名を使用するか、既存チームを削除 |
| **members.jsonファイルのフォーマットエラー** | JSONの形式を確認 |

#### デバッグ手順

```bash
# 1. Claude Codeの確認
claude --version

# 2. teamsディレクトリの確認
ls -la ~/.claude/teams/

# 3. 既存チームの確認
python -m orchestrator.cli list-teams

# 4. メンバーファイルの検証
python -m json.tool members.json
```

---

### ダッシュボードに接続できない

#### 症状

- ブラウザで `http://localhost:8000` にアクセスしても接続できない
- WebSocket 接続が切断される

#### 原因と解決方法

| 原因 | 解決方法 |
|------|----------|
| **ダッシュボードが起動していない** | `python -m orchestrator.web.dashboard` を実行 |
| **ポートが使用中** | `lsof -i :8000` でプロセスを確認 |
| **ファイアウォールがブロックしている** | ポート 8000 を開放 |
| **Pythonモジュールが見つからない** | `pip install -e .` を実行 |

#### デバッグ手順

```bash
# 1. ポート使用状況の確認
lsof -i :8000

# 2. ダッシュボードプロセスの確認
ps aux | grep dashboard

# 3. API エンドポイントの確認
curl http://localhost:8000/api/health

# 4. ログの確認
tail -f logs/dashboard.log
```

---

### エージェントが応答しない

#### 症状

- エージェントが「実行中」と表示されるが応答がない
- メッセージが送信されない
- ヘルスチェックでタイムアウト

#### 原因と解決方法

| 原因 | 解決方法 |
|------|----------|
| **Claude Codeプロセスが停止している** | Claude Code Desktopを再起動 |
| **タイムアウト値が短すぎる** | `timeoutThreshold` を増やす |
| **メッセージファイルの権限問題** | `~/.claude/teams/` の権限を確認 |
| **ネットワーク接続の問題** | インターネット接続を確認 |

#### デバッグ手順

```bash
# 1. チームの状態を確認
python -m orchestrator.cli team-status my-team

# 2. チームのメッセージを確認
python -m orchestrator.cli team-messages my-team

# 3. ヘルスステータスを確認
python -m orchestrator.cli health

# 4. Claude Codeのプロセス確認
ps aux | grep -i claude
```

---

### ヘルスモニタリングが動作しない

#### 症状

- エージェントのタイムアウトが検知されない
- ヘルスステータスが更新されない

#### 原因と解決方法

| 原因 | 解決方法 |
|------|----------|
| **ヘルスモニターが起動していない** | `get_agent_health_monitor().start_monitoring()` を実行 |
| **エージェントが登録されていない** | `register_agent()` でエージェントを登録 |
| **タイムアウト値が長すぎる** | 適切な値に調整（デフォルト: 300秒） |

#### デバッグ手順

```bash
# 1. ヘルスステータスを確認
python -m orchestrator.cli health

# 2. チームの状態を確認
python -m orchestrator.cli team-status my-team

# 3. ダッシュボードで確認
open http://localhost:8000
```

---

### 思考ログが保存されない

#### 症状

- 思考ログがダッシュボードに表示されない
- `~/.claude/thinking-logs/` にファイルが作成されない

#### 原因と解決方法

| 原因 | 解決方法 |
|------|----------|
| **思考ログハンドラーが起動していない** | `ThinkingLogHandler.start_monitoring()` を実行 |
| **ログディレクトリの権限問題** | `mkdir -p ~/.claude/thinking-logs` を実行 |
| **エージェントがログを出力していない** | エージェントの設定を確認 |

#### デバッグ手順

```bash
# 1. 思考ログを確認
python -m orchestrator.cli show-logs my-team

# 2. ログディレクトリの確認
ls -la ~/.claude/thinking-logs/

# 3. ログファイルの確認
cat ~/.claude/thinking-logs/my-team/*.json
```

---

### WebSocket接続が不安定

#### 症状

- ダッシュボードのリアルタイム更新が動作しない
- WebSocket接続が頻繁に切断される

#### 原因と解決方法

| 原因 | 解決方法 |
|------|----------|
| **ファイアウォール/プロキシの問題** | WebSocket接続を許可 |
| **ブラウザの拡張機能** | プライベートモードで確認 |
| **ダッシュボードのバージョン** | 最新版にアップデート |

#### デバッグ手順

```bash
# 1. ダッシュボードを再起動
python -m orchestrator.web.dashboard

# 2. ブラウザの開発者ツールで確認
# ConsoleタブでWebSocketエラーを確認

# 3. ログを確認
tail -f logs/dashboard.log
```

---

## ログの見方

### ログファイルの場所

```
orchestrator-cc/
├── logs/
│   ├── orchestrator.log        # メインログ
│   ├── dashboard.log           # ダッシュボードログ
│   └── health_monitor.log      # ヘルスモニターログ
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

# 過去100行を表示
tail -n 100 logs/orchestrator.log

# 特定のチームのログを確認
grep "my-team" logs/orchestrator.log
```

---

## デバッグモード

### 詳細ログの有効化

```bash
# 環境変数でログレベルを設定
export ORCHESTRATOR_LOG_LEVEL=DEBUG
python -m orchestrator.web.dashboard
```

---

## 状態確認コマンド

### チームステータス

```bash
# CLI からの確認
python -m orchestrator.cli list-teams
python -m orchestrator.cli team-status my-team
python -m orchestrator.cli team-messages my-team
python -m orchestrator.cli team-tasks my-team

# 出力例
# Team: my-team
# Status: active
# Members: 3
# Tasks: 5
```

### API からの確認

```bash
# ヘルスチェック
curl http://localhost:8000/api/health

# チーム一覧
curl http://localhost:8000/api/teams

# チーム詳細
curl http://localhost:8000/api/teams/my-team/status
```

---

## 緊急対応手順

### ダッシュボードの完全再起動

```bash
# 1. ダッシュボードプロセスの停止
pkill -f "orchestrator.web.dashboard"

# 2. プロセスの確認
ps aux | grep dashboard

# 3. ダッシュボードの再起動
python -m orchestrator.web.dashboard
```

### チームの再作成

```bash
# 1. チームの削除
python -m orchestrator.cli delete-team my-team

# 2. チームの再作成
python -m orchestrator.cli create-team my-team \
  --description "My team" \
  --members members.json
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

3. **Claude Code バージョン**
   ```bash
   claude --version
   ```

4. **エラーメッセージ**
   ```bash
   # 実行時の出力をコピー
   ```

5. **ログファイル**
   ```bash
   # logs/ 以下の関連ログを添付
   ```

6. **再現手順**
   ```markdown
   ## 再現手順
   1. コマンドXを実行
   2. 設定Yを変更
   3. コマンドZを実行
   ## 期待される動作
   XXX
   ## 実際の動作
   YYY
   ```

---

## 関連ドキュメント

- [README.md](README.md) - デプロイ手順
- [configuration.md](configuration.md) - 設定管理
- [monitoring.md](monitoring.md) - 監視とアラート
- [../architecture.md](../architecture.md) - アーキテクチャ詳細
