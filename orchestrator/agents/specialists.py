"""Specialistエージェント

このモジュールでは、各専門分野を担当する3種類のSpecialistエージェントを定義します。
- CodingWritingSpecialist: コーディング + ドキュメント作成
- ResearchAnalysisSpecialist: 調査・分析
- TestingSpecialist: テスト・品質保証
"""

import asyncio
from typing import TYPE_CHECKING, Final

from orchestrator.agents.cc_agent_base import (
    CCAgentBase,
    CCAgentTimeoutError,
)
from orchestrator.core.pane_io import PaneTimeoutError
from orchestrator.core.yaml_protocol import (
    AgentState,
    MessageStatus,
    MessageType as YAMLMessageType,
    TaskMessage,
)

if TYPE_CHECKING:
    from orchestrator.core.cc_cluster_manager import CCClusterManager
    from orchestrator.core.message_logger import MessageLogger

# 定数
CODING_SPECIALIST_NAME: Final[str] = "specialist_coding_writing"
RESEARCH_SPECIALIST_NAME: Final[str] = "specialist_research_analysis"
TESTING_SPECIALIST_NAME: Final[str] = "specialist_testing"
MIDDLE_MANAGER_NAME: Final[str] = "middle_manager"
DEFAULT_TASK_TIMEOUT: Final[float] = 120.0
YAML_POLL_INTERVAL: Final[float] = 1.0  # YAML確認間隔（秒）

# 合言葉（マーカー）
CODING_MARKER: Final[str] = "CODING OK"
RESEARCH_MARKER: Final[str] = "RESEARCH OK"
TESTING_MARKER: Final[str] = "TESTING OK"


class CodingWritingSpecialist(CCAgentBase):
    """Coding & Writing Specialistエージェント

    コーディングとドキュメント作成を担当するスペシャリストです。
    Middle Managerからのタスクを受領し、実装とドキュメント作成を行います。

    Attributes:
        _name: エージェント名（"specialist_coding_writing"固定）
        _cluster_manager: CCClusterManagerインスタンス
        _logger: MessageLoggerインスタンス
        _default_timeout: デフォルトのタイムアウト時間（秒）

    Example:
        >>> from orchestrator.core import CCClusterManager
        >>> cluster = CCClusterManager("config/cc-cluster.yaml")
        >>> agent = CodingWritingSpecialist("specialist_coding_writing", cluster_manager=cluster)
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
            name: エージェント名（"specialist_coding_writing"である必要があります）
            cluster_manager: CCClusterManagerインスタンス
            logger: MessageLoggerインスタンス（Noneの場合は新規作成）
            default_timeout: デフォルトのタイムアウト時間（秒）

        Raises:
            ValueError: nameが"specialist_coding_writing"でない場合
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

    async def check_and_process_yaml_messages(self) -> None:
        """YAMLメッセージを確認して処理します。

        Middle Managerからのタスクメッセージを確認して処理します。
        """
        messages = await self._check_and_process_messages()

        for message in messages:
            if message.type == YAMLMessageType.TASK:
                self.log_thought(f"タスクを受信しました: {message.id}")
                # タスクを処理
                try:
                    # ステータスをWORKINGに更新
                    await self._update_status(AgentState.WORKING, current_task=message.id)

                    result = await self.handle_task(message.content)

                    # 結果をMiddle Managerに返信
                    await self._write_yaml_message(
                        to_agent=MIDDLE_MANAGER_NAME,
                        content=result,
                        msg_type=YAMLMessageType.RESULT,
                    )

                    # ステータスをIDLEに戻す
                    await self._update_status(AgentState.IDLE, statistics={"tasks_completed": 1})

                except Exception as e:
                    # エラーを返信
                    await self._write_yaml_message(
                        to_agent=MIDDLE_MANAGER_NAME,
                        content=f"エラーが発生: {e}",
                        msg_type=YAMLMessageType.ERROR,
                    )
                    await self._update_status(AgentState.ERROR)

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

    async def check_and_process_yaml_messages(self) -> None:
        """YAMLメッセージを確認して処理します。

        Middle Managerからのタスクメッセージを確認して処理します。
        """
        messages = await self._check_and_process_messages()

        for message in messages:
            if message.type == YAMLMessageType.TASK:
                self.log_thought(f"タスクを受信しました: {message.id}")
                # タスクを処理
                try:
                    # ステータスをWORKINGに更新
                    await self._update_status(AgentState.WORKING, current_task=message.id)

                    result = await self.handle_task(message.content)

                    # 結果をMiddle Managerに返信
                    await self._write_yaml_message(
                        to_agent=MIDDLE_MANAGER_NAME,
                        content=result,
                        msg_type=YAMLMessageType.RESULT,
                    )
                    # ステータスをCOMPLETEDに更新
                    await self._update_status(
                        AgentState.IDLE,
                        statistics={"tasks_completed": 1}
                    )
                    self.log_thought(f"結果を返信しました: {message.id}")

                    # 元のメッセージをCOMPLETEDに更新
                    message.status = MessageStatus.COMPLETED
                    original_path = Path("queue") / f"{MIDDLE_MANAGER_NAME}_to_{self._name}.yaml"
                    await write_message_async(message, original_path)

                except Exception as e:
                    # エラーを返信
                    await self._write_yaml_message(
                        to_agent=MIDDLE_MANAGER_NAME,
                        content=f"エラーが発生: {e}",
                        msg_type=YAMLMessageType.ERROR,
                    )
                    # ステータスをERRORに更新
                    await self._update_status(AgentState.ERROR)

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


# ResearchAnalysisSpecialistとTestingSpecialistにも同様のメソッドを追加
for cls in [ResearchAnalysisSpecialist, TestingSpecialist]:
    cls.check_and_process_yaml_messages = CodingWritingSpecialist.check_and_process_yaml_messages
    cls.run_yaml_loop = CodingWritingSpecialist.run_yaml_loop
