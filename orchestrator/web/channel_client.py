"""エージェント向けチャンネル操作クライアントモジュール

このモジュールでは、エージェントが会話チャンネルに参加して
メッセージの送受信を行うためのクライアントクラスを提供します。

機能:
- チャンネルへの参加/退出
- メッセージの送信
- チャンネル一覧の取得
- チャンネル情報の取得
"""

import logging
import threading
import time
from typing import Any

from orchestrator.web.message_handler import ChannelManager

# ロガーの設定
logger = logging.getLogger(__name__)

# グローバルチャンネルマネージャーインスタンス
_channel_manager: ChannelManager | None = None
_client_instance: "ChannelClient | None" = None
_lock = threading.Lock()


class ChannelClient:
    """エージェント向けチャンネル操作クライアント

    ChannelManagerをラップして、エージェントが簡単に
    チャンネル操作を行えるようにします。

    スレッド安全性: このクラスはスレッドセーフです。
    """

    def __init__(self, channel_manager: ChannelManager) -> None:
        """ChannelClientを初期化します。

        Args:
            channel_manager: ChannelManagerインスタンス
        """
        self._manager = channel_manager
        logger.info("ChannelClientを初期化しました")

    def join_channel(
        self, channel_name: str, agent_id: str, agent_name: str
    ) -> dict[str, Any]:
        """チャンネルに参加します。

        Args:
            channel_name: チャンネル名
            agent_id: エージェントID
            agent_name: エージェント名

        Returns:
            参加結果を含む辞書
        """
        try:
            channel = self._manager.create_channel(channel_name)
            channel.join(agent_id)

            result = {
                "success": True,
                "channel": channel_name,
                "agent_id": agent_id,
                "agent_name": agent_name,
                "participants": list(channel.get_participants()),
            }

            logger.info(
                f"エージェント {agent_name}({agent_id}) がチャンネル {channel_name} に参加しました"
            )

            return result

        except ValueError as e:
            logger.error(f"チャンネル参加エラー: {e}")
            return {
                "success": False,
                "error": str(e),
                "channel": channel_name,
                "agent_id": agent_id,
            }

    def leave_channel(self, channel_name: str, agent_id: str) -> dict[str, Any]:
        """チャンネルから退出します。

        Args:
            channel_name: チャンネル名
            agent_id: エージェントID

        Returns:
            退出結果を含む辞書
        """
        try:
            channel = self._manager.get_channel(channel_name)

            if channel is None:
                return {
                    "success": False,
                    "error": f"Channel {channel_name} not found",
                    "channel": channel_name,
                    "agent_id": agent_id,
                }

            channel.leave(agent_id)

            result = {
                "success": True,
                "channel": channel_name,
                "agent_id": agent_id,
            }

            # 参加者がいなくなったらチャンネルを削除
            if not channel.get_participants():
                self._manager.delete_channel(channel_name)

            logger.info(f"エージェント {agent_id} がチャンネル {channel_name} から退出しました")

            return result

        except Exception as e:
            logger.error(f"チャンネル退出エラー: {e}")
            return {
                "success": False,
                "error": str(e),
                "channel": channel_name,
                "agent_id": agent_id,
            }

    def send_message(
        self, channel_name: str, content: str, agent_id: str, agent_name: str
    ) -> dict[str, Any]:
        """メッセージをチャンネルに送信します。

        Args:
            channel_name: チャンネル名
            content: メッセージ内容
            agent_id: エージェントID
            agent_name: エージェント名

        Returns:
            送信結果を含む辞書
        """
        try:
            channel = self._manager.get_channel(channel_name)

            if channel is None:
                return {
                    "success": False,
                    "error": f"Channel {channel_name} not found",
                    "channel": channel_name,
                    "agent_id": agent_id,
                }

            # メッセージを作成
            message = {
                "type": "channel_message",
                "channel": channel_name,
                "sender": agent_name,
                "sender_id": agent_id,
                "content": content,
                "timestamp": time.time(),
            }

            # チャンネルにメッセージを追加
            channel.add_message(message)

            result = {
                "success": True,
                "channel": channel_name,
                "message_id": f"{int(time.time() * 1000)}-{agent_id}",
                "timestamp": message["timestamp"],
            }

            logger.info(
                f"エージェント {agent_name}({agent_id}) がチャンネル {channel_name} にメッセージを送信しました: {content[:50]}..."
            )

            return result

        except Exception as e:
            logger.error(f"メッセージ送信エラー: {e}")
            return {
                "success": False,
                "error": str(e),
                "channel": channel_name,
                "agent_id": agent_id,
            }

    def list_channels(self) -> list[dict[str, Any]]:
        """チャンネル一覧を取得します。

        Returns:
            チャンネル情報のリスト
        """
        try:
            channel_names = self._manager.list_channels()
            channel_info = []

            for name in channel_names:
                ch = self._manager.get_channel(name)
                if ch:
                    channel_info.append({
                        "name": ch.channel_name,
                        "participants": list(ch.get_participants()),
                        "message_count": len(ch.get_messages()),
                    })

            return channel_info

        except Exception as e:
            logger.error(f"チャンネル一覧取得エラー: {e}")
            return []

    def get_channel_info(self, channel_name: str) -> dict[str, Any] | None:
        """チャンネル情報を取得します。

        Args:
            channel_name: チャンネル名

        Returns:
            チャンネル情報、存在しない場合はNone
        """
        try:
            channel = self._manager.get_channel(channel_name)

            if channel is None:
                return None

            return {
                "name": channel.channel_name,
                "participants": list(channel.get_participants()),
                "message_count": len(channel.get_messages()),
                "messages": channel.get_messages(limit=50),
            }

        except Exception as e:
            logger.error(f"チャンネル情報取得エラー: {e}")
            return None

    def get_channel_messages(
        self, channel_name: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """チャンネルのメッセージ履歴を取得します。

        Args:
            channel_name: チャンネル名
            limit: 取得する最大件数

        Returns:
            メッセージのリスト
        """
        try:
            channel = self._manager.get_channel(channel_name)

            if channel is None:
                return []

            return channel.get_messages(limit=limit)

        except Exception as e:
            logger.error(f"メッセージ履歴取得エラー: {e}")
            return []

    def is_participant(self, channel_name: str, agent_id: str) -> bool:
        """エージェントがチャンネルの参加者かどうかを確認します。

        Args:
            channel_name: チャンネル名
            agent_id: エージェントID

        Returns:
            参加している場合はTrue、それ以外はFalse
        """
        try:
            channel = self._manager.get_channel(channel_name)

            if channel is None:
                return False

            return agent_id in channel.get_participants()

        except Exception as e:
            logger.error(f"参加者確認エラー: {e}")
            return False


def init_channel_client(channel_manager: ChannelManager) -> ChannelClient:
    """ChannelClientを初期化します。

    この関数はアプリケーション起動時に一度だけ呼び出されます。

    Args:
        channel_manager: ChannelManagerインスタンス

    Returns:
        ChannelClientインスタンス
    """
    global _channel_manager, _client_instance

    with _lock:
        _channel_manager = channel_manager
        _client_instance = ChannelClient(channel_manager)
        logger.info("ChannelClientをグローバルに初期化しました")
        return _client_instance


def get_channel_client() -> ChannelClient | None:
    """グローバルChannelClientインスタンスを取得します。

    Returns:
        ChannelClientインスタンス、未初期化の場合はNone
    """
    return _client_instance


def reset_channel_client() -> None:
    """グローバルChannelClientインスタンスをリセットします。

    主にテスト用です。
    """
    global _channel_manager, _client_instance

    with _lock:
        _client_instance = None
        _channel_manager = None
        logger.info("ChannelClientをリセットしました")
