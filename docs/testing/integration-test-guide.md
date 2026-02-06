# 統合テスト実施ガイド

このドキュメントでは、orchestrator-cc プロジェクトの統合テストを実行する方法と、各テストの内容について説明します。

## 目的と範囲

統合テストの目的は、各モジュールが正しく連携して動作することを検証することです。

- **チーム管理**: チームの作成・削除・設定
- **エージェント間通信**: ダイレクトメッセージ・ブロードキャスト・タスク割り振り
- **タスク管理**: 依存関係・自動割り振り
- **思考ログ**: 送信・監視・ファイル永続化
- **ヘルスモニタリング**: エージェント登録・タイムアウト検知
- **Dashboard API**: REST API・WebSocket

## テストの種類

| 種類 | マーカー | 説明 |
|------|----------|------|
| 統合テスト | `integration` | 複数モジュールの連携を検証 |
| 単体テスト | `unit` | 個別モジュールの動作を検証 |
| 並列実行不可 | `serial` | イベントループ使用等で並列実行不可 |
| Playwright使用 | `playwright` | ブラウザテスト（pytest-asyncioと競合） |

## テスト実行方法

### すべてのテストを実行

```bash
pytest tests/ -v
```

### 統合テストのみ実行

```bash
pytest tests/integration/ -v -m integration
```

### 特定のテストファイルを実行

```bash
pytest tests/integration/test_team_creation.py -v
```

### カバレッジ付きで実行

```bash
pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html
```

HTMLレポートは `htmlcov/index.html` で確認できます。

### Playwrightテストを除外して実行

```bash
pytest tests/ -v -m "not playwright"
```

## 統合テスト一覧

### 1. チーム作成・削除 (`test_team_creation.py`)

| テストID | テスト名 | 検証内容 |
|----------|----------|----------|
| V-TM-001 | チーム作成 | config.json の作成とヘルスモニターへの登録 |
| V-TM-002 | チーム削除 | ディレクトリとタスクの削除 |

### 2. エージェント間通信 (`test_agent_communication.py`)

| テストID | テスト名 | 検証内容 |
|----------|----------|----------|
| V-AC-001 | ダイレクトメッセージ | メッセージ送信とinbox配信 |
| V-AC-002 | ブロードキャスト | 全メンバーへの配信 |
| V-AC-003 | タスク割り振り | TaskCreate・TaskUpdate・TaskList |

### 3. タスク管理 (`test_task_management.py`)

| テストID | テスト名 | 検証内容 |
|----------|----------|----------|
| V-TS-001 | 依存関係チェーン | タスクA→B→CのblockedBy設定 |
| V-TS-002 | 自動割り振り | オーナーなしタスクの自動割り振り |

### 4. 思考ログ (`test_thinking_logs.py`)

| テストID | テスト名 | 検証内容 |
|----------|----------|----------|
| V-TL-001 | 思考ログ送信 | send_thinking_log() とファイル永続化 |
| V-TL-002 | 思考ログ監視 | 外部書き込みでコールバック発火 |

### 5. ヘルスモニタリング (`test_health_monitoring.py`)

| テストID | テスト名 | 検証内容 |
|----------|----------|----------|
| V-HM-001 | エージェント登録 | get_health_status() で確認 |
| V-HM-002 | タイムアウト検知 | タイムアウトとコールバック |

### 6. Dashboard API (`test_dashboard_api.py`)

| テストID | テスト名 | 検証内容 |
|----------|----------|----------|
| V-DB-001 | REST API | 各エンドポイントのレスポンス形式 |
| V-DB-002 | WebSocket | 接続・メッセージ配信・切断 |

### 7. エンドツーエンド (`test_end_to_end.py`)

| シナリオ | 説明 |
|----------|------|
| シナリオ1 | 簡単なタスク実行（リーダー + コーダー） |
| シナリオ2 | 複数エージェント協調（リーダー + リサーチャー + コーダー） |
| シナリオ3 | エラーハンドリング（タイムアウト検知） |

## トラブルシューティング

### イベントループエラー

```
RuntimeError: Runner.run() cannot be called from a running event loop
```

**原因**: pytest-asyncio と coverage の組み合わせによる既知の問題。

**対策**: テストは単独ではパスします。全テスト実行時は `test_message_handler.py` をスキップしてください。

```bash
pytest tests/ -v --ignore=tests/web/test_message_handler.py
```

### Playwrightテストが失敗する

**原因**: Dashboardが起動していない、またはポートが競合している。

**対策**:

```bash
# Dashboardを起動
python -m orchestrator.web.dashboard

# 別のターミナルでテスト実行
pytest tests/ui/ -v
```

### 404 Not Found エラー

**原因**: Agent Teams 移行後に削除された古いAPIエンドポイントをテストが参照している。

**対策**: 古いテストケースには `@pytest.mark.skip` マークが付いています。スキップされるのは正常な動作です。

## テストカバレッジ目標

| 項目 | 目標 | 現在 |
|------|------|------|
| 全体カバレッジ | 80%+ | 81.62% ✅ |
| thinking_log_handler.py | 80%+ | 94% ✅ |
| dashboard.py | 70%+ | 57% ⚠️ |
| cli/main.py | 70%+ | 79% ✅ |
| message_handler.py | 70%+ | 86% ✅ |

## まとめ

統合テストは以下の機能を検証しています：

- ✅ 85件の統合テストがパス
- ✅ 全体カバレッジ 81.62%
- ✅ リントチェック（ruff）パス
- ✅ 型チェック（mypy）パス
