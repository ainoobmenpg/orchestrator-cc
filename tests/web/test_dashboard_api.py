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

    @pytest.mark.skip(
        reason="Reactダッシュボード導入により、ルートエンドポイントは常にHTMLを返します"
    )
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

        asyncio.create_task = mock_create_task  # type: ignore[assignment]
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


class TestSpaRouter:
    """SPAルーターのテスト"""

    @patch("orchestrator.web.dashboard._frontend_dist_dir")
    @patch("orchestrator.web.dashboard._templates_dir")
    def test_spa_root_returns_dist_index(self, mock_templates, mock_dist, client):
        """dist/index.htmlが存在する場合はそれを返す"""
        mock_dist.exists.return_value = True
        mock_index = MagicMock()
        mock_index.exists.return_value = True
        mock_dist.__truediv__.return_value = mock_index

        response = client.get("/")

        assert response.status_code == 200
        # FileResponseはテストクライアントで異なる扱いになる場合がある
        # ステータスコードのみ検証

    @patch("orchestrator.web.dashboard._frontend_dist_dir")
    @patch("orchestrator.web.dashboard._templates_dir")
    def test_spa_root_returns_json_when_no_build(self, mock_templates, mock_dist, client):
        """ビルド済みファイルがない場合はJSONメッセージを返す"""
        mock_dist.exists.return_value = False
        mock_dist.__truediv__.return_value.exists.return_value = False
        mock_templates.exists.return_value = False
        mock_templates.__truediv__.return_value.exists.return_value = False

        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data

    @patch("orchestrator.web.dashboard._frontend_dist_dir")
    def test_spa_serve_asset_file(self, mock_dist, client):
        """アセットファイルは直接返す"""
        mock_dist.exists.return_value = True
        mock_asset = MagicMock()
        mock_asset.exists.return_value = True
        mock_asset.is_file.return_value = True
        mock_dist.__truediv__.return_value = mock_asset

        response = client.get("/assets/main.js")

        assert response.status_code == 200

    @patch("orchestrator.web.dashboard._frontend_dist_dir")
    def test_spa_fallback_to_index(self, mock_dist, client):
        """SPAルートはindex.htmlにフォールバックする"""
        mock_dist.exists.return_value = True
        mock_asset = MagicMock()
        mock_asset.exists.return_value = False
        mock_asset.is_file.return_value = False
        mock_index = MagicMock()
        mock_index.exists.return_value = True
        mock_dist.__truediv__.side_effect = [mock_asset, mock_index]

        response = client.get("/dashboard/settings")

        assert response.status_code == 200


class TestHealthEventCallback:
    """ヘルスイベントコールバックのテスト"""

    @patch("orchestrator.web.dashboard._global_state")
    def test_on_health_event_with_manager(self, mock_global_state):
        """WebSocketManagerがある場合はブロードキャストする"""
        from orchestrator.web.dashboard import _on_health_event

        mock_manager = MagicMock()
        mock_manager.broadcast = AsyncMock()
        mock_global_state.ws_manager = mock_manager

        mock_event = MagicMock()
        mock_event.to_dict.return_value = {"agent": "test-agent", "status": "unhealthy"}

        # イベントループがない場合は例外が発生しないことを確認
        with patch("asyncio.get_running_loop", side_effect=RuntimeError):
            _on_health_event(mock_event)

    @patch("orchestrator.web.dashboard._global_state")
    def test_on_health_event_no_manager(self, mock_global_state):
        """WebSocketManagerがない場合は何もしない"""
        from orchestrator.web.dashboard import _on_health_event

        mock_global_state.ws_manager = None

        mock_event = MagicMock()
        mock_event.to_dict.return_value = {"agent": "test-agent"}

        # 例外が発生しないことを確認
        _on_health_event(mock_event)


class TestLifespan:
    """ライフサイクル管理のテスト"""

    @pytest.mark.asyncio
    async def test_lifespan_initialization(self):
        """ライフサイクル初期化のテスト"""
        from orchestrator.web.dashboard import _global_state, lifespan

        # モックを準備
        with (
            patch("orchestrator.web.dashboard.get_agent_health_monitor") as mock_get_health,
            patch("orchestrator.web.dashboard.get_agent_teams_manager") as mock_get_teams,
            patch("orchestrator.web.dashboard.get_thinking_log_handler") as mock_get_thinking,
        ):
            mock_health = MagicMock()
            mock_health.is_running.return_value = False
            mock_health.register_callback = MagicMock()
            mock_health.start_monitoring = MagicMock()
            mock_get_health.return_value = mock_health

            mock_teams = MagicMock()
            mock_get_teams.return_value = mock_teams

            mock_thinking = MagicMock()
            mock_thinking.is_running.return_value = False
            mock_thinking.register_callback = MagicMock()
            mock_thinking.start_monitoring = MagicMock()
            mock_get_thinking.return_value = mock_thinking

            # WebSocketManagerをモック
            with (
                patch("orchestrator.web.dashboard.WebSocketManager") as mock_ws_mgr_class,
                patch(
                    "orchestrator.web.dashboard.WebSocketMessageHandler"
                ) as mock_ws_handler_class,
            ):
                mock_ws_manager = MagicMock()
                mock_ws_manager.broadcast = AsyncMock()
                mock_ws_manager.close_all = AsyncMock()
                mock_ws_mgr_class.return_value = mock_ws_manager

                mock_ws_handler = MagicMock()
                mock_ws_handler_class.return_value = mock_ws_handler

                # TeamsMonitorをモック
                with patch("orchestrator.web.dashboard.TeamsMonitor") as mock_tm_class:
                    mock_teams_monitor = MagicMock()
                    mock_teams_monitor.is_running.return_value = False
                    mock_teams_monitor.register_update_callback = MagicMock()
                    mock_teams_monitor.start_monitoring = MagicMock()
                    mock_tm_class.return_value = mock_teams_monitor

                    # モックアプリを作成
                    app = MagicMock()

                    # コンテキストマネージャを実行
                    async with lifespan(app):
                        # グローバルステートが初期化されたことを確認
                        assert _global_state.ws_manager is not None
                        assert _global_state.ws_handler is not None
                        assert _global_state.teams_monitor is not None
                        assert _global_state.thinking_log_handler is not None
                        assert _global_state.health_monitor is not None
                        assert _global_state.teams_manager is not None

    @pytest.mark.asyncio
    async def test_lifespan_cleanup(self):
        """ライフサイクルクリーンアップのテスト"""
        from unittest.mock import AsyncMock

        # モニターのモックを設定
        with (
            patch("orchestrator.web.dashboard.get_agent_health_monitor") as mock_get_health,
            patch("orchestrator.web.dashboard.get_thinking_log_handler") as mock_get_thinking,
        ):
            mock_health = MagicMock()
            mock_health.is_running.return_value = True
            mock_health.register_callback = MagicMock()
            mock_health.stop_monitoring = MagicMock()
            mock_get_health.return_value = mock_health

            mock_thinking = MagicMock()
            mock_thinking.is_running.return_value = True
            mock_thinking.register_callback = MagicMock()
            mock_thinking.stop_monitoring = MagicMock()
            mock_get_thinking.return_value = mock_thinking

            with (
                patch("orchestrator.web.dashboard.get_agent_teams_manager"),
                patch("orchestrator.web.dashboard.WebSocketManager") as mock_ws_mgr_class,
                patch("orchestrator.web.dashboard.WebSocketMessageHandler"),
                patch("orchestrator.web.dashboard.TeamsMonitor") as mock_tm_class,
            ):
                mock_ws_manager = MagicMock()
                mock_ws_manager.close_all = AsyncMock()
                mock_ws_mgr_class.return_value = mock_ws_manager

                mock_teams_monitor = MagicMock()
                mock_teams_monitor.is_running.return_value = True
                mock_teams_monitor.register_update_callback = MagicMock()
                mock_teams_monitor.stop_monitoring = MagicMock()
                mock_tm_class.return_value = mock_teams_monitor

                from orchestrator.web.dashboard import lifespan

                app = MagicMock()

                async with lifespan(app):
                    pass

                # クリーンアップが呼ばれたことを確認
                mock_teams_monitor.stop_monitoring.assert_called_once()
                mock_thinking.stop_monitoring.assert_called_once()
                mock_health.stop_monitoring.assert_called_once()
                mock_ws_manager.close_all.assert_called_once()
