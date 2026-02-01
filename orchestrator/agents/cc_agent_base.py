"""エージェント基底クラス

このモジュールでは、全エージェントで使用する基底クラスCCAgentBaseを定義します。
"""

from abc import ABC, abstractmethod
from typing import Final

from orchestrator.core.cc_cluster_manager import (
    CCClusterAgentNotFoundError,
    CCClusterManager,
)
from orchestrator.core.message_logger import LogLevel, MessageLogger, MessageType
from orchestrator.core.pane_io import PaneTimeoutError


# 例外クラス
class CCAgentError(Exception):
    """エージェントに関する基本例外クラス"""
    pass


class CCAgentSendError(CCAgentError):
    """メッセージ送信失敗時の例外"""
    pass


class CCAgentTimeoutError(CCAgentError):
    """応答タイムアウト時の例外"""
    pass


# 定数
DEFAULT_TIMEOUT: Final[float] = 30.0  # デフォルトタイムアウト（秒）


class CCAgentBase(ABC):
    """エージェントの基底クラス

    全エージェント共通の機能を提供します：
    - 他エージェントへのメッセージ送信（send_to）
    - 応答取得（合言葉検出）
    - ログ記録（MessageLogger経由）

    Attributes:
        _name: エージェント名（例: "grand_boss"）
        _cluster_manager: CCClusterManagerインスタンス
        _logger: MessageLoggerインスタンス
        _default_timeout: デフォルトのタイムアウト時間（秒）
    """

    def __init__(
        self,
        name: str,
        cluster_manager: CCClusterManager,
        logger: MessageLogger | None = None,
        default_timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """CCAgentBaseを初期化します。

        Args:
            name: エージェント名（設定ファイルのnameと一致させる必要あり）
            cluster_manager: CCClusterManagerインスタンス
            logger: MessageLoggerインスタンス（Noneの場合は新規作成）
            default_timeout: デフォルトのタイムアウト時間（秒）

        Raises:
            TypeError: cluster_managerがCCClusterManagerでない場合
            ValueError: nameが空の場合、またはdefault_timeoutが負の値の場合
        """
        if not isinstance(cluster_manager, CCClusterManager):
            raise TypeError("cluster_managerはCCClusterManagerのインスタンスである必要があります")

        if not name:
            raise ValueError("nameは空であってはなりません")
        if default_timeout <= 0:
            raise ValueError("default_timeoutは正の値である必要があります")

        self._name: str = name
        self._cluster_manager: CCClusterManager = cluster_manager
        self._logger: MessageLogger = logger or MessageLogger()
        self._default_timeout: float = default_timeout

    @abstractmethod
    async def handle_task(self, task: str) -> str:
        """タスクを処理します。

        サブクラスで実装する必要がある抽象メソッドです。
        各エージェントの固有の処理をここに記述します。

        Args:
            task: タスク内容

        Returns:
            処理結果
        """
        # サブクラスで実装

    async def send_to(
        self,
        to_agent: str,
        message: str,
        msg_type: MessageType = MessageType.TASK,
        timeout: float | None = None,
    ) -> str:
        """他エージェントにメッセージを送信し、応答を取得します。

        Args:
            to_agent: 送信先エージェント名
            message: 送信するメッセージ
            msg_type: メッセージタイプ（デフォルト: TASK）
            timeout: タイムアウト時間（秒）。Noneの場合はdefault_timeoutを使用

        Returns:
            送信先エージェントからの応答

        Raises:
            CCAgentSendError: メッセージ送信に失敗した場合
            CCAgentTimeoutError: 応答がタイムアウトした場合
            CCClusterAgentNotFoundError: 指定されたエージェントが存在しない場合
            ValueError: to_agentまたはmessageが空の場合
        """
        if not to_agent:
            raise ValueError("to_agentは空であってはなりません")
        if not message:
            raise ValueError("messageは空であってはなりません")

        actual_timeout = timeout if timeout is not None else self._default_timeout

        # 送信ログを記録
        self._logger.log_send(
            from_agent=self._name,
            to_agent=to_agent,
            content=message,
            msg_type=msg_type,
            log_level=LogLevel.INFO,
        )

        try:
            # CCClusterManager経由でメッセージ送信・応答取得
            response = await self._cluster_manager.send_message(
                agent_name=to_agent,
                message=message,
                timeout=actual_timeout,
            )
        except CCClusterAgentNotFoundError:
            # エージェントが見つからない場合はそのまま再送出
            raise
        except PaneTimeoutError as e:
            # タイムアウトをCCAgentTimeoutErrorに変換
            raise CCAgentTimeoutError(
                f"エージェント '{to_agent}' からの応答がタイムアウトしました "
                f"(timeout={actual_timeout}秒): {e}"
            ) from e
        except Exception as e:
            # その他の例外をCCAgentSendErrorに変換
            raise CCAgentSendError(
                f"エージェント '{to_agent}' へのメッセージ送信に失敗しました: {e}"
            ) from e

        # 受信ログを記録
        self._logger.log_receive(
            from_agent=to_agent,
            to_agent=self._name,
            content=response,
            msg_type=MessageType.RESULT,
            log_level=LogLevel.INFO,
        )

        return response

    def _get_name(self) -> str:
        """エージェント名を取得します。

        Returns:
            エージェント名
        """
        return self._name
