"""エージェント基底クラス

このモジュールでは、全エージェントで使用する基底クラスCCAgentBaseを定義します。
"""

import asyncio
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Final

from orchestrator.core.cc_cluster_manager import (
    CCClusterAgentNotFoundError,
    CCClusterManager,
)
from orchestrator.core.message_logger import LogLevel, MessageLogger, MessageType
from orchestrator.core.pane_io import PaneTimeoutError
from orchestrator.core.yaml_protocol import (
    AgentState,
    AgentStatus,
    MessageStatus,
    MessageType as YAMLMessageType,
    TaskMessage,
    read_message_async,
    read_status_async,
    write_message_async,
    write_status_async,
)


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

    def log_thought(self, thought: str, level: LogLevel = LogLevel.DEBUG) -> None:
        """エージェントの思考プロセスをログに出力します。

        Args:
            thought: 思考内容
            level: ログレベル（デフォルト: DEBUG）
        """
        from orchestrator.core.message_models import LogLevel

        # LogLevelのバリデーション
        if not isinstance(level, LogLevel):
            level = LogLevel.DEBUG

        self._logger.log_thought(self._name, thought, level)

    # === YAML通信対応メソッド ===

    def _get_queue_path(self, to_agent: str | None = None) -> Path:
        """YAML通信ファイルのパスを取得します。

        Args:
            to_agent: 送信先エージェント名（Noneの場合は自分宛）

        Returns:
            YAMLファイルのパス
        """
        from_agent = self._name
        to = to_agent if to_agent else self._name

        # queue/{from}_to_{to}.yaml
        filename = f"{from_agent}_to_{to}.yaml"
        return Path("queue") / filename

    def _get_status_path(self) -> Path:
        """ステータスファイルのパスを取得します。

        Returns:
            ステータスファイルのパス
        """
        filename = f"{self._name}.yaml"
        return Path("status") / "agents" / filename

    async def _read_yaml_message(
        self,
        from_agent: str | None = None,
    ) -> TaskMessage | None:
        """YAMLメッセージを読み込みます。

        Args:
            from_agent: 送信元エージェント名（Noneの場合は任意の送信元）

        Returns:
            読み込んだメッセージ。メッセージがない場合はNone。
        """
        if from_agent:
            # 特定のエージェントからのメッセージを読む
            path = Path("queue") / f"{from_agent}_to_{self._name}.yaml"
        else:
            # 自分宛のメッセージを探す
            path = Path("queue") / f"_to_{self._name}.yaml"
            # パターンマッチで見つける必要があるが、ここでは簡略実装

        return await read_message_async(path)

    async def _write_yaml_message(
        self,
        to_agent: str,
        content: str,
        msg_type: YAMLMessageType = YAMLMessageType.TASK,
        msg_id: str | None = None,
        metadata: dict | None = None,
    ) -> str:
        """YAMLメッセージを書き込みます。

        Args:
            to_agent: 送信先エージェント名
            content: メッセージ内容
            msg_type: メッセージタイプ
            msg_id: メッセージID（Noneの場合は自動生成）
            metadata: 追加メタデータ

        Returns:
            メッセージID
        """
        message_id = msg_id or f"msg-{uuid.uuid4().hex[:8]}"

        message = TaskMessage(
            id=message_id,
            from=self._name,
            to=to_agent,
            type=msg_type,
            status=MessageStatus.PENDING,
            content=content,
            timestamp=datetime.now().isoformat(),
            metadata=metadata or {},
        )

        path = self._get_queue_path(to_agent)
        await write_message_async(message, path)

        return message_id

    async def _update_status(
        self,
        state: AgentState,
        current_task: str | None = None,
        statistics: dict | None = None,
    ) -> None:
        """ステータスを更新します。

        Args:
            state: エージェント状態
            current_task: 現在処理中のタスクID
            statistics: 統計情報の更新
        """
        status_path = self._get_status_path()

        # 既存のステータスを読み込む
        existing = await read_status_async(status_path)
        if existing:
            # 既存の統計情報をマージ
            merged_stats = existing.statistics.copy()
            if statistics:
                merged_stats.update(statistics)
            statistics = merged_stats

        status = AgentStatus(
            agent_name=self._name,
            state=state,
            current_task=current_task,
            last_updated=datetime.now().isoformat(),
            statistics=statistics or {},
        )

        await write_status_async(status, status_path)

    async def _check_and_process_messages(self) -> list[TaskMessage]:
        """自分宛のメッセージを確認して処理します。

        Returns:
            見つかったメッセージのリスト
        """
        messages = []

        # 自分宛のメッセージファイルを探す
        queue_dir = Path("queue")
        if not queue_dir.exists():
            return messages

        # パターン: *_to_{self._name}.yaml
        pattern = f"_to_{self._name}.yaml"
        for yaml_file in queue_dir.glob(f"*{pattern}"):
            try:
                message = await read_message_async(yaml_file)
                if message and message.status == MessageStatus.PENDING:
                    messages.append(message)
                    # ステータスをIN_PROGRESSに更新
                    message.status = MessageStatus.IN_PROGRESS
                    await write_message_async(message, yaml_file)
            except Exception:
                # 読み込みエラーはスキップ
                pass

        return messages
