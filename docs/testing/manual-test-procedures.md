# 手動テスト手順書

このドキュメントでは、orchestrator-ccの手動テスト手順について説明します。

## 目的

自動テストでカバーしきれない部分や、実際の使用環境での動作確認を行うための手動テスト手順を提供します。

## 前提条件

- Python 3.10以上がインストールされていること
- Claude Codeが使用可能であること
- 必要な依存関係がインストールされていること

```bash
pip install -e .
```

## 1. CLIコマンドの手動テスト

### 1.1 チーム作成（`create-team`）

**目的**: CLIからチームを作成できることを確認

**手順**:

1. チームを作成
```bash
python -m orchestrator.cli create-team my-team "My Test Team"
```

2. 作成確認
```bash
ls ~/.claude/teams/my-team/
cat ~/.claude/teams/my-team/config.json
```

**期待結果**:
- `config.json` が作成されている
- `config.json` にチーム名と説明が含まれている

### 1.2 チーム一覧表示（`list-teams`）

**目的**: 作成したチームの一覧を表示できることを確認

**手順**:

1. チーム一覧を表示
```bash
python -m orchestrator.cli list-teams
```

**期待結果**:
- 作成したチームが表示される

### 1.3 チームステータス確認（`team-status`）

**目的**: チームのステータスを確認できることを確認

**手順**:

1. ステータスを確認
```bash
python -m orchestrator.cli team-status my-team
```

**期待結果**:
- チームの情報が表示される

### 1.4 思考ログ表示（`show-logs`）

**目的**: チームの思考ログを表示できることを確認

**手順**:

1. ログを表示
```bash
python -m orchestrator.cli show-logs my-team
```

2. JSON形式で表示
```bash
python -m orchestrator.cli show-logs my-team --json
```

3. エージェントでフィルタ
```bash
python -m orchestrator.cli show-logs my-team --agent team-lead
```

**期待結果**:
- 思考ログが表示される
- オプションに応じてフィルタ・フォーマットが適用される

### 1.5 チームアクティビティ表示（`team-activity`）

**目的**: チームのアクティビティ概要を表示できることを確認

**手順**:

1. アクティビティを表示
```bash
python -m orchestrator.cli team-activity my-team
```

**期待結果**:
- アクティビティ概要が表示される

### 1.6 チーム削除（`delete-team`）

**目的**: チームを削除できることを確認

**手順**:

1. チームを削除
```bash
python -m orchestrator.cli delete-team my-team
```

2. 削除確認
```bash
ls ~/.claude/teams/  # my-team が含まれていないことを確認
```

**期待結果**:
- チームが削除される

## 2. Dashboardの手動テスト

### 2.1 Dashboard起動

**目的**: Dashboardを起動できることを確認

**手順**:

1. Dashboardを起動
```bash
python -m orchestrator.web.dashboard
```

2. ブラウザでアクセス
```
http://127.0.0.1:8000
```

**期待結果**:
- Dashboardが表示される
- 接続ステータスが表示される

### 2.2 REST APIエンドポイントのテスト

**目的**: 各REST APIエンドポイントが正しく動作することを確認

**手順**:

1. 別のターミナルで以下のコマンドを実行

#### チーム一覧取得
```bash
curl http://127.0.0.1:8000/api/teams
```

**期待結果**:
```json
{
  "teams": [...]
}
```

#### チームメッセージ取得
```bash
curl http://127.0.0.1:8000/api/teams/my-team/messages
```

**期待結果**:
```json
{
  "teamName": "my-team",
  "messages": [...]
}
```

#### チームタスク取得
```bash
curl http://127.0.0.1:8000/api/teams/my-team/tasks
```

**期待結果**:
```json
{
  "teamName": "my-team",
  "tasks": [...]
}
```

#### ヘルスチェック
```bash
curl http://127.0.0.1:8000/api/health
```

**期待結果**:
```json
{
  "teams": {...}
}
```

## 3. WebSocket通信の手動テスト

### 3.1 WebSocket接続

**目的**: WebSocketで接続できることを確認

**手順**:

1. PythonでWebSocketクライアントを作成
```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://127.0.0.1:8000/ws"
    async with websockets.connect(uri) as websocket:
        # pingメッセージを送信
        await websocket.send(json.dumps({
            "type": "ping",
            "timestamp": "2026-02-06T12:00:00Z"
        }))

        # レスポンスを受信
        response = await websocket.recv()
        print(f"受信: {response}")

asyncio.run(test_websocket())
```

**期待結果**:
- pongメッセージを受信する

### 3.2 メッセージ購読

**目的**: チーム情報の更新を受け取れることを確認

**手順**:

```python
import asyncio
import websockets
import json

async def test_subscribe():
    uri = "ws://127.0.0.1:8000/ws"
    async with websockets.connect(uri) as websocket:
        # subscribeメッセージを送信
        await websocket.send(json.dumps({
            "type": "subscribe",
            "channels": ["teams", "tasks"]
        }))

        # レスポンスを受信
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            print(f"受信: {data['type']}")

asyncio.run(test_subscribe())
```

**期待結果**:
- subscribedメッセージを受信する
- チーム情報の更新があった場合、通知を受信する

## 4. エージェント間通信の手動テスト

### 4.1 タスクの依存関係

**目的**: タスクの依存関係が正しく動作することを確認

**手順**:

1. テスト用のタスクファイルを作成
```bash
mkdir -p ~/.claude/tasks/test-team
```

2. タスクA（依存なし）
```bash
cat > ~/.claude/tasks/test-team/a.json <<EOF
{
  "id": "a",
  "subject": "Task A",
  "description": "First task",
  "status": "pending",
  "blockedBy": []
}
EOF
```

3. タスクB（Aに依存）
```bash
cat > ~/.claude/tasks/test-team/b.json <<EOF
{
  "id": "b",
  "subject": "Task B",
  "description": "Second task",
  "status": "pending",
  "blockedBy": ["a"]
}
EOF
```

4. 確認
```bash
python -m orchestrator.cli team-tasks test-team
```

**期待結果**:
- タスクBがAに依存していることが表示される

### 4.2 思考ログの記録

**目的**: 思考ログが正しく記録されることを確認

**手順**:

1. 思考ログを記録
```python
from orchestrator.web.thinking_log_handler import get_thinking_log_handler

handler = get_thinking_log_handler()
handler.send_thinking_log(
    team_name="test-team",
    agent_name="test-agent",
    content="思考プロセスのテスト",
    category="thinking"
)
```

2. 確認
```bash
python -m orchestrator.cli show-logs test-team
```

**期待結果**:
- 記録した思考ログが表示される

## 5. トラブルシューティング

### 5.1 Dashboardが起動しない

**症状**: `python -m orchestrator.web.dashboard` でエラーが発生

**対処**:
1. ポート8000が使用されていないか確認
```bash
lsof -i :8000
```

2. 必要なモジュールがインストールされているか確認
```bash
pip install fastapi uvicorn
```

### 5.2 WebSocket接続が失敗する

**症状**: WebSocket接続でエラーが発生

**対処**:
1. Dashboardが起動しているか確認
2. ファイアウォール設定を確認

### 5.3 チームが見つからない

**症状**: `team-status` でエラーが発生

**対処**:
1. チームが作成されているか確認
```bash
ls ~/.claude/teams/
```

2. チーム名が正しいか確認

## 6. クリーンアップ

テスト後のクリーンアップ:

```bash
# テスト用チームの削除
python -m orchestrator.cli delete-team my-team

# テスト用タスクの削除
rm -rf ~/.claude/tasks/test-team
```
