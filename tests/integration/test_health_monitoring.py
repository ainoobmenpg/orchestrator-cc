"""ヘルスモニタリングの統合テスト

V-HM-001: エージェント登録検証
V-HM-002: タイムアウト検知検証
"""

import time

from orchestrator.core.agent_health_monitor import (
    HealthCheckEvent,
    get_agent_health_monitor,
)


class TestHealthMonitoringRegistration:
    """ヘルスモニタリング登録の統合テスト (V-HM-001)"""

    def test_agent_registration(self):
        """エージェントをヘルスモニターに登録して確認"""
        monitor = get_agent_health_monitor()

        # エージェントを登録
        monitor.register_agent(
            team_name="test-health-team",
            agent_name="test-agent",
            timeout_threshold=300.0,
        )

        # ヘルスステータスを取得
        status = monitor.get_health_status()

        # チームとエージェントが登録されていることを確認
        assert "test-health-team" in status
        assert "test-agent" in status["test-health-team"]

        agent_status = status["test-health-team"]["test-agent"]
        assert agent_status["isHealthy"] is True
        assert "lastActivity" in agent_status
        assert agent_status["timeoutThreshold"] == 300.0

    def test_multiple_agents_same_team(self):
        """同じチームに複数のエージェントを登録"""
        monitor = get_agent_health_monitor()

        team_name = "multi-agent-team"
        agents = ["agent1", "agent2", "agent3"]

        for agent in agents:
            monitor.register_agent(
                team_name=team_name,
                agent_name=agent,
                timeout_threshold=300.0,
            )

        status = monitor.get_health_status()

        # 全エージェントが登録されていることを確認
        assert team_name in status
        for agent in agents:
            assert agent in status[team_name]
            assert status[team_name][agent]["isHealthy"] is True

    def test_multiple_teams(self):
        """複数のチームを登録"""
        monitor = get_agent_health_monitor()

        teams = {
            "team-a": ["agent-a1", "agent-a2"],
            "team-b": ["agent-b1"],
            "team-c": ["agent-c1", "agent-c2", "agent-c3"],
        }

        for team_name, agents in teams.items():
            for agent in agents:
                monitor.register_agent(
                    team_name=team_name,
                    agent_name=agent,
                    timeout_threshold=300.0,
                )

        status = monitor.get_health_status()

        # 全チームと全エージェントが登録されていることを確認
        for team_name, agents in teams.items():
            assert team_name in status
            for agent in agents:
                assert agent in status[team_name]

    def test_get_team_health_status(self):
        """特定チームのヘルスステータスを取得"""
        monitor = get_agent_health_monitor()

        monitor.register_agent("team-x", "agent-x1", 300.0)
        monitor.register_agent("team-x", "agent-x2", 300.0)
        monitor.register_agent("team-y", "agent-y1", 300.0)

        # 全ステータスを取得して team-x のみを抽出
        all_status = monitor.get_health_status()

        assert "team-x" in all_status
        assert "agent-x1" in all_status["team-x"]
        assert "agent-x2" in all_status["team-x"]
        assert "team-y" in all_status


class TestHealthMonitoringTimeout:
    """ヘルスモニタリングタイムアウトの統合テスト (V-HM-002)"""

    def test_timeout_detection_short_threshold(self):
        """短いタイムアウト（5秒）で検知を確認"""
        monitor = get_agent_health_monitor()

        team_name = "timeout-test-team"
        agent_name = "timeout-agent"

        # 短いタイムアウト（5秒）でエージェントを登録
        monitor.register_agent(
            team_name=team_name,
            agent_name=agent_name,
            timeout_threshold=5.0,
        )

        # 登録直後は健全
        status = monitor.get_health_status()
        assert status[team_name][agent_name]["isHealthy"] is True

        # 6秒待機（タイムアウト超過）
        time.sleep(6)

        # タイムアウト検知（_check_all_agents を呼び出して明示的にチェック）
        monitor._check_all_agents()
        status = monitor.get_health_status()
        assert status[team_name][agent_name]["isHealthy"] is False
        assert status[team_name][agent_name]["elapsed"] > 5.0

    def test_no_timeout_with_activity_update(self):
        """アクティビティ更新でタイムアウトを回避"""
        monitor = get_agent_health_monitor()

        team_name = "heartbeat-team"
        agent_name = "heartbeat-agent"

        # 短いタイムアウト（3秒）で登録
        monitor.register_agent(
            team_name=team_name,
            agent_name=agent_name,
            timeout_threshold=3.0,
        )

        # 2秒待機
        time.sleep(2)

        # アクティビティ更新（ハートビート）
        monitor.update_activity(team_name, agent_name)

        # さらに2秒待機（合計4秒）
        time.sleep(2)

        # アクティビティ更新されたので、まだ健全
        status = monitor.get_health_status()
        # 経過時間はアクティビティ更新からの時間なので3秒未満
        assert status[team_name][agent_name]["isHealthy"] is True

    def test_timeout_callback(self):
        """タイムアウト時のコールバックを確認"""
        monitor = get_agent_health_monitor()

        callback_events = []

        def test_callback(event: HealthCheckEvent) -> None:
            callback_events.append(event)

        # コールバックを登録
        monitor.register_callback(test_callback)

        team_name = "callback-team"
        agent_name = "callback-agent"

        # 短いタイムアウト（2秒）で登録
        monitor.register_agent(
            team_name=team_name,
            agent_name=agent_name,
            timeout_threshold=2.0,
        )

        # 3秒待機（タイムアウト超過）
        time.sleep(3)

        # ヘルスチェックを実行してコールバックをトリガー
        monitor._check_all_agents()

        # コールバックが呼ばれたことを確認
        assert len(callback_events) > 0
        # 最後のイベントを確認（前のテストのイベントが残っている可能性がある）
        assert callback_events[-1].team_name == team_name
        assert callback_events[-1].agent_name == agent_name

    def test_multiple_agents_timeout(self):
        """複数エージェントのタイムアウトを個別に検知"""
        monitor = get_agent_health_monitor()

        team_name = "multi-timeout-team"

        # agent1: タイムアウト2秒
        monitor.register_agent(team_name, "agent1", 2.0)
        # agent2: タイムアウト5秒
        monitor.register_agent(team_name, "agent2", 5.0)

        # 3秒待機
        time.sleep(3)

        monitor._check_all_agents()
        status = monitor.get_health_status()

        # agent1 はタイムアウト
        assert status[team_name]["agent1"]["isHealthy"] is False
        # agent2 はまだ健全
        assert status[team_name]["agent2"]["isHealthy"] is True

        # さらに3秒待機（合計6秒）
        time.sleep(3)

        monitor._check_all_agents()
        status = monitor.get_health_status()

        # 両方ともタイムアウト
        assert status[team_name]["agent1"]["isHealthy"] is False
        assert status[team_name]["agent2"]["isHealthy"] is False
