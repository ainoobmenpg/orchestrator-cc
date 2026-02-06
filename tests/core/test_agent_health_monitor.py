"""Agent Health Monitor テスト

このモジュールでは、AgentHealthMonitorの単体テストを行います。
"""

from unittest.mock import Mock, patch

from orchestrator.core.agent_health_monitor import (
    AgentHealthMonitor,
    AgentHealthStatus,
    HealthCheckEvent,
    get_agent_health_monitor,
)


class TestAgentHealthStatus:
    """AgentHealthStatusのテスト"""

    def test_initialization(self) -> None:
        """初期化テスト"""
        from datetime import datetime

        status = AgentHealthStatus(
            team_name="test-team",
            agent_name="test-agent",
            last_activity=datetime.now(),
            timeout_threshold=300.0,
        )

        assert status.team_name == "test-team"
        assert status.agent_name == "test-agent"
        assert status.is_healthy is True

    def test_check_health_healthy(self) -> None:
        """ヘルスチェック（健康）テスト"""
        from datetime import datetime

        status = AgentHealthStatus(
            team_name="test-team",
            agent_name="test-agent",
            last_activity=datetime.now(),
            timeout_threshold=300.0,
        )

        assert status.check_health() is True

    def test_check_health_unhealthy(self) -> None:
        """ヘルスチェック（不健康）テスト"""
        from datetime import datetime, timedelta

        status = AgentHealthStatus(
            team_name="test-team",
            agent_name="test-agent",
            last_activity=datetime.now() - timedelta(seconds=400),
            timeout_threshold=300.0,
        )

        assert status.check_health() is False


class TestHealthCheckEvent:
    """HealthCheckEventのテスト"""

    def test_to_dict(self) -> None:
        """to_dictメソッドのテスト"""
        from datetime import datetime

        event = HealthCheckEvent(
            event_type="timeout_detected",
            team_name="test-team",
            agent_name="test-agent",
            timestamp=datetime.now(),
            details={"elapsed": 400.0},
        )

        data = event.to_dict()

        assert data["eventType"] == "timeout_detected"
        assert data["teamName"] == "test-team"
        assert data["agentName"] == "test-agent"
        assert "timestamp" in data
        assert data["details"]["elapsed"] == 400.0


class TestAgentHealthMonitor:
    """AgentHealthMonitorのテスト"""

    def test_initialization(self) -> None:
        """初期化テスト"""
        monitor = AgentHealthMonitor(check_interval=30.0)

        assert monitor.is_running() is False
        assert monitor._check_interval == 30.0

    def test_register_agent(self) -> None:
        """エージェント登録テスト"""
        monitor = AgentHealthMonitor()

        monitor.register_agent(
            team_name="test-team",
            agent_name="test-agent",
            timeout_threshold=300.0,
        )

        status = monitor.get_health_status()
        assert "test-team" in status
        assert "test-agent" in status["test-team"]

    def test_register_multiple_agents(self) -> None:
        """複数エージェント登録テスト"""
        monitor = AgentHealthMonitor()

        monitor.register_agent("test-team", "agent1", 300.0)
        monitor.register_agent("test-team", "agent2", 300.0)
        monitor.register_agent("other-team", "agent1", 300.0)

        status = monitor.get_health_status()
        assert "test-team" in status
        assert "other-team" in status
        assert len(status["test-team"]) == 2
        assert len(status["other-team"]) == 1

    def test_update_activity(self) -> None:
        """アクティビティ更新テスト"""
        monitor = AgentHealthMonitor()

        monitor.register_agent("test-team", "test-agent", 300.0)
        monitor.update_activity("test-team", "test-agent")

        status = monitor.get_health_status()
        assert status["test-team"]["test-agent"]["isHealthy"] is True

    def test_callback_registration(self) -> None:
        """コールバック登録テスト"""
        monitor = AgentHealthMonitor()
        callback = Mock()

        monitor.register_callback(callback)

        assert callback in monitor._callbacks

    def test_get_health_status_empty(self) -> None:
        """空のヘルスステータス取得テスト"""
        monitor = AgentHealthMonitor()

        status = monitor.get_health_status()
        assert status == {}

    def test_start_stop_monitoring(self) -> None:
        """監視開始・停止テスト"""
        monitor = AgentHealthMonitor(check_interval=1.0)

        monitor.start_monitoring()
        assert monitor.is_running() is True

        monitor.stop_monitoring()
        assert monitor.is_running() is False

    def test_start_already_running(self) -> None:
        """既に実行中の監視開始テスト"""
        monitor = AgentHealthMonitor()

        monitor.start_monitoring()
        monitor.start_monitoring()  # 重複呼び出し

        assert monitor.is_running() is True

        monitor.stop_monitoring()


class TestSingleton:
    """シングルトン機能のテスト"""

    def test_get_agent_health_monitor_singleton(self) -> None:
        """シングルトンインスタンスのテスト"""
        monitor1 = get_agent_health_monitor()
        monitor2 = get_agent_health_monitor()

        assert monitor1 is monitor2

    @patch("orchestrator.core.agent_health_monitor._health_monitor", None)
    def test_singleton_creates_new_instance(self) -> None:
        """新規インスタンス作成のテスト"""
        # グローバルインスタンスをリセットしてテスト
        import importlib

        import orchestrator.core.agent_health_monitor as module

        # モジュールをリロードしてシングルトンをリセット
        importlib.reload(module)

        monitor1 = module.get_agent_health_monitor()
        monitor2 = module.get_agent_health_monitor()

        assert monitor1 is monitor2
