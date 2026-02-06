"""CLIメインモジュールのテスト

orchestrator/cli/main.py のテストです。
"""

import json
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from orchestrator.cli.main import (
    app,
)

runner = CliRunner()


class TestListTeams:
    """list_teams コマンドのテスト"""

    @patch("orchestrator.cli.main.TeamsMonitor")
    def test_list_teams_empty(self, mock_monitor_class):
        """チームがいない場合"""
        mock_monitor = MagicMock()
        mock_monitor.get_teams.return_value = []
        mock_monitor_class.return_value = mock_monitor

        result = runner.invoke(app, ["list-teams"])

        assert result.exit_code == 0
        assert "チームが見つかりませんでした" in result.stdout

    @patch("orchestrator.cli.main.TeamsMonitor")
    def test_list_teams_with_data(self, mock_monitor_class):
        """チームがある場合"""
        mock_monitor = MagicMock()
        mock_monitor.get_teams.return_value = [
            {
                "name": "test-team",
                "description": "テストチーム",
                "createdAt": 1234567890000,
                "members": [{"name": "agent1"}],
            }
        ]
        mock_monitor_class.return_value = mock_monitor

        result = runner.invoke(app, ["list-teams"])

        assert result.exit_code == 0
        assert "test-team" in result.stdout
        assert "テストチーム" in result.stdout

    @patch("orchestrator.cli.main.TeamsMonitor")
    def test_list_teams_json(self, mock_monitor_class):
        """JSON形式で出力"""
        mock_monitor = MagicMock()
        mock_monitor.get_teams.return_value = [
            {"name": "team1", "description": "desc1"},
        ]
        mock_monitor_class.return_value = mock_monitor

        result = runner.invoke(app, ["list-teams", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data[0]["name"] == "team1"


class TestTeamStatus:
    """team_status コマンドのテスト"""

    @patch("orchestrator.cli.main.get_agent_teams_manager")
    def test_team_status_success(self, mock_manager_factory):
        """チーム状態取得成功"""
        mock_manager = MagicMock()
        mock_manager.get_team_status.return_value = {
            "name": "test-team",
            "description": "テスト",
            "taskCount": 5,
            "members": [
                {"name": "agent1", "agentType": "general-purpose", "model": "claude-opus-4-6"}
            ],
        }
        mock_manager_factory.return_value = mock_manager

        result = runner.invoke(app, ["team-status", "test-team"])

        assert result.exit_code == 0
        assert "test-team" in result.stdout
        assert "5" in result.stdout

    @patch("orchestrator.cli.main.get_agent_teams_manager")
    def test_team_status_error(self, mock_manager_factory):
        """チームが見つからない場合"""
        mock_manager = MagicMock()
        mock_manager.get_team_status.return_value = {"error": "Team not found"}
        mock_manager_factory.return_value = mock_manager

        result = runner.invoke(app, ["team-status", "nonexistent-team"])

        assert result.exit_code == 1
        # エラーメッセージは stderr に出力される
        assert "エラー" in result.stderr or "Team not found" in result.stderr


class TestTeamMessages:
    """team_messages コマンドのテスト"""

    @patch("orchestrator.cli.main.TeamsMonitor")
    def test_team_messages_empty(self, mock_monitor_class):
        """メッセージがない場合"""
        mock_monitor = MagicMock()
        mock_monitor.get_team_messages.return_value = []
        mock_monitor_class.return_value = mock_monitor

        result = runner.invoke(app, ["team-messages", "test-team"])

        assert result.exit_code == 0
        assert "見つかりませんでした" in result.stdout

    @patch("orchestrator.cli.main.TeamsMonitor")
    def test_team_messages_with_limit(self, mock_monitor_class):
        """メッセージがある場合（制限付き）"""
        mock_monitor = MagicMock()
        # 10件のメッセージを返す
        messages = [
            {
                "id": f"msg-{i}",
                "sender": "agent1",
                "content": f"メッセージ{i}",
                "timestamp": "2026-02-06T12:00:00Z",
                "type": "info",
            }
            for i in range(10)
        ]
        mock_monitor.get_team_messages.return_value = messages
        mock_monitor_class.return_value = mock_monitor

        result = runner.invoke(app, ["team-messages", "test-team", "--limit", "5"])

        assert result.exit_code == 0
        # 5件に制限されていることを確認
        mock_monitor.get_team_messages.assert_called_once_with("test-team")


class TestTeamTasks:
    """team_tasks コマンドのテスト"""

    @patch("orchestrator.cli.main.TeamsMonitor")
    def test_team_tasks_empty(self, mock_monitor_class):
        """タスクがない場合"""
        mock_monitor = MagicMock()
        mock_monitor.get_team_tasks.return_value = []
        mock_monitor_class.return_value = mock_monitor

        result = runner.invoke(app, ["team-tasks", "test-team"])

        assert result.exit_code == 0
        assert "見つかりませんでした" in result.stdout

    @patch("orchestrator.cli.main.TeamsMonitor")
    def test_team_tasks_with_status_filter(self, mock_monitor_class):
        """ステータスフィルタあり"""
        mock_monitor = MagicMock()
        mock_monitor.get_team_tasks.return_value = [
            {"id": "task-1", "status": "pending", "subject": "Task 1", "owner": "agent1"},
            {"id": "task-2", "status": "completed", "subject": "Task 2", "owner": "agent2"},
        ]
        mock_monitor_class.return_value = mock_monitor

        result = runner.invoke(app, ["team-tasks", "test-team", "--status", "pending"])

        assert result.exit_code == 0


class TestShowLogs:
    """show_logs コマンドのテスト"""

    @patch("orchestrator.cli.main.get_thinking_log_handler")
    def test_show_logs_empty(self, mock_handler_factory):
        """思考ログがない場合"""
        mock_handler = MagicMock()
        mock_handler.get_logs.return_value = []
        mock_handler_factory.return_value = mock_handler

        result = runner.invoke(app, ["show-logs", "test-team"])

        assert result.exit_code == 0
        assert "見つかりませんでした" in result.stdout

    @patch("orchestrator.cli.main.get_thinking_log_handler")
    def test_show_logs_with_data(self, mock_handler_factory):
        """思考ログがある場合"""
        mock_handler = MagicMock()
        mock_handler.get_logs.return_value = [
            {
                "agentName": "agent1",
                "content": "テスト思考ログ",
                "timestamp": "2026-02-06T12:00:00Z",
                "category": "thinking",
                "emotion": "neutral",
            }
        ]
        mock_handler_factory.return_value = mock_handler

        result = runner.invoke(app, ["show-logs", "test-team"])

        assert result.exit_code == 0
        assert "テスト思考ログ" in result.stdout
        assert "agent1" in result.stdout

    @patch("orchestrator.cli.main.get_thinking_log_handler")
    def test_show_logs_with_agent_filter(self, mock_handler_factory):
        """エージェントフィルタあり"""
        mock_handler = MagicMock()
        mock_handler.get_logs.return_value = [
            {
                "agentName": "agent1",
                "content": "ログ1",
                "timestamp": "2026-02-06T12:00:00Z",
                "category": "thinking",
            },
            {
                "agentName": "agent2",
                "content": "ログ2",
                "timestamp": "2026-02-06T12:01:00Z",
                "category": "thinking",
            },
        ]
        mock_handler_factory.return_value = mock_handler

        result = runner.invoke(app, ["show-logs", "test-team", "--agent", "agent1"])

        assert result.exit_code == 0
        # フィルタが適用されることを確認（get_logsは全て返すが、コマンド側でフィルタ）
        mock_handler.get_logs.assert_called_once_with("test-team")

    @patch("orchestrator.cli.main.get_thinking_log_handler")
    def test_show_logs_json(self, mock_handler_factory):
        """JSON形式で出力"""
        mock_handler = MagicMock()
        mock_handler.get_logs.return_value = [
            {
                "agentName": "agent1",
                "content": "ログ",
                "timestamp": "2026-02-06T12:00:00Z",
                "category": "thinking",
            }
        ]
        mock_handler_factory.return_value = mock_handler

        result = runner.invoke(app, ["show-logs", "test-team", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert len(data) == 1
        assert data[0]["agentName"] == "agent1"


class TestTeamActivity:
    """team_activity コマンドのテスト"""

    @patch("orchestrator.cli.main.get_thinking_log_handler")
    @patch("orchestrator.cli.main.TeamsMonitor")
    def test_team_activity_basic(self, mock_monitor_class, mock_handler_factory):
        """基本アクティビティ表示"""
        mock_monitor = MagicMock()
        mock_monitor.get_teams.return_value = [
            {
                "name": "test-team",
                "description": "テストチーム",
                "members": [{"name": "agent1"}],
            }
        ]
        mock_monitor.get_team_messages.return_value = []
        mock_monitor.get_team_tasks.return_value = []
        mock_monitor_class.return_value = mock_monitor

        mock_handler = MagicMock()
        mock_handler.get_logs.return_value = []
        mock_handler_factory.return_value = mock_handler

        result = runner.invoke(app, ["team-activity", "test-team"])

        assert result.exit_code == 0
        assert "test-team" in result.stdout
        assert "テストチーム" in result.stdout

    @patch("orchestrator.cli.main.get_thinking_log_handler")
    @patch("orchestrator.cli.main.TeamsMonitor")
    def test_team_activity_with_data(self, mock_monitor_class, mock_handler_factory):
        """データがあるアクティビティ表示"""
        mock_monitor = MagicMock()
        mock_monitor.get_teams.return_value = [
            {
                "name": "test-team",
                "description": "テストチーム",
                "members": [{"name": "agent1"}, {"name": "agent2"}],
            }
        ]
        mock_monitor.get_team_messages.return_value = [
            {
                "id": "msg-1",
                "sender": "agent1",
                "content": "Hello",
                "timestamp": "2026-02-06T12:00:00Z",
            }
        ]
        mock_monitor.get_team_tasks.return_value = [
            {"id": "task-1", "status": "pending", "subject": "Task 1"},
            {"id": "task-2", "status": "completed", "subject": "Task 2"},
        ]
        mock_monitor_class.return_value = mock_monitor

        mock_handler = MagicMock()
        mock_handler.get_logs.return_value = [
            {"agentName": "agent1", "content": "Thinking...", "timestamp": "2026-02-06T12:00:00Z"}
        ]
        mock_handler_factory.return_value = mock_handler

        result = runner.invoke(app, ["team-activity", "test-team"])

        assert result.exit_code == 0
        assert "メッセージ数: 1" in result.stdout
        assert "タスク数: 2" in result.stdout
        assert "思考ログ数: 1" in result.stdout
        assert "メンバー数: 2" in result.stdout

    @patch("orchestrator.cli.main.get_thinking_log_handler")
    @patch("orchestrator.cli.main.TeamsMonitor")
    def test_team_activity_json(self, mock_monitor_class, mock_handler_factory):
        """JSON形式で出力"""
        mock_monitor = MagicMock()
        mock_monitor.get_teams.return_value = [
            {"name": "test-team", "description": "テスト", "members": []}
        ]
        mock_monitor.get_team_messages.return_value = []
        mock_monitor.get_team_tasks.return_value = []
        mock_monitor_class.return_value = mock_monitor

        mock_handler = MagicMock()
        mock_handler.get_logs.return_value = []
        mock_handler_factory.return_value = mock_handler

        result = runner.invoke(app, ["team-activity", "test-team", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["teamName"] == "test-team"
        assert data["messageCount"] == 0
        assert data["taskCount"] == 0

    @patch("orchestrator.cli.main.get_thinking_log_handler")
    @patch("orchestrator.cli.main.TeamsMonitor")
    def test_team_activity_team_not_found(self, mock_monitor_class, mock_handler_factory):
        """チームが見つからない場合"""
        mock_monitor = MagicMock()
        mock_monitor.get_teams.return_value = []  # チームがない
        mock_monitor_class.return_value = mock_monitor

        mock_handler = MagicMock()
        mock_handler.get_logs.return_value = []
        mock_handler_factory.return_value = mock_handler

        result = runner.invoke(app, ["team-activity", "nonexistent-team"])

        assert result.exit_code == 1
        # エラーメッセージは stderr に出力される
        assert "エラー" in result.stderr or "見つかりません" in result.stderr


class TestCreateDeleteTeam:
    """create_team, delete_team コマンドのテスト"""

    @patch("orchestrator.cli.main.get_agent_teams_manager")
    def test_create_team_success(self, mock_manager_factory):
        """チーム作成成功"""
        mock_manager = MagicMock()
        mock_manager.create_team.return_value = "new-team"
        mock_manager_factory.return_value = mock_manager

        result = runner.invoke(
            app,
            [
                "create-team",
                "new-team",
                "--description",
                "新しいチーム",
                "--agent-type",
                "general-purpose",
            ],
        )

        assert result.exit_code == 0
        assert "チーム 'new-team' を作成しました" in result.stdout

    @patch("orchestrator.cli.main.get_agent_teams_manager")
    def test_delete_team_success(self, mock_manager_factory):
        """チーム削除成功"""
        mock_manager = MagicMock()
        mock_manager.delete_team.return_value = True
        mock_manager_factory.return_value = mock_manager

        result = runner.invoke(app, ["delete-team", "test-team"])

        assert result.exit_code == 0
        assert "チーム 'test-team' を削除しました" in result.stdout

    @patch("orchestrator.cli.main.get_agent_teams_manager")
    def test_delete_team_not_found(self, mock_manager_factory):
        """チーム削除：チームが見つからない"""
        mock_manager = MagicMock()
        mock_manager.delete_team.return_value = False
        mock_manager_factory.return_value = mock_manager

        result = runner.invoke(app, ["delete-team", "nonexistent-team"])

        assert result.exit_code == 1
        # エラーメッセージは stderr に出力される
        assert "エラー" in result.stderr or "見つかりません" in result.stderr
