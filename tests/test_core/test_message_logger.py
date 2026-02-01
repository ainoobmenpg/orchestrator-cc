"""MessageLoggerのテスト

このモジュールでは、MessageLoggerクラスの単体テストを実装します。
"""

import json
import os
from pathlib import Path

import pytest

from orchestrator.core.message_logger import MessageLogger
from orchestrator.core.message_models import LogLevel, MessageType


class TestMessageLoggerInit:
    """MessageLogger初期化処理のテスト"""

    def test_init_with_default_params(self):
        """デフォルトパラメータで初期化できる"""
        logger = MessageLogger()
        assert logger._log_file == "logs/messages.jsonl"
        assert logger._enabled is True

    def test_init_with_custom_log_file(self):
        """カスタムログファイルパスで初期化できる"""
        logger = MessageLogger(log_file="test/custom.log")
        assert logger._log_file == "test/custom.log"

    def test_init_with_disabled(self):
        """無効状態で初期化できる"""
        logger = MessageLogger(enabled=False)
        assert logger._enabled is False

    def test_init_creates_log_directory(self, tmp_path):
        """ログディレクトリが作成される"""
        log_file = tmp_path / "subdir" / "messages.jsonl"
        logger = MessageLogger(log_file=str(log_file))
        assert os.path.exists(os.path.dirname(log_file))

    def test_init_does_not_create_log_file(self, tmp_path):
        """ログファイル自体は作成されない（初期化時）"""
        log_file = tmp_path / "messages.jsonl"
        MessageLogger(log_file=str(log_file))
        assert not log_file.exists()


class TestMessageLoggerLogSend:
    """log_sendメソッドのテスト"""

    def test_log_send_returns_uuid(self, tmp_path):
        """log_sendがUUIDを返す"""
        log_file = tmp_path / "messages.jsonl"
        logger = MessageLogger(log_file=str(log_file))

        msg_id = logger.log_send("agent_a", "agent_b", "Hello")

        assert isinstance(msg_id, str)
        assert len(msg_id) == 36  # UUID format

    def test_log_send_writes_to_file(self, tmp_path):
        """log_sendがファイルに書き込む"""
        log_file = tmp_path / "messages.jsonl"
        logger = MessageLogger(log_file=str(log_file))

        logger.log_send("agent_a", "agent_b", "Test message")

        assert log_file.exists()
        content = log_file.read_text(encoding="utf-8")
        assert len(content) > 0

    def test_log_send_with_task_type(self, tmp_path):
        """タスクタイプでログを記録"""
        log_file = tmp_path / "messages.jsonl"
        logger = MessageLogger(log_file=str(log_file))

        logger.log_send("agent_a", "agent_b", "Do task", msg_type=MessageType.TASK)

        content = log_file.read_text(encoding="utf-8")
        entry = json.loads(content.strip())
        assert entry["type"] == "task"

    def test_log_send_with_info_type(self, tmp_path):
        """情報タイプでログを記録"""
        log_file = tmp_path / "messages.jsonl"
        logger = MessageLogger(log_file=str(log_file))

        logger.log_send("agent_a", "agent_b", "Info message", msg_type=MessageType.INFO)

        content = log_file.read_text(encoding="utf-8")
        entry = json.loads(content.strip())
        assert entry["type"] == "info"

    def test_log_send_with_error_type(self, tmp_path):
        """エラータイプでログを記録"""
        log_file = tmp_path / "messages.jsonl"
        logger = MessageLogger(log_file=str(log_file))

        logger.log_send("agent_a", "agent_b", "Error occurred", msg_type=MessageType.ERROR)

        content = log_file.read_text(encoding="utf-8")
        entry = json.loads(content.strip())
        assert entry["type"] == "error"

    def test_log_send_when_disabled(self, tmp_path):
        """無効時にlog_sendがUUIDを返すがファイルに書き込まない"""
        log_file = tmp_path / "messages.jsonl"
        logger = MessageLogger(log_file=str(log_file), enabled=False)

        msg_id = logger.log_send("agent_a", "agent_b", "Test")

        assert isinstance(msg_id, str)
        assert not log_file.exists()

    def test_log_send_multiple_messages(self, tmp_path):
        """複数のメッセージを正しく記録"""
        log_file = tmp_path / "messages.jsonl"
        logger = MessageLogger(log_file=str(log_file))

        logger.log_send("agent_a", "agent_b", "Message 1")
        logger.log_send("agent_b", "agent_c", "Message 2")
        logger.log_send("agent_c", "agent_a", "Message 3")

        content = log_file.read_text(encoding="utf-8")
        lines = content.strip().split("\n")
        assert len(lines) == 3

        # 各行が有効なJSONであることを確認
        for line in lines:
            entry = json.loads(line)
            assert "timestamp" in entry
            assert "id" in entry
            assert "from_agent" in entry
            assert "to_agent" in entry
            assert "content" in entry


class TestMessageLoggerLogReceive:
    """log_receiveメソッドのテスト"""

    def test_log_receive_returns_uuid(self, tmp_path):
        """log_receiveがUUIDを返す"""
        log_file = tmp_path / "messages.jsonl"
        logger = MessageLogger(log_file=str(log_file))

        msg_id = logger.log_receive("agent_a", "agent_b", "Response")

        assert isinstance(msg_id, str)
        assert len(msg_id) == 36

    def test_log_receive_writes_to_file(self, tmp_path):
        """log_receiveがファイルに書き込む"""
        log_file = tmp_path / "messages.jsonl"
        logger = MessageLogger(log_file=str(log_file))

        logger.log_receive("agent_a", "agent_b", "Test response")

        assert log_file.exists()
        content = log_file.read_text(encoding="utf-8")
        assert len(content) > 0

    def test_log_receive_with_result_type(self, tmp_path):
        """結果タイプでログを記録"""
        log_file = tmp_path / "messages.jsonl"
        logger = MessageLogger(log_file=str(log_file))

        logger.log_receive("agent_a", "agent_b", "Task done", msg_type=MessageType.RESULT)

        content = log_file.read_text(encoding="utf-8")
        entry = json.loads(content.strip())
        assert entry["type"] == "result"

    def test_log_receive_when_disabled(self, tmp_path):
        """無効時にlog_receiveがUUIDを返すがファイルに書き込まない"""
        log_file = tmp_path / "messages.jsonl"
        logger = MessageLogger(log_file=str(log_file), enabled=False)

        msg_id = logger.log_receive("agent_a", "agent_b", "Test")

        assert isinstance(msg_id, str)
        assert not log_file.exists()


class TestMessageLoggerJsonlFormat:
    """JSONL形式のテスト"""

    def test_log_file_is_valid_jsonl(self, tmp_path):
        """ログファイルが有効なJSONL形式である"""
        log_file = tmp_path / "messages.jsonl"
        logger = MessageLogger(log_file=str(log_file))

        logger.log_send("agent_a", "agent_b", "Message 1")
        logger.log_send("agent_b", "agent_c", "Message 2")

        with open(log_file, encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line)
                assert isinstance(entry, dict)

    def test_each_line_contains_required_fields(self, tmp_path):
        """各エントリに必須フィールドが含まれる"""
        log_file = tmp_path / "messages.jsonl"
        logger = MessageLogger(log_file=str(log_file))

        logger.log_send("agent_a", "agent_b", "Test message")

        with open(log_file, encoding="utf-8") as f:
            entry = json.loads(f.readline())
            assert entry["from_agent"] == "agent_a"
            assert entry["to_agent"] == "agent_b"
            assert entry["content"] == "Test message"
            assert entry["type"] == "task"
            assert "timestamp" in entry
            assert "id" in entry

    def test_timestamp_is_iso8601(self, tmp_path):
        """タイムスタンプがISO 8601形式である"""
        log_file = tmp_path / "messages.jsonl"
        logger = MessageLogger(log_file=str(log_file))

        logger.log_send("agent_a", "agent_b", "Test")

        with open(log_file, encoding="utf-8") as f:
            entry = json.loads(f.readline())
            # ISO 8601形式には「T」が含まれる
            assert "T" in entry["timestamp"]

    def test_unicode_content_preserved(self, tmp_path):
        """Unicodeコンテンツが正しく保存される"""
        log_file = tmp_path / "messages.jsonl"
        logger = MessageLogger(log_file=str(log_file))

        # 日本語、絵文字を含むメッセージ
        content = "こんにちは👋 Hello World 🌍"
        logger.log_send("agent_a", "agent_b", content)

        with open(log_file, encoding="utf-8") as f:
            entry = json.loads(f.readline())
            assert entry["content"] == content


class TestMessageLoggerConsoleOutput:
    """コンソール出力のテスト"""

    def test_log_send_prints_to_console(self, tmp_path, capsys):
        """log_sendがコンソールに出力する"""
        log_file = tmp_path / "messages.jsonl"
        logger = MessageLogger(log_file=str(log_file))

        logger.log_send("agent_a", "agent_b", "Test message")

        captured = capsys.readouterr()
        assert "agent_a" in captured.out
        assert "agent_b" in captured.out
        assert "Test message" in captured.out

    def test_console_output_contains_timestamp(self, tmp_path, capsys):
        """コンソール出力にタイムスタンプが含まれる"""
        log_file = tmp_path / "messages.jsonl"
        logger = MessageLogger(log_file=str(log_file))

        logger.log_send("agent_a", "agent_b", "Test")

        captured = capsys.readouterr()
        assert "[" in captured.out
        assert "]" in captured.out

    def test_console_output_shows_direction(self, tmp_path, capsys):
        """コンソール出力に方向（→）が表示される"""
        log_file = tmp_path / "messages.jsonl"
        logger = MessageLogger(log_file=str(log_file))

        logger.log_send("agent_a", "agent_b", "Test")

        captured = capsys.readouterr()
        assert "→" in captured.out


class TestMessageLoggerAppendMode:
    """追記モードのテスト"""

    def test_log_append_to_existing_file(self, tmp_path):
        """既存ファイルに追記される"""
        log_file = tmp_path / "messages.jsonl"

        # 最初のロガーで1件記録
        logger1 = MessageLogger(log_file=str(log_file))
        logger1.log_send("agent_a", "agent_b", "First")

        # 新しいロガーで追加記録
        logger2 = MessageLogger(log_file=str(log_file))
        logger2.log_send("agent_b", "agent_c", "Second")

        with open(log_file, encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 2

            entry1 = json.loads(lines[0])
            entry2 = json.loads(lines[1])
            assert entry1["content"] == "First"
            assert entry2["content"] == "Second"


class TestMessageLoggerLogLevel:
    """ログレベル機能のテスト"""

    def test_init_with_log_level(self, tmp_path):
        """ログレベルを指定して初期化できる"""
        log_file = tmp_path / "messages.jsonl"
        logger = MessageLogger(log_file=str(log_file), log_level=LogLevel.WARN)
        assert logger.get_log_level() == LogLevel.WARN

    def test_default_log_level_is_info(self, tmp_path):
        """デフォルトのログレベルはINFOである"""
        log_file = tmp_path / "messages.jsonl"
        logger = MessageLogger(log_file=str(log_file))
        assert logger.get_log_level() == LogLevel.INFO

    def test_set_log_level(self, tmp_path):
        """ログレベルを設定できる"""
        log_file = tmp_path / "messages.jsonl"
        logger = MessageLogger(log_file=str(log_file))
        logger.set_log_level(LogLevel.ERROR)
        assert logger.get_log_level() == LogLevel.ERROR

    def test_log_level_filters_debug_messages(self, tmp_path):
        """INFOレベルではDEBUGメッセージがフィルタリングされる"""
        log_file = tmp_path / "messages.jsonl"
        logger = MessageLogger(log_file=str(log_file), log_level=LogLevel.INFO)

        logger.log_send("agent_a", "agent_b", "Debug message", log_level=LogLevel.DEBUG)
        logger.log_send("agent_a", "agent_b", "Info message", log_level=LogLevel.INFO)

        content = log_file.read_text(encoding="utf-8")
        lines = content.strip().split("\n")
        assert len(lines) == 1  # DEBUGメッセージのみフィルタリング
        entry = json.loads(lines[0])
        assert entry["content"] == "Info message"

    def test_log_level_filters_info_messages_when_warn(self, tmp_path):
        """WARNレベルではDEBUG/INFOメッセージがフィルタリングされる"""
        log_file = tmp_path / "messages.jsonl"
        logger = MessageLogger(log_file=str(log_file), log_level=LogLevel.WARN)

        logger.log_send("agent_a", "agent_b", "Debug message", log_level=LogLevel.DEBUG)
        logger.log_send("agent_a", "agent_b", "Info message", log_level=LogLevel.INFO)
        logger.log_send("agent_a", "agent_b", "Warn message", log_level=LogLevel.WARN)

        content = log_file.read_text(encoding="utf-8")
        lines = content.strip().split("\n")
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["content"] == "Warn message"

    def test_log_level_entry_includes_level_field(self, tmp_path):
        """ログエントリにlevelフィールドが含まれる"""
        log_file = tmp_path / "messages.jsonl"
        logger = MessageLogger(log_file=str(log_file))

        logger.log_send("agent_a", "agent_b", "Test", log_level=LogLevel.ERROR)

        content = log_file.read_text(encoding="utf-8")
        entry = json.loads(content.strip())
        assert "level" in entry
        assert entry["level"] == 3  # ERROR = 3


class TestMessageLoggerRotation:
    """ログローテーション機能のテスト"""

    def test_init_with_max_file_size(self, tmp_path):
        """最大ファイルサイズを指定して初期化できる"""
        log_file = tmp_path / "messages.jsonl"
        logger = MessageLogger(log_file=str(log_file), max_file_size=1000)
        assert logger._max_file_size == 1000

    def test_init_without_max_file_size(self, tmp_path):
        """最大ファイルサイズ未指定時はローテーションしない"""
        log_file = tmp_path / "messages.jsonl"
        logger = MessageLogger(log_file=str(log_file))
        assert logger._max_file_size is None

    def test_rotation_creates_new_file(self, tmp_path):
        """ファイルサイズ超過時にローテーションが実行される"""
        log_file = tmp_path / "messages.jsonl"
        logger = MessageLogger(log_file=str(log_file), max_file_size=50)

        # 十分に長いメッセージを送信してローテーションをトリガー
        logger.log_send("agent_a", "agent_b", "X" * 100)

        # ファイルがローテーションされている
        rotated_file = tmp_path / "messages.1.jsonl"
        assert rotated_file.exists()

        # ローテーション後に再度書き込みを実行
        logger.log_send("agent_a", "agent_b", "Y" * 100)

        # 2つ目のローテーションファイルが作成されている
        rotated_file2 = tmp_path / "messages.2.jsonl"
        assert rotated_file2.exists()

    def test_rotation_increments_counter(self, tmp_path):
        """ローテーションカウンターが増加する"""
        log_file = tmp_path / "messages.jsonl"
        logger = MessageLogger(log_file=str(log_file), max_file_size=50)

        # 1回目のローテーション
        logger.log_send("agent_a", "agent_b", "A" * 100)
        assert (tmp_path / "messages.1.jsonl").exists()

        # 2回目のローテーション
        logger.log_send("agent_a", "agent_b", "B" * 100)
        assert (tmp_path / "messages.1.jsonl").exists()
        assert (tmp_path / "messages.2.jsonl").exists()

    def test_rotation_preserves_existing_rotated_files(self, tmp_path):
        """既存のローテーションファイルが上書きされない"""
        log_file = tmp_path / "messages.jsonl"
        logger = MessageLogger(log_file=str(log_file), max_file_size=50)

        # 手動でローテーションファイルを作成
        (tmp_path / "messages.1.jsonl").write_text("existing data", encoding="utf-8")

        # ローテーションを実行
        logger.log_send("agent_a", "agent_b", "X" * 100)

        # 既存の.1.jsonlが保持され、新しく.2.jsonlが作成される
        assert (tmp_path / "messages.1.jsonl").read_text(encoding="utf-8") == "existing data"
        assert (tmp_path / "messages.2.jsonl").exists()

    def test_rotation_does_not_occur_when_under_limit(self, tmp_path):
        """サイズ制限内ではローテーションが実行されない"""
        log_file = tmp_path / "messages.jsonl"
        logger = MessageLogger(log_file=str(log_file), max_file_size=1000)

        logger.log_send("agent_a", "agent_b", "Small message")

        # ローテーションファイルが作成されていない
        assert not (tmp_path / "messages.1.jsonl").exists()
        # 元のファイルのみ存在
        assert log_file.exists()
