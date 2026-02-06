"""タスク管理テスト

Agent Teamsでのタスク管理機能の統合テストです。

検証項目:
- V-TS-001: タスク依存関係検証
- V-TS-002: タスク自動割り振り検証
"""

from pathlib import Path

from orchestrator.core.agent_teams_manager import AgentTeamsManager


class TestTaskDependencies:
    """V-TS-001: タスク依存関係検証"""

    def test_task_dependency_chain(self, tmp_path: Path):
        """タスクA→B→Cの依存チェーン作成"""
        # テスト用のタスクディレクトリを作成（tasks_dir/team_name）
        tasks_dir = tmp_path / "test-team"
        tasks_dir.mkdir(parents=True)

        import json

        # タスクA（依存なし）
        task_a = {
            "id": "a",
            "subject": "Task A",
            "description": "First task",
            "status": "pending",
            "blockedBy": [],
        }
        (tasks_dir / "a.json").write_text(json.dumps(task_a))

        # タスクB（Aに依存）
        task_b = {
            "id": "b",
            "subject": "Task B",
            "description": "Second task",
            "status": "pending",
            "blockedBy": ["a"],
        }
        (tasks_dir / "b.json").write_text(json.dumps(task_b))

        # タスクC（Bに依存）
        task_c = {
            "id": "c",
            "subject": "Task C",
            "description": "Third task",
            "status": "pending",
            "blockedBy": ["b"],
        }
        (tasks_dir / "c.json").write_text(json.dumps(task_c))

        # タスク一覧取得
        manager = AgentTeamsManager(teams_dir=tmp_path, tasks_dir=tmp_path)
        tasks = manager.get_team_tasks("test-team")

        # 依存関係が正しく設定されていることを確認
        assert len(tasks) == 3

        task_a_data = next((t for t in tasks if t["id"] == "a"), None)
        task_b_data = next((t for t in tasks if t["id"] == "b"), None)
        task_c_data = next((t for t in tasks if t["id"] == "c"), None)

        assert task_a_data is not None
        assert task_b_data is not None
        assert task_c_data is not None
        assert task_b_data["blockedBy"] == ["a"]
        assert task_c_data["blockedBy"] == ["b"]

    def test_multiple_blocking_tasks(self, tmp_path: Path):
        """複数のタスクによるブロック"""
        tasks_dir = tmp_path / "test-team"
        tasks_dir.mkdir(parents=True)

        import json

        # タスクXとY（並列実行可能）
        task_x = {
            "id": "x",
            "subject": "Task X",
            "description": "Parallel task 1",
            "status": "pending",
            "blockedBy": [],
        }
        (tasks_dir / "x.json").write_text(json.dumps(task_x))

        task_y = {
            "id": "y",
            "subject": "Task Y",
            "description": "Parallel task 2",
            "status": "pending",
            "blockedBy": [],
        }
        (tasks_dir / "y.json").write_text(json.dumps(task_y))

        # タスクZ（XとYの両方が完了する必要がある）
        task_z = {
            "id": "z",
            "subject": "Task Z",
            "description": "Depends on X and Y",
            "status": "pending",
            "blockedBy": ["x", "y"],
        }
        (tasks_dir / "z.json").write_text(json.dumps(task_z))

        # 依存関係の確認
        manager = AgentTeamsManager(teams_dir=tmp_path, tasks_dir=tmp_path)
        tasks = manager.get_team_tasks("test-team")

        task_z_data = next((t for t in tasks if t["id"] == "z"), None)
        assert task_z_data is not None
        assert set(task_z_data["blockedBy"]) == {"x", "y"}

    def test_empty_blocked_by(self, tmp_path: Path):
        """blockedByが空の場合は実行可能"""
        tasks_dir = tmp_path / "test-team"
        tasks_dir.mkdir(parents=True)

        import json

        task = {
            "id": "ready",
            "subject": "Ready to execute",
            "description": "No dependencies",
            "status": "pending",
            "blockedBy": [],
        }
        (tasks_dir / "ready.json").write_text(json.dumps(task))

        # blockedByが空であることを確認
        manager = AgentTeamsManager(teams_dir=tmp_path, tasks_dir=tmp_path)
        tasks = manager.get_team_tasks("test-team")

        assert len(tasks) == 1
        assert tasks[0]["blockedBy"] == []
        assert tasks[0]["status"] == "pending"


class TestTaskAutoAssignment:
    """V-TS-002: タスク自動割り振り検証"""

    def test_task_without_owner(self, tmp_path: Path):
        """オーナーなしタスクの状態確認"""
        tasks_dir = tmp_path / "test-team"
        tasks_dir.mkdir(parents=True)

        import json

        # オーナーなしのタスクを作成
        task = {
            "id": "unassigned",
            "subject": "Unassigned task",
            "description": "Task without owner",
            "status": "pending",
            "blockedBy": [],
        }
        (tasks_dir / "unassigned.json").write_text(json.dumps(task))

        # オーナーがNoneであることを確認
        manager = AgentTeamsManager(teams_dir=tmp_path, tasks_dir=tmp_path)
        tasks = manager.get_team_tasks("test-team")

        assert len(tasks) == 1
        assert "owner" not in tasks[0] or tasks[0].get("owner") is None
        assert tasks[0]["status"] == "pending"

    def test_task_status_filtering(self, tmp_path: Path):
        """ステータスによるタスクフィルタリング"""
        tasks_dir = tmp_path / "test-team"
        tasks_dir.mkdir(parents=True)

        import json

        # 異なるステータスのタスクを作成
        for i, status in enumerate(["pending", "in_progress", "completed"]):
            task = {
                "id": f"task-{i}",
                "subject": f"Task {i}",
                "description": f"Task with status {status}",
                "status": status,
            }
            (tasks_dir / f"task-{i}.json").write_text(json.dumps(task))

        # 全タスク取得
        manager = AgentTeamsManager(teams_dir=tmp_path, tasks_dir=tmp_path)
        all_tasks = manager.get_team_tasks("test-team")

        assert len(all_tasks) == 3

        # ステータスでフィルタリング
        pending_tasks = [t for t in all_tasks if t["status"] == "pending"]
        in_progress_tasks = [t for t in all_tasks if t["status"] == "in_progress"]
        completed_tasks = [t for t in all_tasks if t["status"] == "completed"]

        assert len(pending_tasks) == 1
        assert len(in_progress_tasks) == 1
        assert len(completed_tasks) == 1

    def test_update_task_status(self, tmp_path: Path):
        """タスクステータスの更新"""
        tasks_dir = tmp_path / "test-team"
        tasks_dir.mkdir(parents=True)

        import json

        # 初期タスク
        task = {
            "id": "update-test",
            "subject": "Update test",
            "description": "Test status update",
            "status": "pending",
            "owner": None,
        }
        task_file = tasks_dir / "update-test.json"
        task_file.write_text(json.dumps(task))

        # ステータスを更新
        task["status"] = "in_progress"
        task["owner"] = "agent-1"
        task_file.write_text(json.dumps(task))

        # 更新を確認
        manager = AgentTeamsManager(teams_dir=tmp_path, tasks_dir=tmp_path)
        tasks = manager.get_team_tasks("test-team")

        assert len(tasks) == 1
        assert tasks[0]["status"] == "in_progress"
        assert tasks[0]["owner"] == "agent-1"
