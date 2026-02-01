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

        assert result == "CODING OK\n実装が完了しました"

    @pytest.mark.asyncio
    async def test_handle_task_sends_to_specialists(self, agent, mock_cluster_manager):
        """タスクが全Specialistに送信されること"""
        await agent.handle_task("新しい機能を実装してください")

        # 3つのSpecialistに送信されていること
        assert mock_cluster_manager.send_message.call_count == 3

        # 呼び出しを確認
        call_args_list = mock_cluster_manager.send_message.call_args_list
        agent_names = {call.kwargs["agent_name"] for call in call_args_list}
        expected_agents = {
            CODING_SPECIALIST_NAME,
            RESEARCH_SPECIALIST_NAME,
            TESTING_SPECIALIST_NAME,
        }
        assert agent_names == expected_agents

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
        call_args_list = mock_cluster_manager.send_message.call_args_list
        timeouts = {call.kwargs.get("timeout") for call in call_args_list}
        assert custom_timeout in timeouts

    @pytest.mark.asyncio
    async def test_handle_task_logs_communication(self, agent, mock_logger):
        """通信ログが記録されること"""
        await agent.handle_task("テストタスク")

        # 送信ログが記録されていること（3つのSpecialist分）
        assert mock_logger.log_send.call_count == 3

        # 受信ログが記録されていること（最初の応答分以上）
        # 注意: 並列実行されるため、複数の応答がログに記録される可能性があります
        assert mock_logger.log_receive.call_count >= 1

    @pytest.mark.asyncio
    async def test_handle_task_returns_first_response(self, mock_cluster_manager, mock_logger):
        """最初の応答が返されること"""
        # 応答順序を制御するための設定
        call_count = 0

        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return "RESEARCH OK\n調査が完了しました"
            elif call_count == 2:
                await asyncio.sleep(0.1)  # 遅延させて最初の応答にならないように
                return "CODING OK\n実装が完了しました"
            else:
                await asyncio.sleep(0.1)  # 遅延させて最初の応答にならないように
                return "TESTING OK\nテストが完了しました"

        mock_cluster_manager.send_message = AsyncMock(side_effect=side_effect)

        agent = MiddleManagerAgent(
            name="middle_manager",
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
        )

        result = await agent.handle_task("タスク")

        assert result == "RESEARCH OK\n調査が完了しました"


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
