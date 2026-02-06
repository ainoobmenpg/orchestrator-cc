"""TeamsMonitorテスト

TeamsMonitor統合監視クラスのテストです。
"""

import json
from pathlib import Path
<<<<<<< HEAD
from unittest.mock import patch

from orchestrator.web.team_models import TeamInfo
from orchestrator.web.teams_monitor import TeamsMonitor

=======
from unittest.mock import MagicMock, patch

import pytest

from orchestrator.web.team_models import TeamInfo, TeamMember
from orchestrator.web.teams_monitor import TeamsMonitor


>>>>>>> main
# ============================================================================
# TeamsMonitor 初期化テスト
# ============================================================================


class TestTeamsMonitorInit:
    """TeamsMonitor初期化のテスト"""

<<<<<<< HEAD
    @patch("orchestrator.web.teams_monitor.Path")
    def test_initialization(self, mock_path):
        """初期化テスト

        Note: tmux_session_name引数は互換性のために残されていますが、
        使用されていません（ファイルベースの思考ログを使用）。
        """
        # チームディレクトリが存在しないようにモック
        mock_path.home.return_value = Path("/tmp/empty_teams")
        mock_path.return_value.exists.return_value = False
        mock_path.return_value.iterdir.return_value = []

        monitor = TeamsMonitor()

        # チーム状態が初期化されていることを確認
        assert monitor._teams == {}
        assert monitor._messages == {}
        assert monitor._tasks == {}
        assert monitor._thinking_logs == {}
        assert not monitor.is_running()

    @patch("orchestrator.web.teams_monitor.Path")
    def test_initialization_with_session_name(self, mock_path):
        """tmux_session_nameを指定した初期化テスト

        Note: tmux_session_name引数は互換性のために残されていますが、
        使用されていません。
        """
        # チームディレクトリが存在しないようにモック
        mock_path.home.return_value = Path("/tmp/empty_teams")
        mock_path.return_value.exists.return_value = False
        mock_path.return_value.iterdir.return_value = []

        # tmux_session_nameを指定しても例外が発生しないことを確認
        monitor = TeamsMonitor(tmux_session_name="test-session")

        assert monitor._teams == {}
        assert not monitor.is_running()

=======
    @patch('orchestrator.web.teams_monitor.Path')
    def test_initialization_without_tmux(self, mock_path):
        """tmuxセッション名なしでの初期化"""
        # チームディレクトリが存在しないようにモック
        mock_path.home.return_value = Path("/tmp/empty_teams")
        mock_path.return_value.exists.return_value = False

        monitor = TeamsMonitor()

        assert monitor._tmux_manager is None
        assert monitor._teams == {}
        assert not monitor.is_running()

    def test_initialization_with_tmux(self):
        """tmuxセッション名ありでの初期化"""
        with patch('orchestrator.web.teams_monitor.TmuxSessionManager') as mock_tmux:
            monitor = TeamsMonitor(tmux_session_name="test-session")

            assert monitor._tmux_manager is not None
            assert not monitor.is_running()

>>>>>>> main

# ============================================================================
# TeamsMonitor チーム管理テスト
# ============================================================================


class TestTeamsMonitorTeamManagement:
    """TeamsMonitorチーム管理機能のテスト"""

<<<<<<< HEAD
    @patch("orchestrator.web.teams_monitor.Path")
=======
    @patch('orchestrator.web.teams_monitor.Path')
>>>>>>> main
    def test_get_teams_empty(self, mock_path):
        """チームがいない場合"""
        # チームディレクトリが存在しないようにモック
        mock_path.home.return_value = Path("/tmp/empty_teams")
        mock_path.return_value.exists.return_value = False
<<<<<<< HEAD
        mock_path.return_value.iterdir.return_value = []
=======
>>>>>>> main

        monitor = TeamsMonitor()

        teams = monitor.get_teams()

        assert teams == []

    def test_get_teams_with_data(self, tmp_path: Path):
        """チームデータがある場合"""
        monitor = TeamsMonitor()

        # 環境のチームをクリアしてからテスト用チームを追加
        monitor._teams.clear()
        team_info = TeamInfo(
            name="test-team",
            description="Test",
            created_at=1234567890,
            lead_agent_id="lead@test",
            lead_session_id="session-123",
            members=[],
        )
        monitor._teams["test-team"] = team_info

        teams = monitor.get_teams()

        assert len(teams) == 1
        assert teams[0]["name"] == "test-team"

    def test_get_team_messages_empty(self):
        """メッセージがない場合"""
        monitor = TeamsMonitor()

        messages = monitor.get_team_messages("test-team")

        assert messages == []

    def test_get_team_messages_with_data(self):
        """メッセージがある場合"""
        from orchestrator.web.team_models import TeamMessage

        monitor = TeamsMonitor()

        # テスト用メッセージを追加
        msg = TeamMessage(
            id="msg-001",
            sender="agent1",
            recipient="agent2",
            content="Hello",
            timestamp="2026-02-06T12:00:00Z",
        )
        monitor._messages["test-team"] = [msg]

        messages = monitor.get_team_messages("test-team")

        assert len(messages) == 1
        assert messages[0]["content"] == "Hello"

    def test_get_team_tasks_empty(self):
        """タスクがない場合"""
        monitor = TeamsMonitor()

        tasks = monitor.get_team_tasks("test-team")

        assert tasks == []

    def test_get_team_thinking_empty(self):
        """思考ログがない場合"""
        monitor = TeamsMonitor()

        logs = monitor.get_team_thinking("test-team")

        assert logs == []


# ============================================================================
# TeamsMonitor 監視制御テスト
# ============================================================================


class TestTeamsMonitorControl:
    """TeamsMonitor監視制御のテスト"""

    def test_start_monitoring(self):
        """監視開始テスト"""
        monitor = TeamsMonitor()

        monitor.start_monitoring()

        assert monitor.is_running()

        monitor.stop_monitoring()

    def test_stop_monitoring(self):
        """監視停止テスト"""
        monitor = TeamsMonitor()

        monitor.start_monitoring()
        assert monitor.is_running()

        monitor.stop_monitoring()
        assert not monitor.is_running()

    def test_stop_when_not_running(self):
        """監視未実行時の停止テスト"""
        monitor = TeamsMonitor()

        # 例外が発生しないことを確認
        monitor.stop_monitoring()
        assert not monitor.is_running()


# ============================================================================
# TeamsMonitor コールバックテスト
# ============================================================================


class TestTeamsMonitorCallbacks:
    """TeamsMonitorコールバック機能のテスト"""

    def test_register_callback(self):
        """コールバック登録テスト"""
        monitor = TeamsMonitor()

        called = []

        def callback(data):
            called.append(data)

        monitor.register_update_callback(callback)

        assert len(monitor._update_callbacks) == 1

    def test_broadcast_to_callbacks(self):
        """コールバックへのブロードキャストテスト"""
        monitor = TeamsMonitor()

        called = []

        def callback(data):
            called.append(data)

        monitor.register_update_callback(callback)

        # 内部メソッドを呼び出してブロードキャスト
        monitor._broadcast({"type": "test", "data": "test"})

        assert len(called) == 1
        assert called[0]["type"] == "test"

    def test_multiple_callbacks(self):
        """複数コールバックのテスト"""
        monitor = TeamsMonitor()

        called1 = []
        called2 = []

        monitor.register_update_callback(lambda d: called1.append(d))
        monitor.register_update_callback(lambda d: called2.append(d))

        monitor._broadcast({"type": "test"})

        assert len(called1) == 1
        assert len(called2) == 1


# ============================================================================
# TeamsMonitor イベントハンドラテスト
# ============================================================================


class TestTeamsMonitorEventHandlers:
    """TeamsMonitorイベントハンドラのテスト"""

    def test_on_team_created(self, tmp_path: Path):
        """チーム作成イベントハンドラ"""
        monitor = TeamsMonitor()

        # チームディレクトリとconfig.jsonを作成
        team_dir = tmp_path / "test-team"
        team_dir.mkdir()
        config_file = team_dir / "config.json"
<<<<<<< HEAD
        config_file.write_text(
            json.dumps(
                {
                    "name": "test-team",
                    "description": "Test team",
                    "createdAt": 1234567890,
                    "leadAgentId": "lead@test",
                    "leadSessionId": "session-123",
                    "members": [],
                }
            )
        )
=======
        config_file.write_text(json.dumps({
            "name": "test-team",
            "description": "Test team",
            "createdAt": 1234567890,
            "leadAgentId": "lead@test",
            "leadSessionId": "session-123",
            "members": [],
        }))
>>>>>>> main

        monitor._on_team_created("test-team", team_dir)

        assert "test-team" in monitor._teams
        assert monitor._teams["test-team"].name == "test-team"

    def test_on_team_deleted(self):
        """チーム削除イベントハンドラ"""
        monitor = TeamsMonitor()

        # テスト用チームを追加
        team_info = TeamInfo(
            name="test-team",
            description="Test",
            created_at=1234567890,
            lead_agent_id="lead@test",
            lead_session_id="session-123",
            members=[],
        )
        monitor._teams["test-team"] = team_info
        monitor._messages["test-team"] = []

        monitor._on_team_deleted("test-team", Path("/dummy"))

        assert "test-team" not in monitor._teams
        assert "test-team" not in monitor._messages

    def test_on_config_changed(self, tmp_path: Path):
        """config変更イベントハンドラ"""
        monitor = TeamsMonitor()

        team_dir = tmp_path / "test-team"
        team_dir.mkdir()
        config_file = team_dir / "config.json"
<<<<<<< HEAD
        config_file.write_text(
            json.dumps(
                {
                    "name": "test-team",
                    "description": "Updated description",
                    "createdAt": 1234567890,
                    "leadAgentId": "lead@test",
                    "leadSessionId": "session-123",
                    "members": [],
                }
            )
        )
=======
        config_file.write_text(json.dumps({
            "name": "test-team",
            "description": "Updated description",
            "createdAt": 1234567890,
            "leadAgentId": "lead@test",
            "leadSessionId": "session-123",
            "members": [],
        }))
>>>>>>> main

        monitor._on_config_changed("test-team", config_file)

        assert monitor._teams["test-team"].description == "Updated description"

    def test_on_inbox_changed(self, tmp_path: Path):
        """inbox変更イベントハンドラ"""
<<<<<<< HEAD
=======
        from orchestrator.web.team_models import TeamMessage
>>>>>>> main

        monitor = TeamsMonitor()

        inbox_dir = tmp_path / "test-team" / "inboxes"
        inbox_dir.mkdir(parents=True)
        inbox_file = inbox_dir / "agent1.json"
<<<<<<< HEAD
        inbox_file.write_text(
            json.dumps(
                [
                    {
                        "id": "msg-001",
                        "sender": "user",
                        "recipient": "agent1",
                        "content": "Hello",
                        "timestamp": "2026-02-06T12:00:00Z",
                    }
                ]
            )
        )
=======
        inbox_file.write_text(json.dumps([{
            "id": "msg-001",
            "sender": "user",
            "recipient": "agent1",
            "content": "Hello",
            "timestamp": "2026-02-06T12:00:00Z",
        }]))
>>>>>>> main

        monitor._on_inbox_changed("test-team", inbox_file)

        messages = monitor._messages.get("test-team", [])
        assert len(messages) == 1
        assert messages[0].content == "Hello"


# ============================================================================
# TeamsMonitor 思考ログキャプチャテスト
# ============================================================================


class TestTeamsMonitorThinkingCapture:
    """TeamsMonitor思考ログキャプチャのテスト"""

<<<<<<< HEAD
    @patch("orchestrator.web.teams_monitor.ThinkingLog")
=======
    def test_get_pane_index_for_member(self):
        """メンバーのペイン番号取得テスト"""
        monitor = TeamsMonitor()

        # team-lead -> 0
        assert monitor._get_pane_index_for_member(
            "test-team",
            type("obj", (object,), {"name": "team-lead"})
        ) == 0

        # researcher -> 1
        assert monitor._get_pane_index_for_member(
            "test-team",
            type("obj", (object,), {"name": "researcher"})
        ) == 1

        # 不明なメンバー -> None
        assert monitor._get_pane_index_for_member(
            "test-team",
            type("obj", (object,), {"name": "unknown"})
        ) is None

    @patch('orchestrator.web.teams_monitor.ThinkingLog')
>>>>>>> main
    def test_capture_thinking_no_tmux(self, mock_thinking_log):
        """tmuxマネージャーがない場合の思考ログキャプチャ"""
        monitor = TeamsMonitor()  # tmux_session_nameなし

        # 例外が発生しないことを確認
        monitor._capture_thinking()

        # ThinkingLog.from_pane_outputは呼ばれないはず
        mock_thinking_log.from_pane_output.assert_not_called()
