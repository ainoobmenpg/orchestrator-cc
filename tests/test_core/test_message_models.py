"""MessageModelの単体テスト"""

import pytest

from orchestrator.core.message_models import (
    CCMessage,
    LogLevel,
    MessageLogEntry,
    MessageType,
)


class TestLogLevel:
    """LogLevel列挙型のテスト"""

    def test_level_values(self):
        """各レベルの値が正しいことを確認"""
        assert LogLevel.DEBUG.value == 0
        assert LogLevel.INFO.value == 1
        assert LogLevel.WARN.value == 2
        assert LogLevel.ERROR.value == 3

    def test_level_comparison(self):
        """レベルの比較が正しく動作することを確認"""
        assert LogLevel.DEBUG < LogLevel.INFO
        assert LogLevel.INFO < LogLevel.WARN
        assert LogLevel.WARN < LogLevel.ERROR


class TestMessageType:
    """MessageType列挙型のテスト"""

    def test_type_values(self):
        """各タイプの値が正しいことを確認"""
        assert MessageType.TASK.value == "task"
        assert MessageType.INFO.value == "info"
        assert MessageType.RESULT.value == "result"
        assert MessageType.ERROR.value == "error"

    def test_type_is_string_enum(self):
        """文字列列挙型として振る舞うことを確認"""
        msg_type = MessageType.TASK
        assert isinstance(msg_type.value, str)
        assert msg_type == "task"


class TestCCMessage:
    """CCMessageのテスト"""

    def test_creation(self):
        """全フィールドを指定してメッセージを作成"""
        message = CCMessage(
            from_agent="grand_boss",
            to_agent="middle_manager",
            content="Hello, World!",
        )
        assert message.from_agent == "grand_boss"
        assert message.to_agent == "middle_manager"
        assert message.content == "Hello, World!"

    def test_creation_with_empty_content(self):
        """空のコンテンツでメッセージを作成"""
        message = CCMessage(
            from_agent="agent_a",
            to_agent="agent_b",
            content="",
        )
        assert message.content == ""

    def test_creation_with_multiline_content(self):
        """複数行のコンテンツでメッセージを作成"""
        content = "Line 1\nLine 2\nLine 3"
        message = CCMessage(
            from_agent="agent_a",
            to_agent="agent_b",
            content=content,
        )
        assert message.content == content


class TestMessageLogEntry:
    """MessageLogEntryのテスト"""

    def test_creation(self):
        """全フィールドを指定してログエントリを作成"""
        entry = MessageLogEntry(
            timestamp="2026-02-01T12:00:00",
            id="123e4567-e89b-12d3-a456-426614174000",
            from_agent="grand_boss",
            to_agent="middle_manager",
            type="task",
            content="Please review this code",
            level=1,
        )
        assert entry.timestamp == "2026-02-01T12:00:00"
        assert entry.id == "123e4567-e89b-12d3-a456-426614174000"
        assert entry.from_agent == "grand_boss"
        assert entry.to_agent == "middle_manager"
        assert entry.type == "task"
        assert entry.content == "Please review this code"
        assert entry.level == 1

    def test_creation_default_level(self):
        """デフォルトのログレベルはINFO(1)である"""
        entry = MessageLogEntry(
            timestamp="2026-02-01T12:00:00",
            id="test-id",
            from_agent="agent_a",
            to_agent="agent_b",
            type="info",
            content="Test",
        )
        assert entry.level == 1

    def test_creation_with_error_type(self):
        """エラータイプでログエントリを作成"""
        entry = MessageLogEntry(
            timestamp="2026-02-01T12:00:00",
            id="error-id",
            from_agent="agent_a",
            to_agent="agent_b",
            type="error",
            content="Something went wrong",
        )
        assert entry.type == "error"
        assert entry.content == "Something went wrong"

    def test_creation_with_result_type(self):
        """結果タイプでログエントリを作成"""
        entry = MessageLogEntry(
            timestamp="2026-02-01T12:00:00",
            id="result-id",
            from_agent="middle_manager",
            to_agent="grand_boss",
            type="result",
            content="Task completed successfully",
        )
        assert entry.type == "result"
        assert entry.content == "Task completed successfully"

    def test_creation_with_info_type(self):
        """情報タイプでログエントリを作成"""
        entry = MessageLogEntry(
            timestamp="2026-02-01T12:00:00",
            id="info-id",
            from_agent="system",
            to_agent="all",
            type="info",
            content="Cluster started",
        )
        assert entry.type == "info"
        assert entry.content == "Cluster started"
