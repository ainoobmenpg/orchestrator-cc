"""Grand Bossエージェント

このモジュールでは、ユーザーとの窓口であるGrand Bossエージェントを定義します。
"""

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Final

from orchestrator.agents.cc_agent_base import (
    CCAgentBase,
)
from orchestrator.core.yaml_protocol import (
    AgentState,
    MessageStatus,
    read_message_async,
    write_message_async,
)
from orchestrator.core.yaml_protocol import (
    MessageType as YAMLMessageType,
)

if TYPE_CHECKING:
    from orchestrator.core.cc_cluster_manager import CCClusterManager
    from orchestrator.core.message_logger import MessageLogger

# 定数
MIDDLE_MANAGER_NAME: Final[str] = "middle_manager"
DEFAULT_TASK_TIMEOUT: Final[float] = 120.0
YAML_POLL_INTERVAL: Final[float] = 1.0  # YAML確認間隔（秒）


class GrandBossAgent(CCAgentBase):
    """Grand Bossエージェント

    orchestrator-ccプロジェクトの最高責任者として、ユーザーとの窓口を務めます。
    Middle Managerにタスクを委任し、最終結果をユーザーに提示します。

    Attributes:
        _name: エージェント名（"grand_boss"固定）
        _cluster_manager: CCClusterManagerインスタンス
        _logger: MessageLoggerインスタンス
        _default_timeout: デフォルトのタイムアウト時間（秒）

    Example:
        >>> from orchestrator.core import CCClusterManager
        >>> cluster = CCClusterManager("config/cc-cluster.yaml")
        >>> agent = GrandBossAgent("grand_boss", cluster_manager=cluster)
        >>> result = await agent.handle_task("新しい機能を実装してください")
        >>> print(result)
    """

    def __init__(
        self,
        name: str,
        cluster_manager: "CCClusterManager",
        logger: "MessageLogger | None" = None,
        default_timeout: float = DEFAULT_TASK_TIMEOUT,
    ) -> None:
        """GrandBossAgentを初期化します。

        Args:
            name: エージェント名（"grand_boss"である必要があります）
            cluster_manager: CCClusterManagerインスタンス
            logger: MessageLoggerインスタンス（Noneの場合は新規作成）
            default_timeout: デフォルトのタイムアウト時間（秒）

        Raises:
            ValueError: nameが"grand_boss"でない場合
            TypeError: cluster_managerがCCClusterManagerでない場合
        """
        # nameのバリデーション
        if name != "grand_boss":
            raise ValueError(f"nameは'grand_boss'である必要があります: {name}")

        # 親クラスを初期化
        super().__init__(name, cluster_manager, logger, default_timeout)

    async def handle_task(self, task: str) -> str:
        """タスクを処理します。

        ユーザーからのタスクを受領し、Middle Managerに委任して結果を整形して返します。
        YAMLベースの通信を使用します。

        Args:
            task: ユーザーからのタスク内容

        Returns:
            処理結果（Middle Managerからの応答を整形したもの）

        Raises:
            ValueError: taskが空の場合
            CCAgentSendError: Middle Managerへの送信に失敗した場合
            CCAgentTimeoutError: Middle Managerからの応答がタイムアウトした場合
            CCClusterAgentNotFoundError: Middle Managerが存在しない場合

        Note:
            - タスクは空であってはなりません
            - タイムアウトはインスタンスのdefault_timeoutを使用します
            - Middle Managerからの結果を整形して返します
        """
        if not task or not task.strip():
            raise ValueError("taskは空であってはなりません")

        # ステータスをWORKINGに更新
        await self._update_status(AgentState.WORKING, current_task="user_task")

        # YAMLメッセージを送信
        msg_id = await self._write_yaml_message(
            to_agent=MIDDLE_MANAGER_NAME,
            content=task,
            msg_type=YAMLMessageType.TASK,
            metadata={"source": "user"},
        )

        self.log_thought(f"タスクをYAMLで送信しました: {msg_id}")

        # Middle Managerからの結果を待つ
        result = await self._wait_for_result(msg_id, timeout=self._default_timeout)

        # ステータスをIDLEに戻す
        await self._update_status(AgentState.IDLE, statistics={"tasks_completed": 1})

        # 結果を整形して返す
        return self._format_final_result(result, task)

    async def _wait_for_result(self, msg_id: str, timeout: float) -> str:
        """YAMLメッセージの結果を待ちます。

        Args:
            msg_id: 待機するメッセージID
            timeout: タイムアウト時間（秒）

        Returns:
            結果の内容

        Raises:
            CCAgentTimeoutError: タイムアウトした場合
        """
        start_time = asyncio.get_event_loop().time()
        result_path = Path("queue") / f"{MIDDLE_MANAGER_NAME}_to_{self._name}.yaml"

        while asyncio.get_event_loop().time() - start_time < timeout:
            # 結果メッセージを確認
            message = await read_message_async(result_path)
            if message and message.status == MessageStatus.COMPLETED:
                return message.content

            await asyncio.sleep(YAML_POLL_INTERVAL)

        raise TimeoutError(f"メッセージ {msg_id} の結果がタイムアウトしました")

    async def check_and_process_yaml_messages(self) -> None:
        """YAMLメッセージを確認して処理します。

        Middle Managerからの結果メッセージを確認して処理します。
        """
        messages = await self._check_and_process_messages()

        for message in messages:
            if message.type == YAMLMessageType.RESULT:
                self.log_thought(f"結果を受信しました: {message.id}")
                # 結果を処理（必要に応じて応答を返す）
                # ステータスをCOMPLETEDに更新
                message.status = MessageStatus.COMPLETED
                result_path = self._get_queue_path(MIDDLE_MANAGER_NAME)
                await write_message_async(message, result_path)

    async def run_yaml_loop(self) -> None:
        """YAMLメッセージ監視ループを実行します。

        定期的にYAMLメッセージを確認して処理します。
        """
        while True:
            try:
                await self.check_and_process_yaml_messages()
            except Exception as e:
                self.log_thought(f"YAML処理でエラーが発生: {e}")
            await asyncio.sleep(YAML_POLL_INTERVAL)

    def _format_final_result(self, middle_manager_result: str, original_task: str) -> str:
        """Middle Managerからの結果を最終成果物として整形します。

        Args:
            middle_manager_result: Middle Managerからの結果
            original_task: ユーザーからの元のタスク

        Returns:
            整形された最終成果物
        """
        return f"""# タスク実行結果

## 元のタスク
{original_task}

## Middle Managerによる集約結果
{middle_manager_result}

---
Grand Boss as Executive"""
