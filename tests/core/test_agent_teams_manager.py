"""Agent Teams Manager テスト

このモジュールでは、AgentTeamsManagerの単体テストを行います。
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from orchestrator.core.agent_teams_manager import (
    AgentTeamsManager,
    TeamConfig,
    get_agent_teams_manager,
)


class TestTeamConfig:
    """TeamConfigのテスト"""

    def test_initialization(self) -> None:
        """初期化テスト"""
        config = TeamConfig(
            name="test-team",
            description="Test team",
            agent_type="general-purpose",
            members=[
                {"name": "agent1", "agentType": "general-purpose"},
                {"name": "agent2", "agentType": "coding"},
            ],
        )

        assert config.name == "test-team"
        assert config.description == "Test team"
        assert config.agent_type == "general-purpose"
        assert len(config.members) == 2

    def test_to_dict(self) -> None:
        """to_dictメソッドのテスト"""
        config = TeamConfig(
            name="test-team",
            description="Test team",
            agent_type="general-purpose",
            members=[{"name": "agent1"}],
        )

        data = config.to_dict()

        assert data["name"] == "test-team"
        assert data["description"] == "Test team"
        assert data["agentType"] == "general-purpose"
        assert len(data["members"]) == 1


class TestAgentTeamsManager:
    """AgentTeamsManagerのテスト"""

    def test_initialization(self) -> None:
        """初期化テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            teams_dir = Path(tmpdir) / "teams"
            tasks_dir = Path(tmpdir) / "tasks"

            AgentTeamsManager(
                teams_dir=teams_dir,
                tasks_dir=tasks_dir,
            )

            assert teams_dir.exists()
            assert tasks_dir.exists()

    def test_create_team(self) -> None:
        """チーム作成テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            teams_dir = Path(tmpdir) / "teams"
            tasks_dir = Path(tmpdir) / "tasks"

            manager = AgentTeamsManager(
                teams_dir=teams_dir,
                tasks_dir=tasks_dir,
            )

            config = TeamConfig(
                name="test-team",
                description="Test team",
                agent_type="general-purpose",
                members=[
                    {
                        "name": "team-lead",
                        "agentType": "general-purpose",
                        "model": "claude-opus-4-6",
                    },
                ],
            )

            team_name = manager.create_team(config)

            assert team_name == "test-team"

            # config.jsonが作成されている
            config_file = teams_dir / "test-team" / "config.json"
            assert config_file.exists()

            # 内容を確認
            with open(config_file, encoding="utf-8") as f:
                data = json.load(f)

            assert data["name"] == "test-team"
            assert data["description"] == "Test team"
            assert len(data["members"]) == 1

    def test_create_team_already_exists(self) -> None:
        """既存チームの作成テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            teams_dir = Path(tmpdir) / "teams"
            tasks_dir = Path(tmpdir) / "tasks"

            manager = AgentTeamsManager(
                teams_dir=teams_dir,
                tasks_dir=tasks_dir,
            )

            config = TeamConfig(
                name="test-team",
                description="Test team",
            )

            manager.create_team(config)
            manager.create_team(config)  # 重複呼び出し

            # エラーにならずに既存のチーム名を返す
            assert manager.create_team(config) == "test-team"

    def test_delete_team(self) -> None:
        """チーム削除テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            teams_dir = Path(tmpdir) / "teams"
            tasks_dir = Path(tmpdir) / "tasks"

            manager = AgentTeamsManager(
                teams_dir=teams_dir,
                tasks_dir=tasks_dir,
            )

            config = TeamConfig(
                name="test-team",
                description="Test team",
            )

            manager.create_team(config)

            # チームを削除
            result = manager.delete_team("test-team")

            assert result is True

            # ディレクトリが削除されている
            team_dir = teams_dir / "test-team"
            assert not team_dir.exists()

    def test_delete_team_not_found(self) -> None:
        """存在しないチームの削除テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            teams_dir = Path(tmpdir) / "teams"
            tasks_dir = Path(tmpdir) / "tasks"

            manager = AgentTeamsManager(
                teams_dir=teams_dir,
                tasks_dir=tasks_dir,
            )

            result = manager.delete_team("non-existent")

            assert result is False

    def test_get_team_tasks_empty(self) -> None:
        """空のタスクリスト取得テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            teams_dir = Path(tmpdir) / "teams"
            tasks_dir = Path(tmpdir) / "tasks"

            manager = AgentTeamsManager(
                teams_dir=teams_dir,
                tasks_dir=tasks_dir,
            )

            tasks = manager.get_team_tasks("test-team")

            assert tasks == []

    def test_get_team_tasks_with_data(self) -> None:
        """タスクありのリスト取得テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            teams_dir = Path(tmpdir) / "teams"
            tasks_dir = Path(tmpdir) / "tasks"

            manager = AgentTeamsManager(
                teams_dir=teams_dir,
                tasks_dir=tasks_dir,
            )

            # タスクファイルを作成
            team_tasks_dir = tasks_dir / "test-team"
            team_tasks_dir.mkdir(parents=True)

            task_file = team_tasks_dir / "task1.json"
            task_data = {
                "id": "task1",
                "subject": "Test task",
                "description": "Test description",
                "status": "pending",
            }

            with open(task_file, "w", encoding="utf-8") as f:
                json.dump(task_data, f)

            # タスクを取得
            tasks = manager.get_team_tasks("test-team")

            assert len(tasks) == 1
            assert tasks[0]["id"] == "task1"

    def test_get_team_status_not_found(self) -> None:
        """存在しないチームの状態取得テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            teams_dir = Path(tmpdir) / "teams"
            tasks_dir = Path(tmpdir) / "tasks"

            manager = AgentTeamsManager(
                teams_dir=teams_dir,
                tasks_dir=tasks_dir,
            )

            status = manager.get_team_status("non-existent")

            assert "error" in status

    def test_update_agent_activity(self) -> None:
        """エージェントアクティビティ更新テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            teams_dir = Path(tmpdir) / "teams"
            tasks_dir = Path(tmpdir) / "tasks"

            manager = AgentTeamsManager(
                teams_dir=teams_dir,
                tasks_dir=tasks_dir,
            )

            # アクティビティ更新（エラーにならない）
            manager.update_agent_activity("test-team", "test-agent")

    def test_restart_agent(self) -> None:
        """エージェント再起動テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            teams_dir = Path(tmpdir) / "teams"
            tasks_dir = Path(tmpdir) / "tasks"

            manager = AgentTeamsManager(
                teams_dir=teams_dir,
                tasks_dir=tasks_dir,
            )

            result = manager.restart_agent("test-team", "test-agent")

            assert result is True


class TestSingleton:
    """シングルトン機能のテスト"""

    def test_get_agent_teams_manager_singleton(self) -> None:
        """シングルトンインスタンスのテスト"""
        manager1 = get_agent_teams_manager()
        manager2 = get_agent_teams_manager()

        assert manager1 is manager2

    @patch("orchestrator.core.agent_teams_manager._teams_manager", None)
    def test_singleton_creates_new_instance(self) -> None:
        """新規インスタンス作成のテスト"""
        # グローバルインスタンスをリセットしてテスト
        import importlib

        import orchestrator.core.agent_teams_manager as module

        # モジュールをリロードしてシングルトンをリセット
        importlib.reload(module)

        manager1 = module.get_agent_teams_manager()
        manager2 = module.get_agent_teams_manager()

        assert manager1 is manager2
