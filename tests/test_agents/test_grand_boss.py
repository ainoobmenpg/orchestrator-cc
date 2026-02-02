"""GrandBossAgentの単体テスト

このモジュールでは、GrandBossAgentクラスの単体テストを実装します。
YAMLプロトコルに対応したテストです。
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

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
from orchestrator.core.yaml_protocol import (
    AgentState,
    MessageStatus,
    MessageType as YAMLMessageType,
    TaskMessage,
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
        return mock

    @pytest.fixture
    def agent(self, mock_cluster_manager, mock_logger) -> GrandBossAgent:
        """GrandBossAgentインスタンス（YAMLメソッドをモック）"""
        agent = GrandBossAgent(
            name="grand_boss",
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
        )
        return agent

    @pytest.mark.asyncio
    async def test_handle_task_returns_response(self, agent):
        """タスク処理が成功し、応答が返されること"""
        # YAMLメソッドをモック
        with patch.object(agent, '_update_status', new_callable=AsyncMock):
            with patch.object(agent, '_write_yaml_message', new_callable=AsyncMock, return_value="msg-test-001"):
                with patch.object(agent, '_wait_for_result', new_callable=AsyncMock, return_value="MIDDLE MANAGER OK\nタスクを完了しました"):
                    result = await agent.handle_task("新しい機能を実装してください")

        # 新しいフォーマットで結果が返される
        assert "タスク実行結果" in result
        assert "元のタスク" in result
        assert "新しい機能を実装してください" in result
        assert "Middle Managerによる集約結果" in result
        assert "MIDDLE MANAGER OK" in result
        assert "Grand Boss as Executive" in result

    @pytest.mark.asyncio
    async def test_handle_task_sends_to_middle_manager(self, agent):
        """タスクがYAMLメッセージとしてMiddle Managerに送信されること"""
        # YAMLメソッドをモック
        with patch.object(agent, '_update_status', new_callable=AsyncMock):
            with patch.object(agent, '_write_yaml_message', new_callable=AsyncMock, return_value="msg-test-002") as mock_write:
                with patch.object(agent, '_wait_for_result', new_callable=AsyncMock, return_value="OK"):
                    await agent.handle_task("新しい機能を実装してください")

        # _write_yaml_messageが正しく呼ばれたことを確認
        mock_write.assert_called_once()
        call_kwargs = mock_write.call_args.kwargs
        assert call_kwargs["to_agent"] == MIDDLE_MANAGER_NAME
        assert call_kwargs["content"] == "新しい機能を実装してください"
        assert call_kwargs["msg_type"] == YAMLMessageType.TASK

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

        # YAMLメソッドをモック
        with patch.object(agent, '_update_status', new_callable=AsyncMock):
            with patch.object(agent, '_write_yaml_message', new_callable=AsyncMock, return_value="msg-test-003"):
                with patch.object(agent, '_wait_for_result', new_callable=AsyncMock, return_value="OK") as mock_wait:
                    await agent.handle_task("タスク")

        # _wait_for_resultがカスタムタイムアウトで呼ばれたことを確認
        mock_wait.assert_called_once_with("msg-test-003", timeout=custom_timeout)

    @pytest.mark.asyncio
    async def test_handle_task_updates_status(self, agent):
        """ステータス更新が正しく行われること"""
        # YAMLメソッドをモック
        with patch.object(agent, '_update_status', new_callable=AsyncMock) as mock_status:
            with patch.object(agent, '_write_yaml_message', new_callable=AsyncMock, return_value="msg-test-004"):
                with patch.object(agent, '_wait_for_result', new_callable=AsyncMock, return_value="OK"):
                    await agent.handle_task("テストタスク")

        # ステータスが2回更新されることを確認（WORKING -> IDLE）
        assert mock_status.call_count == 2
        # 1回目はWORKING（位置引数）
        first_call_args = mock_status.call_args_list[0].args
        assert first_call_args[0] == AgentState.WORKING
        # 2回目はIDLE（位置引数）
        second_call_args = mock_status.call_args_list[1].args
        assert second_call_args[0] == AgentState.IDLE


class TestGrandBossAgentHandleTaskErrors:
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
    async def test_handle_task_propagates_timeout_error(self, agent):
        """_wait_for_resultのタイムアウトがTimeoutErrorとして伝播すること"""
        # YAMLメソッドをモック
        with patch.object(agent, '_update_status', new_callable=AsyncMock):
            with patch.object(agent, '_write_yaml_message', new_callable=AsyncMock, return_value="msg-test-timeout"):
                with patch.object(agent, '_wait_for_result', new_callable=AsyncMock, side_effect=TimeoutError("メッセージの結果がタイムアウトしました")):
                    # TimeoutErrorがそのまま伝播することを確認
                    with pytest.raises(TimeoutError, match="タイムアウトしました"):
                        await agent.handle_task("テストタスク")


class TestGrandBossAgentMiddleManagerCommunication:
    """Middle Managerとの通信テスト（YAMLプロトコル対応）"""

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
        """Middle ManagerへのYAMLメッセージ送信が成功すること"""
        # YAMLメソッドをモック
        with patch.object(agent, '_update_status', new_callable=AsyncMock):
            with patch.object(agent, '_write_yaml_message', new_callable=AsyncMock, return_value="msg-test-send-001") as mock_write:
                with patch.object(agent, '_wait_for_result', new_callable=AsyncMock, return_value="MIDDLE MANAGER OK\n完了"):
                    result = await agent.handle_task("テストメッセージ")

        # 結果が正しく返されることを確認
        assert "MIDDLE MANAGER OK" in result
        assert "完了" in result

    @pytest.mark.asyncio
    async def test_receive_from_middle_manager_success(self, agent):
        """Middle Managerからの応答が正しく受信されること"""
        response = "MIDDLE MANAGER OK\n実行結果: 成功"

        # YAMLメソッドをモック
        with patch.object(agent, '_update_status', new_callable=AsyncMock):
            with patch.object(agent, '_write_yaml_message', new_callable=AsyncMock, return_value="msg-test-recv-001"):
                with patch.object(agent, '_wait_for_result', new_callable=AsyncMock, return_value=response) as mock_wait:
                    result = await agent.handle_task("テストタスク")

        # 新しいフォーマットで結果が返されることを確認
        assert "タスク実行結果" in result
        assert "元のタスク" in result
        assert "テストタスク" in result
        assert "Middle Managerによる集約結果" in result
        assert response in result
        assert "Grand Boss as Executive" in result

    @pytest.mark.asyncio
    async def test_middle_manager_not_found_error(self, agent):
        """Middle Managerが存在しない場合、適切なエラーが発生すること"""
        # _write_yaml_messageがエラーをスローするシナリオ
        # YAMLプロトコルでは、エージェントが見つからない場合もYAMLファイルへの書き込みは成功する
        # そのため、ここでは_timeoutエラーをシミュレート
        with patch.object(agent, '_update_status', new_callable=AsyncMock):
            with patch.object(agent, '_write_yaml_message', new_callable=AsyncMock, return_value="msg-test-error-001"):
                with patch.object(agent, '_wait_for_result', new_callable=AsyncMock, side_effect=TimeoutError("応答が返ってきません")):
                    # 応答がない場合はタイムアウトエラー
                    with pytest.raises(TimeoutError):
                        await agent.handle_task("テストタスク")


class TestGrandBossAgentConstants:
    """定数のテスト"""

    def test_middle_manager_name_constant(self):
        """MIDDLE_MANAGER_NAME定数が正しいこと"""
        assert MIDDLE_MANAGER_NAME == "middle_manager"

    def test_default_task_timeout_constant(self):
        """DEFAULT_TASK_TIMEOUT定数が正しいこと"""
        assert DEFAULT_TASK_TIMEOUT == 120.0
