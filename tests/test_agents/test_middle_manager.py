"""MiddleManagerAgentの単体テスト

このモジュールでは、MiddleManagerAgentクラスの単体テストを実装します。
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from orchestrator.agents.cc_agent_base import (
    CCAgentSendError,
    CCAgentTimeoutError,
)
from orchestrator.agents.middle_manager import (
    CODING_SPECIALIST_NAME,
    DEFAULT_TASK_TIMEOUT,
    RESEARCH_SPECIALIST_NAME,
    TESTING_SPECIALIST_NAME,
    MiddleManagerAgent,
)
from orchestrator.core import (
    CCClusterAgentNotFoundError,
    CCClusterManager,
    MessageLogger,
    PaneTimeoutError,
)


class TestMiddleManagerAgentInit:
    """MiddleManagerAgent初期化処理のテスト"""

    @pytest.fixture
    def mock_cluster_manager(self) -> MagicMock:
        """CCClusterManagerのモック"""
        mock = MagicMock(spec=CCClusterManager)
        return mock

    @pytest.fixture
    def mock_logger(self) -> MagicMock:
        """MessageLoggerのモック"""
        mock = MagicMock(spec=MessageLogger)
        return mock

    def test_init_with_valid_parameters(self, mock_cluster_manager, mock_logger):
        """正常なパラメータで初期化が成功すること"""
        agent = MiddleManagerAgent(
            name="middle_manager",
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
        )

        assert agent._get_name() == "middle_manager"
        assert agent._cluster_manager is mock_cluster_manager
        assert agent._logger is mock_logger

    def test_init_with_default_logger(self, mock_cluster_manager):
        """loggerを省略した場合、新規MessageLoggerが作成されること"""
        agent = MiddleManagerAgent(
            name="middle_manager",
            cluster_manager=mock_cluster_manager,
        )

        assert agent._get_name() == "middle_manager"
        assert isinstance(agent._logger, MessageLogger)
        assert agent._default_timeout == DEFAULT_TASK_TIMEOUT

    def test_init_with_custom_timeout(self, mock_cluster_manager, mock_logger):
        """カスタムタイムアウトを指定した場合、それが設定されること"""
        custom_timeout = 180.0
        agent = MiddleManagerAgent(
            name="middle_manager",
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
            default_timeout=custom_timeout,
        )

        assert agent._default_timeout == custom_timeout

    def test_init_with_invalid_name(self, mock_cluster_manager):
        """nameが'middle_manager'でない場合、ValueErrorが発生すること"""
        with pytest.raises(ValueError, match="nameは'middle_manager'である必要があります"):
            MiddleManagerAgent(
                name="grand_boss",
                cluster_manager=mock_cluster_manager,
            )

    def test_init_with_invalid_cluster_manager(self):
        """cluster_managerがCCClusterManagerでない場合、TypeErrorが発生すること"""
        with pytest.raises(TypeError, match="cluster_managerはCCClusterManagerのインスタンス"):
            MiddleManagerAgent(
                name="middle_manager",
                cluster_manager="not_a_manager",  # type: ignore[arg-type]
            )


class TestMiddleManagerAgentHandleTask:
    """handle_task正常系のテスト"""

    @pytest.fixture
    def mock_cluster_manager(self) -> MagicMock:
        """CCClusterManagerのモック"""
        mock = MagicMock(spec=CCClusterManager)
        mock.send_message = AsyncMock(return_value="CODING OK\n実装が完了しました")
        return mock

    @pytest.fixture
    def mock_logger(self) -> MagicMock:
        """MessageLoggerのモック"""
        mock = MagicMock(spec=MessageLogger)
        mock.log_send = MagicMock(return_value="msg-id-1")
        mock.log_receive = MagicMock(return_value="msg-id-2")
        return mock

    @pytest.fixture
    def agent(self, mock_cluster_manager, mock_logger) -> MiddleManagerAgent:
        """MiddleManagerAgentインスタンス"""
        return MiddleManagerAgent(
            name="middle_manager",
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
        )

    @pytest.mark.asyncio
    async def test_handle_task_returns_response(self, agent):
        """タスク処理が成功し、応答が返されること"""
        result = await agent.handle_task("新しい機能を実装してください")

        # 新しいフォーマットで結果が返される
        assert "Middle Managerによる集約結果" in result
        assert "進捗:" in result
        assert "Coding Writing Specialist" in result
        assert "CODING OK" in result
        assert "実装が完了しました" in result

    @pytest.mark.asyncio
    async def test_handle_task_sends_to_specialists(self, agent, mock_cluster_manager):
        """タスクが適切なSpecialistに送信されること"""
        await agent.handle_task("新しい機能を実装してください")

        # "実装"というキーワードを含むため、Coding Specialistにのみ送信される
        assert mock_cluster_manager.send_message.call_count == 1

        # 呼び出しを確認
        call_args = mock_cluster_manager.send_message.call_args
        assert call_args.kwargs["agent_name"] == CODING_SPECIALIST_NAME

    @pytest.mark.asyncio
    async def test_handle_task_with_custom_timeout(self, mock_cluster_manager, mock_logger):
        """カスタムタイムアウトを指定したインスタンスで正しく動作すること"""
        custom_timeout = 180.0
        agent = MiddleManagerAgent(
            name="middle_manager",
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
            default_timeout=custom_timeout,
        )

        await agent.handle_task("タスク")

        # いずれかの呼び出しでcustom_timeoutが使用されていること
        # キーワードパターンマッチングで特定のSpecialistにのみ送信される
        if mock_cluster_manager.send_message.call_count > 0:
            call_args = mock_cluster_manager.send_message.call_args
            assert call_args.kwargs.get("timeout") == custom_timeout

    @pytest.mark.asyncio
    async def test_handle_task_logs_communication(self, agent, mock_logger):
        """通信ログが記録されること"""
        await agent.handle_task("テストタスク")

        # 送信ログが記録されていること（Middle Manager自身のログ + Specialistへの送信）
        # キーワードパターンマッチングで特定のSpecialistにのみ送信される
        assert mock_logger.log_send.call_count >= 1

        # 受信ログが記録されていること
        assert mock_logger.log_receive.call_count >= 1

    @pytest.mark.asyncio
    async def test_handle_task_aggregates_all_results(self, mock_cluster_manager, mock_logger):
        """全Specialistの結果が集約されて返されること"""
        # 複数のSpecialistからの応答をシミュレート
        call_count = 0

        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return "CODING OK\n実装が完了しました"
            elif call_count == 2:
                return "RESEARCH OK\n調査が完了しました"
            else:
                return "TESTING OK\nテストが完了しました"

        mock_cluster_manager.send_message = AsyncMock(side_effect=side_effect)

        agent = MiddleManagerAgent(
            name="middle_manager",
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
        )

        # キーワードを含まないタスクなので、全Specialistに送信される
        result = await agent.handle_task("一般的なタスク")

        # すべての結果が集約されていること
        assert "Middle Managerによる集約結果" in result
        assert "進捗: 3/3 サブタスク完了" in result
        assert "Coding Writing Specialist" in result
        assert "Research Analysis Specialist" in result
        assert "Testing Specialist" in result
        assert "CODING OK" in result
        assert "RESEARCH OK" in result
        assert "TESTING OK" in result

    @pytest.mark.asyncio
    async def test_decompose_task_with_coding_keyword(self, agent):
        """コーディング関連キーワードでタスク分解されること"""
        subtasks = agent._decompose_task("新しい関数を実装してください")

        assert CODING_SPECIALIST_NAME in subtasks
        assert len(subtasks[CODING_SPECIALIST_NAME]) == 1
        assert "実装" in subtasks[CODING_SPECIALIST_NAME][0]

        # 他のSpecialistには送信されない
        assert len(subtasks[RESEARCH_SPECIALIST_NAME]) == 0
        assert len(subtasks[TESTING_SPECIALIST_NAME]) == 0

    @pytest.mark.asyncio
    async def test_decompose_task_with_multiple_keywords(self, agent):
        """複数のキーワードを含むタスクで適切に分解されること"""
        subtasks = agent._decompose_task("コードを実装してテストしてください")

        # "実装"と"テスト"の両方のキーワードが含まれる
        assert CODING_SPECIALIST_NAME in subtasks
        assert TESTING_SPECIALIST_NAME in subtasks

    @pytest.mark.asyncio
    async def test_decompose_task_with_no_keywords(self, agent):
        """キーワードを含まないタスクは全Specialistに送信されること"""
        subtasks = agent._decompose_task("一般的なタスク")

        # 全Specialistに送信される
        assert CODING_SPECIALIST_NAME in subtasks
        assert RESEARCH_SPECIALIST_NAME in subtasks
        assert TESTING_SPECIALIST_NAME in subtasks
        assert len(subtasks[CODING_SPECIALIST_NAME]) == 1
        assert len(subtasks[RESEARCH_SPECIALIST_NAME]) == 1
        assert len(subtasks[TESTING_SPECIALIST_NAME]) == 1


class TestMiddleManagerAgentHandleTaskErrors:
    """handle_task異常系のテスト"""

    @pytest.fixture
    def mock_cluster_manager(self) -> MagicMock:
        """CCClusterManagerのモック"""
        mock = MagicMock(spec=CCClusterManager)
        mock.send_message = AsyncMock()
        return mock

    @pytest.fixture
    def mock_logger(self) -> MagicMock:
        """MessageLoggerのモック"""
        mock = MagicMock(spec=MessageLogger)
        mock.log_send = MagicMock(return_value="msg-id-1")
        return mock

    @pytest.fixture
    def agent(self, mock_cluster_manager, mock_logger) -> MiddleManagerAgent:
        """MiddleManagerAgentインスタンス"""
        return MiddleManagerAgent(
            name="middle_manager",
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
        )

    @pytest.mark.asyncio
    async def test_handle_task_with_empty_task(self, agent):
        """空のタスクの場合、ValueErrorが発生すること"""
        with pytest.raises(ValueError, match="taskは空であってはなりません"):
            await agent.handle_task("")

    @pytest.mark.asyncio
    async def test_handle_task_with_whitespace_task(self, agent):
        """空白のみのタスクの場合、ValueErrorが発生すること"""
        with pytest.raises(ValueError, match="taskは空であってはなりません"):
            await agent.handle_task("   ")

    @pytest.mark.asyncio
    async def test_handle_task_propagates_send_error(self, agent, mock_cluster_manager):
        """CCAgentSendErrorがそのまま再送出されること"""
        mock_cluster_manager.send_message.side_effect = RuntimeError("送信エラー")

        # 親クラスのsend_toでRuntimeErrorがCCAgentSendErrorに変換される
        with pytest.raises(CCAgentSendError, match="メッセージ送信に失敗しました"):
            await agent.handle_task("テストタスク")

    @pytest.mark.asyncio
    async def test_handle_task_propagates_timeout_error(self, agent, mock_cluster_manager):
        """CCAgentTimeoutErrorがそのまま再送出されること"""
        mock_cluster_manager.send_message.side_effect = PaneTimeoutError("タイムアウト")

        # 親クラスのsend_toでPaneTimeoutErrorがCCAgentTimeoutErrorに変換される
        with pytest.raises(CCAgentTimeoutError, match="応答がタイムアウトしました"):
            await agent.handle_task("テストタスク")


class TestMiddleManagerAgentSpecialistCommunication:
    """Specialistとの通信テスト"""

    @pytest.fixture
    def mock_cluster_manager(self) -> MagicMock:
        """CCClusterManagerのモック"""
        mock = MagicMock(spec=CCClusterManager)
        mock.send_message = AsyncMock(return_value="CODING OK\n完了")
        return mock

    @pytest.fixture
    def mock_logger(self) -> MagicMock:
        """MessageLoggerのモック"""
        mock = MagicMock(spec=MessageLogger)
        mock.log_send = MagicMock(return_value="msg-id-1")
        mock.log_receive = MagicMock(return_value="msg-id-2")
        return mock

    @pytest.fixture
    def agent(self, mock_cluster_manager, mock_logger) -> MiddleManagerAgent:
        """MiddleManagerAgentインスタンス"""
        return MiddleManagerAgent(
            name="middle_manager",
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
        )

    @pytest.mark.asyncio
    async def test_send_to_coding_specialist_success(self, agent):
        """Coding Specialistへの送信が成功すること"""
        result = await agent.send_to(
            to_agent=CODING_SPECIALIST_NAME,
            message="テストメッセージ",
        )

        assert result == "CODING OK\n完了"

    @pytest.mark.asyncio
    async def test_send_to_research_specialist_success(self, agent):
        """Research Specialistへの送信が成功すること"""
        agent._cluster_manager.send_message = AsyncMock(return_value="RESEARCH OK\n調査完了")

        result = await agent.send_to(
            to_agent=RESEARCH_SPECIALIST_NAME,
            message="テストメッセージ",
        )

        assert result == "RESEARCH OK\n調査完了"

    @pytest.mark.asyncio
    async def test_send_to_testing_specialist_success(self, agent):
        """Testing Specialistへの送信が成功すること"""
        agent._cluster_manager.send_message = AsyncMock(return_value="TESTING OK\nテスト完了")

        result = await agent.send_to(
            to_agent=TESTING_SPECIALIST_NAME,
            message="テストメッセージ",
        )

        assert result == "TESTING OK\nテスト完了"

    @pytest.mark.asyncio
    async def test_specialist_not_found_error(self, agent, mock_cluster_manager):
        """Specialistが存在しない場合、CCClusterAgentNotFoundErrorが発生すること"""
        mock_cluster_manager.send_message.side_effect = CCClusterAgentNotFoundError(
            f"エージェント '{CODING_SPECIALIST_NAME}' が見つかりません"
        )

        with pytest.raises(CCClusterAgentNotFoundError, match="エージェント.*が見つかりません"):
            await agent.handle_task("テストタスク")


class TestMiddleManagerAgentConstants:
    """定数のテスト"""

    def test_coding_specialist_name_constant(self):
        """CODING_SPECIALIST_NAME定数が正しいこと"""
        assert CODING_SPECIALIST_NAME == "coding_writing_specialist"

    def test_research_specialist_name_constant(self):
        """RESEARCH_SPECIALIST_NAME定数が正しいこと"""
        assert RESEARCH_SPECIALIST_NAME == "research_analysis_specialist"

    def test_testing_specialist_name_constant(self):
        """TESTING_SPECIALIST_NAME定数が正しいこと"""
        assert TESTING_SPECIALIST_NAME == "testing_specialist"

    def test_default_task_timeout_constant(self):
        """DEFAULT_TASK_TIMEOUT定数が正しいこと"""
        assert DEFAULT_TASK_TIMEOUT == 120.0
