"""Thinking Log Handler テスト

このモジュールでは、ThinkingLogHandlerの単体テストを行います。
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from orchestrator.web.thinking_log_handler import (
    ThinkingLogEntry,
    ThinkingLogHandler,
    get_thinking_log_handler,
    send_thinking_log,
)


class TestThinkingLogEntry:
    """ThinkingLogEntryのテスト"""

    def test_initialization(self) -> None:
        """初期化テスト"""
        entry = ThinkingLogEntry(
            agent_name="test-agent",
            content="Test thinking log",
            timestamp="2026-02-06T12:00:00",
            category="thinking",
            emotion="neutral",
            team_name="test-team",
        )

        assert entry.agent_name == "test-agent"
        assert entry.content == "Test thinking log"
        assert entry.timestamp == "2026-02-06T12:00:00"
        assert entry.category == "thinking"
        assert entry.emotion == "neutral"
        assert entry.team_name == "test-team"

    def test_to_dict(self) -> None:
        """to_dictメソッドのテスト"""
        entry = ThinkingLogEntry(
            agent_name="test-agent",
            content="Test thinking log",
            timestamp="2026-02-06T12:00:00",
            category="thinking",
            emotion="neutral",
            team_name="test-team",
        )

        data = entry.to_dict()

        assert data["agentName"] == "test-agent"
        assert data["content"] == "Test thinking log"
        assert data["timestamp"] == "2026-02-06T12:00:00"
        assert data["category"] == "thinking"
        assert data["emotion"] == "neutral"
        assert data["teamName"] == "test-team"

    def test_to_dict_defaults(self) -> None:
        """デフォルト値付きのto_dictテスト"""
        entry = ThinkingLogEntry(
            agent_name="test-agent",
            content="Test thinking log",
            timestamp="2026-02-06T12:00:00",
        )

        data = entry.to_dict()

        assert data["category"] == "thinking"
        assert data["emotion"] == "neutral"
        assert data["teamName"] == ""


class TestThinkingLogHandler:
    """ThinkingLogHandlerのテスト"""

    def test_initialization(self) -> None:
        """初期化テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            handler = ThinkingLogHandler(log_dir=tmpdir)

            assert handler.is_running() is False
            assert Path(tmpdir).exists()

    def test_initialization_default_dir(self) -> None:
        """デフォルトディレクトリでの初期化テスト"""
        handler = ThinkingLogHandler()

        assert handler.is_running() is False

    def test_register_callback(self) -> None:
        """コールバック登録テスト"""
        handler = ThinkingLogHandler()
        callback = Mock()

        handler.register_callback(callback)

        assert callback in handler._callbacks

    def test_add_log(self) -> None:
        """ログ追加テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            handler = ThinkingLogHandler(log_dir=tmpdir)
            callback = Mock()
            handler.register_callback(callback)

            entry = ThinkingLogEntry(
                agent_name="test-agent",
                content="Test thinking log",
                timestamp="2026-02-06T12:00:00",
                team_name="test-team",
            )

            handler.add_log(entry)

            # ログが追加されている
            logs = handler.get_logs("test-team")
            assert len(logs) == 1
            assert logs[0]["content"] == "Test thinking log"

            # コールバックが呼ばれている
            callback.assert_called_once()

    def test_add_log_duplicate(self) -> None:
        """重複ログ追加テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            handler = ThinkingLogHandler(log_dir=tmpdir)
            callback = Mock()
            handler.register_callback(callback)

            entry = ThinkingLogEntry(
                agent_name="test-agent",
                content="Test thinking log",
                timestamp="2026-02-06T12:00:00",
                team_name="test-team",
            )

            handler.add_log(entry)
            handler.add_log(entry)  # 重複

            # 重複は追加されない
            logs = handler.get_logs("test-team")
            assert len(logs) == 1

            # コールバックは1回のみ
            callback.assert_called_once()

    def test_add_log_different_teams(self) -> None:
        """異なるチームのログ追加テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            handler = ThinkingLogHandler(log_dir=tmpdir)

            entry1 = ThinkingLogEntry(
                agent_name="agent1",
                content="Log 1",
                timestamp="2026-02-06T12:00:00",
                team_name="team1",
            )

            entry2 = ThinkingLogEntry(
                agent_name="agent2",
                content="Log 2",
                timestamp="2026-02-06T12:01:00",
                team_name="team2",
            )

            handler.add_log(entry1)
            handler.add_log(entry2)

            assert len(handler.get_logs("team1")) == 1
            assert len(handler.get_logs("team2")) == 1

    def test_get_logs_empty_team(self) -> None:
        """空のチームログ取得テスト"""
        handler = ThinkingLogHandler()

        logs = handler.get_logs("non-existent")

        assert logs == []

    def test_start_stop_monitoring(self) -> None:
        """監視開始・停止テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            handler = ThinkingLogHandler(log_dir=tmpdir)

            handler.start_monitoring()
            assert handler.is_running() is True

            handler.stop_monitoring()
            assert handler.is_running() is False

    def test_write_log_to_file(self) -> None:
        """ログファイル書き込みテスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            handler = ThinkingLogHandler(log_dir=tmpdir)

            entry = ThinkingLogEntry(
                agent_name="test-agent",
                content="Test thinking log",
                timestamp="2026-02-06T12:00:00",
                team_name="test-team",
            )

            handler.add_log(entry)

            # ファイルが作成されている
            log_file = Path(tmpdir) / "test-team.jsonl"
            assert log_file.exists()

            # 内容を確認
            with open(log_file, encoding="utf-8") as f:
                lines = f.readlines()

            assert len(lines) == 1
            data = json.loads(lines[0])
            assert data["content"] == "Test thinking log"

    def test_load_existing_logs(self) -> None:
        """既存ログの読み込みテスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 既存のログファイルを作成
            log_file = Path(tmpdir) / "test-team.jsonl"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "agentName": "agent1",
                    "content": "Existing log",
                    "timestamp": "2026-02-06T12:00:00",
                    "category": "thinking",
                    "emotion": "neutral",
                    "teamName": "test-team",
                }, ensure_ascii=False) + "\n")

            # ハンドラーを初期化（既存ログを読み込む）
            handler = ThinkingLogHandler(log_dir=tmpdir)

            logs = handler.get_logs("test-team")
            assert len(logs) == 1
            assert logs[0]["content"] == "Existing log"


class TestSendThinkingLog:
    """send_thinking_log関数のテスト"""

    def test_send_thinking_log(self) -> None:
        """思考ログ送信テスト"""
        with patch("orchestrator.web.thinking_log_handler._thinking_log_handler"), \
             patch("orchestrator.web.thinking_log_handler.get_thinking_log_handler") as mock_get:
            mock_handler = Mock()
            mock_get.return_value = mock_handler

            send_thinking_log(
                agent_name="test-agent",
                content="Test thinking",
                team_name="test-team",
                category="thinking",
                emotion="neutral",
            )

            # add_logが呼ばれている
            mock_handler.add_log.assert_called_once()

            # 引数を確認
            call_args = mock_handler.add_log.call_args[0][0]
            assert call_args.agent_name == "test-agent"
            assert call_args.content == "Test thinking"
            assert call_args.team_name == "test-team"


class TestSingleton:
    """シングルトン機能のテスト"""

    def test_get_thinking_log_handler_singleton(self) -> None:
        """シングルトンインスタンスのテスト"""
        handler1 = get_thinking_log_handler()
        handler2 = get_thinking_log_handler()

        assert handler1 is handler2

    @patch("orchestrator.web.thinking_log_handler._thinking_log_handler", None)
    def test_singleton_creates_new_instance(self) -> None:
        """新規インスタンス作成のテスト"""
        # グローバルインスタンスをリセットしてテスト
        import importlib

        import orchestrator.web.thinking_log_handler as module

        # モジュールをリロードしてシングルトンをリセット
        importlib.reload(module)

        handler1 = module.get_thinking_log_handler()
        handler2 = module.get_thinking_log_handler()

        assert handler1 is handler2
