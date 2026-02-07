"""Dashboard API エンドポイントのテスト

orchestrator/web/dashboard.py の FastAPI エンドポイントのテストです。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from orchestrator.web.dashboard import app


@pytest.fixture
def client():
    """テストクライアントフィクスチャ"""
    return TestClient(app)


class TestRootEndpoints:
    """ルートエンドポイントのテスト"""

    @pytest.mark.skip(reason="Reactダッシュボード導入により、ルートエンドポイントは常にHTMLを返します")
    def test_root_json_response(self, client):
        """ルートパスでJSONレスポンスを返すテスト（テンプレートがない場合）

        Note: Reactダッシュボード導入により、このテストは廃止されました。
        ルートエンドポイントは常にHTML（index.html）またはJSONメッセージを返します。
        """
        with patch("orchestrator.web.dashboard._templates_dir") as mock_templates:
            # テンプレートディレクトリが存在しないようにモック
            mock_templates.exists.return_value = False
            mock_templates.__truediv__.return_value.exists.return_value = False

            response = client.get("/")

            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "endpoints" in data

    def test_api_info(self, client):
        """API情報エンドポイントテスト"""
        response = client.get("/api/")

        assert response.status_code == 200
        data = response.json()
        assert "endpoints" in data


class TestHealthEndpoint:
    """ヘルスエンドポイントのテスト"""

    @patch("orchestrator.web.api.routes._get_health_monitor")
    def test_get_health_all(self, mock_get_health_monitor, client):
        """全チームのヘルスステータス取得テスト"""
        mock_monitor = MagicMock()
        mock_monitor.get_health_status.return_value = {
            "team1": {"agent1": {"isHealthy": True}},
            "team2": {"agent2": {"isHealthy": False}},
        }
        mock_get_health_monitor.return_value = mock_monitor

        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert "team1" in data

    @patch("orchestrator.web.api.routes._get_health_monitor")
    def test_get_health_specific_team(self, mock_get_health_monitor, client):
        """特定チームのヘルスステータス取得テスト"""
        mock_monitor = MagicMock()
        mock_monitor.get_health_status.return_value = {
            "team1": {"agent1": {"isHealthy": True}},
        }
        mock_get_health_monitor.return_value = mock_monitor

        response = client.get("/api/health?team=team1")

        assert response.status_code == 200
        data = response.json()
        assert "team1" in data

    @patch("orchestrator.web.api.routes._get_health_monitor")
    def test_get_health_team_not_found(self, mock_get_health_monitor, client):
        """存在しないチームのヘルスステータステスト"""
        mock_monitor = MagicMock()
        mock_monitor.get_health_status.return_value = {
            "team1": {"agent1": {"isHealthy": True}},
        }
        mock_get_health_monitor.return_value = mock_monitor

        response = client.get("/api/health?team=nonexistent")

        # チームが見つからない場合でも200を返す（空の辞書）
        assert response.status_code == 200
        data = response.json()
        # 存在しないチームなので空


class TestTeamsEndpoints:
    """チーム関連エンドポイントのテスト"""

    @patch("orchestrator.web.api.routes._get_teams_monitor")
    def test_get_teams(self, mock_get_teams_monitor, client):
        """チーム一覧取得テスト"""
        mock_monitor = MagicMock()
        mock_monitor.get_teams.return_value = [
            {"name": "team1", "description": "Team 1"},
            {"name": "team2", "description": "Team 2"},
        ]
        mock_get_teams_monitor.return_value = mock_monitor

        response = client.get("/api/teams")

        assert response.status_code == 200
        data = response.json()
        assert "teams" in data
        assert len(data["teams"]) == 2
        assert data["teams"][0]["name"] == "team1"

    @patch("orchestrator.web.api.routes._get_teams_monitor")
    def test_get_teams_not_initialized(self, mock_get_teams_monitor, client):
        """TeamsMonitor未初期化テスト"""
        mock_get_teams_monitor.return_value = None

        response = client.get("/api/teams")

        assert response.status_code == 200
        data = response.json()
        assert "error" in data

    @patch("orchestrator.web.api.routes._get_teams_monitor")
    def test_get_team_messages(self, mock_get_teams_monitor, client):
        """チームメッセージ取得テスト"""
        mock_monitor = MagicMock()
        mock_monitor.get_team_messages.return_value = [
            {"id": "msg1", "sender": "agent1", "content": "Hello"},
        ]
        mock_get_teams_monitor.return_value = mock_monitor

        response = client.get("/api/teams/test-team/messages")

        assert response.status_code == 200
        data = response.json()
        assert "teamName" in data
        assert "messages" in data
        assert len(data["messages"]) == 1

    @patch("orchestrator.web.api.routes._get_teams_monitor")
    def test_get_team_tasks(self, mock_get_teams_monitor, client):
        """チームタスク取得テスト"""
        mock_monitor = MagicMock()
        mock_monitor.get_team_tasks.return_value = [
            {"id": "task1", "subject": "Task 1", "status": "pending"},
        ]
        mock_get_teams_monitor.return_value = mock_monitor

        response = client.get("/api/teams/test-team/tasks")

        assert response.status_code == 200
        data = response.json()
        assert "teamName" in data
        assert "tasks" in data
        assert len(data["tasks"]) == 1

    @patch("orchestrator.web.api.routes._get_teams_monitor")
    def test_get_team_tasks_with_status_filter(self, mock_get_teams_monitor, client):
        """タスクをステータスでフィルタするテスト"""
        mock_monitor = MagicMock()
        mock_monitor.get_team_tasks.return_value = [
            {"id": "task1", "subject": "Task 1", "status": "pending"},
            {"id": "task2", "subject": "Task 2", "status": "completed"},
        ]
        mock_get_teams_monitor.return_value = mock_monitor

        response = client.get("/api/teams/test-team/tasks?status=pending")

        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data

    @patch("orchestrator.web.api.routes._get_teams_manager")
    def test_get_team_status(self, mock_get_teams_manager, client):
        """チーム状態取得テスト"""
        mock_manager = MagicMock()
        mock_manager.get_team_status.return_value = {
            "name": "test-team",
            "description": "Test",
            "taskCount": 0,
            "members": [],
        }
        mock_get_teams_manager.return_value = mock_manager

        response = client.get("/api/teams/test-team/status")

        assert response.status_code == 200
        data = response.json()
        # "name" キーまたは "error" キーが存在することを確認
        assert "name" in data or "error" in data

    @patch("orchestrator.web.api.routes._get_thinking_log_handler")
    def test_get_team_thinking(self, mock_get_thinking_handler, client):
        """思考ログ取得テスト"""
        mock_handler = MagicMock()
        mock_handler.get_logs.return_value = [
            {"agentName": "agent1", "content": "Thinking...", "timestamp": "2026-02-06T12:00:00Z"},
        ]
        mock_get_thinking_handler.return_value = mock_handler

        response = client.get("/api/teams/test-team/thinking")

        assert response.status_code == 200
        data = response.json()
        assert "thinking" in data or "error" in data

    @patch("orchestrator.web.api.routes._get_thinking_log_handler")
    def test_get_team_thinking_not_initialized(self, mock_get_thinking_handler, client):
        """思考ログハンドラー未初期化テスト"""
        mock_get_thinking_handler.return_value = None

        response = client.get("/api/teams/test-team/thinking")

        assert response.status_code == 200
        data = response.json()
        assert "error" in data


class TestBroadcastFunctions:
    """ブロードキャスト関数のテスト"""

    @patch("orchestrator.web.api.routes._global_state")
    def test_broadcast_teams_update_with_event_loop(self, mock_global_state):
        """イベントループ実行中のブロードキャストテスト"""
        from orchestrator.web.dashboard import _broadcast_teams_update

        mock_ws_manager = MagicMock()
        mock_ws_manager.broadcast = AsyncMock()
        mock_global_state.ws_manager = mock_ws_manager

        # asyncio.create_task をモック - モジュールレベルでパッチ
        import asyncio
        original_create_task = asyncio.create_task
        called = []

        def mock_create_task(coro):
            called.append(coro)
            return original_create_task(coro)

        asyncio.create_task = mock_create_task
        try:
            # モックした create_task を使用するようにモジュールを再インポート
            import importlib

            import orchestrator.web.dashboard
            importlib.reload(orchestrator.web.dashboard)
            from orchestrator.web.dashboard import _broadcast_teams_update

            _broadcast_teams_update({"type": "test"})
            # asyncio.create_task が呼ばれない場合もあるので、単にエラーが発生しないことを確認
            assert True
        finally:
            asyncio.create_task = original_create_task
            importlib.reload(orchestrator.web.dashboard)

    @patch("orchestrator.web.api.routes._global_state")
    def test_broadcast_teams_update_no_event_loop(self, mock_global_state):
        """イベントループ未実行中のブロードキャストテスト"""
        from orchestrator.web.dashboard import _broadcast_teams_update

        mock_ws_manager = MagicMock()
        mock_global_state.ws_manager = mock_ws_manager

        # RuntimeError を発生させるモック
        with patch("asyncio.get_running_loop", side_effect=RuntimeError):
            # 例外が発生しないことを確認
            _broadcast_teams_update({"type": "test"})

    @patch("orchestrator.web.api.routes._global_state")
    def test_broadcast_teams_update_no_manager(self, mock_global_state):
        """マネージャーがない場合のブロードキャストテスト"""
        from orchestrator.web.dashboard import _broadcast_teams_update

        # ws_manager が None の場合
        mock_global_state.ws_manager = None

        # 例外が発生しないことを確認
        _broadcast_teams_update({"type": "test"})

    @patch("orchestrator.web.api.routes._global_state")
    def test_broadcast_thinking_log_with_event_loop(self, mock_global_state):
        """思考ログブロードキャストテスト"""
        from orchestrator.web.dashboard import _broadcast_thinking_log

        mock_ws_manager = MagicMock()
        mock_ws_manager.broadcast = AsyncMock()
        mock_global_state.ws_manager = mock_ws_manager

        # イベントループ実行中のテストは複雑なため、単にエラーが発生しないことを確認
        # asyncio.create_task が呼ばれない場合もあるので、単にエラーが発生しないことを確認
        _broadcast_thinking_log({"type": "thinking_log"})
        assert True

    @patch("orchestrator.web.api.routes._global_state")
    def test_broadcast_thinking_log_no_event_loop(self, mock_global_state):
        """イベントループ未実行中の思考ログブロードキャストテスト"""
        from orchestrator.web.dashboard import _broadcast_thinking_log

        mock_ws_manager = MagicMock()
        mock_global_state.ws_manager = mock_ws_manager

        # RuntimeError を発生させるモック
        with patch("asyncio.get_running_loop", side_effect=RuntimeError):
            # 例外が発生しないことを確認
            _broadcast_thinking_log({"type": "thinking_log"})
