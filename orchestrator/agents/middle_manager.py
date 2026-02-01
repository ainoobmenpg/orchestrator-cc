"""Middle Managerエージェント

このモジュールでは、タスク分解とSpecialistの取りまとめを行うMiddle Managerエージェントを定義します。
"""

import asyncio
from typing import TYPE_CHECKING, Final

from orchestrator.agents.cc_agent_base import CCAgentBase

if TYPE_CHECKING:
    from orchestrator.core.cc_cluster_manager import CCClusterManager
    from orchestrator.core.message_logger import MessageLogger

# 定数
CODING_SPECIALIST_NAME: Final[str] = "coding_writing_specialist"
RESEARCH_SPECIALIST_NAME: Final[str] = "research_analysis_specialist"
TESTING_SPECIALIST_NAME: Final[str] = "testing_specialist"
DEFAULT_TASK_TIMEOUT: Final[float] = 120.0


class MiddleManagerAgent(CCAgentBase):
    """Middle Managerエージェント

    orchestrator-ccプロジェクトの中間管理職として、Grand Bossから
    タスクを受領し、各Specialistに割り当てて結果を集約します。

    Attributes:
        _name: エージェント名（"middle_manager"固定）
        _cluster_manager: CCClusterManagerインスタンス
        _logger: MessageLoggerインスタンス
        _default_timeout: デフォルトのタイムアウト時間（秒）

    Example:
        >>> from orchestrator.core import CCClusterManager
        >>> cluster = CCClusterManager("config/cc-cluster.yaml")
        >>> agent = MiddleManagerAgent("middle_manager", cluster_manager=cluster)
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
        """MiddleManagerAgentを初期化します。

        Args:
            name: エージェント名（"middle_manager"である必要があります）
            cluster_manager: CCClusterManagerインスタンス
            logger: MessageLoggerインスタンス（Noneの場合は新規作成）
            default_timeout: デフォルトのタイムアウト時間（秒）

        Raises:
            ValueError: nameが"middle_manager"でない場合
            TypeError: cluster_managerがCCClusterManagerでない場合
        """
        # nameのバリデーション
        if name != "middle_manager":
            raise ValueError(f"nameは'middle_manager'である必要があります: {name}")

        # 親クラスを初期化
        super().__init__(name, cluster_manager, logger, default_timeout)

    async def handle_task(self, task: str) -> str:
        """タスクを処理します。

        Grand Bossからのタスクを受領し、各Specialistに割り当てて結果を返します。

        現在の実装は簡易版で、全Specialistに並列送信し、最初の応答を返します。
        将来的には、タスク分解、進捗管理、品質確認などの機能を追加予定です。

        Args:
            task: Grand Bossからのタスク内容

        Returns:
            処理結果（最初に応答したSpecialistからの応答）

        Raises:
            ValueError: taskが空の場合
            CCAgentSendError: Specialistへの送信に失敗した場合
            CCAgentTimeoutError: Specialistからの応答がタイムアウトした場合
            CCClusterAgentNotFoundError: Specialistが存在しない場合

        Note:
            - タスクは空であってはなりません
            - タイムアウトはインスタンスのdefault_timeoutを使用します
        """
        if not task or not task.strip():
            raise ValueError("taskは空であってはなりません")

        return await self._forward_to_specialists(task)

    async def _forward_to_specialists(self, task: str) -> str:
        """全Specialistにタスクを転送し、最初の応答を返します。

        全Specialist（Coding、Research、Testing）に並列でタスクを送信し、
        最初に応答が返ってきたものを結果として返します。
        残りのリクエストはキャンセルされます。

        Args:
            task: 転送するタスク内容

        Returns:
            最初に応答したSpecialistからの応答

        Raises:
            CCAgentSendError: いずれかのSpecialistへの送信に失敗した場合
            CCAgentTimeoutError: 全Specialistからの応答がタイムアウトした場合
            CCClusterAgentNotFoundError: Specialistが存在しない場合
        """
        # 全Specialistに並列送信（Taskとして作成）
        tasks = [
            asyncio.create_task(
                self.send_to(to_agent=CODING_SPECIALIST_NAME, message=task, timeout=self._default_timeout)
            ),
            asyncio.create_task(
                self.send_to(to_agent=RESEARCH_SPECIALIST_NAME, message=task, timeout=self._default_timeout)
            ),
            asyncio.create_task(
                self.send_to(to_agent=TESTING_SPECIALIST_NAME, message=task, timeout=self._default_timeout)
            ),
        ]

        # 最初の完了を待つ
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

        # 待機中のタスクをキャンセル
        for t in pending:
            t.cancel()

        # 最初の応答を返す
        return done.pop().result()
