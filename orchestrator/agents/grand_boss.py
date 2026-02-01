"""Grand Bossエージェント

このモジュールでは、ユーザーとの窓口であるGrand Bossエージェントを定義します。
"""

from typing import TYPE_CHECKING, Final

from orchestrator.agents.cc_agent_base import (
    CCAgentBase,
)

if TYPE_CHECKING:
    from orchestrator.core.cc_cluster_manager import CCClusterManager
    from orchestrator.core.message_logger import MessageLogger

# 定数
MIDDLE_MANAGER_NAME: Final[str] = "middle_manager"
DEFAULT_TASK_TIMEOUT: Final[float] = 120.0


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

        # Middle Managerにタスクを転送
        response = await self.send_to(
            to_agent=MIDDLE_MANAGER_NAME,
            message=task,
            timeout=self._default_timeout,
        )

        # 結果を整形して返す
        return self._format_final_result(response, task)

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
