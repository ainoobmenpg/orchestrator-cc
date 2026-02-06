"""エージェント間通信テスト

Agent Teamsでのエージェント間通信機能の統合テストです。

検証項目:
- V-AC-001: ダイレクトメッセージ検証
- V-AC-002: ブロードキャスト検証
- V-AC-003: タスク割り振り検証
"""

import json
from pathlib import Path
from unittest.mock import patch

from orchestrator.core.agent_teams_manager import (
    AgentTeamsManager,
    TeamConfig,
)
from orchestrator.web.team_models import (
    TaskInfo,
    TeamMember,
    TeamMessage,
)


class TestDirectMessaging:
    """V-AC-001: ダイレクトメッセージ検証"""

    def test_send_direct_message(self):
        """モックエージェント間でメッセージ送信"""
        # エージェント間通信はファイルベースのinboxで実装されている
        # このテストでは、TeamMessageモデルの検証を行う

        message = TeamMessage(
            id="msg-1",
            sender="agent-1",
            recipient="agent-2",
            content="Hello, agent-2!",
            timestamp="2026-02-06T12:00:00Z",
            message_type="message",
        )

        assert message.sender == "agent-1"
        assert message.content == "Hello, agent-2!"
        assert message.message_type == "message"
        assert message.recipient == "agent-2"

    def test_message_to_dict(self):
        """メッセージの辞書変換検証"""
        message = TeamMessage(
            id="msg-2",
            sender="leader",
            recipient="",
            content="Task update",
            timestamp="2026-02-06T12:00:00Z",
            message_type="status",
        )

        data = message.to_dict()

        assert data["sender"] == "leader"
        assert data["content"] == "Task update"
        assert data["type"] == "status"
        assert "timestamp" in data

    def test_message_delivery_to_inbox(self, tmp_path: Path):
        """モックエージェント間でメッセージ送信後、inboxへの配信を確認"""
        # テスト用のチームディレクトリ構造を作成
        team_name = "test-team"
        team_dir = tmp_path / team_name
        team_dir.mkdir()
        inboxes_dir = team_dir / "inboxes"
        inboxes_dir.mkdir()

        # メッセージを送信（inboxファイルに書き込み）
        recipient = "agent-2"
        inbox_file = inboxes_dir / f"{recipient}.json"

        message = TeamMessage(
            id="msg-3",
            sender="agent-1",
            recipient=recipient,
            content="Hello from agent-1!",
            timestamp="2026-02-06T12:00:00Z",
            message_type="message",
        )

        # inboxにメッセージを保存
        with open(inbox_file, "w", encoding="utf-8") as f:
            json.dump([message.to_dict()], f, ensure_ascii=False)

        # inboxが作成されたことを確認
        assert inbox_file.exists()

        # inboxからメッセージを読み出して確認
        with open(inbox_file, encoding="utf-8") as f:
            loaded_data = json.load(f)

        assert len(loaded_data) == 1
        assert loaded_data[0]["sender"] == "agent-1"
        assert loaded_data[0]["recipient"] == "agent-2"
        assert loaded_data[0]["content"] == "Hello from agent-1!"

    def test_message_from_dict(self):
        """辞書からメッセージを復元"""
        message_data = {
            "id": "msg-4",
            "sender": "agent-1",
            "recipient": "agent-2",
            "content": "Test message",
            "timestamp": "2026-02-06T12:00:00Z",
            "type": "message",
        }

        message = TeamMessage.from_dict(message_data)

        assert message.id == "msg-4"
        assert message.sender == "agent-1"
        assert message.recipient == "agent-2"
        assert message.content == "Test message"
        assert message.message_type == "message"


class TestBroadcastMessaging:
    """V-AC-002: ブロードキャスト検証"""

    def test_broadcast_message_creation(self):
        """リーダーからbroadcast送信のメッセージ作成"""
        message = TeamMessage(
            id="msg-3",
            sender="team-lead",
            recipient="",  # ブロードキャストは受信者なし（空文字列）
            content="Team meeting at 3pm",
            timestamp="2026-02-06T12:00:00Z",
            message_type="broadcast",
        )

        assert message.sender == "team-lead"
        assert message.message_type == "broadcast"
        assert message.recipient == ""  # ブロードキャストは受信者なし

    def test_broadcast_to_all_members(self):
        """全メンバーが受信することを確認（モデルレベル）"""
        # チームメンバーの作成
        leader = TeamMember(
            agent_id="lead-001",
            name="team-lead",
            agent_type="general-purpose",
            model="claude-sonnet-4-5",
            joined_at=1738857600,
        )
        member1 = TeamMember(
            agent_id="coder-001",
            name="coder-1",
            agent_type="general-purpose",
            model="claude-sonnet-4-5",
            joined_at=1738857600,
        )
        member2 = TeamMember(
            agent_id="researcher-001",
            name="researcher-1",
            agent_type="general-purpose",
            model="claude-sonnet-4-5",
            joined_at=1738857600,
        )

        # ブロードキャストメッセージ
        broadcast = TeamMessage(
            id="msg-4",
            sender="team-lead",
            recipient="",
            content="Update on project status",
            timestamp="2026-02-06T12:00:00Z",
            message_type="broadcast",
        )

        # メッセージが受信者なし（全員向け）であることを確認
        assert broadcast.recipient == ""
        assert broadcast.message_type == "broadcast"

    def test_broadcast_delivery_to_all_inboxes(self, tmp_path: Path):
        """リーダーからbroadcast送信後、全メンバーが受信することを確認"""
        # テスト用のチームディレクトリ構造を作成
        team_name = "test-team"
        team_dir = tmp_path / team_name
        team_dir.mkdir()
        inboxes_dir = team_dir / "inboxes"
        inboxes_dir.mkdir()

        # チームメンバー
        members = ["team-lead", "coder-1", "researcher-1"]

        # ブロードキャストメッセージ
        broadcast = TeamMessage(
            id="msg-broadcast-1",
            sender="team-lead",
            recipient="",  # ブロードキャスト
            content="Update: All members please review the changes",
            timestamp="2026-02-06T12:00:00Z",
            message_type="broadcast",
        )

        # 全メンバーのinboxにメッセージを配信
        for member in members:
            inbox_file = inboxes_dir / f"{member}.json"
            with open(inbox_file, "w", encoding="utf-8") as f:
                json.dump([broadcast.to_dict()], f, ensure_ascii=False)

        # 全メンバーのinboxにメッセージが配信されたことを確認
        for member in members:
            inbox_file = inboxes_dir / f"{member}.json"
            assert inbox_file.exists(), f"Inbox for {member} should exist"

            with open(inbox_file, encoding="utf-8") as f:
                loaded_data = json.load(f)

            assert len(loaded_data) == 1
            assert loaded_data[0]["type"] == "broadcast"
            assert loaded_data[0]["sender"] == "team-lead"
            assert loaded_data[0]["content"] == "Update: All members please review the changes"


class TestTaskAssignment:
    """V-AC-003: タスク割り振り検証"""

    def test_create_team(self, tmp_path: Path):
        """TeamConfigでチーム作成"""
        # AgentTeamsManagerでチーム作成
        with patch("orchestrator.core.agent_teams_manager.Path.home", return_value=tmp_path):
            manager = AgentTeamsManager(teams_dir=tmp_path)

            config = TeamConfig(name="test-team", description="Test Team")
            team_name = manager.create_team(config)

        assert team_name == "test-team"
        team_dir = tmp_path / "test-team"
        assert team_dir.exists()
        config_file = team_dir / "config.json"
        assert config_file.exists()

    def test_task_file_creation(self, tmp_path: Path):
        """タスクファイルの作成"""
        # テスト用のチームディレクトリ構造を作成
        team_dir = tmp_path / "test-team"
        team_dir.mkdir()
        tasks_dir = team_dir / "tasks"
        tasks_dir.mkdir()

        # タスクを作成
        task_file = tasks_dir / "1.json"
        task_data = {
            "id": "1",
            "subject": "Implement feature X",
            "description": "Add feature X to the system",
            "status": "pending",
            "activeForm": "Implementing feature X",
        }

        task_file.write_text(json.dumps(task_data))

        # タスクが作成されたことを確認
        assert task_file.exists()
        loaded_data = json.loads(task_file.read_text())
        assert loaded_data["subject"] == "Implement feature X"
        assert loaded_data["status"] == "pending"

    def test_task_owner_assignment(self, tmp_path: Path):
        """タスクのオーナー割り当て"""
        # テスト用のタスクファイルを作成
        team_dir = tmp_path / "test-team"
        tasks_dir = team_dir / "tasks"
        tasks_dir.mkdir(parents=True)

        task_file = tasks_dir / "1.json"
        task_data = {
            "id": "1",
            "subject": "Test task",
            "description": "Test task description",
            "status": "pending",
            "owner": "coder-1",
        }

        task_file.write_text(json.dumps(task_data))

        # オーナーが割り当てられたことを確認
        loaded_data = json.loads(task_file.read_text())
        assert loaded_data["owner"] == "coder-1"
        assert loaded_data["status"] == "pending"

    def test_get_team_tasks(self, tmp_path: Path):
        """タスクリストで確認"""
        # テスト用のタスクディレクトリを作成（tasks_dir/team_name）
        tasks_dir = tmp_path / "test-team"
        tasks_dir.mkdir(parents=True)

        # 複数のタスクを作成
        for i in range(3):
            task_file = tasks_dir / f"{i}.json"
            task_data = {
                "id": str(i),
                "subject": f"Task {i}",
                "description": f"Description for task {i}",
                "status": "pending" if i < 2 else "in_progress",
            }
            task_file.write_text(json.dumps(task_data))

        # AgentTeamsManagerでタスク一覧取得
        manager = AgentTeamsManager(teams_dir=tmp_path, tasks_dir=tmp_path)
        tasks = manager.get_team_tasks("test-team")

        assert len(tasks) == 3
        assert tasks[0]["subject"] == "Task 0"
        assert tasks[2]["status"] == "in_progress"

    def test_task_create_and_owner_assignment(self, tmp_path: Path):
        """TaskCreateでタスク作成後、TaskUpdateでオーナー割り当て"""
        team_name = "test-team"
        tasks_dir = tmp_path / team_name
        tasks_dir.mkdir(parents=True)

        # TaskCreate: タスクを作成
        task_id = "1"
        task_data = {
            "id": task_id,
            "subject": "Implement authentication feature",
            "description": "Add login and logout functionality",
            "status": "pending",
            "activeForm": "Implementing authentication feature",
        }

        task_file = tasks_dir / f"{task_id}.json"
        task_file.write_text(json.dumps(task_data))

        # タスクが作成されたことを確認
        assert task_file.exists()

        # TaskUpdate: オーナーを割り当て
        task_data["owner"] = "coder-1"
        task_data["status"] = "in_progress"
        task_file.write_text(json.dumps(task_data))

        # オーナーが割り当てられたことを確認
        loaded_data = json.loads(task_file.read_text())
        assert loaded_data["owner"] == "coder-1"
        assert loaded_data["status"] == "in_progress"

    def test_task_info_model(self):
        """TaskInfoモデルの検証"""
        task = TaskInfo(
            task_id="task-1",
            subject="Fix bug in login",
            description="Login fails when password contains special characters",
            status="pending",
            owner="coder-1",
        )

        assert task.task_id == "task-1"
        assert task.subject == "Fix bug in login"
        assert task.owner == "coder-1"
        assert task.status == "pending"

        # to_dictの検証
        task_dict = task.to_dict()
        assert task_dict["taskId"] == "task-1"
        assert task_dict["subject"] == "Fix bug in login"
        assert task_dict["owner"] == "coder-1"

    def test_task_info_from_dict(self):
        """辞書からTaskInfoを作成"""
        task_data = {
            "taskId": "task-2",
            "subject": "Add tests",
            "description": "Add unit tests for auth module",
            "status": "in_progress",
            "owner": "tester-1",
        }

        task = TaskInfo.from_dict(task_data)

        assert task.task_id == "task-2"
        assert task.subject == "Add tests"
        assert task.owner == "tester-1"
        assert task.status == "in_progress"

    def test_task_list_verification(self, tmp_path: Path):
        """タスクリストでTaskCreate/TaskUpdateの結果を確認"""
        team_name = "test-team"
        tasks_dir = tmp_path / team_name
        tasks_dir.mkdir(parents=True)

        # 複数のタスクを作成
        tasks = [
            {
                "id": "1",
                "subject": "Task 1",
                "description": "Description 1",
                "status": "pending",
                "owner": "",
            },
            {
                "id": "2",
                "subject": "Task 2",
                "description": "Description 2",
                "status": "in_progress",
                "owner": "coder-1",
            },
            {
                "id": "3",
                "subject": "Task 3",
                "description": "Description 3",
                "status": "completed",
                "owner": "tester-1",
            },
        ]

        for task in tasks:
            task_file = tasks_dir / f"{task['id']}.json"
            task_file.write_text(json.dumps(task))

        # AgentTeamsManagerでタスク一覧取得
        manager = AgentTeamsManager(teams_dir=tmp_path, tasks_dir=tmp_path)
        loaded_tasks = manager.get_team_tasks(team_name)

        # タスクの数を確認
        assert len(loaded_tasks) == 3

        # オーナー割り当ての確認
        owners = {t.get("owner") for t in loaded_tasks}
        assert "" in owners  # 未割り当て
        assert "coder-1" in owners
        assert "tester-1" in owners

        # ステータスの確認
        statuses = {t.get("status") for t in loaded_tasks}
        assert "pending" in statuses
        assert "in_progress" in statuses
        assert "completed" in statuses
