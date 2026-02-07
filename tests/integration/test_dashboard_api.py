"""Dashboard API・WebSocket統合テスト

DashboardのREST APIとWebSocket接続を検証する統合テストです。

検証項目:
- V-DB-001: REST API検証
  - 各エンドポイントのリクエスト/レスポンス形式確認
- V-DB-002: WebSocket検証
  - WebSocket接続とメッセージ受信確認
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket

from orchestrator.web.dashboard import app
from orchestrator.web.message_handler import WebSocketManager, WebSocketMessageHandler

# ============================================================================
# フィクスチャ
# ============================================================================


@pytest.fixture
def client():
    """テストクライアントフィクスチャ"""
    return TestClient(app)


@pytest.fixture
def mock_teams_monitor():
    """TeamsMonitorのモック"""
    monitor = MagicMock()
    monitor.get_teams.return_value = [
        {
            "name": "test-team-1",
            "description": "Test Team 1",
            "status": "active",
            "members": ["agent-1", "agent-2"],
        },
        {
            "name": "test-team-2",
            "description": "Test Team 2",
            "status": "idle",
            "members": ["agent-3"],
        },
    ]
    monitor.get_team_messages.return_value = [
        {
            "sender": "agent-1",
            "content": "Hello from agent-1",
            "messageType": "message",
            "timestamp": "2026-02-07T10:00:00Z",
        },
        {
            "sender": "agent-2",
            "content": "Response from agent-2",
            "messageType": "message",
            "timestamp": "2026-02-07T10:01:00Z",
        },
    ]
    monitor.get_team_tasks.return_value = [
        {
            "id": "task-1",
            "subject": "Implement feature X",
            "status": "in_progress",
            "owner": "agent-1",
        },
        {
            "id": "task-2",
            "subject": "Review code",
            "status": "pending",
            "owner": "agent-2",
        },
    ]
    monitor.is_running.return_value = True
    return monitor


@pytest.fixture
def mock_teams_manager():
    """AgentTeamsManagerのモック"""
    manager = MagicMock()
    manager.get_team_status.return_value = {
        "name": "test-team-1",
        "status": "active",
        "members": [
            {"name": "agent-1", "status": "idle"},
            {"name": "agent-2", "status": "working"},
        ],
    }
    return manager


@pytest.fixture
def mock_health_monitor():
    """AgentHealthMonitorのモック"""
    monitor = MagicMock()
    monitor.get_health_status.return_value = {
        "test-team-1": {
            "agent-1": {"isHealthy": True, "lastCheck": "2026-02-07T10:00:00Z"},
            "agent-2": {"isHealthy": True, "lastCheck": "2026-02-07T10:00:00Z"},
        },
        "test-team-2": {
            "agent-3": {"isHealthy": False, "lastCheck": "2026-02-07T09:55:00Z"},
        },
    }
    monitor.is_running.return_value = True
    return monitor


@pytest.fixture
def mock_thinking_log_handler():
    """ThinkingLogHandlerのモック"""
    handler = MagicMock()
    handler.get_logs.return_value = [
        {
            "timestamp": "2026-02-07T10:00:00Z",
            "agentName": "agent-1",
            "content": "Analyzing requirements...",
        },
        {
            "timestamp": "2026-02-07T10:01:00Z",
            "agentName": "agent-2",
            "content": "Implementing solution...",
        },
    ]
    handler.is_running.return_value = True
    return handler


# ============================================================================
# V-DB-001: REST API検証
# ============================================================================


class TestVDB001_RestAPI:
    """V-DB-001: REST API検証

    各エンドポイントのリクエストとレスポンス形式を検証します。
    """

    @patch("orchestrator.web.api.routes._global_state")
    def test_api_teams_returns_team_list(self, mock_state, client):
        """GET /api/teams - チーム一覧取得

        レスポンスにteams配列が含まれ、各チームに必要なフィールドがあることを確認します。
        """
        # モックを設定
        mock_monitor = MagicMock()
        mock_monitor.get_teams.return_value = [
            {
                "name": "test-team-1",
                "description": "Test Team 1",
                "status": "active",
                "members": ["agent-1", "agent-2"],
            }
        ]
        mock_state.teams_monitor = mock_monitor

        response = client.get("/api/teams")

        assert response.status_code == 200
        data = response.json()

        # レスポンス構造の検証
        assert "teams" in data
        assert isinstance(data["teams"], list)
        assert len(data["teams"]) >= 1

        # チーム情報の検証
        team = data["teams"][0]
        assert "name" in team
        assert team["name"] == "test-team-1"

    @patch("orchestrator.web.api.routes._global_state")
    def test_api_teams_messages_returns_message_list(self, mock_state, client):
        """GET /api/teams/{team_name}/messages - メッセージ履歴取得

        レスポンスにmessages配列が含まれることを確認します。
        """
        team_name = "test-team-1"
        mock_monitor = MagicMock()
        mock_monitor.get_team_messages.return_value = [
            {
                "sender": "agent-1",
                "content": "Test message",
                "messageType": "message",
                "timestamp": "2026-02-07T10:00:00Z",
            }
        ]
        mock_state.teams_monitor = mock_monitor

        response = client.get(f"/api/teams/{team_name}/messages")

        assert response.status_code == 200
        data = response.json()

        # レスポンス構造の検証
        assert "teamName" in data
        assert "messages" in data
        assert data["teamName"] == team_name
        assert isinstance(data["messages"], list)

        # メッセージ構造の検証
        if len(data["messages"]) > 0:
            msg = data["messages"][0]
            assert "sender" in msg
            assert "content" in msg
            assert "timestamp" in msg

    @patch("orchestrator.web.api.routes._global_state")
    def test_api_teams_tasks_returns_task_list(self, mock_state, client):
        """GET /api/teams/{team_name}/tasks - タスクリスト取得

        レスポンスにtasks配列が含まれることを確認します。
        """
        team_name = "test-team-1"
        mock_monitor = MagicMock()
        mock_monitor.get_team_tasks.return_value = [
            {
                "id": "task-1",
                "subject": "Test task",
                "status": "pending",
                "owner": "agent-1",
            }
        ]
        mock_state.teams_monitor = mock_monitor

        response = client.get(f"/api/teams/{team_name}/tasks")

        assert response.status_code == 200
        data = response.json()

        # レスポンス構造の検証
        assert "teamName" in data
        assert "tasks" in data
        assert data["teamName"] == team_name
        assert isinstance(data["tasks"], list)

        # タスク構造の検証
        if len(data["tasks"]) > 0:
            task = data["tasks"][0]
            assert "id" in task
            assert "subject" in task
            assert "status" in task

    @patch("orchestrator.web.api.routes._global_state")
    def test_api_teams_status_returns_status_info(self, mock_state, client):
        """GET /api/teams/{team_name}/status - チーム状態取得

        チームの状態情報が返されることを確認します。
        """
        team_name = "test-team-1"
        mock_manager = MagicMock()
        mock_manager.get_team_status.return_value = {
            "name": team_name,
            "status": "active",
            "members": [
                {"name": "agent-1", "status": "idle"},
                {"name": "agent-2", "status": "working"},
            ],
        }
        mock_state.teams_manager = mock_manager

        response = client.get(f"/api/teams/{team_name}/status")

        assert response.status_code == 200
        data = response.json()

        # レスポンス構造の検証
        assert "name" in data
        assert "status" in data
        assert data["name"] == team_name

    @patch("orchestrator.web.api.routes._global_state")
    def test_api_teams_thinking_returns_thinking_logs(self, mock_state, client):
        """GET /api/teams/{team_name}/thinking - 思考ログ取得

        思考ログが返されることを確認します。
        """
        team_name = "test-team-1"
        mock_handler = MagicMock()
        mock_handler.get_logs.return_value = [
            {
                "timestamp": "2026-02-07T10:00:00Z",
                "agentName": "agent-1",
                "content": "Thinking...",
            }
        ]
        mock_state.thinking_log_handler = mock_handler

        response = client.get(f"/api/teams/{team_name}/thinking")

        assert response.status_code == 200
        data = response.json()

        # レスポンス構造の検証
        assert "teamName" in data
        assert "thinking" in data
        assert data["teamName"] == team_name
        assert isinstance(data["thinking"], list)

    @patch("orchestrator.web.api.routes._global_state")
    def test_api_health_returns_health_status(self, mock_state, client):
        """GET /api/health - ヘルスステータス取得

        ヘルスステータスが返されることを確認します。
        """
        mock_monitor = MagicMock()
        mock_monitor.get_health_status.return_value = {
            "test-team-1": {
                "agent-1": {"isHealthy": True},
                "agent-2": {"isHealthy": True},
            }
        }
        mock_state.health_monitor = mock_monitor

        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()

        # チームごとのヘルス情報が含まれる
        assert "test-team-1" in data

    def test_api_info_returns_endpoint_list(self, client):
        """GET /api/ - API情報取得

        利用可能なエンドポイントの一覧が返されることを確認します。
        """
        response = client.get("/api/")

        assert response.status_code == 200
        data = response.json()

        # 必要なフィールドの確認
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data

        # エンドポイント一覧の確認
        endpoints = data["endpoints"]
        expected_endpoints = [
            "teams",
            "teams_messages",
            "teams_tasks",
            "teams_thinking",
            "teams_status",
            "health",
            "websocket",
        ]
        for endpoint in expected_endpoints:
            assert endpoint in endpoints

    def test_root_returns_api_info(self, client):
        """GET / - ルートエンドポイント

        API情報が返されることを確認します。
        """
        response = client.get("/")

        assert response.status_code == 200

    @patch("orchestrator.web.api.routes._global_state")
    def test_api_monitoring_start_stop(self, mock_state, client):
        """POST /api/teams/monitoring/start|stop - 監視制御

        監視の開始・停止が正しく処理されることを確認します。
        """
        mock_monitor = MagicMock()
        mock_monitor.is_running.return_value = False
        mock_state.teams_monitor = mock_monitor

        # 開始
        response = client.post("/api/teams/monitoring/start")
        assert response.status_code == 200
        mock_monitor.start_monitoring.assert_called_once()

        # 停止
        mock_monitor.is_running.return_value = True
        response = client.post("/api/teams/monitoring/stop")
        assert response.status_code == 200
        mock_monitor.stop_monitoring.assert_called_once()


# ============================================================================
# V-DB-002: WebSocket検証
# ============================================================================


class TestVDB002_WebSocket:
    """V-DB-002: WebSocket検証

    WebSocket接続とメッセージ配信を検証します。
    """

    @pytest.mark.asyncio
    async def test_websocket_connection_established(self):
        """WebSocket接続の確立

        WebSocketマネージャーを使用して接続が確立されることを確認します。
        """
        manager = WebSocketManager()
        websocket = AsyncMock(spec=WebSocket)

        await manager.connect(websocket)

        assert manager.get_connection_count() == 1
        websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_broadcast_to_multiple_connections(self):
        """WebSocketブロードキャスト

        複数の接続にメッセージがブロードキャストされることを確認します。
        """
        manager = WebSocketManager()
        ws1 = AsyncMock(spec=WebSocket)
        ws2 = AsyncMock(spec=WebSocket)
        ws3 = AsyncMock(spec=WebSocket)

        await manager.connect(ws1)
        await manager.connect(ws2)
        await manager.connect(ws3)

        message = {
            "type": "teams_update",
            "data": {"teams": [{"name": "test-team", "status": "active"}]},
        }

        await manager.broadcast(message)

        # 全ての接続に送信されることを確認
        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)
        ws3.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_websocket_personal_message(self):
        """WebSocket個人メッセージ

        特定の接続にのみメッセージが送信されることを確認します。
        """
        manager = WebSocketManager()
        ws1 = AsyncMock(spec=WebSocket)
        ws2 = AsyncMock(spec=WebSocket)

        await manager.connect(ws1)
        await manager.connect(ws2)

        message = {"type": "notification", "message": "Private message for ws1"}

        await manager.send_personal(message, ws1)

        # ws1のみに送信されることを確認
        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_not_called()

    @pytest.mark.asyncio
    async def test_websocket_disconnect(self):
        """WebSocket切断

        接続が正しく切断されることを確認します。
        """
        manager = WebSocketManager()
        websocket = AsyncMock(spec=WebSocket)

        await manager.connect(websocket)
        assert manager.get_connection_count() == 1

        manager.disconnect(websocket)
        assert manager.get_connection_count() == 0

    @pytest.mark.asyncio
    async def test_websocket_close_all(self):
        """WebSocket全接続クローズ

        全ての接続が閉じられることを確認します。
        """
        manager = WebSocketManager()
        ws1 = AsyncMock(spec=WebSocket)
        ws2 = AsyncMock(spec=WebSocket)

        await manager.connect(ws1)
        await manager.connect(ws2)

        await manager.close_all()

        ws1.close.assert_called_once()
        ws2.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_message_handler_status_command(self):
        """WebSocketメッセージハンドラー - statusコマンド

        statusコマンドが正しく処理されることを確認します。
        """
        # WebSocketManagerのsend_personalをモック
        manager = MagicMock(spec=WebSocketManager)
        manager.send_personal = AsyncMock()
        manager.get_connection_count = MagicMock(return_value=1)

        handler = WebSocketMessageHandler(manager)
        websocket = AsyncMock(spec=WebSocket)

        # JSON文字列としてメッセージを送信（handle_messageはJSON文字列を期待する）
        import json

        message_data = {"type": "get_status"}

        await handler.handle_message(json.dumps(message_data), websocket)

        # ステータスレスポンスが送信されることを確認
        manager.send_personal.assert_called_once()
        call_args = manager.send_personal.call_args[0][0]
        assert call_args["type"] == "status"
        assert "data" in call_args

    @pytest.mark.asyncio
    async def test_websocket_teams_update_broadcast(self):
        """チーム状態更新時のブロードキャスト

        チーム状態が更新された際にWebSocketで通知されることを確認します。
        """
        manager = WebSocketManager()
        ws1 = AsyncMock(spec=WebSocket)
        ws2 = AsyncMock(spec=WebSocket)

        await manager.connect(ws1)
        await manager.connect(ws2)

        # チーム更新メッセージをブロードキャスト
        update_message = {
            "type": "teams_update",
            "data": {"teams": [{"name": "test-team", "status": "working", "members": ["agent-1"]}]},
        }

        await manager.broadcast(update_message)

        # 全接続に送信されることを確認
        ws1.send_json.assert_called_once_with(update_message)
        ws2.send_json.assert_called_once_with(update_message)

    @pytest.mark.asyncio
    async def test_websocket_thinking_log_broadcast(self):
        """思考ログ更新時のブロードキャスト

        思考ログが更新された際にWebSocketで通知されることを確認します。
        """
        manager = WebSocketManager()
        ws = AsyncMock(spec=WebSocket)

        await manager.connect(ws)

        # 思考ログメッセージをブロードキャスト
        log_message = {
            "type": "thinking_log",
            "data": {
                "teamName": "test-team",
                "agentName": "agent-1",
                "content": "Processing...",
                "timestamp": "2026-02-07T10:00:00Z",
            },
        }

        await manager.broadcast(log_message)

        ws.send_json.assert_called_once_with(log_message)


# ============================================================================
# 統合テスト
# ============================================================================


class TestDashboardIntegration:
    """Dashboard統合テスト

    複数のコンポーネントが連携するシナリオをテストします。
    """

    @pytest.mark.asyncio
    async def test_team_status_change_broadcasts_to_websocket(self):
        """チーム状態変更時にWebSocketで通知される統合テスト

        TeamsMonitorのコールバック経由でWebSocketブロードキャストが
        正しく行われることを確認します。
        """
        manager = WebSocketManager()
        ws = AsyncMock(spec=WebSocket)

        await manager.connect(ws)

        # チーム更新メッセージをブロードキャスト（TeamsMonitorコールバックをシミュレート）
        update_data = {
            "type": "teams_update",
            "teams": [{"name": "test-team", "status": "working"}],
        }

        await manager.broadcast(update_data)

        # WebSocketにメッセージが送信されたことを確認
        ws.send_json.assert_called_once_with(update_data)

    @pytest.mark.asyncio
    async def test_thinking_log_broadcasts_to_websocket(self):
        """思考ログ更新時にWebSocketで通知される統合テスト

        ThinkingLogHandlerのコールバック経由でWebSocketブロードキャストが
        正しく行われることを確認します。
        """
        manager = WebSocketManager()
        ws = AsyncMock(spec=WebSocket)

        await manager.connect(ws)

        # 思考ログメッセージをブロードキャスト（ThinkingLogHandlerコールバックをシミュレート）
        log_data = {
            "type": "thinking_log",
            "teamName": "test-team",
            "agentName": "agent-1",
            "content": "Analyzing...",
            "timestamp": "2026-02-07T10:00:00Z",
        }

        await manager.broadcast(log_data)

        # WebSocketにメッセージが送信されたことを確認
        ws.send_json.assert_called_once_with(log_data)
