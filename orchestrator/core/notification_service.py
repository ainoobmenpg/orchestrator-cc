"""通知サービスモジュール

このモジュールでは、エージェントへの通知機能を提供します。
tmuxを通じて各ペインのClaude Codeプロセスに通知を送信します。
"""

from typing import Final

from orchestrator.core.tmux_session_manager import TmuxSessionManager

# 定数
DEFAULT_NOTIFY_MESSAGE: Final[str] = "/check-yaml"  # YAMLチェックを促すコマンド


class NotificationService:
    """通知サービスクラス

    tmuxを通じて各エージェント（ペイン）に通知を送信します。
    """

    def __init__(self, session_name: str) -> None:
        """NotificationServiceを初期化します。

        Args:
            session_name: tmuxセッション名
        """
        self._tmux = TmuxSessionManager(session_name)

    def notify_agent(
        self,
        pane_index: int,
        message: str = DEFAULT_NOTIFY_MESSAGE,
        send_enter: bool = True,
    ) -> None:
        """エージェントに通知を送信します。

        Args:
            pane_index: 通知先のペイン番号
            message: 送信するメッセージ（デフォルト: "/check-yaml"）
            send_enter: Enterキーを送信するかどうか（デフォルト: True）
        """
        self._tmux.send_keys(pane_index, message)
        if send_enter:
            self._tmux.send_keys(pane_index, "Enter")

    def notify_multiple_agents(
        self,
        pane_indices: list[int],
        message: str = DEFAULT_NOTIFY_MESSAGE,
        send_enter: bool = True,
    ) -> None:
        """複数のエージェントに通知を送信します。

        Args:
            pane_indices: 通知先のペイン番号のリスト
            message: 送信するメッセージ（デフォルト: "/check-yaml"）
            send_enter: Enterキーを送信するかどうか（デフォルト: True）
        """
        for pane_index in pane_indices:
            self.notify_agent(pane_index, message, send_enter)

    def broadcast(
        self,
        message: str = DEFAULT_NOTIFY_MESSAGE,
        send_enter: bool = True,
    ) -> None:
        """全エージェントにブロードキャストします。

        Args:
            message: 送信するメッセージ（デフォルト: "/check-yaml"）
            send_enter: Enterキーを送信するかどうか（デフォルト: True）
        """
        # すべてのペイン（0〜4）に通知
        for pane_index in range(5):
            try:
                self.notify_agent(pane_index, message, send_enter)
            except Exception:
                # ペインが存在しない場合はスキップ
                pass

    def send_custom_command(
        self,
        pane_index: int,
        command: str,
    ) -> None:
        """カスタムコマンドを送信します。

        Args:
            pane_index: 送信先のペイン番号
            command: 送信するコマンド
        """
        self._tmux.send_keys(pane_index, command)
        self._tmux.send_keys(pane_index, "Enter")
