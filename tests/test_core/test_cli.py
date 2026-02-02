"""CLIモジュールのテスト

このモジュールでは、orchestrator/cli/main.pyのテストを実装します。
"""

from unittest.mock import MagicMock, patch

import pytest

from orchestrator.cli.main import show_logs, show_tasks


class TestShowLogs:
    """show_logsコマンドのテスト"""

    def test_show_logs_with_no_entries(self, capsys):
        """ログがない場合の動作を確認"""
        # Namespaceオブジェクトを作成
        args = MagicMock(
            log_file="nonexistent.jsonl",
            from_agent=None,
            to_agent=None,
            msg_type=None,
            level=None,
            limit=10,
            recent=False,
            json=False,
        )

        with patch("orchestrator.core.cluster_logger.ClusterLogger") as mock_logger_class:
            mock_logger = MagicMock()
            mock_logger.read_logs.return_value = []
            mock_logger_class.return_value = mock_logger

            show_logs(args)

            captured = capsys.readouterr()
            assert "ログが見つかりませんでした" in captured.out

    def test_show_logs_with_entries(self, capsys):
        """ログがある場合の動作を確認"""
        from orchestrator.core.cluster_logger import LogEntry

        args = MagicMock(
            log_file="messages.jsonl",
            from_agent=None,
            to_agent=None,
            msg_type=None,
            level=None,
            limit=10,
            recent=False,
            json=False,
        )

        entries = [
            LogEntry(
                timestamp="2025-01-01T12:00:00",
                id="msg-001",
                from_agent="grand_boss",
                to_agent="middle_manager",
                type="task",
                content="テストタスク",
                level="INFO",
            )
        ]

        with patch("orchestrator.core.cluster_logger.ClusterLogger") as mock_logger_class:
            mock_logger = MagicMock()
            mock_logger.read_logs.return_value = entries
            mock_logger_class.return_value = mock_logger

            show_logs(args)

            captured = capsys.readouterr()
            assert "通信ログ" in captured.out
            assert "grand_boss" in captured.out


class TestShowTasks:
    """show_tasksコマンドのテスト"""

    def test_show_tasks_with_no_tasks(self, capsys):
        """タスクがない場合の動作を確認"""
        args = MagicMock(
            status=None,
            agent=None,
            json=False,
        )

        with patch("orchestrator.core.task_tracker.TaskTracker") as mock_tracker_class:
            mock_tracker = MagicMock()
            mock_tracker.get_all_subtasks.return_value = []
            mock_tracker_class.return_value = mock_tracker

            show_tasks(args)

            captured = capsys.readouterr()
            assert "タスクが見つかりませんでした" in captured.out

    def test_show_tasks_with_tasks(self, capsys):
        """タスクがある場合の動作を確認"""
        from orchestrator.core.task_tracker import SubTask, TaskStatus

        args = MagicMock(
            status=None,
            agent=None,
            json=False,
        )

        tasks = [
            SubTask(
                id="task-001",
                description="テストタスク",
                assigned_to="eng1",
                status=TaskStatus.COMPLETED,
                result="完了",
            )
        ]

        with patch("orchestrator.core.task_tracker.TaskTracker") as mock_tracker_class:
            mock_tracker = MagicMock()
            mock_tracker.get_all_subtasks.return_value = tasks
            mock_tracker.get_summary.return_value = "1/1 サブタスク完了"
            mock_tracker_class.return_value = mock_tracker

            show_tasks(args)

            captured = capsys.readouterr()
            assert "タスク一覧" in captured.out
            assert "テストタスク" in captured.out

    def test_show_tasks_with_invalid_status(self, capsys):
        """無効なステータスを指定した場合の動作を確認"""
        from orchestrator.core.task_tracker import SubTask, TaskStatus

        args = MagicMock(
            status="invalid_status",
            agent=None,
            json=False,
        )

        # タスクを用意（ステータスフィルタ前にチェックされるように）
        tasks = [
            SubTask(
                id="task-001",
                description="テストタスク",
                assigned_to="eng1",
                status=TaskStatus.PENDING,
            )
        ]

        with patch("orchestrator.core.task_tracker.TaskTracker") as mock_tracker_class:
            mock_tracker = MagicMock()
            mock_tracker.get_all_subtasks.return_value = tasks
            mock_tracker_class.return_value = mock_tracker

            show_tasks(args)

            captured = capsys.readouterr()
            assert "無効なステータス" in captured.out
