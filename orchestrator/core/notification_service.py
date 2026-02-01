"""通知サービスモジュール

このモジュールでは、YAML更新時にエージェントへ通知するサービスを提供します。
tmux send-keysを使用して各エージェントのペインに通知を送信します。
"""

import logging
from pathlib import Path

from orchestrator.core.tmux_session_manager import TmuxSessionManager
from orchestrator.core.yaml_protocol import TaskMessage, TaskStatus

logger = logging.getLogger(__name__)


class NotificationService:
    """エージェント通知サービス

    YAMLファイルの更新時に、tmux send-keysを使用して各エージェントに通知を送信します。
    """

    # エージェント名とtmuxペイン番号のマッピング
    AGENT_PANES = {
        "grand_boss": 0,
        "middle_manager": 1,
        "coding_writing_specialist": 2,
        "research_analysis_specialist": 3,
        "testing_specialist": 4,
    }

    def __init__(self, tmux_manager: TmuxSessionManager) -> None:
        """NotificationServiceを初期化します。

        Args:
            tmux_manager: TmuxSessionManagerインスタンス
        """
        self._tmux = tmux_manager

    def notify_agent(self, message: TaskMessage, queue_file: Path) -> None:
        """エージェントに通知を送信します。

        Args:
            message: タスクメッセージ
            queue_file: メッセージが含まれるYAMLファイルパス

        Raises:
            ValueError: 宛先エージェントが不明な場合
        """
        to_agent = message.to_agent

        # ペイン番号を取得
        if to_agent not in self.AGENT_PANES:
            raise ValueError(f"不明なエージェント: {to_agent}")

        pane_index = self.AGENT_PANES[to_agent]

        # 通知メッセージを構築
        notification = self._build_notification(message, queue_file)

        logger.info(
            f"エージェントに通知を送信: {to_agent} (pane={pane_index}) - "
            f"{message.type.value} from {message.from_agent}"
        )

        # tmux send-keysで通知を送信
        try:
            # Enterキーを押してメッセージを送信
            self._tmux.send_keys(pane_index, notification)
            self._tmux.send_keys(pane_index, "Enter")
        except Exception as e:
            logger.error(f"通知の送信に失敗しました: {e}")

    def _build_notification(self, message: TaskMessage, queue_file: Path) -> str:
        """通知メッセージを構築します。

        Args:
            message: タスクメッセージ
            queue_file: メッセージが含まれるYAMLファイルパス

        Returns:
            通知メッセージ文字列
        """
        # ファイルパスを相対パスに変換（見やすくするため）
        try:
            rel_path = queue_file.relative_to(Path.cwd())
        except ValueError:
            rel_path = queue_file

        status_emoji = self._get_status_emoji(message.status)
        type_emoji = self._get_type_emoji(message.type)

        notification = f"\n{status_emoji} 新しいメッセージがあります {type_emoji}\n"
        notification += f"送信元: {message.from_agent}\n"
        notification += f"ファイル: {rel_path}\n"

        if message.type.value == "task" and message.status == TaskStatus.PENDING:
            notification += "\nタスク内容を確認してください。\n"
            notification += "完了したら、対応するYAMLファイルの status を 'completed' に更新してください。\n"

        return notification

    def _get_status_emoji(self, status: TaskStatus) -> str:
        """ステータスに対応する絵文字を取得します。

        Args:
            status: タスクステータス

        Returns:
            絵文字文字列
        """
        emoji_map = {
            TaskStatus.PENDING: "📥",
            TaskStatus.IN_PROGRESS: "⏳",
            TaskStatus.COMPLETED: "✅",
            TaskStatus.FAILED: "❌",
        }
        return emoji_map.get(status, "📨")

    def _get_type_emoji(self, msg_type) -> str:
        """メッセージタイプに対応する絵文字を取得します。

        Args:
            msg_type: メッセージタイプ

        Returns:
            絵文字文字列
        """
        from orchestrator.core.yaml_protocol import MessageType

        emoji_map = {
            MessageType.TASK: "📋",
            MessageType.INFO: "ℹ️",
            MessageType.RESULT: "📤",
            MessageType.ERROR: "⚠️",
        }
        return emoji_map.get(msg_type, "📨")

    def notify_all_agents(self, message: str) -> None:
        """全エージェントに通知を送信します。

        Args:
            message: 通知メッセージ
        """
        logger.info(f"全エージェントに通知を送信: {message}")

        for agent_name, pane_index in self.AGENT_PANES.items():
            try:
                self._tmux.send_keys(pane_index, message)
                self._tmux.send_keys(pane_index, "Enter")
            except Exception as e:
                logger.error(f"エージェント {agent_name} への通知送信に失敗しました: {e}")

    def notify_dashboard_update(self) -> None:
        """ダッシュボードの更新を通知します。

        全エージェントにダッシュボードが更新されたことを通知します。
        """
        notification = "\n📊 ダッシュボードが更新されました\n"
        notification += "status/dashboard.md を確認してください。\n"

        self.notify_all_agents(notification)


class NotificationError(Exception):
    """通知エラー"""

    pass


class AgentNotFoundError(NotificationError):
    """エージェントが見つからない場合のエラー"""

    pass


class TmuxSendError(NotificationError):
    """tmux send-keys 送信エラー"""

    pass
