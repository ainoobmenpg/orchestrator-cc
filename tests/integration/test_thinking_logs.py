"""思考ログの統合テスト

V-TL-001: 思考ログ送信検証
V-TL-002: 思考ログ監視検証
"""

from datetime import datetime
from pathlib import Path

from orchestrator.web.thinking_log_handler import (
    ThinkingLogEntry,
    get_thinking_log_handler,
    send_thinking_log,
)


class TestThinkingLogSending:
    """思考ログ送信の統合テスト (V-TL-001)"""

    def test_send_thinking_log(self):
        """send_thinking_log() 呼び出しでログが記録される"""
        handler = get_thinking_log_handler()

        # 思考ログを送信
        send_thinking_log(
            agent_name="test-agent",
            content="これはテスト用の思考ログです",
            team_name="test-team",
            category="thinking",
            emotion="neutral",
        )

        # ログが記録されていることを確認
        logs = handler.get_logs("test-team")

        assert len(logs) > 0
        assert logs[-1]["agentName"] == "test-agent"
        assert "テスト用の思考ログ" in logs[-1]["content"]
        assert logs[-1]["teamName"] == "test-team"

    def test_send_thinking_log_with_different_categories(self):
        """異なるカテゴリの思考ログを送信"""
        handler = get_thinking_log_handler()
        team_name = "category-test-team"

        # 異なるカテゴリでログを送信
        categories = ["thinking", "planning", "decision", "question"]

        for category in categories:
            send_thinking_log(
                agent_name="test-agent",
                content=f"{category} ログ",
                team_name=team_name,
                category=category,
            )

        # 全てのログが記録されていることを確認
        logs = handler.get_logs(team_name)

        assert len(logs) >= len(categories)

        logged_categories = {log["category"] for log in logs}
        for category in categories:
            assert category in logged_categories

    def test_thinking_log_entry_to_dict(self):
        """ThinkingLogEntry の to_dict() メソッドのテスト"""
        entry = ThinkingLogEntry(
            agent_name="test-agent",
            content="テスト内容",
            timestamp="2026-02-06T12:00:00",
            category="thinking",
            emotion="neutral",
            team_name="test-team",
        )

        result = entry.to_dict()

        assert result["agentName"] == "test-agent"
        assert result["content"] == "テスト内容"
        assert result["timestamp"] == "2026-02-06T12:00:00"
        assert result["category"] == "thinking"
        assert result["emotion"] == "neutral"
        assert result["teamName"] == "test-team"


class TestThinkingLogMonitoring:
    """思考ログ監視の統合テスト (V-TL-002)"""

    def test_log_persistence_to_file(self, tmp_path: Path):
        """ログがファイルに保存されることを確認"""
        log_dir = tmp_path / "thinking-logs"
        log_dir.mkdir(parents=True)

        handler = get_thinking_log_handler()

        # ハンドラーのログディレクトリを一時ディレクトリに変更
        handler._log_dir = log_dir

        # ログを追加
        entry = ThinkingLogEntry(
            agent_name="file-test-agent",
            content="ファイル保存テスト",
            timestamp=datetime.now().isoformat(),
            category="thinking",
            emotion="neutral",
            team_name="file-test-team",
        )

        handler.add_log(entry)

        # ファイルが作成されていることを確認
        log_file = log_dir / "file-test-team.jsonl"
        assert log_file.exists()

        # ファイルの内容を確認
        content = log_file.read_text(encoding="utf-8")
        assert "ファイル保存テスト" in content
        assert "file-test-agent" in content

    def test_callback_on_new_log(self):
        """新しいログ追加時にコールバックが呼ばれることを確認"""
        handler = get_thinking_log_handler()

        callback_called = []

        def test_callback(data):
            callback_called.append(data)

        # コールバックを登録
        handler.register_callback(test_callback)

        # ログを送信
        send_thinking_log(
            agent_name="callback-test-agent",
            content="コールバックテスト",
            team_name="callback-test-team",
        )

        # コールバックが呼ばれたことを確認
        assert len(callback_called) > 0
        assert callback_called[0]["type"] == "thinking_log"
        assert callback_called[0]["teamName"] == "callback-test-team"

    def test_multiple_teams_logs(self):
        """複数チームのログが正しく分離されることを確認"""
        handler = get_thinking_log_handler()

        # 異なるチームにログを送信
        send_thinking_log(
            agent_name="agent1",
            content="チームAのログ",
            team_name="team-a",
        )

        send_thinking_log(
            agent_name="agent2",
            content="チームBのログ",
            team_name="team-b",
        )

        # 各チームのログを取得して確認
        logs_a = handler.get_logs("team-a")
        logs_b = handler.get_logs("team-b")

        assert len(logs_a) > 0
        assert len(logs_b) > 0

        # チームAのログにチームBの内容が混ざっていないことを確認
        a_contents = [log["content"] for log in logs_a]
        b_contents = [log["content"] for log in logs_b]

        assert any("チームA" in c for c in a_contents)
        assert not any("チームB" in c for c in a_contents)
        assert any("チームB" in c for c in b_contents)
        assert not any("チームA" in c for c in b_contents)
