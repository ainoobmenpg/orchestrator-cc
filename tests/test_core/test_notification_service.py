"""notification_serviceモジュールのユニットテスト"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, call

import pytest

from orchestrator.core.notification_service import NotificationService
from orchestrator.core.yaml_protocol import MessageType, TaskMessage, TaskStatus


class TestNotificationService:
    """NotificationServiceクラスのテスト"""

    def test_init(self) -> None:
        """初期化テスト"""
        mock_tmux = MagicMock()
        service = NotificationService(mock_tmux)

        assert service._tmux is mock_tmux

    def test_agent_panes_mapping(self) -> None:
        """エージェントとペイン番号のマッピングテスト"""
        expected_mapping = {
            "grand_boss": 0,
            "middle_manager": 1,
            "coding_writing_specialist": 2,
            "research_analysis_specialist": 3,
            "testing_specialist": 4,
        }

        assert NotificationService.AGENT_PANES == expected_mapping

    def test_notify_agent(self) -> None:
        """エージェント通知テスト"""
        mock_tmux = MagicMock()
        service = NotificationService(mock_tmux)

        message = TaskMessage(
            id="msg-001",
            from_agent="grand_boss",
            to_agent="middle_manager",
            type=MessageType.TASK,
            content="テストタスク",
        )
        queue_file = Path("/test/queue/test.yaml")

        service.notify_agent(message, queue_file)

        # send_keysが2回呼ばれることを確認（通知 + Enter）
        assert mock_tmux.send_keys.call_count == 2

        # 最初の呼び出しは通知メッセージ
        first_call = mock_tmux.send_keys.call_args_list[0]
        assert first_call[0][0] == 1  # pane_index
        assert "新しいメッセージがあります" in first_call[0][1]

        # 2回目の呼び出しはEnter
        second_call = mock_tmux.send_keys.call_args_list[1]
        assert second_call[0][0] == 1  # pane_index
        assert second_call[0][1] == "Enter"

    def test_notify_agent_unknown_agent(self) -> None:
        """不明なエージェントへの通知テスト"""
        mock_tmux = MagicMock()
        service = NotificationService(mock_tmux)

        message = TaskMessage(
            id="msg-002",
            from_agent="unknown",
            to_agent="unknown_agent",
            type=MessageType.TASK,
            content="テスト",
        )
        queue_file = Path("/test/queue/test.yaml")

        with pytest.raises(ValueError, match="不明なエージェント"):
            service.notify_agent(message, queue_file)

    def test_notify_all_agents(self) -> None:
        """全エージェント通知テスト"""
        mock_tmux = MagicMock()
        service = NotificationService(mock_tmux)

        message = "全エージェントへの通知"
        service.notify_all_agents(message)

        # 5エージェント × 2回（通知 + Enter）= 10回
        assert mock_tmux.send_keys.call_count == 10

    def test_notify_dashboard_update(self) -> None:
        """ダッシュボード更新通知テスト"""
        mock_tmux = MagicMock()
        service = NotificationService(mock_tmux)

        service.notify_dashboard_update()

        # 5エージェント × 2回（通知 + Enter）= 10回
        assert mock_tmux.send_keys.call_count == 10

        # 通知内容を確認
        calls = mock_tmux.send_keys.call_args_list
        # 各エージェントの最初の呼び出しにダッシュボードメッセージが含まれる
        for i in range(5):
            notification_call = calls[i * 2]
            assert "ダッシュボードが更新されました" in notification_call[0][1]

    def test_build_notification_task_message(self) -> None:
        """タスクメッセージの通知構築テスト"""
        mock_tmux = MagicMock()
        service = NotificationService(mock_tmux)

        message = TaskMessage(
            id="msg-003",
            from_agent="grand_boss",
            to_agent="middle_manager",
            type=MessageType.TASK,
            content="実装してください",
            status=TaskStatus.PENDING,
        )
        queue_file = Path("/test/queue/test.yaml")

        notification = service._build_notification(message, queue_file)

        assert "新しいメッセージがあります" in notification
        assert "送信元: grand_boss" in notification
        assert "test.yaml" in notification
        assert "タスク内容を確認してください" in notification

    def test_build_notification_result_message(self) -> None:
        """結果メッセージの通知構築テスト"""
        mock_tmux = MagicMock()
        service = NotificationService(mock_tmux)

        message = TaskMessage(
            id="msg-004",
            from_agent="coding_writing_specialist",
            to_agent="middle_manager",
            type=MessageType.RESULT,
            content="実装完了",
        )
        queue_file = Path("/test/queue/test.yaml")

        notification = service._build_notification(message, queue_file)

        assert "新しいメッセージがあります" in notification
        assert "送信元: coding_writing_specialist" in notification

    def test_get_status_emoji(self) -> None:
        """ステータス絵文字取得テスト"""
        mock_tmux = MagicMock()
        service = NotificationService(mock_tmux)

        assert service._get_status_emoji(TaskStatus.PENDING) == "📥"
        assert service._get_status_emoji(TaskStatus.IN_PROGRESS) == "⏳"
        assert service._get_status_emoji(TaskStatus.COMPLETED) == "✅"
        assert service._get_status_emoji(TaskStatus.FAILED) == "❌"

    def test_get_type_emoji(self) -> None:
        """タイプ絵文字取得テスト"""
        mock_tmux = MagicMock()
        service = NotificationService(mock_tmux)

        assert service._get_type_emoji(MessageType.TASK) == "📋"
        assert service._get_type_emoji(MessageType.INFO) == "ℹ️"
        assert service._get_type_emoji(MessageType.RESULT) == "📤"
        assert service._get_type_emoji(MessageType.ERROR) == "⚠️"

    def test_notify_agent_send_keys_error(self, caplog) -> None:
        """send_keysエラー時のテスト"""
        import logging

        mock_tmux = MagicMock()
        mock_tmux.send_keys.side_effect = Exception("tmux error")

        service = NotificationService(mock_tmux)

        message = TaskMessage(
            id="msg-005",
            from_agent="grand_boss",
            to_agent="middle_manager",
            type=MessageType.TASK,
            content="テスト",
        )
        queue_file = Path("/test/queue/test.yaml")

        with caplog.at_level(logging.ERROR):
            service.notify_agent(message, queue_file)

        # エラーログが記録されていることを確認
        assert any("通知の送信に失敗しました" in record.message for record in caplog.records)

    def test_notify_all_agents_partial_failure(self, caplog) -> None:
        """一部エージェントで失敗した場合のテスト"""
        import logging

        mock_tmux = MagicMock()
        # 奇数回目の呼び出しでエラーを発生させる
        call_count = [0]

        def side_effect_func(pane_index, keys):
            call_count[0] += 1
            if call_count[0] % 2 == 1:
                raise Exception("tmux error")

        mock_tmux.send_keys.side_effect = side_effect_func

        service = NotificationService(mock_tmux)

        with caplog.at_level(logging.ERROR):
            service.notify_all_agents("test message")

        # 一部のエージェントでエラーが記録されていることを確認
        assert any("通知送信に失敗しました" in record.message for record in caplog.records)


class TestNotificationExceptions:
    """通知関連例外クラスのテスト"""

    def test_notification_error(self) -> None:
        """NotificationErrorテスト"""
        from orchestrator.core.notification_service import NotificationError

        with pytest.raises(NotificationError):
            raise NotificationError("test error")

    def test_agent_not_found_error(self) -> None:
        """AgentNotFoundErrorテスト"""
        from orchestrator.core.notification_service import AgentNotFoundError

        with pytest.raises(AgentNotFoundError):
            raise AgentNotFoundError("agent not found")

    def test_tmux_send_error(self) -> None:
        """TmuxSendErrorテスト"""
        from orchestrator.core.notification_service import TmuxSendError

        with pytest.raises(TmuxSendError):
            raise TmuxSendError("send error")
