"""WebSocketルート定義

このモジュールでは、WebSocketエンドポイントを定義します。
"""

import logging
from typing import Any

from fastapi import Query, WebSocket
from fastapi.websockets import WebSocketDisconnect

from orchestrator.web.message_handler import (
    ChannelManager,
    WebSocketManager,
    WebSocketMessageHandler,
)
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


def _get_channel_manager() -> ChannelManager | None:
    """ChannelManagerを取得します。

    Returns:
        ChannelManagerインスタンス、未初期化の場合はNone
    """
    return _global_state.channel_manager if _global_state else None


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


# ============================================================================
# チャンネル関連ハンドラー関数
# ============================================================================


async def handle_join_channel(
    websocket: WebSocket,
    message: dict[str, Any],
    _handler: WebSocketMessageHandler,
) -> None:
    """チャンネル参加リクエストを処理します。

    Args:
        websocket: WebSocket接続オブジェクト
        message: メッセージデータ
        handler: WebSocketメッセージハンドラー
    """
    channel_name = message.get("channel")
    if not channel_name:
        await websocket.send_json(
            {"type": "error", "message": "Channel name is required"}
        )
        return

    channel_manager = _get_channel_manager()
    if not channel_manager:
        await websocket.send_json(
            {"type": "error", "message": "Channel manager not available"}
        )
        return

    # ChannelManagerからチャンネルを取得または作成
    channel = channel_manager.create_channel(channel_name)
    agent_id = message.get("agent_id", "unknown")
    channel.join(agent_id)

    await websocket.send_json(
        {
            "type": "channel_joined",
            "channel": channel_name,
            "agent_id": agent_id,
            "participants": list(channel.get_participants()),
        }
    )


async def handle_leave_channel(
    websocket: WebSocket,
    message: dict[str, Any],
    _handler: WebSocketMessageHandler,
) -> None:
    """チャンネル退出リクエストを処理します。

    Args:
        websocket: WebSocket接続オブジェクト
        message: メッセージデータ
        handler: WebSocketメッセージハンドラー
    """
    channel_name = message.get("channel")
    if not channel_name:
        await websocket.send_json(
            {"type": "error", "message": "Channel name is required"}
        )
        return

    channel_manager = _get_channel_manager()
    if not channel_manager:
        await websocket.send_json(
            {"type": "error", "message": "Channel manager not available"}
        )
        return

    channel = channel_manager.get_channel(channel_name)
    if channel:
        agent_id = message.get("agent_id", "unknown")
        channel.leave(agent_id)

        await websocket.send_json(
            {
                "type": "channel_left",
                "channel": channel_name,
                "agent_id": agent_id,
            }
        )


async def handle_channel_message(
    websocket: WebSocket,
    message: dict[str, Any],
    _handler: WebSocketMessageHandler,
) -> None:
    """チャンネル内メッセージを処理します。

    Args:
        websocket: WebSocket接続オブジェクト
        message: メッセージデータ
        handler: WebSocketメッセージハンドラー
    """
    channel_name = message.get("channel")
    if not channel_name:
        await websocket.send_json(
            {"type": "error", "message": "Channel name is required"}
        )
        return

    channel_manager = _get_channel_manager()
    if not channel_manager:
        await websocket.send_json(
            {"type": "error", "message": "Channel manager not available"}
        )
        return

    channel = channel_manager.get_channel(channel_name)
    if channel:
        # メッセージをチャンネルに追加
        channel.add_message(message)
        # チャンネル内にブロードキャスト
        ws_manager = _get_ws_manager()
        if ws_manager:
            await channel.broadcast(message, ws_manager)


async def handle_list_channels(
    websocket: WebSocket,
    _message: dict[str, Any],
    _handler: WebSocketMessageHandler,
) -> None:
    """チャンネル一覧を返します。

    Args:
        websocket: WebSocket接続オブジェクト
        message: メッセージデータ
        handler: WebSocketメッセージハンドラー
    """
    channel_manager = _get_channel_manager()
    if not channel_manager:
        await websocket.send_json(
            {"type": "error", "message": "Channel manager not available"}
        )
        return

    channels = channel_manager.list_channels()
    channel_info = []
    for name in channels:
        ch = channel_manager.get_channel(name)
        if ch:
            channel_info.append(
                {
                    "name": ch.channel_name,
                    "participants": list(ch.get_participants()),
                    "message_count": len(ch.get_messages()),
                }
            )

    await websocket.send_json(
        {
            "type": "channels_list",
            "channels": channel_info,
        }
    )
