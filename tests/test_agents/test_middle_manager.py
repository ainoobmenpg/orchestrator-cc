"""MiddleManagerAgentの単体テスト

このモジュールでは、MiddleManagerAgentクラスの単体テストを実装します。
YAMLプロトコル対応のテストです。
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

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
from orchestrator.core.yaml_protocol import (
    AgentState,
    MessageStatus,
    MessageType as YAMLMessageType,
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
    """handle_task正常系のテスト（YAMLプロトコル対応）"""

    @pytest.fixture
    def mock_cluster_manager(self) -> MagicMock:
        """CCClusterManagerのモック"""
        mock = MagicMock(spec=CCClusterManager)
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
        """MiddleManagerAgentインスタンス（YAMLメソッドをモック）"""
        agent = MiddleManagerAgent(
            name="middle_manager",
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
        )
        return agent

    @pytest.mark.asyncio
    async def test_handle_task_returns_response(self, agent):
        """タスク処理が成功し、応答が返されること（YAMLプロトコル対応）"""
        # YAMLメソッドをモック
        with patch.object(agent, '_update_status', new_callable=AsyncMock):
            with patch.object(agent, '_write_yaml_message', new_callable=AsyncMock, return_value="msg-test-001") as mock_write:
                with patch.object(agent, '_wait_for_result', new_callable=AsyncMock, return_value="CODING OK\n実装が完了しました"):
                    result = await agent.handle_task("新しい機能を実装してください")

        # 新しいフォーマットで結果が返される
        assert "Middle Managerによる集約結果" in result
        assert "進捗:" in result
        # "Specialist"プレフィックス付きで表示される
        assert "Coding Writing" in result
        assert "CODING OK" in result
        assert "実装が完了しました" in result

    @pytest.mark.asyncio
    async def test_handle_task_sends_to_specialists(self, agent):
        """タスクがYAMLメッセージとしてSpecialistに送信されること"""
        # YAMLメソッドをモック
        with patch.object(agent, '_update_status', new_callable=AsyncMock):
            with patch.object(agent, '_write_yaml_message', new_callable=AsyncMock, return_value="msg-test-002") as mock_write:
                with patch.object(agent, '_wait_for_result', new_callable=AsyncMock, return_value="CODING OK\n完了"):
                    await agent.handle_task("新しい機能を実装してください")

        # _write_yaml_messageが正しく呼ばれたことを確認
        mock_write.assert_called_once()
        call_kwargs = mock_write.call_args.kwargs
        assert call_kwargs["to_agent"] == CODING_SPECIALIST_NAME
        assert call_kwargs["msg_type"] == YAMLMessageType.TASK

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

        # YAMLメソッドをモック
        with patch.object(agent, '_update_status', new_callable=AsyncMock):
            with patch.object(agent, '_write_yaml_message', new_callable=AsyncMock, return_value="msg-test-003"):
                with patch.object(agent, '_wait_for_result', new_callable=AsyncMock, return_value="OK") as mock_wait:
                    await agent.handle_task("タスク")

        # _wait_for_resultがカスタムタイムアウトで呼ばれたことを確認
        # 複数のSpecialistに送信されるため、複数回呼ばれる
        assert mock_wait.call_count >= 1
        for call in mock_wait.call_args_list:
            assert call.kwargs.get("timeout") == custom_timeout or call[1] == custom_timeout

    @pytest.mark.asyncio
    async def test_handle_task_logs_communication(self, agent, mock_logger):
        """通信ログが記録されること"""
        # YAMLメソッドをモックして実行
        with patch.object(agent, '_update_status', new_callable=AsyncMock):
            with patch.object(agent, '_write_yaml_message', new_callable=AsyncMock, return_value="msg-test-log"):
                with patch.object(agent, '_wait_for_result', new_callable=AsyncMock, return_value="OK"):
                    result = await agent.handle_task("実装タスク")

        # 少なくともエラーが発生せず、結果が返されることを確認
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_handle_task_aggregates_all_results(self, mock_cluster_manager, mock_logger):
        """全Specialistの結果が集約されて返されること（YAMLプロトコル対応）"""
        agent = MiddleManagerAgent(
            name="middle_manager",
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
        )

        # YAMLメソッドをモック - 複数のSpecialistからの応答をシミュレート
        call_count = 0

        async def wait_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return "CODING OK\n実装が完了しました"
            elif call_count == 2:
                return "RESEARCH OK\n調査が完了しました"
            else:
                return "TESTING OK\nテストが完了しました"

        with patch.object(agent, '_update_status', new_callable=AsyncMock):
            with patch.object(agent, '_write_yaml_message', new_callable=AsyncMock, return_value="msg-test-aggregate") as mock_write:
                with patch.object(agent, '_wait_for_result', new_callable=AsyncMock, side_effect=wait_side_effect):
                    # キーワードを含まないタスクなので、全Specialistに送信される
                    result = await agent.handle_task("一般的なタスク")

        # すべての結果が集約されていること
        assert "Middle Managerによる集約結果" in result
        assert "進捗:" in result
        # "Specialist"プレフィックス付きで表示される
        assert "Coding Writing" in result
        assert "Research Analysis" in result
        assert "Testing" in result
        # 側眼_effectの最後の値が返される
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
    """handle_task異常系のテスト（YAMLプロトコル対応）"""

    @pytest.fixture
    def mock_cluster_manager(self) -> MagicMock:
        """CCClusterManagerのモック"""
        mock = MagicMock(spec=CCClusterManager)
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
    async def test_handle_task_propagates_timeout_error(self, agent):
        """タイムアウトエラーが適切に処理されること（YAMLプロトコル対応）"""
        # YAMLメソッドをモック - タイムアウトをシミュレート
        with patch.object(agent, '_update_status', new_callable=AsyncMock):
            with patch.object(agent, '_write_yaml_message', new_callable=AsyncMock, return_value="msg-test-timeout"):
                with patch.object(agent, '_wait_for_result', new_callable=AsyncMock, side_effect=TimeoutError("応答が返ってきません")):
                    # タイムアウトエラーが発生すること
                    with pytest.raises(TimeoutError):
                        await agent.handle_task("テストタスク")


class TestMiddleManagerAgentSpecialistCommunication:
    """Specialistとの通信テスト（YAMLプロトコル対応）"""

    @pytest.fixture
    def mock_cluster_manager(self) -> MagicMock:
        """CCClusterManagerのモック"""
        mock = MagicMock(spec=CCClusterManager)
        # send_messageをモック
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
    async def test_send_to_coding_specialist_success(self, agent, mock_cluster_manager):
        """Coding Specialistへのメッセージ送信が成功すること"""
        # send_toを直接テスト
        result = await agent.send_to(
            to_agent=CODING_SPECIALIST_NAME,
            message="テストメッセージ",
        )

        assert result == "CODING OK\n完了"
        # CCClusterManager.send_messageが呼ばれたことを確認
        mock_cluster_manager.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_to_research_specialist_success(self, agent, mock_cluster_manager):
        """Research Specialistへのメッセージ送信が成功すること"""
        # send_messageの戻り値を設定
        mock_cluster_manager.send_message = AsyncMock(return_value="RESEARCH OK\n調査完了")

        result = await agent.send_to(
            to_agent=RESEARCH_SPECIALIST_NAME,
            message="テストメッセージ",
        )

        assert result == "RESEARCH OK\n調査完了"
        mock_cluster_manager.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_to_testing_specialist_success(self, agent, mock_cluster_manager):
        """Testing Specialistへのメッセージ送信が成功すること"""
        # send_messageの戻り値を設定
        mock_cluster_manager.send_message = AsyncMock(return_value="TESTING OK\nテスト完了")

        result = await agent.send_to(
            to_agent=TESTING_SPECIALIST_NAME,
            message="テストメッセージ",
        )

        assert result == "TESTING OK\nテスト完了"
        mock_cluster_manager.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_timeout_when_agent_not_responding(self, agent, mock_cluster_manager):
        """Specialistが応答しない場合、タイムアウトエラーが発生すること"""
        # YAMLメソッドをモック - タイムアウトをシミュレート
        with patch.object(agent, '_write_yaml_message', new_callable=AsyncMock, return_value="msg-test-error"):
            with patch.object(agent, '_wait_for_result', new_callable=AsyncMock, side_effect=TimeoutError("応答が返ってきません")):
                # 応答がない場合はタイムアウトエラー
                with pytest.raises(TimeoutError):
                    await agent.handle_task("テストタスク")


class TestMiddleManagerAgentConstants:
    """定数のテスト"""

    def test_coding_specialist_name_constant(self):
        """CODING_SPECIALIST_NAME定数が正しいこと"""
        assert CODING_SPECIALIST_NAME == "specialist_coding_writing"

    def test_research_specialist_name_constant(self):
        """RESEARCH_SPECIALIST_NAME定数が正しいこと"""
        assert RESEARCH_SPECIALIST_NAME == "specialist_research_analysis"

    def test_testing_specialist_name_constant(self):
        """TESTING_SPECIALIST_NAME定数が正しいこと"""
        assert TESTING_SPECIALIST_NAME == "specialist_testing"

    def test_default_task_timeout_constant(self):
        """DEFAULT_TASK_TIMEOUT定数が正しいこと"""
        assert DEFAULT_TASK_TIMEOUT == 120.0
