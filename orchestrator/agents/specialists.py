"""Specialistエージェント

このモジュールでは、各専門分野を担当する3種類のSpecialistエージェントを定義します。
- CodingWritingSpecialist: コーディング + ドキュメント作成
- ResearchAnalysisSpecialist: 調査・分析
- TestingSpecialist: テスト・品質保証
"""

from typing import TYPE_CHECKING, Final

from orchestrator.agents.cc_agent_base import (
    CCAgentBase,
    CCAgentTimeoutError,
)
from orchestrator.core.pane_io import PaneTimeoutError

if TYPE_CHECKING:
    from orchestrator.core.cc_cluster_manager import CCClusterManager
    from orchestrator.core.message_logger import MessageLogger

# 定数
CODING_SPECIALIST_NAME: Final[str] = "coding_writing_specialist"
RESEARCH_SPECIALIST_NAME: Final[str] = "research_analysis_specialist"
TESTING_SPECIALIST_NAME: Final[str] = "testing_specialist"
CODING_MARKER: Final[str] = "CODING OK"
RESEARCH_MARKER: Final[str] = "RESEARCH OK"
TESTING_MARKER: Final[str] = "TESTING OK"
DEFAULT_TASK_TIMEOUT: Final[float] = 120.0


class CodingWritingSpecialist(CCAgentBase):
    """Coding & Writing Specialistエージェント

    コーディングとドキュメント作成を担当するスペシャリストです。
    Middle Managerからのタスクを受領し、実装とドキュメント作成を行います。

    Attributes:
        _name: エージェント名（"coding_writing_specialist"固定）
        _cluster_manager: CCClusterManagerインスタンス
        _logger: MessageLoggerインスタンス
        _default_timeout: デフォルトのタイムアウト時間（秒）

    Example:
        >>> from orchestrator.core import CCClusterManager
        >>> cluster = CCClusterManager("config/cc-cluster.yaml")
        >>> agent = CodingWritingSpecialist("coding_writing_specialist", cluster_manager=cluster)
        >>> result = await agent.handle_task("ユーザー認証機能を実装してください")
        >>> print(result)
    """

    def __init__(
        self,
        name: str,
        cluster_manager: "CCClusterManager",
        logger: "MessageLogger | None" = None,
        default_timeout: float = DEFAULT_TASK_TIMEOUT,
    ) -> None:
        """CodingWritingSpecialistを初期化します。

        Args:
            name: エージェント名（"coding_writing_specialist"である必要があります）
            cluster_manager: CCClusterManagerインスタンス
            logger: MessageLoggerインスタンス（Noneの場合は新規作成）
            default_timeout: デフォルトのタイムアウト時間（秒）

        Raises:
            ValueError: nameが"coding_writing_specialist"でない場合
            TypeError: cluster_managerがCCClusterManagerでない場合
        """
        if name != CODING_SPECIALIST_NAME:
            raise ValueError(f"nameは'{CODING_SPECIALIST_NAME}'である必要があります: {name}")

        super().__init__(name, cluster_manager, logger, default_timeout)

    async def handle_task(self, task: str) -> str:
        """タスクを処理します。

        コーディング・ドキュメント作成のタスクを受領し、処理結果を返します。
        tmuxペインでClaude Codeプロセスと通信して実装を行います。

        Args:
            task: タスク内容（コーディング・ドキュメント作成の指示）

        Returns:
            処理結果（CODING OKを含む文字列）

        Raises:
            ValueError: taskが空の場合
            CCAgentTimeoutError: タスク処理がタイムアウトした場合

        Note:
            - タスクは空であってはなりません
            - 実際のClaude Codeプロセスと通信してタスクを実行します
        """
        if not task or not task.strip():
            raise ValueError("taskは空であってはなりません")

        return await self._process_task(task)

    async def _process_task(self, task: str) -> str:
        """タスクを処理して結果を返します（完全版）。

        CCClusterManager経由で自分のCCProcessLauncherを取得し、
        tmuxペインでClaude Codeと通信してタスクを実行します。

        Args:
            task: タスク内容

        Returns:
            処理結果（合言葉を含む）

        Raises:
            CCAgentTimeoutError: タスク処理がタイムアウトした場合
        """
        # CCClusterManager経由で自分のCCProcessLauncherを取得
        launcher = self._cluster_manager.get_launcher(self._name)

        # 自分のペインにタスクを送信（Claude Codeに作業指示）
        try:
            response = await launcher.send_message(
                message=task,
                timeout=self._default_timeout,
            )
        except PaneTimeoutError as e:
            raise CCAgentTimeoutError(
                f"Coding Specialistのタスク処理がタイムアウトしました "
                f"(timeout={self._default_timeout}秒): {e}"
            ) from e

        return response


class ResearchAnalysisSpecialist(CCAgentBase):
    """Research & Analysis Specialistエージェント

    調査・分析を担当するスペシャリストです。
    Middle Managerからのタスクを受領し、情報収集・分析を行います。

    Attributes:
        _name: エージェント名（"research_analysis_specialist"固定）
        _cluster_manager: CCClusterManagerインスタンス
        _logger: MessageLoggerインスタンス
        _default_timeout: デフォルトのタイムアウト時間（秒）

    Example:
        >>> from orchestrator.core import CCClusterManager
        >>> cluster = CCClusterManager("config/cc-cluster.yaml")
        >>> agent = ResearchAnalysisSpecialist("research_analysis_specialist", cluster_manager=cluster)
        >>> result = await agent.handle_task("ベストプラクティスを調査してください")
        >>> print(result)
    """

    def __init__(
        self,
        name: str,
        cluster_manager: "CCClusterManager",
        logger: "MessageLogger | None" = None,
        default_timeout: float = DEFAULT_TASK_TIMEOUT,
    ) -> None:
        """ResearchAnalysisSpecialistを初期化します。

        Args:
            name: エージェント名（"research_analysis_specialist"である必要があります）
            cluster_manager: CCClusterManagerインスタンス
            logger: MessageLoggerインスタンス（Noneの場合は新規作成）
            default_timeout: デフォルトのタイムアウト時間（秒）

        Raises:
            ValueError: nameが"research_analysis_specialist"でない場合
            TypeError: cluster_managerがCCClusterManagerでない場合
        """
        if name != RESEARCH_SPECIALIST_NAME:
            raise ValueError(f"nameは'{RESEARCH_SPECIALIST_NAME}'である必要があります: {name}")

        super().__init__(name, cluster_manager, logger, default_timeout)

    async def handle_task(self, task: str) -> str:
        """タスクを処理します。

        調査・分析のタスクを受領し、処理結果を返します。
        tmuxペインでClaude Codeプロセスと通信して調査を行います。

        Args:
            task: タスク内容（調査・分析の指示）

        Returns:
            処理結果（RESEARCH OKを含む文字列）

        Raises:
            ValueError: taskが空の場合
            CCAgentTimeoutError: タスク処理がタイムアウトした場合

        Note:
            - タスクは空であってはなりません
            - 実際のClaude Codeプロセスと通信してタスクを実行します
        """
        if not task or not task.strip():
            raise ValueError("taskは空であってはなりません")

        return await self._process_task(task)

    async def _process_task(self, task: str) -> str:
        """タスクを処理して結果を返します（完全版）。

        CCClusterManager経由で自分のCCProcessLauncherを取得し、
        tmuxペインでClaude Codeと通信してタスクを実行します。

        Args:
            task: タスク内容

        Returns:
            処理結果（合言葉を含む）

        Raises:
            CCAgentTimeoutError: タスク処理がタイムアウトした場合
        """
        # CCClusterManager経由で自分のCCProcessLauncherを取得
        launcher = self._cluster_manager.get_launcher(self._name)

        # 自分のペインにタスクを送信（Claude Codeに作業指示）
        try:
            response = await launcher.send_message(
                message=task,
                timeout=self._default_timeout,
            )
        except PaneTimeoutError as e:
            raise CCAgentTimeoutError(
                f"Research Specialistのタスク処理がタイムアウトしました "
                f"(timeout={self._default_timeout}秒): {e}"
            ) from e

        return response


class TestingSpecialist(CCAgentBase):
    """Testing Specialistエージェント

    テスト・品質保証を担当するスペシャリストです。
    Middle Managerからのタスクを受領し、テスト実行・品質チェックを行います。

    Attributes:
        _name: エージェント名（"testing_specialist"固定）
        _cluster_manager: CCClusterManagerインスタンス
        _logger: MessageLoggerインスタンス
        _default_timeout: デフォルトのタイムアウト時間（秒）

    Example:
        >>> from orchestrator.core import CCClusterManager
        >>> cluster = CCClusterManager("config/cc-cluster.yaml")
        >>> agent = TestingSpecialist("testing_specialist", cluster_manager=cluster)
        >>> result = await agent.handle_task("単体テストを実行してください")
        >>> print(result)
    """

    def __init__(
        self,
        name: str,
        cluster_manager: "CCClusterManager",
        logger: "MessageLogger | None" = None,
        default_timeout: float = DEFAULT_TASK_TIMEOUT,
    ) -> None:
        """TestingSpecialistを初期化します。

        Args:
            name: エージェント名（"testing_specialist"である必要があります）
            cluster_manager: CCClusterManagerインスタンス
            logger: MessageLoggerインスタンス（Noneの場合は新規作成）
            default_timeout: デフォルトのタイムアウト時間（秒）

        Raises:
            ValueError: nameが"testing_specialist"でない場合
            TypeError: cluster_managerがCCClusterManagerでない場合
        """
        if name != TESTING_SPECIALIST_NAME:
            raise ValueError(f"nameは'{TESTING_SPECIALIST_NAME}'である必要があります: {name}")

        super().__init__(name, cluster_manager, logger, default_timeout)

    async def handle_task(self, task: str) -> str:
        """タスクを処理します。

        テスト・品質保証のタスクを受領し、処理結果を返します。
        tmuxペインでClaude Codeプロセスと通信してテストを実行します。

        Args:
            task: タスク内容（テスト・品質保証の指示）

        Returns:
            処理結果（TESTING OKを含む文字列）

        Raises:
            ValueError: taskが空の場合
            CCAgentTimeoutError: タスク処理がタイムアウトした場合

        Note:
            - タスクは空であってはなりません
            - 実際のClaude Codeプロセスと通信してタスクを実行します
        """
        if not task or not task.strip():
            raise ValueError("taskは空であってはなりません")

        return await self._process_task(task)

    async def _process_task(self, task: str) -> str:
        """タスクを処理して結果を返します（完全版）。

        CCClusterManager経由で自分のCCProcessLauncherを取得し、
        tmuxペインでClaude Codeと通信してタスクを実行します。

        Args:
            task: タスク内容

        Returns:
            処理結果（合言葉を含む）

        Raises:
            CCAgentTimeoutError: タスク処理がタイムアウトした場合
        """
        # CCClusterManager経由で自分のCCProcessLauncherを取得
        launcher = self._cluster_manager.get_launcher(self._name)

        # 自分のペインにタスクを送信（Claude Codeに作業指示）
        try:
            response = await launcher.send_message(
                message=task,
                timeout=self._default_timeout,
            )
        except PaneTimeoutError as e:
            raise CCAgentTimeoutError(
                f"Testing Specialistのタスク処理がタイムアウトしました "
                f"(timeout={self._default_timeout}秒): {e}"
            ) from e

        return response
