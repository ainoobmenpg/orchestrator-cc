"""WebSocketメッセージハンドラモジュール

このモジュールでは、WebSocket接続の管理とメッセージ処理を提供します。

機能:
- WebSocket接続の管理
- クライアント登録・削除
- メッセージのルーティング
- ブロードキャスト
- 会話チャンネル管理
"""

import json
import logging
import re
import threading
from contextlib import suppress
from typing import Any

from fastapi import WebSocket

# ロガーの設定
logger = logging.getLogger(__name__)


# ============================================================================
# チャンネル名検証
# ============================================================================

# チャンネル名の正規表現: 英数字、ハイフン、アンダースコアのみ（1-50文字）
CHANNEL_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,50}$")


def validate_channel_name(channel_name: str) -> bool:
    """チャンネル名を検証します。

    Args:
        channel_name: チャンネル名

    Returns:
        有効な場合はTrue、無効な場合はFalse

    検証ルール:
    - 1〜50文字であること
    - 英数字（a-z, A-Z, 0-9）、ハイフン（-）、アンダースコア（_）のみ使用可能
    """
    if not isinstance(channel_name, str):
        return False
    return bool(CHANNEL_NAME_PATTERN.match(channel_name))


# ============================================================================
# 会話チャンネルクラス
# ============================================================================

class ConversationChannel:
    """会話チャンネルクラス

    チーム内のエージェント同士が会話するための共有スペースです。

    スレッド安全性: メッセージ追加操作はロックで保護されています。
    """

    def __init__(self, channel_name: str) -> None:
        """会話チャンネルを初期化します。

        Args:
            channel_name: チャンネル名
        """
        self.channel_name = channel_name
        self.participants: set[str] = set()
        self.messages: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def join(self, agent_id: str) -> None:
        """エージェントをチャンネルに参加させます。

        Args:
            agent_id: エージェントID
        """
        self.participants.add(agent_id)
        logger.info(f"エージェント {agent_id} がチャンネル {self.channel_name} に参加しました")

    def leave(self, agent_id: str) -> None:
        """エージェントをチャンネルから退出させます。

        Args:
            agent_id: エージェントID
        """
        self.participants.discard(agent_id)
        logger.info(f"エージェント {agent_id} がチャンネル {self.channel_name} から退出しました")

    async def broadcast(self, message: dict[str, Any], ws_manager: "WebSocketManager") -> None:
        """チャンネル内にメッセージをブロードキャストします。

        Args:
            message: メッセージデータ
            ws_manager: WebSocketマネージャー
        """
        message["channel"] = self.channel_name
        await ws_manager.broadcast(message)

    def add_message(self, message: dict[str, Any]) -> None:
        """メッセージをチャンネル履歴に追加します。

        スレッド安全: ロックを使用して競合を防ぎます。

        Args:
            message: メッセージデータ
        """
        with self._lock:
            self.messages.append(message)
            # 最大100件のメッセージを保持
            if len(self.messages) > 100:
                self.messages.pop(0)

    def get_participants(self) -> set[str]:
        """参加者リストを取得します。

        Returns:
            参加者IDのセット
        """
        return self.participants.copy()

    def get_messages(self, limit: int = 50) -> list[dict[str, Any]]:
        """メッセージ履歴を取得します。

        Args:
            limit: 取得する最大件数

        Returns:
            メッセージリスト
        """
        return self.messages[-limit:]


class ChannelManager:
    """チャンネルマネージャークラス

    複数の会話チャンネルを管理します。
    """

    def __init__(self) -> None:
        """チャンネルマネージャーを初期化します。"""
        self.channels: dict[str, ConversationChannel] = {}

    def create_channel(self, channel_name: str) -> ConversationChannel:
        """新しいチャンネルを作成します。

        Args:
            channel_name: チャンネル名

        Returns:
            作成されたチャンネル

        Raises:
            ValueError: チャンネル名が無効な場合
        """
        if not validate_channel_name(channel_name):
            raise ValueError(
                f"Invalid channel name: '{channel_name}'. "
                "Channel names must be 1-50 characters, containing only letters, numbers, hyphens, and underscores."
            )

        if channel_name in self.channels:
            return self.channels[channel_name]

        channel = ConversationChannel(channel_name)
        self.channels[channel_name] = channel
        logger.info(f"チャンネル {channel_name} を作成しました")
        return channel

    def get_channel(self, channel_name: str) -> ConversationChannel | None:
        """チャンネルを取得します。

        Args:
            channel_name: チャンネル名

        Returns:
            チャンネル、存在しない場合はNone
        """
        return self.channels.get(channel_name)

    def delete_channel(self, channel_name: str) -> bool:
        """チャンネルを削除します。

        Args:
            channel_name: チャンネル名

        Returns:
            削除成功の場合True、失敗の場合False
        """
        if channel_name in self.channels:
            del self.channels[channel_name]
            logger.info(f"チャンネル {channel_name} を削除しました")
            return True
        return False

    def list_channels(self) -> list[str]:
        """全チャンネル名を取得します。

        Returns:
            チャンネル名のリスト
        """
        return list(self.channels.keys())


class WebSocketManager:
    """WebSocket接続管理クラス

    複数のWebSocket接続を管理し、メッセージのブロードキャストや
    個別送信を行います。

    Attributes:
        active_connections: アクティブなWebSocket接続のリスト
    """

    def __init__(self) -> None:
        """WebSocketManagerを初期化します。"""
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """新しい接続を受け入れます。

        Args:
            websocket: WebSocket接続オブジェクト
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket接続を確立しました: {websocket.client}")

    def disconnect(self, websocket: WebSocket) -> None:
        """接続を削除します。

        Args:
            websocket: WebSocket接続オブジェクト
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
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
        for connection in self.active_connections:
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
        for connection in self.active_connections:
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
        return len(self.active_connections)

    def get_connections(self) -> list[WebSocket]:
        """全てのアクティブな接続を取得します。

        Returns:
            アクティブなWebSocket接続のリスト
        """
        return self.active_connections.copy()

    async def close_all(self) -> None:
        """全ての接続を閉じます。"""
        for connection in self.active_connections:
            with suppress(Exception):
                await connection.close()
        self.active_connections.clear()
        logger.info("全てのWebSocket接続を閉じました")


class WebSocketMessageHandler:
    """WebSocketメッセージハンドラクラス

    受信したメッセージを解析して適切な処理を実行します。

    Attributes:
        _manager: WebSocketManagerインスタンス
    """

    def __init__(
        self,
        manager: WebSocketManager,
        channel_manager: ChannelManager | None = None,
    ) -> None:
        """WebSocketMessageHandlerを初期化します。

        Args:
            manager: WebSocketManagerインスタンス
            channel_manager: ChannelManagerインスタンス（オプション）
        """
        self._manager = manager
        self._channel_manager = channel_manager
        self._handlers: dict[str, Any] = {
            "ping": self._handle_ping,
            "subscribe": self._handle_subscribe,
            "unsubscribe": self._handle_unsubscribe,
            "get_status": self._handle_get_status,
            "channel_message": self._handle_channel_message,
            "join_channel": self._handle_join_channel,
            "leave_channel": self._handle_leave_channel,
            "list_channels": self._handle_list_channels,
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

    async def _handle_channel_message(self, data: dict[str, Any], websocket: WebSocket) -> None:
        """チャンネルメッセージを処理します。

        Args:
            data: メッセージデータ
            websocket: WebSocket接続
        """
        if self._channel_manager is None:
            await self._manager.send_personal(
                {"type": "error", "message": "Channel manager not available"}, websocket
            )
            return

        channel_name = data.get("channel")
        if not channel_name:
            await self._manager.send_personal(
                {"type": "error", "message": "Channel name is required"}, websocket
            )
            return

        channel = self._channel_manager.get_channel(channel_name)
        if not channel:
            await self._manager.send_personal(
                {"type": "error", "message": f"Channel {channel_name} not found"}, websocket
            )
            return

        # メッセージをチャンネルに追加してブロードキャスト
        message = {
            "type": "channel_message",
            "channel": channel_name,
            "sender": data.get("sender", "unknown"),
            "content": data.get("content", ""),
            "timestamp": data.get("timestamp"),
        }
        channel.add_message(message)
        await channel.broadcast(message, self._manager)

    async def _handle_join_channel(self, data: dict[str, Any], websocket: WebSocket) -> None:
        """チャンネル参加メッセージを処理します。

        Args:
            data: メッセージデータ
            websocket: WebSocket接続
        """
        if self._channel_manager is None:
            await self._manager.send_personal(
                {"type": "error", "message": "Channel manager not available"}, websocket
            )
            return

        channel_name = data.get("channel")
        agent_id = data.get("agent_id")

        if not channel_name:
            await self._manager.send_personal(
                {"type": "error", "message": "Channel name is required"}, websocket
            )
            return

        if not agent_id:
            await self._manager.send_personal(
                {"type": "error", "message": "Agent ID is required"}, websocket
            )
            return

        # チャンネルを取得または作成
        channel = self._channel_manager.get_channel(channel_name)
        if not channel:
            channel = self._channel_manager.create_channel(channel_name)

        # 参加者を追加
        channel.join(agent_id)

        # 参加成功を通知
        await self._manager.send_personal(
            {
                "type": "channel_joined",
                "channel": channel_name,
                "agent_id": agent_id,
                "participants": list(channel.get_participants()),
            },
            websocket,
        )

        # 他の参加者に通知
        await self._manager.broadcast(
            {
                "type": "participant_joined",
                "channel": channel_name,
                "agent_id": agent_id,
            }
        )

    async def _handle_leave_channel(self, data: dict[str, Any], websocket: WebSocket) -> None:
        """チャンネル退出メッセージを処理します。

        Args:
            data: メッセージデータ
            websocket: WebSocket接続
        """
        if self._channel_manager is None:
            await self._manager.send_personal(
                {"type": "error", "message": "Channel manager not available"}, websocket
            )
            return

        channel_name = data.get("channel")
        agent_id = data.get("agent_id")

        if not channel_name:
            await self._manager.send_personal(
                {"type": "error", "message": "Channel name is required"}, websocket
            )
            return

        if not agent_id:
            await self._manager.send_personal(
                {"type": "error", "message": "Agent ID is required"}, websocket
            )
            return

        channel = self._channel_manager.get_channel(channel_name)
        if not channel:
            await self._manager.send_personal(
                {"type": "error", "message": f"Channel {channel_name} not found"}, websocket
            )
            return

        # 参加者を削除
        channel.leave(agent_id)

        # 退出成功を通知
        await self._manager.send_personal(
            {
                "type": "channel_left",
                "channel": channel_name,
                "agent_id": agent_id,
            },
            websocket,
        )

        # 他の参加者に通知
        await self._manager.broadcast(
            {
                "type": "participant_left",
                "channel": channel_name,
                "agent_id": agent_id,
            }
        )

        # 参加者がいなくなったらチャンネルを削除
        if not channel.get_participants():
            self._channel_manager.delete_channel(channel_name)

    async def _handle_list_channels(self, _data: dict[str, Any], websocket: WebSocket) -> None:
        """チャンネル一覧メッセージを処理します。

        Args:
            _data: メッセージデータ（未使用）
            websocket: WebSocket接続
        """
        if self._channel_manager is None:
            await self._manager.send_personal(
                {"type": "error", "message": "Channel manager not available"}, websocket
            )
            return

        channel_names = self._channel_manager.list_channels()
        channel_info = []
        for name in channel_names:
            ch = self._channel_manager.get_channel(name)
            if ch:
                channel_info.append({
                    "name": ch.channel_name,
                    "participants": list(ch.get_participants()),
                    "message_count": len(ch.get_messages()),
                })

        await self._manager.send_personal(
            {
                "type": "channels_list",
                "channels": channel_info,
            },
            websocket,
        )
