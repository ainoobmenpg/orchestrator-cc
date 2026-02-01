"""TaskTrackerの単体テスト"""

import pytest

from orchestrator.core.task_tracker import SubTask, TaskStatus, TaskTracker


class TestTaskStatus:
    """TaskStatus列挙型のテスト"""

    def test_status_values(self) -> None:
        """各状態の値が正しいことを確認"""
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.IN_PROGRESS == "in_progress"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"


class TestSubTask:
    """SubTaskデータクラスのテスト"""

    def test_creation(self) -> None:
        """サブタスクを作成"""
        subtask = SubTask(
            id="test_task",
            description="テストタスク",
            assigned_to="test_agent",
        )
        assert subtask.id == "test_task"
        assert subtask.description == "テストタスク"
        assert subtask.assigned_to == "test_agent"
        assert subtask.status == TaskStatus.PENDING
        assert subtask.result is None
        assert subtask.completed_at is None

    def test_creation_with_result(self) -> None:
        """結果を指定してサブタスクを作成"""
        subtask = SubTask(
            id="test_task",
            description="テストタスク",
            assigned_to="test_agent",
            status=TaskStatus.COMPLETED,
            result="完了しました",
        )
        assert subtask.status == TaskStatus.COMPLETED
        assert subtask.result == "完了しました"


class TestTaskTracker:
    """TaskTrackerクラスのテスト"""

    def test_init(self) -> None:
        """初期化"""
        tracker = TaskTracker()
        assert tracker.get_all_subtasks() == []

    def test_create_subtask(self) -> None:
        """サブタスクを作成"""
        tracker = TaskTracker()
        subtask = tracker.create_subtask("テストタスク", "agent_a")

        assert subtask.id == "agent_a_0"
        assert subtask.description == "テストタスク"
        assert subtask.assigned_to == "agent_a"
        assert subtask.status == TaskStatus.PENDING

    def test_create_multiple_subtasks(self) -> None:
        """複数のサブタスクを作成"""
        tracker = TaskTracker()
        subtask1 = tracker.create_subtask("タスク1", "agent_a")
        subtask2 = tracker.create_subtask("タスク2", "agent_b")

        assert subtask1.id == "agent_a_0"
        assert subtask2.id == "agent_b_1"
        assert len(tracker.get_all_subtasks()) == 2

    def test_update_status(self) -> None:
        """サブタスクの状態を更新"""
        tracker = TaskTracker()
        subtask = tracker.create_subtask("テストタスク", "agent_a")

        tracker.update_status(subtask.id, TaskStatus.IN_PROGRESS)
        assert subtask.status == TaskStatus.IN_PROGRESS

        tracker.update_status(subtask.id, TaskStatus.COMPLETED, result="完了")
        assert subtask.status == TaskStatus.COMPLETED
        assert subtask.result == "完了"
        assert subtask.completed_at is not None

    def test_update_status_with_result(self) -> None:
        """結果を指定して状態を更新"""
        tracker = TaskTracker()
        subtask = tracker.create_subtask("テストタスク", "agent_a")

        tracker.update_status(subtask.id, TaskStatus.COMPLETED, result="成功しました")
        assert subtask.result == "成功しました"

    def test_get_progress(self) -> None:
        """進捗状況を取得"""
        tracker = TaskTracker()
        subtask1 = tracker.create_subtask("タスク1", "agent_a")
        subtask2 = tracker.create_subtask("タスク2", "agent_b")
        subtask3 = tracker.create_subtask("タスク3", "agent_c")

        tracker.update_status(subtask1.id, TaskStatus.COMPLETED)
        tracker.update_status(subtask2.id, TaskStatus.IN_PROGRESS)

        progress = tracker.get_progress()
        assert progress[subtask1.id] == TaskStatus.COMPLETED
        assert progress[subtask2.id] == TaskStatus.IN_PROGRESS
        assert progress[subtask3.id] == TaskStatus.PENDING

    def test_get_summary(self) -> None:
        """進捗サマリーを取得"""
        tracker = TaskTracker()
        subtask1 = tracker.create_subtask("タスク1", "agent_a")
        subtask2 = tracker.create_subtask("タスク2", "agent_b")
        subtask3 = tracker.create_subtask("タスク3", "agent_c")

        assert tracker.get_summary() == "0/3 サブタスク完了"

        tracker.update_status(subtask1.id, TaskStatus.COMPLETED)
        assert tracker.get_summary() == "1/3 サブタスク完了"

        tracker.update_status(subtask2.id, TaskStatus.COMPLETED)
        assert tracker.get_summary() == "2/3 サブタスク完了"

    def test_get_subtask(self) -> None:
        """指定されたサブタスクを取得"""
        tracker = TaskTracker()
        subtask = tracker.create_subtask("テストタスク", "agent_a")

        retrieved = tracker.get_subtask(subtask.id)
        assert retrieved is subtask

        # 存在しないタスク
        assert tracker.get_subtask("nonexistent") is None

    def test_get_all_subtasks(self) -> None:
        """すべてのサブタスクを取得"""
        tracker = TaskTracker()
        subtask1 = tracker.create_subtask("タスク1", "agent_a")
        subtask2 = tracker.create_subtask("タスク2", "agent_b")

        subtasks = tracker.get_all_subtasks()
        assert len(subtasks) == 2
        assert subtask1 in subtasks
        assert subtask2 in subtasks

    def test_get_subtasks_by_agent(self) -> None:
        """指定されたエージェントのサブタスクを取得"""
        tracker = TaskTracker()
        subtask1 = tracker.create_subtask("タスク1", "agent_a")
        subtask2 = tracker.create_subtask("タスク2", "agent_a")
        subtask3 = tracker.create_subtask("タスク3", "agent_b")

        agent_a_tasks = tracker.get_subtasks_by_agent("agent_a")
        agent_b_tasks = tracker.get_subtasks_by_agent("agent_b")

        assert len(agent_a_tasks) == 2
        assert len(agent_b_tasks) == 1
        assert subtask1 in agent_a_tasks
        assert subtask2 in agent_a_tasks
        assert subtask3 in agent_b_tasks

    def test_get_subtasks_by_agent_empty(self) -> None:
        """存在しないエージェントのサブタスクを取得"""
        tracker = TaskTracker()
        tasks = tracker.get_subtasks_by_agent("nonexistent")
        assert tasks == []
