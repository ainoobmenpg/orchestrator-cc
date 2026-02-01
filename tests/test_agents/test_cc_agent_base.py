"""CCAgentBaseの単体テスト

このモジュールでは、CCAgentBaseクラスの単体テストを実装します。
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from orchestrator.agents.cc_agent_base import (
    DEFAULT_TIMEOUT,
    CCAgentBase,
    CCAgentSendError,
    CCAgentTimeoutError,
)
from orchestrator.core import (
    CCClusterAgentNotFoundError,
    CCClusterManager,
    LogLevel,
    MessageLogger,
    MessageType,
    PaneTimeoutError,
)


# テスト用の具象エージェントクラス（pytestのwarning回避のため'Dummy'を使用）
class DummyAgent(CCAgentBase):
    """テスト用の具象エージェントクラス"""

    async def handle_task(self, task: str) -> str:
        """テスト用のタスク処理"""
        return f"処理完了: {task}"


class TestCCAgentBaseInit:
    """CCAgentBase初期化処理のテスト"""

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

    def test_init_with_all_parameters(self, mock_cluster_manager, mock_logger):
        """全パラメータを指定した初期化が成功すること"""
        agent = DummyAgent(
            name="test_agent",
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
            default_timeout=60.0,
        )

        assert agent._get_name() == "test_agent"
        assert agent._cluster_manager is mock_cluster_manager
        assert agent._logger is mock_logger
        assert agent._default_timeout == 60.0

    def test_init_with_default_logger(self, mock_cluster_manager):
        """loggerを省略した場合、新規MessageLoggerが作成されること"""
        agent = DummyAgent(
            name="test_agent",
            cluster_manager=mock_cluster_manager,
        )

        assert agent._get_name() == "test_agent"
        assert isinstance(agent._logger, MessageLogger)
        assert agent._default_timeout == DEFAULT_TIMEOUT

    def test_init_with_invalid_cluster_manager(self):
        """cluster_managerがCCClusterManagerでない場合、TypeErrorが発生すること"""
        with pytest.raises(TypeError, match="cluster_managerはCCClusterManagerのインスタンス"):
            DummyAgent(name="test_agent", cluster_manager="not_a_manager")

    def test_init_with_empty_name(self, mock_cluster_manager):
        """nameが空の場合、ValueErrorが発生すること"""
        with pytest.raises(ValueError, match="nameは空であってはなりません"):
            DummyAgent(name="", cluster_manager=mock_cluster_manager)

    def test_init_with_negative_timeout(self, mock_cluster_manager):
        """default_timeoutが負の値の場合、ValueErrorが発生すること"""
        with pytest.raises(ValueError, match="default_timeoutは正の値である必要があります"):
            DummyAgent(name="test_agent", cluster_manager=mock_cluster_manager, default_timeout=-1.0)

    def test_init_with_zero_timeout(self, mock_cluster_manager):
        """default_timeoutが0の場合、ValueErrorが発生すること"""
        with pytest.raises(ValueError, match="default_timeoutは正の値である必要があります"):
            DummyAgent(name="test_agent", cluster_manager=mock_cluster_manager, default_timeout=0.0)


class TestCCAgentBaseSendTo:
    """send_toメソッドのテスト"""

    @pytest.fixture
    def mock_cluster_manager(self) -> MagicMock:
        """CCClusterManagerのモック"""
        mock = MagicMock(spec=CCClusterManager)
        mock.send_message = AsyncMock(return_value="応答メッセージ")
        return mock

    @pytest.fixture
    def mock_logger(self) -> MagicMock:
        """MessageLoggerのモック"""
        mock = MagicMock(spec=MessageLogger)
        mock.log_send = MagicMock(return_value="msg-id-1")
        mock.log_receive = MagicMock(return_value="msg-id-2")
        return mock

    @pytest.fixture
    def agent(self, mock_cluster_manager, mock_logger) -> DummyAgent:
        """テスト用エージェントインスタンス"""
        return DummyAgent(
            name="sender",
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
        )

    @pytest.mark.asyncio
    async def test_send_to_success(self, agent, mock_cluster_manager, mock_logger):
        """メッセージ送信が成功すること"""
        response = await agent.send_to(
            to_agent="receiver",
            message="テストメッセージ",
        )

        # 応答が返されること
        assert response == "応答メッセージ"

        # CCClusterManager.send_messageが呼ばれること
        mock_cluster_manager.send_message.assert_called_once_with(
            agent_name="receiver",
            message="テストメッセージ",
            timeout=DEFAULT_TIMEOUT,
        )

        # 送信ログが記録されること
        mock_logger.log_send.assert_called_once_with(
            from_agent="sender",
            to_agent="receiver",
            content="テストメッセージ",
            msg_type=MessageType.TASK,
            log_level=LogLevel.INFO,
        )

        # 受信ログが記録されること
        mock_logger.log_receive.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_to_with_custom_timeout(self, agent, mock_cluster_manager):
        """カスタムタイムアウトを指定した場合、それが使用されること"""
        await agent.send_to(
            to_agent="receiver",
            message="テストメッセージ",
            timeout=60.0,
        )

        # 指定したタイムアウトで呼ばれること
        mock_cluster_manager.send_message.assert_called_once_with(
            agent_name="receiver",
            message="テストメッセージ",
            timeout=60.0,
        )

    @pytest.mark.asyncio
    async def test_send_to_with_custom_message_type(self, agent, mock_logger):
        """カスタムメッセージタイプを指定した場合、ログに反映されること"""
        await agent.send_to(
            to_agent="receiver",
            message="通知メッセージ",
            msg_type=MessageType.INFO,
        )

        # 指定したメッセージタイプでログが記録されること
        mock_logger.log_send.assert_called_once()
        call_kwargs = mock_logger.log_send.call_args.kwargs
        assert call_kwargs["msg_type"] == MessageType.INFO

    @pytest.mark.asyncio
    async def test_send_to_with_empty_to_agent(self, agent):
        """to_agentが空の場合、ValueErrorが発生すること"""
        with pytest.raises(ValueError, match="to_agentは空であってはなりません"):
            await agent.send_to(to_agent="", message="メッセージ")

    @pytest.mark.asyncio
    async def test_send_to_with_empty_message(self, agent):
        """messageが空の場合、ValueErrorが発生すること"""
        with pytest.raises(ValueError, match="messageは空であってはなりません"):
            await agent.send_to(to_agent="receiver", message="")


class TestCCAgentBaseErrorHandling:
    """エラーハンドリングのテスト"""

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
    def agent(self, mock_cluster_manager, mock_logger) -> DummyAgent:
        """テスト用エージェントインスタンス"""
        return DummyAgent(
            name="sender",
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
        )

    @pytest.mark.asyncio
    async def test_agent_not_found_error_propagates(self, agent, mock_cluster_manager):
        """CCClusterAgentNotFoundErrorがそのまま再送出されること"""
        mock_cluster_manager.send_message.side_effect = CCClusterAgentNotFoundError("エージェントが見つかりません")

        with pytest.raises(CCClusterAgentNotFoundError, match="エージェントが見つかりません"):
            await agent.send_to(to_agent="unknown_agent", message="メッセージ")

    @pytest.mark.asyncio
    async def test_timeout_error_converted(self, agent, mock_cluster_manager):
        """PaneTimeoutErrorがCCAgentTimeoutErrorに変換されること"""
        mock_cluster_manager.send_message.side_effect = PaneTimeoutError("タイムアウトしました")

        with pytest.raises(CCAgentTimeoutError, match="応答がタイムアウトしました"):
            await agent.send_to(to_agent="receiver", message="メッセージ")

    @pytest.mark.asyncio
    async def test_timeout_error_preserves_cause(self, agent, mock_cluster_manager):
        """CCAgentTimeoutErrorが元の例外をチェーンすること"""
        original_error = PaneTimeoutError("元のエラー")
        mock_cluster_manager.send_message.side_effect = original_error

        try:
            await agent.send_to(to_agent="receiver", message="メッセージ")
            pytest.fail("例外が発生するべきです")
        except CCAgentTimeoutError as e:
            assert e.__cause__ is original_error

    @pytest.mark.asyncio
    async def test_generic_error_converted_to_send_error(self, agent, mock_cluster_manager):
        """一般的な例外がCCAgentSendErrorに変換されること"""
        mock_cluster_manager.send_message.side_effect = RuntimeError("予期しないエラー")

        with pytest.raises(CCAgentSendError, match="メッセージ送信に失敗しました"):
            await agent.send_to(to_agent="receiver", message="メッセージ")

    @pytest.mark.asyncio
    async def test_send_error_preserves_cause(self, agent, mock_cluster_manager):
        """CCAgentSendErrorが元の例外をチェーンすること"""
        original_error = RuntimeError("元のエラー")
        mock_cluster_manager.send_message.side_effect = original_error

        try:
            await agent.send_to(to_agent="receiver", message="メッセージ")
            pytest.fail("例外が発生するべきです")
        except CCAgentSendError as e:
            assert e.__cause__ is original_error


class TestCCAgentBaseAbstractMethod:
    """抽象メソッドのテスト"""

    def test_handle_task_is_abstract(self):
        """handle_taskが抽象メソッドであること"""
        with pytest.raises(TypeError):
            # 抽象メソッドを実装していないクラスはインスタンス化できない
            CCAgentBase(
                name="test",
                cluster_manager=MagicMock(spec=CCClusterManager),
            )

    def test_concrete_class_can_be_instantiated(self):
        """具象クラスがインスタンス化できること"""
        agent = DummyAgent(
            name="test",
            cluster_manager=MagicMock(spec=CCClusterManager),
        )
        assert isinstance(agent, CCAgentBase)


class TestCCAgentBaseLogging:
    """ログ機能のテスト"""

    @pytest.fixture
    def mock_cluster_manager(self) -> MagicMock:
        """CCClusterManagerのモック"""
        mock = MagicMock(spec=CCClusterManager)
        mock.send_message = AsyncMock(return_value="応答メッセージ")
        return mock

    @pytest.fixture
    def mock_logger(self) -> MagicMock:
        """MessageLoggerのモック"""
        mock = MagicMock(spec=MessageLogger)
        mock.log_send = MagicMock(return_value="msg-id-1")
        mock.log_receive = MagicMock(return_value="msg-id-2")
        return mock

    @pytest.fixture
    def agent(self, mock_cluster_manager, mock_logger) -> DummyAgent:
        """テスト用エージェントインスタンス"""
        return DummyAgent(
            name="sender",
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
        )

    @pytest.mark.asyncio
    async def test_send_log_is_called(self, agent, mock_logger):
        """送信ログが記録されること"""
        await agent.send_to(to_agent="receiver", message="メッセージ")

        mock_logger.log_send.assert_called_once_with(
            from_agent="sender",
            to_agent="receiver",
            content="メッセージ",
            msg_type=MessageType.TASK,
            log_level=LogLevel.INFO,
        )

    @pytest.mark.asyncio
    async def test_receive_log_is_called(self, agent, mock_logger):
        """受信ログが記録されること"""
        await agent.send_to(to_agent="receiver", message="メッセージ")

        mock_logger.log_receive.assert_called_once()
        call_kwargs = mock_logger.log_receive.call_args.kwargs

        assert call_kwargs["from_agent"] == "receiver"
        assert call_kwargs["to_agent"] == "sender"
        assert call_kwargs["content"] == "応答メッセージ"
        assert call_kwargs["msg_type"] == MessageType.RESULT
        assert call_kwargs["log_level"] == LogLevel.INFO

    @pytest.mark.asyncio
    async def test_log_not_called_on_validation_error(self, agent, mock_logger):
        """バリデーションエラー時にログが記録されないこと"""
        with pytest.raises(ValueError):
            await agent.send_to(to_agent="", message="メッセージ")

        # ログが記録されていないこと
        mock_logger.log_send.assert_not_called()
        mock_logger.log_receive.assert_not_called()

    @pytest.mark.asyncio
    async def test_log_not_called_on_agent_not_found(self, agent, mock_cluster_manager, mock_logger):
        """エージェント未検出時に送信ログのみが記録されること"""
        mock_cluster_manager.send_message.side_effect = CCClusterAgentNotFoundError("見つかりません")

        with pytest.raises(CCClusterAgentNotFoundError):
            await agent.send_to(to_agent="unknown", message="メッセージ")

        # 送信ログは記録されていること
        mock_logger.log_send.assert_called_once()
        # 受信ログは記録されていないこと
        mock_logger.log_receive.assert_not_called()


class TestCCAgentBaseGetName:
    """_get_nameメソッドのテスト"""

    def test_get_name_returns_correct_name(self):
        """正しいエージェント名が返されること"""
        agent = DummyAgent(
            name="test_agent",
            cluster_manager=MagicMock(spec=CCClusterManager),
        )
        assert agent._get_name() == "test_agent"

    def test_get_name_returns_different_names(self):
        """異なるエージェント名が区別されること"""
        agent1 = DummyAgent(
            name="agent_1",
            cluster_manager=MagicMock(spec=CCClusterManager),
        )
        agent2 = DummyAgent(
            name="agent_2",
            cluster_manager=MagicMock(spec=CCClusterManager),
        )
        assert agent1._get_name() == "agent_1"
        assert agent2._get_name() == "agent_2"
