"""GrandBossAgentの単体テスト

このモジュールでは、GrandBossAgentクラスの単体テストを実装します。
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from orchestrator.agents.cc_agent_base import (
    CCAgentSendError,
    CCAgentTimeoutError,
)
from orchestrator.agents.grand_boss import (
    DEFAULT_TASK_TIMEOUT,
    MIDDLE_MANAGER_NAME,
    GrandBossAgent,
)
from orchestrator.core import (
    CCClusterAgentNotFoundError,
    CCClusterManager,
    LogLevel,
    MessageLogger,
    MessageType,
    PaneTimeoutError,
)


class TestGrandBossAgentInit:
    """GrandBossAgent初期化処理のテスト"""

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
        agent = GrandBossAgent(
            name="grand_boss",
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
        )

        assert agent._get_name() == "grand_boss"
        assert agent._cluster_manager is mock_cluster_manager
        assert agent._logger is mock_logger

    def test_init_with_default_logger(self, mock_cluster_manager):
        """loggerを省略した場合、新規MessageLoggerが作成されること"""
        agent = GrandBossAgent(
            name="grand_boss",
            cluster_manager=mock_cluster_manager,
        )

        assert agent._get_name() == "grand_boss"
        assert isinstance(agent._logger, MessageLogger)
        assert agent._default_timeout == DEFAULT_TASK_TIMEOUT

    def test_init_with_custom_timeout(self, mock_cluster_manager, mock_logger):
        """カスタムタイムアウトを指定した場合、それが設定されること"""
        custom_timeout = 180.0
        agent = GrandBossAgent(
            name="grand_boss",
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
            default_timeout=custom_timeout,
        )

        assert agent._default_timeout == custom_timeout

    def test_init_with_invalid_name(self, mock_cluster_manager):
        """nameが'grand_boss'でない場合、ValueErrorが発生すること"""
        with pytest.raises(ValueError, match="nameは'grand_boss'である必要があります"):
            GrandBossAgent(
                name="middle_manager",
                cluster_manager=mock_cluster_manager,
            )

    def test_init_with_invalid_cluster_manager(self):
        """cluster_managerがCCClusterManagerでない場合、TypeErrorが発生すること"""
        with pytest.raises(TypeError, match="cluster_managerはCCClusterManagerのインスタンス"):
            GrandBossAgent(
                name="grand_boss",
                cluster_manager="not_a_manager",  # type: ignore[arg-type]
            )


class TestGrandBossAgentHandleTask:
    """handle_task正常系のテスト"""

    @pytest.fixture
    def mock_cluster_manager(self) -> MagicMock:
        """CCClusterManagerのモック"""
        mock = MagicMock(spec=CCClusterManager)
        mock.send_message = AsyncMock(return_value="MIDDLE MANAGER OK\nタスクを完了しました")
        return mock

    @pytest.fixture
    def mock_logger(self) -> MagicMock:
        """MessageLoggerのモック"""
        mock = MagicMock(spec=MessageLogger)
        mock.log_send = MagicMock(return_value="msg-id-1")
        mock.log_receive = MagicMock(return_value="msg-id-2")
        return mock

    @pytest.fixture
    def agent(self, mock_cluster_manager, mock_logger) -> GrandBossAgent:
        """GrandBossAgentインスタンス"""
        return GrandBossAgent(
            name="grand_boss",
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
        )

    @pytest.mark.asyncio
    async def test_handle_task_returns_response(self, agent):
        """タスク処理が成功し、応答が返されること"""
        result = await agent.handle_task("新しい機能を実装してください")

        # 新しいフォーマットで結果が返される
        assert "タスク実行結果" in result
        assert "元のタスク" in result
        assert "新しい機能を実装してください" in result
        assert "Middle Managerによる集約結果" in result
        assert "MIDDLE MANAGER OK" in result
        assert "Grand Boss as Executive" in result

    @pytest.mark.asyncio
    async def test_handle_task_sends_to_middle_manager(self, agent, mock_cluster_manager):
        """タスクがMiddle Managerに送信されること"""
        await agent.handle_task("新しい機能を実装してください")

        mock_cluster_manager.send_message.assert_called_once_with(
            agent_name=MIDDLE_MANAGER_NAME,
            message="新しい機能を実装してください",
            timeout=DEFAULT_TASK_TIMEOUT,
        )

    @pytest.mark.asyncio
    async def test_handle_task_with_custom_timeout(self, mock_cluster_manager, mock_logger):
        """カスタムタイムアウトを指定したインスタンスで正しく動作すること"""
        custom_timeout = 180.0
        agent = GrandBossAgent(
            name="grand_boss",
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
            default_timeout=custom_timeout,
        )

        await agent.handle_task("タスク")

        mock_cluster_manager.send_message.assert_called_once_with(
            agent_name=MIDDLE_MANAGER_NAME,
            message="タスク",
            timeout=custom_timeout,
        )

    @pytest.mark.asyncio
    async def test_handle_task_logs_communication(self, agent, mock_logger):
        """通信ログが記録されること"""
        await agent.handle_task("テストタスク")

        # 送信ログが記録されていること
        mock_logger.log_send.assert_called_once()
        call_kwargs = mock_logger.log_send.call_args.kwargs
        assert call_kwargs["from_agent"] == "grand_boss"
        assert call_kwargs["to_agent"] == MIDDLE_MANAGER_NAME
        assert call_kwargs["content"] == "テストタスク"
        assert call_kwargs["msg_type"] == MessageType.TASK
        assert call_kwargs["log_level"] == LogLevel.INFO

        # 受信ログが記録されていること
        mock_logger.log_receive.assert_called_once()
        call_kwargs = mock_logger.log_receive.call_args.kwargs
        assert call_kwargs["from_agent"] == MIDDLE_MANAGER_NAME
        assert call_kwargs["to_agent"] == "grand_boss"
        assert call_kwargs["msg_type"] == MessageType.RESULT


class TestGrandBossAgentHandleTaskErrors:
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
    def agent(self, mock_cluster_manager, mock_logger) -> GrandBossAgent:
        """GrandBossAgentインスタンス"""
        return GrandBossAgent(
            name="grand_boss",
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


class TestGrandBossAgentMiddleManagerCommunication:
    """Middle Managerとの通信テスト"""

    @pytest.fixture
    def mock_cluster_manager(self) -> MagicMock:
        """CCClusterManagerのモック"""
        mock = MagicMock(spec=CCClusterManager)
        mock.send_message = AsyncMock(return_value="MIDDLE MANAGER OK\n完了")
        return mock

    @pytest.fixture
    def mock_logger(self) -> MagicMock:
        """MessageLoggerのモック"""
        mock = MagicMock(spec=MessageLogger)
        mock.log_send = MagicMock(return_value="msg-id-1")
        mock.log_receive = MagicMock(return_value="msg-id-2")
        return mock

    @pytest.fixture
    def agent(self, mock_cluster_manager, mock_logger) -> GrandBossAgent:
        """GrandBossAgentインスタンス"""
        return GrandBossAgent(
            name="grand_boss",
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
        )

    @pytest.mark.asyncio
    async def test_send_to_middle_manager_success(self, agent):
        """Middle Managerへの送信が成功すること"""
        result = await agent.send_to(
            to_agent=MIDDLE_MANAGER_NAME,
            message="テストメッセージ",
        )

        assert result == "MIDDLE MANAGER OK\n完了"

    @pytest.mark.asyncio
    async def test_receive_from_middle_manager_success(self, agent):
        """Middle Managerからの応答が正しく受信されること"""
        response = "MIDDLE MANAGER OK\n実行結果: 成功"

        # モックの戻り値を設定
        agent._cluster_manager.send_message = AsyncMock(return_value=response)

        result = await agent.handle_task("テストタスク")

        # 新しいフォーマットで結果が返される
        assert "タスク実行結果" in result
        assert "元のタスク" in result
        assert "テストタスク" in result
        assert "Middle Managerによる集約結果" in result
        assert response in result  # 元のレスポンスが含まれている
        assert "Grand Boss as Executive" in result

    @pytest.mark.asyncio
    async def test_middle_manager_not_found_error(self, agent, mock_cluster_manager):
        """Middle Managerが存在しない場合、CCClusterAgentNotFoundErrorが発生すること"""
        mock_cluster_manager.send_message.side_effect = CCClusterAgentNotFoundError(
            f"エージェント '{MIDDLE_MANAGER_NAME}' が見つかりません"
        )

        with pytest.raises(CCClusterAgentNotFoundError, match="エージェント.*が見つかりません"):
            await agent.handle_task("テストタスク")


class TestGrandBossAgentConstants:
    """定数のテスト"""

    def test_middle_manager_name_constant(self):
        """MIDDLE_MANAGER_NAME定数が正しいこと"""
        assert MIDDLE_MANAGER_NAME == "middle_manager"

    def test_default_task_timeout_constant(self):
        """DEFAULT_TASK_TIMEOUT定数が正しいこと"""
        assert DEFAULT_TASK_TIMEOUT == 120.0
