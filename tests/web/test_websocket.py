"""WebSocketエンドポイントのテスト

orchestrator/web/api/websocket.py のテストです。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.websockets import WebSocket

from orchestrator.web.api import websocket
from orchestrator.web.message_handler import WebSocketManager, WebSocketMessageHandler
from orchestrator.web.team_models import GlobalState
from orchestrator.web.teams_monitor import TeamsMonitor


@pytest.fixture
def reset_global_state():
    """各テスト前にグローバルステートをリセット"""
    original_state = websocket._global_state
    websocket._global_state = None
    yield
    websocket._global_state = original_state


class TestSetGlobalState:
    """set_global_state関数のテスト"""

    def test_set_global_state(self, reset_global_state):
        """グローバルステートを設定できること"""
        test_state = GlobalState()
        websocket.set_global_state(test_state)

        # モジュール変数が設定されたことを確認
        assert websocket._global_state is test_state


class TestGetWsManager:
    """_get_ws_manager関数のテスト"""

    def test_get_ws_manager_when_initialized(self, reset_global_state):
        """初期化済みの場合はWebSocketManagerを返す"""
        ws_manager = WebSocketManager()
        state = GlobalState(ws_manager=ws_manager)
        websocket._global_state = state

        manager = websocket._get_ws_manager()
        assert manager is ws_manager

    def test_get_ws_manager_when_not_initialized(self, reset_global_state):
        """未初期化の場合はNoneを返す"""
        manager = websocket._get_ws_manager()
        assert manager is None


class TestGetWsHandler:
    """_get_ws_handler関数のテスト"""

    def test_get_ws_handler_when_initialized(self, reset_global_state):
        """初期化済みの場合はWebSocketMessageHandlerを返す"""
        ws_manager = WebSocketManager()
        ws_handler = WebSocketMessageHandler(ws_manager)
        state = GlobalState(ws_handler=ws_handler)
        websocket._global_state = state

        handler = websocket._get_ws_handler()
        assert handler is ws_handler

    def test_get_ws_handler_when_not_initialized(self, reset_global_state):
        """未初期化の場合はNoneを返す"""
        handler = websocket._get_ws_handler()
        assert handler is None


class TestGetTeamsMonitor:
    """_get_teams_monitor関数のテスト"""

    def test_get_teams_monitor_when_initialized(self, reset_global_state):
        """初期化済みの場合はTeamsMonitorを返す"""
        teams_monitor = MagicMock(spec=TeamsMonitor)
        state = GlobalState(teams_monitor=teams_monitor)
        websocket._global_state = state

        monitor = websocket._get_teams_monitor()
        assert monitor is teams_monitor

    def test_get_teams_monitor_when_not_initialized(self, reset_global_state):
        """未初期化の場合はNoneを返す"""
        monitor = websocket._get_teams_monitor()
        assert monitor is None


class TestWebSocketEndpoint:
    """websocket_endpoint関数のテスト"""

    @pytest.mark.asyncio
    async def test_websocket_not_initialized(self, reset_global_state):
        """サーバー未初期化時は接続を拒否する"""
        mock_websocket = AsyncMock(spec=WebSocket)
        await websocket.websocket_endpoint(mock_websocket)

        # 接続が拒否されたことを確認
        mock_websocket.close.assert_called_once_with(code=1011, reason="Server not initialized")

    @pytest.mark.asyncio
    async def test_websocket_connect_and_disconnect(self, reset_global_state):
        """接続確立と切断のテスト"""
        # グローバルステートをセットアップ
        ws_manager = WebSocketManager()
        ws_handler = WebSocketMessageHandler(ws_manager)
        state = GlobalState(ws_manager=ws_manager, ws_handler=ws_handler)

        with patch.object(websocket, "_get_ws_manager", return_value=ws_manager), \
             patch.object(websocket, "_get_ws_handler", return_value=ws_handler):

            mock_websocket = MagicMock(spec=WebSocket)
            mock_websocket.client = ("127.0.0.1", 12345)
            mock_websocket.receive_text = AsyncMock(side_effect=Exception("Disconnect"))

            # WebSocketManagerのメソッドをモック
            ws_manager.connect = AsyncMock()
            ws_manager.send_personal = AsyncMock()
            ws_manager.disconnect = MagicMock()

            # WebSocketDisconnect例外をシミュレート
            from fastapi.websockets import WebSocketDisconnect
            mock_websocket.receive_text = AsyncMock(side_effect=WebSocketDisconnect())

            await websocket.websocket_endpoint(mock_websocket)

            # 接続処理が呼ばれたことを確認
            ws_manager.connect.assert_called_once()
            ws_manager.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_sends_connected_message(self, reset_global_state):
        """接続時にconnectedメッセージを送信する"""
        ws_manager = WebSocketManager()
        ws_handler = WebSocketMessageHandler(ws_manager)

        with patch.object(websocket, "_get_ws_manager", return_value=ws_manager), \
             patch.object(websocket, "_get_ws_handler", return_value=ws_handler):

            mock_websocket = MagicMock(spec=WebSocket)
            mock_websocket.client = ("127.0.0.1", 12345)

            ws_manager.connect = AsyncMock()
            ws_manager.send_personal = AsyncMock()
            ws_manager.disconnect = MagicMock()

            from fastapi.websockets import WebSocketDisconnect
            mock_websocket.receive_text = AsyncMock(side_effect=WebSocketDisconnect())

            await websocket.websocket_endpoint(mock_websocket)

            # 接続メッセージが送信されたことを確認
            assert ws_manager.send_personal.call_count >= 1

    @pytest.mark.asyncio
    async def test_websocket_sends_initial_teams_data(self, reset_global_state):
        """接続時に初期チームデータを送信する"""
        ws_manager = WebSocketManager()
        ws_handler = WebSocketMessageHandler(ws_manager)
        teams_monitor = MagicMock(spec=TeamsMonitor)
        teams_monitor.get_teams.return_value = [
            {"name": "test-team", "status": "active"}
        ]

        with patch.object(websocket, "_get_ws_manager", return_value=ws_manager), \
             patch.object(websocket, "_get_ws_handler", return_value=ws_handler), \
             patch.object(websocket, "_get_teams_monitor", return_value=teams_monitor):

            mock_websocket = MagicMock(spec=WebSocket)
            mock_websocket.client = ("127.0.0.1", 12345)

            ws_manager.connect = AsyncMock()
            ws_manager.send_personal = AsyncMock()
            ws_manager.disconnect = MagicMock()

            from fastapi.websockets import WebSocketDisconnect
            mock_websocket.receive_text = AsyncMock(side_effect=WebSocketDisconnect())

            await websocket.websocket_endpoint(mock_websocket)

            # チームデータが取得されたことを確認
            teams_monitor.get_teams.assert_called()

    @pytest.mark.asyncio
    async def test_websocket_handles_message(self, reset_global_state):
        """メッセージ受信ハンドラーのテスト"""
        from fastapi.websockets import WebSocketDisconnect

        ws_manager = WebSocketManager()
        ws_handler = WebSocketMessageHandler(ws_manager)

        with patch.object(websocket, "_get_ws_manager", return_value=ws_manager), \
             patch.object(websocket, "_get_ws_handler", return_value=ws_handler):

            mock_websocket = MagicMock(spec=WebSocket)
            mock_websocket.client = ("127.0.0.1", 12345)

            ws_manager.connect = AsyncMock()
            ws_manager.send_personal = AsyncMock()
            ws_manager.disconnect = MagicMock()

            # メッセージを受信してから切断される
            mock_websocket.receive_text = AsyncMock(
                side_effect=['{"type": "ping"}', WebSocketDisconnect()]
            )

            await websocket.websocket_endpoint(mock_websocket)

            # メッセージがハンドルされたことを確認
            # handle_messageが内部的に呼ばれるので、send_personalが呼ばれることを確認
            assert ws_manager.send_personal.call_count >= 1

    @pytest.mark.asyncio
    async def test_websocket_exception_handling(self, reset_global_state):
        """例外処理のテスト"""
        ws_manager = WebSocketManager()
        ws_handler = WebSocketMessageHandler(ws_manager)

        with patch.object(websocket, "_get_ws_manager", return_value=ws_manager), \
             patch.object(websocket, "_get_ws_handler", return_value=ws_handler):

            mock_websocket = MagicMock(spec=WebSocket)
            mock_websocket.client = ("127.0.0.1", 12345)

            ws_manager.connect = AsyncMock()
            ws_manager.send_personal = AsyncMock()
            ws_manager.disconnect = MagicMock()

            # 一般的な例外をスロー
            mock_websocket.receive_text = AsyncMock(side_effect=Exception("Test error"))

            await websocket.websocket_endpoint(mock_websocket)

            # 例外が発生しても接続がクリーンアップされることを確認
            ws_manager.disconnect.assert_called_once()
