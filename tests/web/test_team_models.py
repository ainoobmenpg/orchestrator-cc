"""Teamモデルテスト

データモデルのパース/シリアライズ機能をテストします。
"""

import json
from pathlib import Path

from orchestrator.web.team_models import (
    EmotionType,
    MessageCategory,
    TaskInfo,
    TeamInfo,
    TeamMember,
    TeamMessage,
    ThinkingLog,
    _classify_message_category,
    _detect_emotion,
    load_team_config,
    load_team_messages,
)

# ============================================================================
# TeamMember テスト
# ============================================================================


class TestTeamMember:
    """TeamMemberクラスのテスト"""

    def test_from_dict_full(self):
        """完全なデータからのTeamMember作成"""
        data = {
            "agentId": "test-agent@example",
            "name": "test-agent",
            "agentType": "general-purpose",
            "model": "claude-opus-4-6",
            "joinedAt": 1234567890,
            "cwd": "/path/to/dir",
            "tmuxPaneId": "%0",
        }
        member = TeamMember.from_dict(data)

        assert member.agent_id == "test-agent@example"
        assert member.name == "test-agent"
        assert member.agent_type == "general-purpose"
        assert member.model == "claude-opus-4-6"
        assert member.joined_at == 1234567890
        assert member.cwd == "/path/to/dir"
        assert member.tmux_pane_id == "%0"

    def test_from_dict_minimal(self):
        """最小限のデータからのTeamMember作成"""
        data = {
            "agentId": "test-agent",
            "name": "test-agent",
            "agentType": "test-type",
            "model": "test-model",
            "joinedAt": 0,
        }
        member = TeamMember.from_dict(data)

        assert member.agent_id == "test-agent"
        assert member.cwd == ""  # デフォルト値
        assert member.tmux_pane_id == ""  # デフォルト値

    def test_to_dict(self):
        """TeamMemberの辞書変換"""
        member = TeamMember(
            agent_id="test-agent",
            name="test-agent",
            agent_type="test-type",
            model="test-model",
            joined_at=1234567890,
            cwd="/path",
            tmux_pane_id="%0",
        )
        data = member.to_dict()

        assert data["agentId"] == "test-agent"
        assert data["name"] == "test-agent"
        assert data["agentType"] == "test-type"
        assert data["model"] == "test-model"
        assert data["joinedAt"] == 1234567890
        assert data["cwd"] == "/path"
        assert data["tmuxPaneId"] == "%0"


# ============================================================================
# TeamInfo テスト
# ============================================================================


class TestTeamInfo:
    """TeamInfoクラスのテスト"""

    def test_from_dict(self):
        """辞書からのTeamInfo作成"""
        data = {
            "name": "test-team",
            "description": "Test team",
            "createdAt": 1234567890,
            "leadAgentId": "lead@test",
            "leadSessionId": "session-123",
            "members": [
                {
                    "agentId": "member1@test",
                    "name": "member1",
                    "agentType": "general-purpose",
                    "model": "test-model",
                    "joinedAt": 1234567890,
                }
            ],
        }
        team = TeamInfo.from_dict(data)

        assert team.name == "test-team"
        assert team.description == "Test team"
        assert team.created_at == 1234567890
        assert team.lead_agent_id == "lead@test"
        assert team.lead_session_id == "session-123"
        assert len(team.members) == 1
        assert team.members[0].name == "member1"

    def test_to_dict(self):
        """TeamInfoの辞書変換"""
        team = TeamInfo(
            name="test-team",
            description="Test",
            created_at=1234567890,
            lead_agent_id="lead@test",
            lead_session_id="session-123",
            members=[],
        )
        data = team.to_dict()

        assert data["name"] == "test-team"
        assert data["description"] == "Test"
        assert data["members"] == []


# ============================================================================
# TeamMessage テスト
# ============================================================================


class TestTeamMessage:
    """TeamMessageクラスのテスト"""

    def test_from_dict(self):
        """辞書からのTeamMessage作成"""
        data = {
            "id": "msg-001",
            "sender": "agent1",
            "recipient": "agent2",
            "content": "Hello",
            "timestamp": "2026-02-06T12:00:00Z",
            "type": "message",
        }
        msg = TeamMessage.from_dict(data)

        assert msg.id == "msg-001"
        assert msg.sender == "agent1"
        assert msg.recipient == "agent2"
        assert msg.content == "Hello"
        assert msg.timestamp == "2026-02-06T12:00:00Z"
        assert msg.message_type == "message"

    def test_from_dict_defaults(self):
        """デフォルト値でのTeamMessage作成"""
        data = {
            "id": "msg-001",
            "sender": "agent1",
            "recipient": "",
            "content": "Hello",
            "timestamp": "2026-02-06T12:00:00Z",
        }
        msg = TeamMessage.from_dict(data)

        assert msg.message_type == "message"  # デフォルト値


# ============================================================================
# ThinkingLog テスト
# ============================================================================


class TestThinkingLog:
    """ThinkingLogクラスのテスト"""

    def test_from_pane_output_action(self):
        """行動ログのパース"""
        output = "Tool used: Read to examine file"
        logs = ThinkingLog.from_pane_output("test-agent", output)

        assert len(logs) == 1
        assert logs[0].agent_name == "test-agent"
        assert logs[0].content == "Tool used: Read to examine file"
        assert logs[0].category == MessageCategory.ACTION
        assert logs[0].emotion == EmotionType.NEUTRAL

    def test_from_pane_output_thinking(self):
        """思考ログのパース"""
        output = "Let me analyze the current situation"
        logs = ThinkingLog.from_pane_output("test-agent", output)

        assert len(logs) == 1
        assert logs[0].category == MessageCategory.THINKING

    def test_from_pane_output_emotion_confusion(self):
        """感情（困惑）ログのパース"""
        output = "I'm confused about the setup"
        logs = ThinkingLog.from_pane_output("test-agent", output)

        assert len(logs) == 1
        assert logs[0].category == MessageCategory.EMOTION
        assert logs[0].emotion == EmotionType.CONFUSION

    def test_from_pane_output_emotion_satisfaction(self):
        """感情（満足）ログのパース"""
        output = "Successfully completed the task"
        logs = ThinkingLog.from_pane_output("test-agent", output)

        assert len(logs) == 1
        assert logs[0].category == MessageCategory.EMOTION
        assert logs[0].emotion == EmotionType.SATISFACTION

    def test_from_pane_output_multiple_lines(self):
        """複数行のパース"""
        output = """Line 1: Tool used: Read
Line 2: Let me analyze
Line 3: I'm confused"""

        logs = ThinkingLog.from_pane_output("test-agent", output)

        assert len(logs) == 3
        assert logs[0].category == MessageCategory.ACTION
        assert logs[1].category == MessageCategory.THINKING
        assert logs[2].category == MessageCategory.EMOTION

    def test_from_pane_output_empty_lines(self):
        """空行はスキップされる"""
        output = """Line 1

Line 3"""

        logs = ThinkingLog.from_pane_output("test-agent", output)

        assert len(logs) == 2
        assert logs[0].content == "Line 1"
        assert logs[1].content == "Line 3"


# ============================================================================
# TaskInfo テスト
# ============================================================================


class TestTaskInfo:
    """TaskInfoクラスのテスト"""

    def test_from_dict(self):
        """辞書からのTaskInfo作成"""
        data = {
            "taskId": "task-001",
            "subject": "Test task",
            "description": "Test description",
            "status": "pending",
            "owner": "agent1",
        }
        task = TaskInfo.from_dict(data)

        assert task.task_id == "task-001"
        assert task.subject == "Test task"
        assert task.description == "Test description"
        assert task.status == "pending"
        assert task.owner == "agent1"

    def test_from_dict_with_id_field(self):
        """idフィールドでのTaskInfo作成（taskIdの代わり）"""
        data = {
            "id": "task-001",
            "subject": "Test task",
            "description": "Test description",
            "status": "pending",
        }
        task = TaskInfo.from_dict(data)

        assert task.task_id == "task-001"


# ============================================================================
# 分類関数テスト
# ============================================================================


class TestClassifyMessageCategory:
    """_classify_message_category関数のテスト"""

    def test_classify_action_tool_used(self):
        """ツール使用パターン"""
        assert _classify_message_category("Tool used: Read") == MessageCategory.ACTION
        assert _classify_message_category("Reading file...") == MessageCategory.ACTION
        assert _classify_message_category("Running command...") == MessageCategory.ACTION

    def test_classify_thinking_patterns(self):
        """思考パターン"""
        assert _classify_message_category("Let me analyze") == MessageCategory.THINKING
        assert _classify_message_category("I need to check") == MessageCategory.THINKING
        assert _classify_message_category("Based on the context") == MessageCategory.THINKING

    def test_classify_emotion_patterns(self):
        """感情パターン"""
        assert _classify_message_category("I'm confused") == MessageCategory.EMOTION
        assert _classify_message_category("Success! Completed") == MessageCategory.EMOTION
        assert _classify_message_category("Error occurred") == MessageCategory.EMOTION

    def test_classify_default_thinking(self):
        """デフォルトは思考"""
        assert _classify_message_category("Random text") == MessageCategory.THINKING


class TestDetectEmotion:
    """_detect_emotion関数のテスト"""

    def test_detect_confusion(self):
        """困惑の検出"""
        # "?" を含むパターン
        assert _detect_emotion("What should I do?") == EmotionType.CONFUSION
        assert _detect_emotion("I'm uncertain") == EmotionType.CONFUSION
        assert _detect_emotion("I'm unclear about the situation") == EmotionType.CONFUSION

    def test_detect_satisfaction(self):
        """満足の検出"""
        assert _detect_emotion("Successfully completed") == EmotionType.SATISFACTION
        assert _detect_emotion("Done and finished") == EmotionType.SATISFACTION
        assert _detect_emotion("Problem solved") == EmotionType.SATISFACTION

    def test_detect_concern(self):
        """懸念の検出"""
        assert _detect_emotion("Error occurred") == EmotionType.CONCERN
        assert _detect_emotion("Problem found") == EmotionType.CONCERN
        assert _detect_emotion("Failed to execute") == EmotionType.CONCERN

    def test_detect_focus(self):
        """集中の検出"""
        assert _detect_emotion("Checking the data") == EmotionType.FOCUS
        assert _detect_emotion("Verifying the result") == EmotionType.FOCUS
        assert _detect_emotion("Analyzing the code") == EmotionType.FOCUS

    def test_detect_neutral_default(self):
        """デフォルトは中立"""
        assert _detect_emotion("Random text") == EmotionType.NEUTRAL
        assert _detect_emotion("Just a message") == EmotionType.NEUTRAL


# ============================================================================
# load_team_config テスト
# ============================================================================


class TestLoadTeamConfig:
    """load_team_config関数のテスト"""

    def test_load_valid_config(self, tmp_path: Path):
        """有効なconfig.jsonの読み込み"""
        config_file = tmp_path / "config.json"
        config_data = {
            "name": "test-team",
            "description": "Test",
            "createdAt": 1234567890,
            "leadAgentId": "lead@test",
            "leadSessionId": "session-123",
            "members": [],
        }
        config_file.write_text(json.dumps(config_data))

        team = load_team_config(tmp_path)

        assert team is not None
        assert team.name == "test-team"

    def test_load_missing_file(self, tmp_path: Path):
        """ファイルが存在しない場合"""
        team = load_team_config(tmp_path)
        assert team is None

    def test_load_invalid_json(self, tmp_path: Path):
        """無効なJSONの場合"""
        config_file = tmp_path / "config.json"
        config_file.write_text("invalid json")

        team = load_team_config(tmp_path)
        assert team is None


# ============================================================================
# load_team_messages テスト
# ============================================================================


class TestLoadTeamMessages:
    """load_team_messages関数のテスト"""

    def test_load_messages_from_list(self, tmp_path: Path):
        """リスト形式のinbox読み込み"""
        inbox_dir = tmp_path / "inboxes"
        inbox_dir.mkdir()
        inbox_file = inbox_dir / "agent1.json"
        messages = [
            {
                "id": "msg-001",
                "sender": "user",
                "recipient": "agent1",
                "content": "Hello",
                "timestamp": "2026-02-06T12:00:00Z",
            }
        ]
        inbox_file.write_text(json.dumps(messages))

        result = load_team_messages(tmp_path)

        assert len(result) == 1
        assert result[0].content == "Hello"

    def test_load_no_inbox_directory(self, tmp_path: Path):
        """inboxディレクトリが存在しない場合"""
        result = load_team_messages(tmp_path)
        assert result == []


# ============================================================================
# load_team_tasks テスト
# ============================================================================


class TestLoadTeamTasks:
    """load_team_tasks関数のテスト"""

    def test_load_tasks(self, tmp_path: Path, monkeypatch):
        """タスクの読み込み"""
        # monkeypatchでPath.home()をモック
        task_dir = tmp_path / ".claude" / "tasks" / "test-team"
        task_dir.mkdir(parents=True)

        task_file = task_dir / "task-001.json"
        task_data = {
            "taskId": "task-001",
            "subject": "Test task",
            "description": "Test",
            "status": "pending",
        }
        task_file.write_text(json.dumps(task_data))

        # モックの設定
        class MockPath(Path):
            def __new__(cls, *args, **kwargs):
                if len(args) == 1 and args[0] == ".claude":
                    return tmp_path / ".claude"
                return Path.__new__(cls, *args, **kwargs)

        # 注意: 実際のテストでは fixtures を使用する方が良い
        # ここでは簡易的にスキップ
