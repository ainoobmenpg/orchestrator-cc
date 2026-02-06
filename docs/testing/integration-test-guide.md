# 統合テスト実施ガイド

このドキュメントでは、orchestrator-ccの統合テストについて説明します。

## 目的

統合テストは、複数のモジュールが連携して正しく動作することを検証するためのテストです。単体テストが個々の関数やクラスをテストするのに対し、統合テストはモジュール間のインターフェースとデータフローを検証します。

## テスト構成

統合テストは `tests/integration/` ディレクトリに配置されています。

| テストファイル | 検証内容 | テスト数 |
|--------------|----------|---------|
| `test_team_creation.py` | チーム作成・削除 (V-TM-001, V-TM-002) | 5 |
| `test_thinking_logs.py` | 思考ログ (V-TL-001, V-TL-002) | 6 |
| `test_health_monitoring.py` | ヘルスモニター (V-HM-001, V-HM-002) | 6 |
| `test_agent_communication.py` | エージェント間通信 (V-AC-001~003) | 8 |
| `test_task_management.py` | タスク管理 (V-TS-001, V-TS-002) | 6 |
| `test_dashboard_integration.py` | Dashboard API (V-DB-001, V-DB-002) | 9 |

## 検証項目詳細

### V-TM-001: チーム作成検証

**目的**: CLI `create-team` でチーム作成が正しく動作することを確認

**検証内容**:
- `config.json` の存在と内容を確認
- ヘルスモニターへの登録を確認

**テスト**: `test_team_creation.py::TestTeamCreation::test_create_team_via_cli`

### V-TM-002: チーム削除検証

**目的**: チーム削除が正しく動作することを確認

**検証内容**:
- ディレクトリとタスクの削除を確認
- 存在しないチームの削除が適切に処理されることを確認

**テスト**: `test_team_creation.py::TestTeamDeletion::test_delete_team_via_manager`

### V-TL-001: 思考ログ送信検証

**目的**: `send_thinking_log()` 呼び出しでログが記録されることを確認

**検証内容**:
- JSONLファイルへの保存を確認
- `ThinkingLogHandler.get_logs()` で取得できることを確認

**テスト**: `test_thinking_logs.py::TestThinkingLogSending::test_send_thinking_log`

### V-TL-002: 思考ログ監視検証

**目的**: `ThinkingLogHandler` の監視機能が動作することを確認

**検証内容**:
- 外部書き込みでコールバックが発火することを確認
- 複数チームのログが正しく分離されることを確認

**テスト**: `test_thinking_logs.py::TestThinkingLogMonitoring::test_callback_on_new_log`

### V-HM-001: エージェント登録検証

**目的**: エージェントをヘルスモニターに登録できることを確認

**検証内容**:
- `register_agent()` でエージェントが登録されることを確認
- `get_health_status()` で登録状態を取得できることを確認

**テスト**: `test_health_monitoring.py::TestHealthMonitoringRegistration::test_agent_registration`

### V-HM-002: タイムアウト検知検証

**目的**: エージェントのタイムアウトが検知されることを確認

**検証内容**:
- 短いタイムアウト（5秒）で検知されることを確認
- アクティビティ更新でタイムアウトが回避されることを確認

**テスト**: `test_health_monitoring.py::TestHealthMonitoringTimeout::test_timeout_detection_short_threshold`

### V-AC-001: ダイレクトメッセージ検証

**目的**: エージェント間のダイレクトメッセージ機能を確認

**検証内容**:
- `TeamMessage` モデルでメッセージを作成できることを確認
- 受信者指定が正しく動作することを確認

**テスト**: `test_agent_communication.py::TestDirectMessaging::test_send_direct_message`

### V-AC-002: ブロードキャスト検証

**目的**: ブロードキャストメッセージ機能を確認

**検証内容**:
- 受信者なしのメッセージがブロードキャストとして扱われることを確認

**テスト**: `test_agent_communication.py::TestBroadcastMessaging::test_broadcast_message_creation`

### V-AC-003: タスク割り振り検証

**目的**: タスクの作成と割り当て機能を確認

**検証内容**:
- `TeamConfig` でチームを作成できることを確認
- タスクファイルが正しく作成されることを確認
- オーナー割り当てが正しく動作することを確認

**テスト**: `test_agent_communication.py::TestTaskAssignment::test_create_team`

### V-TS-001: タスク依存関係検証

**目的**: タスクの依存関係（`blockedBy`）が正しく動作することを確認

**検証内容**:
- タスクA→B→Cの依存チェーンが正しく設定されることを確認
- 複数のタスクによるブロックが正しく動作することを確認

**テスト**: `test_task_management.py::TestTaskDependencies::test_task_dependency_chain`

### V-TS-002: タスク自動割り振り検証

**目的**: タスクのステータス管理が正しく動作することを確認

**検証内容**:
- オーナーなしタスクの状態が正しく保持されることを確認
- ステータスによるフィルタリングが正しく動作することを確認

**テスト**: `test_task_management.py::TestTaskAutoAssignment::test_task_without_owner`

### V-DB-001: REST API検証

**目的**: DashboardのREST APIエンドポイントが正しく動作することを確認

**検証内容**:
- `/api/teams` - チーム一覧取得
- `/api/teams/{team_name}/messages` - メッセージ取得
- `/api/teams/{team_name}/tasks` - タスク取得
- `/api/teams/{team_name}/status` - ステータス取得
- `/api/health` - ヘルスチェック

**テスト**: `test_dashboard_integration.py::TestRestAPI::test_api_teams_endpoint`

### V-DB-002: WebSocket検証

**目的**: WebSocket接続とメッセージ配信が正しく動作することを確認

**検証内容**:
- WebSocket接続の確立
- メッセージブロードキャスト
- 個人メッセージ送信
- 切断処理

**テスト**: `test_dashboard_integration.py::TestWebSocketIntegration::test_websocket_connection`

## 実行方法

### 全統合テストの実行

```bash
pytest tests/integration/ -v
```

### 特定のテストファイルの実行

```bash
pytest tests/integration/test_team_creation.py -v
```

### 特定のテストクラスの実行

```bash
pytest tests/integration/test_team_creation.py::TestTeamCreation -v
```

### 特定のテストの実行

```bash
pytest tests/integration/test_team_creation.py::TestTeamCreation::test_create_team_via_cli -v
```

### カバレッジ付きで実行

```bash
pytest tests/integration/ -v --cov=. --cov-report=term-missing
```

## テスト結果の解釈

### 成功時の出力

```
============================= 43 passed in 19.31s ==============================
```

全てのテストがパスしたことを示します。

### 失敗時の出力

```
FAILED tests/integration/test_team_creation.py::TestTeamCreation::test_create_team_via_cli
```

失敗したテストが特定されます。詳細なエラーメッセージが表示されるので、原因を特定して修正してください。

## 注意事項

1. **並列実行**: 統合テストはファイルシステム操作を含むため、並列実行（`-n` オプション）を使用しないでください。

2. **クリーン環境**: テストは一時ディレクトリ（`tmp_path`）を使用しますが、複数のテストを同時に実行する場合は注意が必要です。

3. **モックの使用**: 外部リソース（ファイルシステム、ネットワーク）は適切にモックされています。

## トラブルシューティング

### ValueError: not in the subpath

`team_file_observer` のテストで一時ディレクトリのパスに関する警告が出る場合がありますが、これはテスト環境の制約によるもので、実際の使用環境では発生しません。

### KeyError: 'xxx'

モデルのAPI変更に伴うエラーです。`team_models.py` の定義を確認して、テストを更新してください。
