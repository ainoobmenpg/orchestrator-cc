"""dashboard_managerモジュールのユニットテスト"""

import asyncio
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from orchestrator.core.dashboard_manager import (
    DashboardManager,
    DashboardManagerError,
    DashboardWriteError,
    StatusFileReadError,
)
from orchestrator.core.yaml_protocol import AgentStatus


class TestDashboardManager:
    """DashboardManagerクラスのテスト"""

    def test_init(self, tmp_path: Path) -> None:
        """初期化テスト"""
        status_dir = tmp_path / "status"
        dashboard_path = tmp_path / "dashboard.md"

        manager = DashboardManager(status_dir, dashboard_path)

        assert manager._status_dir == status_dir
        assert manager._dashboard_path == dashboard_path

        # ディレクトリが作成されていることを確認
        assert status_dir.exists()
        assert status_dir.is_dir()

    def test_init_creates_directories(self, tmp_path: Path) -> None:
        """初期化時のディレクトリ作成テスト"""
        status_dir = tmp_path / "nested" / "status"
        dashboard_path = tmp_path / "nested" / "dashboard.md"

        DashboardManager(status_dir, dashboard_path)

        assert status_dir.exists()
        assert status_dir.is_dir()

    def test_agent_display_names(self) -> None:
        """エージェント表示名マッピングテスト"""
        expected = {
            "grand_boss": "Grand Boss",
            "middle_manager": "Middle Manager",
            "coding_writing_specialist": "Coding & Writing Specialist",
            "research_analysis_specialist": "Research & Analysis Specialist",
            "testing_specialist": "Testing Specialist",
        }

        assert DashboardManager.AGENT_DISPLAY_NAMES == expected

    def test_get_default_status(self, tmp_path: Path) -> None:
        """デフォルトステータス取得テスト"""
        status_dir = tmp_path / "status"
        dashboard_path = tmp_path / "dashboard.md"

        manager = DashboardManager(status_dir, dashboard_path)

        default_status = manager._get_default_status("grand_boss")

        assert default_status["agent_name"] == "grand_boss"
        assert default_status["state"] == "idle"
        assert default_status["current_task"] is None
        assert "last_updated" in default_status
        assert default_status["statistics"] == {"tasks_completed": 0}

    def test_get_state_emoji(self, tmp_path: Path) -> None:
        """状態絵文字取得テスト"""
        status_dir = tmp_path / "status"
        dashboard_path = tmp_path / "dashboard.md"

        manager = DashboardManager(status_dir, dashboard_path)

        assert manager._get_state_emoji("idle") == "💤"
        assert manager._get_state_emoji("working") == "⚙️"
        assert manager._get_state_emoji("completed") == "✅"
        assert manager._get_state_emoji("error") == "❌"
        assert manager._get_state_emoji("unknown") == "❓"

    def test_generate_agent_section(self, tmp_path: Path) -> None:
        """エージェントセクション生成テスト"""
        status_dir = tmp_path / "status"
        dashboard_path = tmp_path / "dashboard.md"

        manager = DashboardManager(status_dir, dashboard_path)

        status = {
            "agent_name": "grand_boss",
            "state": "working",
            "current_task": "タスク管理中",
            "last_updated": "2026-02-01T10:00:00",
            "statistics": {"tasks_completed": 5},
        }

        section = manager._generate_agent_section(
            "grand_boss", "Grand Boss", status
        )

        assert "### ⚙️ Grand Boss" in section
        assert "**状態**: `working`" in section
        assert "**現在のタスク**: タスク管理中" in section
        assert "**完了タスク数**: 5" in section

    def test_generate_agent_section_no_current_task(self, tmp_path: Path) -> None:
        """現在のタスクがない場合のエージェントセクション生成テスト"""
        status_dir = tmp_path / "status"
        dashboard_path = tmp_path / "dashboard.md"

        manager = DashboardManager(status_dir, dashboard_path)

        status = {
            "agent_name": "middle_manager",
            "state": "idle",
            "current_task": None,
            "last_updated": "2026-02-01T10:00:00",
            "statistics": {"tasks_completed": 0},
        }

        section = manager._generate_agent_section(
            "middle_manager", "Middle Manager", status
        )

        assert "**現在のタスク**: なし" in section

    def test_generate_summary(self, tmp_path: Path) -> None:
        """サマリー生成テスト"""
        status_dir = tmp_path / "status"
        dashboard_path = tmp_path / "dashboard.md"

        manager = DashboardManager(status_dir, dashboard_path)

        agent_statuses = {
            "grand_boss": {
                "agent_name": "grand_boss",
                "state": "idle",
                "current_task": None,
                "last_updated": "2026-02-01T10:00:00",
                "statistics": {"tasks_completed": 3},
            },
            "middle_manager": {
                "agent_name": "middle_manager",
                "state": "working",
                "current_task": "タスク中",
                "last_updated": "2026-02-01T10:00:00",
                "statistics": {"tasks_completed": 5},
            },
            "coding_writing_specialist": {
                "agent_name": "coding_writing_specialist",
                "state": "working",
                "current_task": "実装中",
                "last_updated": "2026-02-01T10:00:00",
                "statistics": {"tasks_completed": 2},
            },
            "research_analysis_specialist": {
                "agent_name": "research_analysis_specialist",
                "state": "completed",
                "current_task": None,
                "last_updated": "2026-02-01T10:00:00",
                "statistics": {"tasks_completed": 1},
            },
            "testing_specialist": {
                "agent_name": "testing_specialist",
                "state": "error",
                "current_task": None,
                "last_updated": "2026-02-01T10:00:00",
                "statistics": {"tasks_completed": 0},
            },
        }

        summary = manager._generate_summary(agent_statuses)

        summary_text = "".join(summary)

        assert "**総完了タスク数**: 11" in summary_text
        assert "**アイドル中**: 1" in summary_text
        assert "**作業中**: 2" in summary_text
        assert "**完了**: 1" in summary_text
        assert "**エラー**: 1" in summary_text

    @pytest.mark.asyncio
    async def test_update_dashboard(self, tmp_path: Path) -> None:
        """ダッシュボード更新テスト"""
        status_dir = tmp_path / "status" / "agents"
        dashboard_path = tmp_path / "dashboard.md"

        # ステータスファイルを作成
        status_dir.mkdir(parents=True)

        agent_status = AgentStatus(
            agent_name="grand_boss",
            state="idle",
        )
        agent_status.to_file(status_dir / "grand_boss.yaml")

        manager = DashboardManager(status_dir.parent, dashboard_path)

        await manager.update_dashboard()

        # ダッシュボードファイルが作成されていることを確認
        assert dashboard_path.exists()

        content = dashboard_path.read_text(encoding="utf-8")

        assert "# orchestrator-cc ダッシュボード" in content
        assert "Grand Boss" in content

    @pytest.mark.asyncio
    async def test_update_dashboard_with_missing_status_files(self, tmp_path: Path) -> None:
        """ステータスファイルがない場合のダッシュボード更新テスト"""
        status_dir = tmp_path / "status" / "agents"
        dashboard_path = tmp_path / "dashboard.md"

        # ディレクトリのみ作成（ファイルなし）
        status_dir.mkdir(parents=True)

        manager = DashboardManager(status_dir.parent, dashboard_path)

        await manager.update_dashboard()

        # ダッシュボードファイルが作成されていることを確認
        assert dashboard_path.exists()

        content = dashboard_path.read_text(encoding="utf-8")

        # 全エージェントがデフォルトステータスで表示される
        for display_name in DashboardManager.AGENT_DISPLAY_NAMES.values():
            assert display_name in content

    def test_generate_dashboard(self, tmp_path: Path) -> None:
        """ダッシュボード生成テスト"""
        status_dir = tmp_path / "status"
        dashboard_path = tmp_path / "dashboard.md"

        manager = DashboardManager(status_dir, dashboard_path)

        agent_statuses = {
            "grand_boss": {
                "agent_name": "grand_boss",
                "state": "idle",
                "current_task": None,
                "last_updated": "2026-02-01T10:00:00",
                "statistics": {"tasks_completed": 0},
            }
        }

        dashboard = manager._generate_dashboard(agent_statuses)

        assert "# orchestrator-cc ダッシュボード" in dashboard
        assert "## 📊 サマリー" in dashboard
        assert "## 👥 エージェントステータス" in dashboard
        assert "Grand Boss" in dashboard
        assert "このダッシュボードは自動更新されています" in dashboard

    @pytest.mark.asyncio
    async def test_update_dashboard_error_handling(self, tmp_path: Path, caplog) -> None:
        """ダッシュボード更新エラーハンドリングテスト"""
        import logging

        status_dir = tmp_path / "status"
        # __init__でディレクトリが作成される
        dashboard_path = tmp_path / "dashboard.md"

        manager = DashboardManager(status_dir, dashboard_path)

        # エラーを発生させるためにモックを使用
        with caplog.at_level(logging.ERROR):
            with patch.object(manager, "_load_agent_statuses", side_effect=Exception("test error")):
                await manager.update_dashboard()

        # エラーログが記録されていることを確認
        assert any(
            "ダッシュボードの更新に失敗しました" in record.message
            for record in caplog.records
        )


class TestDashboardManagerExceptions:
    """DashboardManager例外クラスのテスト"""

    def test_dashboard_manager_error(self) -> None:
        """DashboardManagerErrorテスト"""
        with pytest.raises(DashboardManagerError):
            raise DashboardManagerError("test error")

    def test_status_file_read_error(self) -> None:
        """StatusFileReadErrorテスト"""
        with pytest.raises(StatusFileReadError):
            raise StatusFileReadError("read error")

    def test_dashboard_write_error(self) -> None:
        """DashboardWriteErrorテスト"""
        with pytest.raises(DashboardWriteError):
            raise DashboardWriteError("write error")
