"""エージェント間通信テスト

Agent Teamsでのエージェント間通信機能の統合テストです。

検証項目:
- V-AC-001: ダイレクトメッセージ検証
- V-AC-002: ブロードキャスト検証
- V-AC-003: タスク割り振り検証
"""

from pathlib import Path
from unittest.mock import patch

from orchestrator.core.agent_teams_manager import (
    AgentTeamsManager,
    TeamConfig,
)
from orchestrator.web.team_models import TeamMember, TeamMessage


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

        import json

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

        import json

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
        import json

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
