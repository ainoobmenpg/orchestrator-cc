"""タスク追跡モジュール

このモジュールでは、タスクの進捗を追跡するTaskTrackerクラスを定義します。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """タスクの状態列挙型"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SubTask:
    """サブタスクの状態管理

    Attributes:
        id: サブタスクID
        description: サブタスクの説明
        assigned_to: 担当エージェント名
        status: タスク状態
        result: サブタスクの結果
        created_at: 作成日時
        completed_at: 完了日時
    """

    id: str
    description: str
    assigned_to: str
    status: TaskStatus = TaskStatus.PENDING
    result: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str | None = None


class TaskTracker:
    """タスクの進捗を追跡するクラス

    複数のサブタスクの状態を管理し、進捗状況を追跡します。

    Attributes:
        _subtasks: サブタスクの辞書（キーはタスクID）
    """

    def __init__(self) -> None:
        """TaskTrackerを初期化します。"""
        self._subtasks: dict[str, SubTask] = {}

    def create_subtask(self, description: str, assigned_to: str) -> SubTask:
        """サブタスクを作成します。

        Args:
            description: サブタスクの説明
            assigned_to: 担当エージェント名

        Returns:
            作成されたサブタスク
        """
        task_id = f"{assigned_to}_{len(self._subtasks)}"
        subtask = SubTask(
            id=task_id,
            description=description,
            assigned_to=assigned_to,
        )
        self._subtasks[task_id] = subtask
        return subtask

    def update_status(
        self, task_id: str, status: TaskStatus, result: str | None = None
    ) -> None:
        """サブタスクの状態を更新します。

        Args:
            task_id: サブタスクID
            status: 新しい状態
            result: 結果（オプション）
        """
        if task_id in self._subtasks:
            self._subtasks[task_id].status = status
            if result:
                self._subtasks[task_id].result = result
            if status == TaskStatus.COMPLETED:
                self._subtasks[task_id].completed_at = datetime.now().isoformat()

    def get_progress(self) -> dict[str, TaskStatus]:
        """進捗状況を取得します。

        Returns:
            タスクIDと状態の辞書
        """
        return {task_id: task.status for task_id, task in self._subtasks.items()}

    def get_summary(self) -> str:
        """進捗サマリーを取得します。

        Returns:
            進捗サマリー文字列（例: "2/3 サブタスク完了"）
        """
        total = len(self._subtasks)
        completed = sum(1 for t in self._subtasks.values() if t.status == TaskStatus.COMPLETED)
        return f"{completed}/{total} サブタスク完了"

    def get_subtask(self, task_id: str) -> SubTask | None:
        """指定されたサブタスクを取得します。

        Args:
            task_id: サブタスクID

        Returns:
            サブタスク（存在しない場合はNone）
        """
        return self._subtasks.get(task_id)

    def get_all_subtasks(self) -> list[SubTask]:
        """すべてのサブタスクを取得します。

        Returns:
            すべてのサブタスクのリスト
        """
        return list(self._subtasks.values())

    def get_subtasks_by_agent(self, agent_name: str) -> list[SubTask]:
        """指定されたエージェントのサブタスクを取得します。

        Args:
            agent_name: エージェント名

        Returns:
            指定されたエージェントに割り当てられたサブタスクのリスト
        """
        return [t for t in self._subtasks.values() if t.assigned_to == agent_name]
