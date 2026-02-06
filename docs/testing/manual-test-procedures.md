# 手動テスト手順書

このドキュメントでは、orchestrator-cc の手動テスト手順について説明します。

## CLI操作テスト

### 1. チーム作成

```bash
# チームを作成
python -m orchestrator.cli create-team test-team \
  --description "テスト用チーム" \
  --agent leader --agent coder

# 確認
ls ~/.claude/teams/test-team/
# config.json が作成されていること
```

**期待される結果**:
- `~/.claude/teams/test-team/config.json` が作成される
- "Created team 'test-team'" と表示される

### 2. チーム一覧表示

```bash
python -m orchestrator.cli list-teams
```

**期待される結果**:
- 作成したチームが表示される

### 3. チームステータス確認

```bash
python -m orchestrator.cli team-status test-team
```

**期待される結果**:
- チームのメンバー一覧が表示される
- タスク一覧が表示される

### 4. 思考ログ表示

```bash
# ログ表示（最新20件）
python -m orchestrator.cli show-logs test-team

# エージェントでフィルタ
python -m orchestrator.cli show-logs test-team --agent leader

# リアルタイム監視
python -m orchestrator.cli show-logs test-team --follow
```

**期待される結果**:
- 思考ログが時系列で表示される
- `--follow` オプションでリアルタイム更新される

### 5. チームアクティビティ表示

```bash
python -m orchestrator.cli team-activity test-team

# JSON形式で出力
python -m orchestrator.cli team-activity test-team --json
```

**期待される結果**:
- メッセージ数・タスク数・ログ数が表示される
- タスクのステータス別集計が表示される

### 6. チーム削除

```bash
python -m orchestrator.cli delete-team test-team
```

**期待される結果**:
- "Deleted team 'test-team'" と表示される
- ディレクトリが削除される

## Dashboard操作テスト

### 1. Dashboard起動

```bash
python -m orchestrator.web.dashboard
```

**期待される結果**:
- "Uvicorn running on http://127.0.0.1:8000" と表示される

### 2. ブラウザでアクセス

```bash
open http://127.0.0.1:8000
```

**期待される結果**:
- Dashboard画面が表示される
- チーム一覧が表示される

### 3. REST APIテスト

#### 3.1 チーム一覧取得

```bash
curl http://127.0.0.1:8000/api/teams
```

**期待される結果**:
```json
{
  "teams": [
    {
      "name": "test-team",
      "description": "テスト用チーム",
      "members": ["leader", "coder"]
    }
  ]
}
```

#### 3.2 チームメッセージ取得

```bash
curl http://127.0.0.1:8000/api/teams/test-team/messages
```

**期待される結果**:
```json
{
  "messages": []
}
```

#### 3.3 チームタスク取得

```bash
curl http://127.0.0.1:8000/api/teams/test-team/tasks
```

**期待される結果**:
```json
{
  "tasks": []
}
```

#### 3.4 チームステータス取得

```bash
curl http://127.0.0.1:8000/api/teams/test-team/status
```

**期待される結果**:
```json
{
  "team_name": "test-team",
  "members": [...],
  "tasks": [...]
}
```

#### 3.5 思考ログ取得

```bash
curl http://127.0.0.1:8000/api/teams/test-team/thinking
```

**期待される結果**:
```json
{
  "logs": []
}
```

#### 3.6 ヘルスステータス取得

```bash
curl http://127.0.0.1:8000/api/health
```

**期待される結果**:
```json
{
  "teams": [...]
}
```

### 4. WebSocketテスト

PythonスクリプトでWebSocket接続をテスト：

```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://127.0.0.1:8000/ws"
    async with websockets.connect(uri) as websocket:
        # ステータスリクエスト送信
        await websocket.send(json.dumps({"type": "get_status"}))
        
        # レスポンス受信
        response = await websocket.recv()
        print(f"Received: {response}")

asyncio.run(test_websocket())
```

**期待される結果**:
- WebSocket接続が確立される
- ステータス情報が返ってくる

## エラーケース対応

### エラー1: チームが見つからない

```bash
python -m orchestrator.cli team-status nonexistent-team
```

**期待される結果**:
- "Error: Team 'nonexistent-team' not found" と表示される

### エラー2: ポート競合

```
OSError: [Errno 48] Address already in use
```

**対策**:
- ポートを使用しているプロセスを特定して停止
- 別のポートでDashboardを起動:
  ```bash
  uvicorn orchestrator.web.dashboard:app --port 8001
  ```

### エラー3: WebSocket接続失敗

**対策**:
- Dashboardが起動しているか確認
- ファイアウォール設定を確認
- ブラウザのコンソールでエラーメッセージを確認

## まとめ

手動テストにより以下を確認できます：

- ✅ CLIコマンドが正しく動作する
- ✅ Dashboardが正しく表示される
- ✅ REST APIが正しく応答する
- ✅ WebSocketが正しく通信する
- ✅ エラーハンドリングが正しく動作する
