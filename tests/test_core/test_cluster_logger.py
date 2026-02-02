"""ClusterLoggerモジュールのテスト

このモジュールでは、cluster_logger.pyのテストを実装します。
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from orchestrator.core.cluster_logger import ClusterLogger, LogEntry, LogFilter


class TestLogEntry:
    """LogEntryのテスト"""

    def test_from_dict(self):
        """辞書からLogEntryを作成できる"""
        data = {
            "timestamp": "2025-01-01T12:00:00",
            "id": "test-id-001",
            "from_agent": "grand_boss",
            "to_agent": "middle_manager",
            "type": "task",
            "content": "テストタスク",
            "level": "INFO",
        }

        entry = LogEntry.from_dict(data)

        assert entry.timestamp == "2025-01-01T12:00:00"
        assert entry.id == "test-id-001"
        assert entry.from_agent == "grand_boss"
        assert entry.to_agent == "middle_manager"
        assert entry.type == "task"
        assert entry.content == "テストタスク"
        assert entry.level == "INFO"

    def test_from_dict_with_missing_fields(self):
        """欠落したフィールドがある場合にデフォルト値を使用する"""
        data = {
            "timestamp": "2025-01-01T12:00:00",
            "id": "test-id-001",
            "from_agent": "grand_boss",
            "to_agent": "middle_manager",
            "type": "task",
            "content": "テストタスク",
            "level": "INFO",
        }

        entry = LogEntry.from_dict({})

        assert entry.timestamp == ""
        assert entry.id == ""
        assert entry.from_agent == ""
        assert entry.to_agent == ""
        assert entry.type == ""
        assert entry.content == ""
        assert entry.level == ""


class TestLogFilter:
    """LogFilterのテスト"""

    def test_default_filter(self):
        """デフォルトのフィルタ条件"""
        log_filter = LogFilter()

        assert log_filter.from_agent is None
        assert log_filter.to_agent is None
        assert log_filter.msg_type is None
        assert log_filter.level is None
        assert log_filter.start_time is None
        assert log_filter.end_time is None
        assert log_filter.limit is None

    def test_filter_with_conditions(self):
        """フィルタ条件を指定する"""
        log_filter = LogFilter(
            from_agent="grand_boss",
            to_agent="middle_manager",
            msg_type="task",
            level="INFO",
            limit=10,
        )

        assert log_filter.from_agent == "grand_boss"
        assert log_filter.to_agent == "middle_manager"
        assert log_filter.msg_type == "task"
        assert log_filter.level == "INFO"
        assert log_filter.limit == 10


class TestClusterLogger:
    """ClusterLoggerのテスト"""

    @pytest.fixture
    def temp_log_dir(self, tmp_path: Path) -> Path:
        """一時ログディレクトリを作成"""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        return log_dir

    @pytest.fixture
    def sample_log_file(self, temp_log_dir: Path) -> Path:
        """サンプルログファイルを作成"""
        log_file = temp_log_dir / "messages.jsonl"

        entries = [
            {
                "timestamp": "2025-01-01T12:00:00",
                "id": "msg-001",
                "from_agent": "grand_boss",
                "to_agent": "middle_manager",
                "type": "task",
                "content": "新しい機能を実装してください",
                "level": "INFO",
            },
            {
                "timestamp": "2025-01-01T12:01:00",
                "id": "msg-002",
                "from_agent": "middle_manager",
                "to_agent": "grand_boss",
                "type": "result",
                "content": "実装が完了しました",
                "level": "INFO",
            },
            {
                "timestamp": "2025-01-01T12:02:00",
                "id": "msg-003",
                "from_agent": "middle_manager",
                "to_agent": "specialist_coding",
                "type": "task",
                "content": "コーディングタスク",
                "level": "DEBUG",
            },
        ]

        with open(log_file, "w", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        return log_file

    def test_read_logs(self, temp_log_dir: Path, sample_log_file: Path):
        """ログを読み込める"""
        logger = ClusterLogger(log_file="messages.jsonl", log_dir=str(temp_log_dir))
        entries = logger.read_logs()

        assert len(entries) == 3
        assert entries[0].from_agent == "grand_boss"
        assert entries[1].from_agent == "middle_manager"
        assert entries[2].from_agent == "middle_manager"

    def test_read_logs_with_filter(self, temp_log_dir: Path, sample_log_file: Path):
        """フィルタを指定してログを読み込める"""
        logger = ClusterLogger(log_file="messages.jsonl", log_dir=str(temp_log_dir))

        # from_agentでフィルタ
        log_filter = LogFilter(from_agent="grand_boss")
        entries = logger.read_logs(log_filter)
        assert len(entries) == 1
        assert entries[0].from_agent == "grand_boss"

        # msg_typeでフィルタ
        log_filter = LogFilter(msg_type="task")
        entries = logger.read_logs(log_filter)
        assert len(entries) == 2

    def test_read_logs_with_limit(self, temp_log_dir: Path, sample_log_file: Path):
        """limitを指定してログを読み込める"""
        logger = ClusterLogger(log_file="messages.jsonl", log_dir=str(temp_log_dir))
        log_filter = LogFilter(limit=2)
        entries = logger.read_logs(log_filter)

        assert len(entries) == 2

    def test_get_stats(self, temp_log_dir: Path, sample_log_file: Path):
        """統計情報を取得できる"""
        logger = ClusterLogger(log_file="messages.jsonl", log_dir=str(temp_log_dir))
        stats = logger.get_stats()

        assert stats["total"] == 3
        assert stats["by_agent"]["grand_boss"] == 1
        assert stats["by_agent"]["middle_manager"] == 2
        assert stats["by_type"]["task"] == 2
        assert stats["by_type"]["result"] == 1

    def test_export_to_json(self, temp_log_dir: Path, sample_log_file: Path):
        """JSONファイルにエクスポートできる"""
        logger = ClusterLogger(log_file="messages.jsonl", log_dir=str(temp_log_dir))
        output_path = temp_log_dir / "export.json"

        logger.export_to_json(str(output_path))

        assert output_path.exists()

        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert len(data) == 3
        assert data[0]["from_agent"] == "grand_boss"

    def test_get_recent_logs(self, temp_log_dir: Path, sample_log_file: Path):
        """最近のログを取得できる"""
        logger = ClusterLogger(log_file="messages.jsonl", log_dir=str(temp_log_dir))
        recent = logger.get_recent_logs(count=2)

        assert len(recent) == 2
        # 新しい順（最後のエントリが最初）
        assert recent[0].id == "msg-003"
        assert recent[1].id == "msg-002"

    def test_read_logs_from_nonexistent_file(self, temp_log_dir: Path):
        """存在しないファイルを読み込もうとした場合に空のリストを返す"""
        logger = ClusterLogger(log_file="nonexistent.jsonl", log_dir=str(temp_log_dir))
        entries = logger.read_logs()

        assert entries == []

    def test_export_with_filter(self, temp_log_dir: Path, sample_log_file: Path):
        """フィルタ適用してエクスポートできる"""
        logger = ClusterLogger(log_file="messages.jsonl", log_dir=str(temp_log_dir))
        output_path = temp_log_dir / "export_filtered.json"

        log_filter = LogFilter(from_agent="grand_boss")
        logger.export_to_json(str(output_path), log_filter)

        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert len(data) == 1
        assert data[0]["from_agent"] == "grand_boss"
