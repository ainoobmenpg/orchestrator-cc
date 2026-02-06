"""WebSocketメッセージハンドラモジュール

このモジュールでは、WebSocket接続の管理とメッセージ処理を提供します。

機能:
- WebSocket接続の管理
- クライアント登録・削除
- メッセージのルーティング
- ブロードキャスト
"""

import json
import logging
from contextlib import suppress
from typing import Any

from fastapi import WebSocket

# ロガーの設定
logger = logging.getLogger(__name__)


class WebSocketManager:
    """WebSocket接続管理クラス

    複数のWebSocket接続を管理し、メッセージのブロードキャストや
    個別送信を行います。

    Attributes:
        _active_connections: アクティブなWebSocket接続のリスト
    """

    def __init__(self) -> None:
        """WebSocketManagerを初期化します。"""
        self._active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """新しい接続を受け入れます。

        Args:
            websocket: WebSocket接続オブジェクト
        """
        await websocket.accept()
        self._active_connections.append(websocket)
        logger.info(f"WebSocket接続を確立しました: {websocket.client}")

    def disconnect(self, websocket: WebSocket) -> None:
        """接続を削除します。

        Args:
            websocket: WebSocket接続オブジェクト
        """
        if websocket in self._active_connections:
            self._active_connections.remove(websocket)
            logger.info(f"WebSocket接続を解除しました: {websocket.client}")

    async def send_personal(self, message: dict[str, Any], websocket: WebSocket) -> None:
        """特定のクライアントにメッセージを送信します。

        Args:
            message: 送信するメッセージ（辞書形式）
            websocket: 送信先のWebSocket接続
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"個別メッセージ送信でエラーが発生: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        """全クライアントにメッセージをブロードキャストします。

        Args:
            message: 送信するメッセージ（辞書形式）
        """
        disconnected = []
        for connection in self._active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"ブロードキャストでエラーが発生: {e}")
                disconnected.append(connection)

        # 切断された接続を削除
        for connection in disconnected:
            self.disconnect(connection)

    async def broadcast_text(self, message: str) -> None:
        """全クライアントにテキストメッセージをブロードキャストします。

        Args:
            message: 送信するテキストメッセージ
        """
        disconnected = []
        for connection in self._active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"テキストブロードキャストでエラーが発生: {e}")
                disconnected.append(connection)

        # 切断された接続を削除
        for connection in disconnected:
            self.disconnect(connection)

    def get_connection_count(self) -> int:
        """現在の接続数を取得します。

        Returns:
            アクティブな接続数
        """
        return len(self._active_connections)

    def get_connections(self) -> list[WebSocket]:
        """全てのアクティブな接続を取得します。

        Returns:
            アクティブなWebSocket接続のリスト
        """
        return self._active_connections.copy()

    async def close_all(self) -> None:
        """全ての接続を閉じます。"""
        for connection in self._active_connections:
            with suppress(Exception):
                await connection.close()
        self._active_connections.clear()
        logger.info("全てのWebSocket接続を閉じました")


class WebSocketMessageHandler:
    """WebSocketメッセージハンドラクラス

    受信したメッセージを解析して適切な処理を実行します。

    Attributes:
        _manager: WebSocketManagerインスタンス
    """

    def __init__(self, manager: WebSocketManager) -> None:
        """WebSocketMessageHandlerを初期化します。

        Args:
            manager: WebSocketManagerインスタンス
        """
        self._manager = manager
        self._handlers: dict[str, Any] = {
            "ping": self._handle_ping,
            "subscribe": self._handle_subscribe,
            "unsubscribe": self._handle_unsubscribe,
            "get_status": self._handle_get_status,
        }

    async def handle_message(self, message: str, websocket: WebSocket) -> None:
        """受信したメッセージを処理します。

        Args:
            message: 受信したメッセージ（JSON文字列）
            websocket: 送信元のWebSocket接続
        """
        try:
            data = json.loads(message)
            message_type = data.get("type")

            if message_type in self._handlers:
                await self._handlers[message_type](data, websocket)
            else:
                await self._manager.send_personal(
                    {"type": "error", "message": f"Unknown message type: {message_type}"}, websocket
                )

        except json.JSONDecodeError:
            await self._manager.send_personal(
                {"type": "error", "message": "Invalid JSON format"}, websocket
            )
        except Exception as e:
            logger.error(f"メッセージ処理でエラーが発生: {e}")
            await self._manager.send_personal({"type": "error", "message": str(e)}, websocket)

    async def _handle_ping(self, data: dict[str, Any], websocket: WebSocket) -> None:
        """pingメッセージを処理します。

        Args:
            data: メッセージデータ
            websocket: WebSocket接続
        """
        await self._manager.send_personal(
            {"type": "pong", "timestamp": data.get("timestamp")}, websocket
        )

    async def _handle_subscribe(self, data: dict[str, Any], websocket: WebSocket) -> None:
        """subscribeメッセージを処理します。

        Args:
            data: メッセージデータ
            websocket: WebSocket接続
        """
        # 将来的にサブスクリプション管理を追加
        await self._manager.send_personal(
            {"type": "subscribed", "channels": data.get("channels", [])}, websocket
        )

    async def _handle_unsubscribe(self, data: dict[str, Any], websocket: WebSocket) -> None:
        """unsubscribeメッセージを処理します。

        Args:
            data: メッセージデータ
            websocket: WebSocket接続
        """
        # 将来的にサブスクリプション管理を追加
        await self._manager.send_personal(
            {"type": "unsubscribed", "channels": data.get("channels", [])}, websocket
        )

    async def _handle_get_status(self, _data: dict[str, Any], websocket: WebSocket) -> None:
        """get_statusメッセージを処理します。

        Args:
            _data: メッセージデータ（未使用）
            websocket: WebSocket接続
        """
        # これは外部から注入される関数で処理する
        # デフォルトでは接続数を返す
        await self._manager.send_personal(
            {
                "type": "status",
                "data": {
                    "connection_count": self._manager.get_connection_count(),
                },
            },
            websocket,
        )

    def set_status_handler(self, handler: Any) -> None:
        """ステータスハンドラを設定します。

        Args:
            handler: ステータス取得用ハンドラ関数
        """
        self._handlers["get_status"] = handler

    def set_team_message_handler(self, handler: Any) -> None:
        """チームメッセージハンドラを設定します。

        Args:
            handler: チームメッセージ取得用ハンドラ関数
        """
        self._handlers["get_teams"] = handler
