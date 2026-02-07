"""WebSocketルート定義

このモジュールでは、WebSocketエンドポイントを定義します。
"""

import logging

from fastapi import Query, WebSocket
from fastapi.websockets import WebSocketDisconnect

from orchestrator.web.message_handler import WebSocketManager, WebSocketMessageHandler
from orchestrator.web.team_models import GlobalState
from orchestrator.web.teams_monitor import TeamsMonitor

# ロガーの設定
logger = logging.getLogger(__name__)

# グローバルステートへのアクセサー
_global_state: GlobalState | None = None


def set_global_state(state: GlobalState) -> None:
    """グローバルステートを設定します。

    Args:
        state: グローバルステート
    """
    global _global_state
    _global_state = state


def _get_ws_manager() -> WebSocketManager | None:
    """WebSocketManagerを取得します。

    Returns:
        WebSocketManagerインスタンス、未初期化の場合はNone
    """
    return _global_state.ws_manager if _global_state else None


def _get_ws_handler() -> WebSocketMessageHandler | None:
    """WebSocketMessageHandlerを取得します。

    Returns:
        WebSocketMessageHandlerインスタンス、未初期化の場合はNone
    """
    return _global_state.ws_handler if _global_state else None


def _get_teams_monitor() -> TeamsMonitor | None:
    """TeamsMonitorを取得します。

    Returns:
        TeamsMonitorインスタンス、未初期化の場合はNone
    """
    return _global_state.teams_monitor if _global_state else None


async def websocket_endpoint(
    websocket: WebSocket,
    _token: str | None = Query(None, description="認証トークン（オプション）"),
) -> None:
    """WebSocketエンドポイント

    クライアントからの接続を受け入れ、リアルタイム更新を配信します。

    Args:
        websocket: WebSocket接続オブジェクト
        _token: 認証トークン（将来的な実装用）
    """
    ws_manager = _get_ws_manager()
    ws_handler = _get_ws_handler()

    if ws_manager is None or ws_handler is None:
        await websocket.close(code=1011, reason="Server not initialized")
        return

    await ws_manager.connect(websocket)

    try:
        # 接続確立メッセージを送信
        await ws_manager.send_personal(
            {
                "type": "connected",
                "message": "Connected to Orchestrator CC Dashboard",
            },
            websocket,
        )

        # 初期システムログを送信
        await ws_manager.send_personal(
            {
                "type": "system_log",
                "timestamp": None,
                "level": "info",
                "content": "ダッシュボードに接続しました",
            },
            websocket,
        )

        # 初期チームデータを送信
        teams_monitor = _get_teams_monitor()
        if teams_monitor:
            teams = teams_monitor.get_teams()
            await ws_manager.send_personal(
                {
                    "type": "teams",
                    "teams": teams,
                },
                websocket,
            )
            await ws_manager.send_personal(
                {
                    "type": "system_log",
                    "timestamp": None,
                    "level": "info",
                    "content": f"チーム状態: {len(teams)} チーム稼働中",
                },
                websocket,
            )

        # メッセージ受信ループ
        while True:
            message = await websocket.receive_text()
            await ws_handler.handle_message(message, websocket)

    except WebSocketDisconnect:
        logger.info(f"WebSocket接続が切断されました: {websocket.client}")
    except Exception as e:
        logger.error(f"WebSocketエラーが発生: {e}")
    finally:
        # 接続クリーンアップ
        ws_manager.disconnect(websocket)
