# 必要な検証事項

## Phase 0: 事前検証

### V-001: `claude mcp serve` の基本動作確認

**目的**: Claude CodeのMCPサーバー機能が期待通り動作することを確認

**手順**:
```bash
# 1. ヘルプ確認
claude mcp serve --help

# 2. 基本動作確認
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | claude mcp serve

# 3. 期待されるレスポンス
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [...]
  }
}
```

**成功基準**:
- [ ] 有効なJSON-RPCレスポンスが返ってくる
- [ ] `tools` フィールドが存在する
- [ ] エラーが発生しない

**失敗時の対処**:
- `mcp serve` が存在しない: 別の起動方法を検討
- JSON-RPCレスポンスが返ってこない: 通信方法を再検討

---

### V-002: `--system-prompt` の動作確認

**目的**: システムプロンプトが正しく適用されることを確認

**検証結果**: ❌ FAIL（2026-02-01）

**詳細**:
- `--system-prompt` オプションは `claude mcp serve` には存在しない
- エラー: `error: unknown option '--system-prompt'`
- `claude mcp serve` で使用可能なオプション: `-d, --debug`、`-h, --help`、`--verbose` のみ

**採用した代替案: 設定ファイル分離アプローチ（ホームディレクトリ分離方式）**

各エージェント専用のHOMEディレクトリを作成し、その中に `.claude/settings.json` を配置して性格設定を管理します。

**ディレクトリ構造**:
```
/tmp/orchestrator-cc/
├── agents/
│   ├── grand_boss/
│   │   └── .claude/
│   │       └── settings.json
│   ├── middle_manager/
│   │   └── .claude/
│   │       └── settings.json
│   └── coding_specialist/
│       └── .claude/
│           └── settings.json
```

**起動方法**:
```bash
HOME=/tmp/orchestrator-cc/agents/grand_boss claude mcp serve
```

**メリット**:
- ✅ 永続性: settings.jsonに保存される
- ✅ プロンプト追従性: Claude Codeがネイティブに読み込む
- ✅ 分離: 各エージェントが独立した設定を持てる
- ✅ 再現性: プロセス再起動で設定が維持される

---

### V-003: プログラム制御の可否

**目的**: Pythonからstdin/stdout経由で制御できることを確認

**手順**:
```python
import subprocess
import json
import asyncio

async def test_mcp_control():
    # プロセス起動
    proc = await asyncio.create_subprocess_exec(
        'claude', 'mcp', 'serve',
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    # リクエスト送信
    request = json.dumps({
        'jsonrpc': '2.0',
        'id': 1,
        'method': 'tools/list',
    })

    proc.stdin.write((request + '\n').encode())
    await proc.stdin.drain()

    # レスポンス受信
    response_line = await proc.stdout.readline()
    response = json.loads(response_line.decode())

    print('Response:', response)

    # クリーンアップ
    proc.terminate()
    await proc.wait()

    return response

# 実行
asyncio.run(test_mcp_control())
```

**成功基準**:
- [ ] プロセスが起動できる
- [ ] stdinに書き込める
- [ ] stdoutから読み取れる
- [ ] 有効なJSON-RPCレスポンスが返ってくる

**失敗時の対処**:
- プロセスが起動しない: 環境変数やパスを確認
- 通信ができない: 別のプロセス間通信方法を検討

---

### V-004: 思考ログの出力確認

**目的**: 思考ログを含むメッセージを処理できることを確認

**手順**:
```python
async def test_thinking_log():
    proc = await asyncio.create_subprocess_exec(
        'claude', 'mcp', 'serve',
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    # 思考ログ付きのリクエスト
    request = json.dumps({
        'jsonrpc': '2.0',
        'id': 1,
        'method': 'tools/call',
        'params': {
            'name': 'send_message',
            'arguments': {
                'content': 'テストメッセージ',
                'thinking': 'これは思考ログです。テストを実行しています。',
            }
        }
    })

    proc.stdin.write((request + '\n').encode())
    await proc.stdin.drain()

    response_line = await proc.stdout.readline()
    response = json.loads(response_line.decode())

    # レスポンスに思考ログが含まれているか確認
    if 'result' in response:
        result = response['result']
        if 'thinking' in result:
            print('思考ログが含まれています:', result['thinking'])

    proc.terminate()
    await proc.wait()

# 実行
asyncio.run(test_thinking_log())
```

**成功基準**:
- [ ] 思考ログを含むリクエストが処理できる
- [ ] レスポンスに思考ログが含まれる（エージェントが出力する場合）
- [ ] エラーが発生しない

**失敗時の対処**:
- 思考ログが処理されない: カスタムフィールドとして扱う
- エラーが発生する: フォーマットを調整

---

## Phase 1: プロセス起動検証

### V-101: 単一プロセス起動

**目的**: 単一のClaude Codeプロセスを起動できることを確認

**手順**:
```python
from orchestrator.core.cc_process_launcher import CCProcessLauncher
from orchestrator.core.cc_process_models import CCProcessConfig, CCProcessRole

config = CCProcessConfig(
    name="test_agent",
    role=CCProcessRole.GRAND_BOSS,
    personality_prompt_path="config/personalities/grand_boss.txt",
)

launcher = CCProcessLauncher(config)
await launcher.start()

# 起動確認
assert launcher.is_running()

# クリーンアップ
await launcher.stop()
```

**成功基準**:
- [ ] プロセスが起動する
- [ ] プロセスが実行中である
- [ ] プロセスが正常に停止する

---

### V-102: 複数プロセス起動

**目的**: 複数のClaude Codeプロセスを同時に起動できることを確認

**手順**:
```python
configs = [
    CCProcessConfig(
        name="grand_boss",
        role=CCProcessRole.GRAND_BOSS,
        mcp_port=9000,
    ),
    CCProcessConfig(
        name="middle_manager",
        role=CCProcessRole.MIDDLE_MANAGER,
        mcp_port=9001,
    ),
]

launchers = []
for config in configs:
    launcher = CCProcessLauncher(config)
    await launcher.start()
    launchers.append(launcher)

# 全プロセスが実行中であることを確認
for launcher in launchers:
    assert launcher.is_running()

# クリーンアップ
for launcher in launchers:
    await launcher.stop()
```

**成功基準**:
- [ ] 全てのプロセスが起動する
- [ ] 全てのプロセスが同時に実行中である
- [ ] 全てのプロセスが正常に停止する

---

### V-103: 自動再起動

**目的**: プロセスがクラッシュした場合、自動的に再起動することを確認

**手順**:
```python
config = CCProcessConfig(
    name="test_agent",
    role=CCProcessRole.GRAND_BOSS,
    auto_restart=True,
    max_restarts=3,
)

launcher = CCProcessLauncher(config)
await launcher.start()

# プロセスを強制終了
os.kill(launcher.get_pid(), signal.SIGKILL)

# 再起動を待機
await asyncio.sleep(5)

# 再起動されたことを確認
assert launcher.is_running()
assert launcher.get_restart_count() == 1
```

**成功基準**:
- [ ] プロセスが自動的に再起動する
- [ ] 再起動回数が正しくカウントされる
- [ ] 最大再起動回数を超えると再起動しない

---

## Phase 2: MCP通信検証

### V-201: メッセージ送信

**目的**: MCP経由でメッセージを送信できることを確認

**手順**:
```python
from orchestrator.core.mcp_message_bridge import MCPMessageBridge

bridge = MCPMessageBridge()

# プロセス起動
await bridge.connect("test_agent")

# メッセージ送信
message = CCMessage(
    id="msg-1",
    from_agent="system",
    to_agent="test_agent",
    type=MessageType.INFO,
    content="テストメッセージ",
)

await bridge.send_message(message)
```

**成功基準**:
- [ ] メッセージが送信できる
- [ ] 送信エラーが発生しない

---

### V-202: メッセージ受信

**目的**: MCP経由でメッセージを受信できることを確認

**手順**:
```python
# メッセージ受信
received = await bridge.receive_message("test_agent")

assert received is not None
assert received.content == "テストメッセージ"
```

**成功基準**:
- [ ] メッセージを受信できる
- [ ] 受信したメッセージの内容が正しい

---

## Phase 3: エージェント間通信検証

### V-301: エンドツーエンド通信

**目的**: Grand Boss → Middle Manager → Specialist で通信できることを確認

**手順**:
```python
# クラスタ起動
await cluster_manager.start()

# Grand Boss からメッセージ送信
grand_boss = cluster_manager.get_agent("grand_boss")
await grand_boss.send_to(
    "middle_manager",
    "タスクの分解をお願い: Webアプリを作って"
)

# Middle Manager で受信
middle_manager = cluster_manager.get_agent("middle_manager")
message = await middle_manager.receive()

assert message.from_agent == "grand_boss"
assert "Webアプリ" in message.content
```

**成功基準**:
- [ ] メッセージが正しくルーティングされる
- [ ] 全てのエージェントがメッセージを送受信できる

---

### V-302: タスク実行

**目的**: タスクがエンドツーエンドで実行できることを確認

**手順**:
```python
# タスク送信
await grand_boss.handle_user_task("Webアプリを作って")

# 結果待機
result = await grand_boss.get_result()

assert "実装完了" in result or "設計完了" in result
```

**成功基準**:
- [ ] タスクが正しく分解される
- [ ] 各Specialistがサブタスクを実行する
- [ ] 結果が正しく集約される

---

## 継続的検証

### CV-001: パフォーマンス

**目的**: システムのパフォーマンス要件を満たすことを確認

**測定項目**:
- メッセージ遅延: < 1秒 (P50)
- スループット: > 100メッセージ/秒
- メモリ使用量: < 1GB (インスタンス1つあたり)

**手順**:
```python
# パフォーマンステスト
import time

start = time.time()
await send_message()
latency = time.time() - start

assert latency < 1.0
```

---

### CV-002: ストレステスト

**目的**: 高負荷時の動作を確認

**手順**:
```python
# 大量のメッセージを送信
for i in range(1000):
    await send_message(f"メッセージ {i}")

# 全て処理されることを確認
```

**成功基準**:
- [ ] 全てのメッセージが処理される
- [ ] プロセスがクラッシュしない
- [ ] メモリリークがない

---

### CV-003: 長時間稼働

**目的**: 長時間稼働時の安定性を確認

**手順**:
```python
# 24時間稼働
await cluster_manager.start()

await asyncio.sleep(24 * 60 * 60)

# 状態確認
status = await cluster_manager.status()
assert status.is_healthy()
```

**成功基準**:
- [ ] 24時間連続稼働する
- [ ] メモリ使用量が安定している
- [ ] エラーが発生しない

---

## 検証スケジュール

| 検証項目 | タイミング | 担当 |
|---------|----------|------|
| V-001〜V-004 | 実装開始前 | 全員 |
| V-101〜V-103 | Phase 1 実装後 | 開発チーム |
| V-201〜V-202 | Phase 2 実装後 | 開発チーム |
| V-301〜V-302 | Phase 3 実装後 | 開発チーム |
| CV-001〜CV-003 | 各Phase完了後 | QAチーム |

---

## 検証結果の記録

### V-001: `claude mcp serve` の基本動作確認

**日付**: 2026-02-01
**結果**: ✅ PASS

**詳細**:
- 有効なJSON-RPCレスポンスが返ってきた
- `tools` フィールドが正しく含まれている
- 利用可能なツール: Task, Bash, Read, Write, Edit, etc.

---

### V-002: `--system-prompt` の動作確認

**日付**: 2026-02-01
**結果**: ❌ FAIL

**詳細**:
- `--system-prompt` オプションは存在しない
- 設定ファイル分離アプローチ（ホームディレクトリ分離方式）を採用

---

### V-003: プログラム制御の可否

**日付**: 2026-02-01
**結果**: ✅ PASS

**詳細**:
- Pythonからプロセス起動が可能
- stdin/stdout経由で通信ができる
- 有効なJSON-RPCレスポンスを取得できる

---

検証結果は以下の形式で記録します：

```
### V-XXX: 検証タイトル

**日付**: 2026-XX-XX
**実行者**: XXX
**結果**: PASS / FAIL

**詳細**:
- 実行内容
- 結果
- 問題点（あれば）

**スクリーンショット**:
（必要に応じて）
```
