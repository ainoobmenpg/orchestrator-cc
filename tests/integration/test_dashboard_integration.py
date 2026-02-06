"""Dashboard統合テスト

Dashboard APIとWebSocketの統合テストです。

検証項目:
- V-DB-001: REST API検証
- V-DB-002: WebSocket検証
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from orchestrator.web.dashboard import app
from orchestrator.web.message_handler import WebSocketManager


@pytest.fixture
def client():
    """テストクライアントフィクスチャ"""
    return TestClient(app)


class TestRestAPI:
    """V-DB-001: REST API検証"""

    @patch("orchestrator.web.dashboard._teams_monitor")
    def test_api_teams_endpoint(self, mock_teams_monitor, client):
        """チーム一覧APIエンドポイント"""
        mock_teams_monitor.get_teams.return_value = [
            {"name": "test-team", "description": "Test Team"}
        ]

        response = client.get("/api/teams")

        assert response.status_code == 200
        data = response.json()
        assert "teams" in data
        assert len(data["teams"]) == 1
        assert data["teams"][0]["name"] == "test-team"

    @patch("orchestrator.web.dashboard._teams_monitor")
    def test_api_team_messages(self, mock_teams_monitor, client):
        """チームメッセージAPIエンドポイント"""
        mock_teams_monitor.get_team_messages.return_value = [
            {
                "sender": "agent-1",
                "content": "Hello team",
                "messageType": "message",
                "timestamp": "2026-02-06T12:00:00Z",
            }
        ]

        response = client.get("/api/teams/test-team/messages")

        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert "teamName" in data
        assert len(data["messages"]) == 1
        assert data["messages"][0]["sender"] == "agent-1"

    @patch("orchestrator.web.dashboard._teams_monitor")
    def test_api_team_tasks(self, mock_teams_monitor, client):
        """チームタスクAPIエンドポイント"""
        mock_teams_monitor.get_team_tasks.return_value = [
            {"id": "1", "subject": "Test task", "status": "pending"}
        ]

        response = client.get("/api/teams/test-team/tasks")

        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert "teamName" in data
        assert len(data["tasks"]) == 1

    @patch("orchestrator.web.dashboard._teams_manager")
    def test_api_team_status(self, mock_teams_manager, client):
        """チームステータスAPIエンドポイント"""
        mock_teams_manager.get_team_status.return_value = {
            "name": "test-team",
            "description": "Test Team",
            "status": "active",
        }

        response = client.get("/api/teams/test-team/status")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test-team"
        assert data["status"] == "active"

    @patch("orchestrator.web.dashboard._health_monitor")
    def test_api_health(self, mock_health_monitor, client):
        """ヘルスチェックAPIエンドポイント"""
        mock_health_monitor.get_health_status.return_value = {
            "test-team": {"agent1": {"isHealthy": True}}
        }

        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert "test-team" in data


class TestWebSocketIntegration:
    """V-DB-002: WebSocket検証"""

    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """WebSocket接続の確立"""
        manager = WebSocketManager()
        websocket = AsyncMock()

        await manager.connect(websocket)

        assert manager.get_connection_count() == 1
        websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_message_broadcast(self):
        """WebSocket経由のメッセージブロードキャスト"""
        manager = WebSocketManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await manager.connect(ws1)
        await manager.connect(ws2)

        message = {"type": "teams_update", "data": {"teams": []}}
        await manager.broadcast(message)

        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_websocket_disconnect_handling(self):
        """WebSocket切断時の処理"""
        manager = WebSocketManager()
        websocket = AsyncMock()

        await manager.connect(websocket)
        assert manager.get_connection_count() == 1

        manager.disconnect(websocket)
        assert manager.get_connection_count() == 0

    @pytest.mark.asyncio
    async def test_websocket_personal_message(self):
        """WebSocket個人メッセージ送信"""
        manager = WebSocketManager()
        ws1 = AsyncMock()
        ws2 = AsyncMock()

        await manager.connect(ws1)
        await manager.connect(ws2)

        # ws1のみに送信
        await manager.send_personal({"type": "notification", "message": "Hello"}, ws1)

        ws1.send_json.assert_called_once()
        ws2.send_json.assert_not_called()

    @pytest.mark.asyncio
    async def test_websocket_status_message(self):
        """WebSocketステータスメッセージ処理"""
        from orchestrator.web.message_handler import WebSocketMessageHandler

        manager = WebSocketManager()
        handler = WebSocketMessageHandler(manager)
        websocket = AsyncMock()

        # 接続を追加
        manager._active_connections = [AsyncMock(), AsyncMock()]

        await handler._handle_get_status({}, websocket)

        websocket.send_json.assert_called_once()
        call_args = websocket.send_json.call_args[0][0]
        assert call_args["type"] == "status"
        assert "data" in call_args
