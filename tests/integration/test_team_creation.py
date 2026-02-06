"""チーム作成・削除の統合テスト

V-TM-001: チーム作成検証
V-TM-002: チーム削除検証
"""

import json
from pathlib import Path

from orchestrator.core.agent_teams_manager import AgentTeamsManager, TeamConfig


class TestTeamCreation:
    """チーム作成の統合テスト (V-TM-001)"""

    def test_v_tm_001_create_team_creates_config_json(self, tmp_path: Path):
        """V-TM-001-1: CLI create-team でチーム作成し、config.json の存在と内容を確認"""
        teams_dir = tmp_path / "teams"
        tasks_dir = tmp_path / "tasks"
        teams_dir.mkdir(parents=True)
        tasks_dir.mkdir(parents=True)

        manager = AgentTeamsManager(teams_dir=teams_dir, tasks_dir=tasks_dir)

        config = TeamConfig(
            name="issue15-verification",
            description="Issue #15検証用チーム",
            agent_type="general-purpose",
            members=[
                {
                    "name": "team-lead",
                    "agentType": "general-purpose",
                    "timeoutThreshold": 300.0,
                },
            ],
        )

        # チームを作成
        team_name = manager.create_team(config)

        # 検証: チーム名が正しいこと
        assert team_name == "issue15-verification"

        # 検証: config.json が存在すること
        config_file = teams_dir / team_name / "config.json"
        assert config_file.exists(), f"config.json not found at {config_file}"

        # 検証: config.json の内容を確認
        with open(config_file, encoding="utf-8") as f:
            config_data = json.load(f)

        assert config_data["name"] == "issue15-verification"
        assert config_data["description"] == "Issue #15検証用チーム"
        assert "members" in config_data
        assert len(config_data["members"]) == 1
        assert config_data["members"][0]["name"] == "team-lead"
        assert config_data["members"][0]["agentType"] == "general-purpose"

    def test_v_tm_001_2_team_registered_in_health_monitor(self, tmp_path: Path):
        """V-TM-001-2: ヘルスモニターへの登録を確認"""
        teams_dir = tmp_path / "teams"
        tasks_dir = tmp_path / "tasks"
        teams_dir.mkdir(parents=True)
        tasks_dir.mkdir(parents=True)

        manager = AgentTeamsManager(teams_dir=teams_dir, tasks_dir=tasks_dir)

        config = TeamConfig(
            name="health-monitor-test-team",
            description="ヘルスモニター登録検証用チーム",
            agent_type="general-purpose",
            members=[
                {
                    "name": "team-lead",
                    "agentType": "general-purpose",
                    "timeoutThreshold": 300.0,
                },
                {
                    "name": "worker",
                    "agentType": "general-purpose",
                    "timeoutThreshold": 600.0,
                },
            ],
        )

        # チームを作成
        team_name = manager.create_team(config)

        # ヘルスモニターの状態を取得
        health_monitor = manager._health_monitor
        status = health_monitor.get_health_status()

        # 検証: チームがヘルスモニターに登録されていること
        assert team_name in status, f"Team '{team_name}' not found in health monitor status"

        # 検証: メンバーが登録されていること
        team_status = status[team_name]
        assert "team-lead" in team_status
        assert "worker" in team_status

        # 検証: timeoutThreshold が正しく設定されていること
        assert team_status["team-lead"]["timeoutThreshold"] == 300.0
        assert team_status["worker"]["timeoutThreshold"] == 600.0

    def test_v_tm_001_3_multiple_members_registration(self, tmp_path: Path):
        """V-TM-001-3: 複数メンバーの登録を確認"""
        teams_dir = tmp_path / "teams"
        tasks_dir = tmp_path / "tasks"
        teams_dir.mkdir(parents=True)
        tasks_dir.mkdir(parents=True)

        manager = AgentTeamsManager(teams_dir=teams_dir, tasks_dir=tasks_dir)

        config = TeamConfig(
            name="multi-member-team",
            description="複数メンバーテスト",
            agent_type="general-purpose",
            members=[
                {"name": "agent1", "agentType": "general-purpose", "timeoutThreshold": 100.0},
                {"name": "agent2", "agentType": "general-purpose", "timeoutThreshold": 200.0},
                {"name": "agent3", "agentType": "general-purpose", "timeoutThreshold": 300.0},
            ],
        )

        team_name = manager.create_team(config)

        # config.json でメンバーが正しく保存されていることを確認
        config_file = teams_dir / team_name / "config.json"
        with open(config_file, encoding="utf-8") as f:
            config_data = json.load(f)

        assert len(config_data["members"]) == 3

        # ヘルスモニターで全メンバーが登録されていることを確認
        health_monitor = manager._health_monitor
        status = health_monitor.get_health_status()

        assert "agent1" in status[team_name]
        assert "agent2" in status[team_name]
        assert "agent3" in status[team_name]


class TestTeamDeletion:
    """チーム削除の統合テスト (V-TM-002)"""

    def test_v_tm_002_1_delete_team_removes_team_directory(self, tmp_path: Path):
        """V-TM-002-1: チーム削除でディレクトリが削除されることを確認"""
        teams_dir = tmp_path / "teams"
        tasks_dir = tmp_path / "tasks"
        teams_dir.mkdir(parents=True)
        tasks_dir.mkdir(parents=True)

        manager = AgentTeamsManager(teams_dir=teams_dir, tasks_dir=tasks_dir)

        # テストチームを作成
        config = TeamConfig(
            name="delete-test-team",
            description="削除テスト用チーム",
            agent_type="general-purpose",
            members=[
                {"name": "agent1", "agentType": "general-purpose", "timeoutThreshold": 300.0},
            ],
        )

        team_name = manager.create_team(config)
        team_dir = teams_dir / team_name

        # チームディレクトリが存在することを確認
        assert team_dir.exists()
        assert (team_dir / "config.json").exists()

        # チームを削除
        result = manager.delete_team(team_name)
        assert result is True

        # チームディレクトリが削除されたことを確認
        assert not team_dir.exists()

    def test_v_tm_002_2_delete_team_removes_task_directory(self, tmp_path: Path):
        """V-TM-002-2: チーム削除でタスクディレクトリも削除されることを確認"""
        teams_dir = tmp_path / "teams"
        tasks_dir = tmp_path / "tasks"
        teams_dir.mkdir(parents=True)
        tasks_dir.mkdir(parents=True)

        manager = AgentTeamsManager(teams_dir=teams_dir, tasks_dir=tasks_dir)

        # テストチームを作成
        config = TeamConfig(
            name="task-delete-test-team",
            description="タスク削除テスト用チーム",
            agent_type="general-purpose",
            members=[
                {"name": "agent1", "agentType": "general-purpose", "timeoutThreshold": 300.0},
            ],
        )

        team_name = manager.create_team(config)

        # タスクディレクトリにテストファイルを作成
        task_dir = tasks_dir / team_name
        task_dir.mkdir(parents=True, exist_ok=True)
        test_task_file = task_dir / "test-task.json"
        with open(test_task_file, "w", encoding="utf-8") as f:
            json.dump({"id": "test-task", "subject": "Test Task"}, f)

        # タスクファイルが存在することを確認
        assert test_task_file.exists()

        # チームを削除
        result = manager.delete_team(team_name)
        assert result is True

        # タスクディレクトリも削除されたことを確認
        assert not task_dir.exists()

    def test_v_tm_002_3_delete_nonexistent_team_returns_false(self, tmp_path: Path):
        """V-TM-002-3: 存在しないチームの削除で False が返ることを確認"""
        teams_dir = tmp_path / "teams"
        tasks_dir = tmp_path / "tasks"
        teams_dir.mkdir(parents=True)
        tasks_dir.mkdir(parents=True)

        manager = AgentTeamsManager(teams_dir=teams_dir, tasks_dir=tasks_dir)

        # 存在しないチームを削除しようとすると False が返る
        result = manager.delete_team("nonexistent-team")
        assert result is False

    def test_v_tm_002_4_delete_team_idempotent(self, tmp_path: Path):
        """V-TM-002-4: 同じチームを2回削除してもエラーにならないことを確認（べき等性）"""
        teams_dir = tmp_path / "teams"
        tasks_dir = tmp_path / "tasks"
        teams_dir.mkdir(parents=True)
        tasks_dir.mkdir(parents=True)

        manager = AgentTeamsManager(teams_dir=teams_dir, tasks_dir=tasks_dir)

        # チームを作成
        config = TeamConfig(
            name="idempotent-test-team",
            description="べき等性テスト用チーム",
            agent_type="general-purpose",
            members=[
                {"name": "agent1", "agentType": "general-purpose", "timeoutThreshold": 300.0},
            ],
        )

        team_name = manager.create_team(config)

        # 1回目の削除
        result1 = manager.delete_team(team_name)
        assert result1 is True
        assert not (teams_dir / team_name).exists()

        # 2回目の削除（既に削除済み）
        result2 = manager.delete_team(team_name)
        assert result2 is False
