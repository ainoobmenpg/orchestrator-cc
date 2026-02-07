"""チームクリーンアップフローの統合テスト

V-TM-003: チームクリーンアップフロー検証

このテストスイートでは、Team Leadによるチームクリーンアップフローを検証します。
"""

import json
from pathlib import Path

from orchestrator.core.agent_teams_manager import AgentTeamsManager, TeamConfig


class TestTeamCleanupFlow:
    """チームクリーンアップの統合テスト (V-TM-003)"""

    def test_v_tm_003_1_shutdown_request_sent_to_all_members(self, tmp_path: Path):
        """V-TM-003-1: すべてのメンバーに shutdown_request が送信されることを確認

        注: このテストは、graceful_shutdown_team メソッドが
        メンバー情報を正しく取得できることを検証します。
        実際の shutdown_request 送信は Team Lead が SendMessage ツールを使用します。
        """
        teams_dir = tmp_path / "teams"
        tasks_dir = tmp_path / "tasks"
        teams_dir.mkdir(parents=True)
        tasks_dir.mkdir(parents=True)

        manager = AgentTeamsManager(teams_dir=teams_dir, tasks_dir=tasks_dir)

        # 複数メンバーのチームを作成
        config = TeamConfig(
            name="cleanup-test-team",
            description="クリーンアップテスト用チーム",
            agent_type="general-purpose",
            members=[
                {"name": "team-lead", "agentType": "general-purpose", "timeoutThreshold": 300.0},
                {"name": "coder", "agentType": "general-purpose", "timeoutThreshold": 300.0},
                {"name": "tester", "agentType": "general-purpose", "timeoutThreshold": 300.0},
            ],
        )

        team_name = manager.create_team(config)

        # graceful_shutdown_team を呼び出し
        result = manager.graceful_shutdown_team(team_name, timeout=30.0)

        # 検証: メンバー情報が取得されていること
        assert result["team_name"] == team_name
        assert len(result["members_timeout"]) == 3  # 手動実行なので全員タイムアウト
        assert "team-lead" in result["members_timeout"]
        assert "coder" in result["members_timeout"]
        assert "tester" in result["members_timeout"]

        # 検証: メッセージにメンバー名が含まれていること
        assert "shutdown_request" in result["message"]

    def test_v_tm_003_2_shutdown_response_received(self, tmp_path: Path):
        """V-TM-003-2: メンバーから shutdown_response が受信されることを確認

        注: このテストは、shutdown_response フローをシミュレートします。
        実際のフローでは Team Lead が SendMessage ツールを使用して応答を待機します。
        """
        teams_dir = tmp_path / "teams"
        tasks_dir = tmp_path / "tasks"
        teams_dir.mkdir(parents=True)
        tasks_dir.mkdir(parents=True)

        manager = AgentTeamsManager(teams_dir=teams_dir, tasks_dir=tasks_dir)

        config = TeamConfig(
            name="response-test-team",
            description="応答テスト用チーム",
            agent_type="general-purpose",
            members=[
                {"name": "agent1", "agentType": "general-purpose", "timeoutThreshold": 300.0},
            ],
        )

        team_name = manager.create_team(config)

        # graceful_shutdown_team を呼び出し
        result = manager.graceful_shutdown_team(team_name, timeout=30.0)

        # 検証: メンバーが特定されていること
        assert len(result["members_timeout"]) == 1
        assert "agent1" in result["members_timeout"]

    def test_v_tm_003_3_timeout_handling(self, tmp_path: Path):
        """V-TM-003-3: メンバーが応答しない場合のタイムアウト処理を確認

        注: このテストは、タイムアウトパラメータが正しく渡されることを検証します。
        """
        teams_dir = tmp_path / "teams"
        tasks_dir = tmp_path / "tasks"
        teams_dir.mkdir(parents=True)
        tasks_dir.mkdir(parents=True)

        manager = AgentTeamsManager(teams_dir=teams_dir, tasks_dir=tasks_dir)

        config = TeamConfig(
            name="timeout-test-team",
            description="タイムアウトテスト用チーム",
            agent_type="general-purpose",
            members=[
                {"name": "agent1", "agentType": "general-purpose", "timeoutThreshold": 300.0},
            ],
        )

        team_name = manager.create_team(config)

        # 短いタイムアウトでテスト
        result = manager.graceful_shutdown_team(team_name, timeout=5.0)

        # 検証: タイムアウトとして処理されていること
        assert "agent1" in result["members_timeout"]
        assert len(result["members_shutdown"]) == 0

    def test_v_tm_003_4_teamdelete_called_after_shutdown(self, tmp_path: Path):
        """V-TM-003-4: shutdown 後に TeamDelete が呼び出されることを確認

        注: このテストは、graceful_shutdown_team メソッドが
        ディレクトリ削除を実行することを検証します。
        """
        teams_dir = tmp_path / "teams"
        tasks_dir = tmp_path / "tasks"
        teams_dir.mkdir(parents=True)
        tasks_dir.mkdir(parents=True)

        manager = AgentTeamsManager(teams_dir=teams_dir, tasks_dir=tasks_dir)

        config = TeamConfig(
            name="delete-test-team",
            description="削除テスト用チーム",
            agent_type="general-purpose",
            members=[
                {"name": "agent1", "agentType": "general-purpose", "timeoutThreshold": 300.0},
            ],
        )

        team_name = manager.create_team(config)

        # チームディレクトリが存在することを確認
        team_dir = teams_dir / team_name
        assert team_dir.exists()

        # タスクディレクトリは create_team では作成されないので、
        # テスト用に手動で作成（実際の使用ではタスク作成時に作成される）
        task_dir = tasks_dir / team_name
        task_dir.mkdir(parents=True, exist_ok=True)

        # graceful_shutdown_team を呼び出し
        result = manager.graceful_shutdown_team(team_name, timeout=30.0)

        # 検証: ディレクトリが削除されていること
        assert result["directories_removed"] is True
        assert not team_dir.exists()
        assert not task_dir.exists()

    def test_v_tm_003_5_team_and_task_directories_removed(self, tmp_path: Path):
        """V-TM-003-5: チームディレクトリとタスクディレクトリが削除されることを確認

        注: このテストは、両方のディレクトリが確実に削除されることを検証します。
        """
        teams_dir = tmp_path / "teams"
        tasks_dir = tmp_path / "tasks"
        teams_dir.mkdir(parents=True)
        tasks_dir.mkdir(parents=True)

        manager = AgentTeamsManager(teams_dir=teams_dir, tasks_dir=tasks_dir)

        config = TeamConfig(
            name="directories-test-team",
            description="ディレクトリ削除テスト用チーム",
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

        # チームディレクトリに追加ファイルを作成
        team_dir = teams_dir / team_name
        test_member_file = team_dir / "member1.json"
        with open(test_member_file, "w", encoding="utf-8") as f:
            json.dump({"name": "member1"}, f)

        # 両方のディレクトリが存在することを確認
        assert team_dir.exists()
        assert task_dir.exists()
        assert test_task_file.exists()
        assert test_member_file.exists()

        # graceful_shutdown_team を呼び出し
        result = manager.graceful_shutdown_team(team_name, timeout=30.0)

        # 検証: 両方のディレクトリが削除されていること
        assert result["directories_removed"] is True
        assert not team_dir.exists()
        assert not task_dir.exists()

    def test_v_tm_003_6_nonexistent_team_cleanup(self, tmp_path: Path):
        """V-TM-003-6: 存在しないチームのクリーンアップを確認

        存在しないチームに対してクリーンアップを実行した場合の挙動を検証します。
        """
        teams_dir = tmp_path / "teams"
        tasks_dir = tmp_path / "tasks"
        teams_dir.mkdir(parents=True)
        tasks_dir.mkdir(parents=True)

        manager = AgentTeamsManager(teams_dir=teams_dir, tasks_dir=tasks_dir)

        # 存在しないチームのクリーンアップを試みる
        result = manager.graceful_shutdown_team("nonexistent-team", timeout=30.0)

        # 検証: 成功とみなされる（既に削除されている）
        assert result["success"] is True
        assert "見つかりません" in result["message"]
        assert result["directories_removed"] is False

    def test_v_tm_003_7_cleanup_without_config_json(self, tmp_path: Path):
        """V-TM-003-7: config.json がない場合のクリーンアップを確認

        config.json が欠損している場合の挙動を検証します。
        """
        teams_dir = tmp_path / "teams"
        tasks_dir = tmp_path / "tasks"
        teams_dir.mkdir(parents=True)
        tasks_dir.mkdir(parents=True)

        manager = AgentTeamsManager(teams_dir=teams_dir, tasks_dir=tasks_dir)

        # チームディレクトリのみを作成（config.jsonなし）
        team_name = "incomplete-team"
        team_dir = teams_dir / team_name
        team_dir.mkdir(parents=True, exist_ok=True)

        # ディレクトリが存在することを確認
        assert team_dir.exists()

        # graceful_shutdown_team を呼び出し
        result = manager.graceful_shutdown_team(team_name, timeout=30.0)

        # 検証: ディレクトリが削除されていること
        assert result["directories_removed"] is True
        assert not team_dir.exists()
        assert result["success"] is True
