"""エージェントヘルスモニターモジュール

このモジュールでは、Agent Teamsのヘルス監視と自動再起動機能を提供します。
"""

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AgentHealthStatus:
    """エージェントのヘルス状態

    Attributes:
        team_name: チーム名
        agent_name: エージェント名
        last_activity: 最終アクティビティ時刻
        is_healthy: ヘルス状態
        timeout_threshold: タイムアウトしきい値（秒）
    """

    team_name: str
    agent_name: str
    last_activity: datetime
    is_healthy: bool = True
    timeout_threshold: float = 300.0  # デフォルト5分

    def check_health(self) -> bool:
        """ヘルスチェックを実行します。

        Returns:
            ヘルチならTrue
        """
        elapsed = (datetime.now() - self.last_activity).total_seconds()
        return elapsed < self.timeout_threshold


@dataclass
class HealthCheckEvent:
    """ヘルスチェックイベント

    Attributes:
        event_type: イベントタイプ（timeout_detected, agent_restarted, etc）
        team_name: チーム名
        agent_name: エージェント名
        timestamp: タイムスタンプ
        details: 詳細情報
    """

    event_type: str
    team_name: str
    agent_name: str
    timestamp: datetime
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """辞書に変換します。"""
        return {
            "eventType": self.event_type,
            "teamName": self.team_name,
            "agentName": self.agent_name,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
        }


class AgentHealthMonitor:
    """エージェントヘルスモニター

    Agent Teamsのエージェントのヘルスを監視し、
    タイムアウトを検知して自動再起動を試みます。

    Attributes:
        _health_status: チーム・エージェントごとのヘルス状態
        _callbacks: イベントコールバックのリスト
        _monitoring_active: 監視中フラグ
        _check_interval: チェック間隔（秒）
        _thread: 監視スレッド
    """

    def __init__(self, check_interval: float = 30.0):
        """AgentHealthMonitorを初期化します。

        Args:
            check_interval: ヘルスチェック間隔（秒）
        """
        self._health_status: dict[str, dict[str, AgentHealthStatus]] = {}
        self._callbacks: list[Callable[[HealthCheckEvent], None]] = []
        self._monitoring_active = False
        self._check_interval = check_interval
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def register_callback(self, callback: Callable[[HealthCheckEvent], None]) -> None:
        """イベントコールバックを登録します。

        Args:
            callback: コールバック関数
        """
        with self._lock:
            self._callbacks.append(callback)

    def register_agent(
        self,
        team_name: str,
        agent_name: str,
        timeout_threshold: float = 300.0,
    ) -> None:
        """エージェントを監視対象に登録します。

        Args:
            team_name: チーム名
            agent_name: エージェント名
            timeout_threshold: タイムアウトしきい値（秒）
        """
        with self._lock:
            if team_name not in self._health_status:
                self._health_status[team_name] = {}

            self._health_status[team_name][agent_name] = AgentHealthStatus(
                team_name=team_name,
                agent_name=agent_name,
                last_activity=datetime.now(),
                timeout_threshold=timeout_threshold,
            )

            logger.info(
                f"Agent registered for health monitoring: "
                f"{team_name}/{agent_name} (timeout: {timeout_threshold}s)"
            )

    def update_activity(self, team_name: str, agent_name: str) -> None:
        """エージェントのアクティビティを更新します。

        Args:
            team_name: チーム名
            agent_name: エージェント名
        """
        with self._lock:
            if team_name in self._health_status and agent_name in self._health_status[team_name]:
                self._health_status[team_name][agent_name].last_activity = datetime.now()

    def start_monitoring(self) -> None:
        """監視を開始します。"""
        if self._monitoring_active:
            logger.warning("Health monitoring is already active")
            return

        self._monitoring_active = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("Agent health monitoring started")

    def stop_monitoring(self) -> None:
        """監視を停止します。"""
        self._monitoring_active = False

        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None

        logger.info("Agent health monitoring stopped")

    def is_running(self) -> bool:
        """監視中かどうかを返します。

        Returns:
            監視中ならTrue
        """
        return self._monitoring_active

    def get_health_status(self) -> dict[str, Any]:
        """現在のヘルス状態を取得します。

        Returns:
            ヘルス状態の辞書
        """
        with self._lock:
            status: dict[str, Any] = {}

            for team_name, agents in self._health_status.items():
                status[team_name] = {}

                for agent_name, health in agents.items():
                    is_healthy = health.check_health()
                    status[team_name][agent_name] = {
                        "isHealthy": is_healthy,
                        "lastActivity": health.last_activity.isoformat(),
                        "timeoutThreshold": health.timeout_threshold,
                        "elapsed": (datetime.now() - health.last_activity).total_seconds(),
                    }

            return status

    def _monitor_loop(self) -> None:
        """監視ループ"""
        while self._monitoring_active:
            try:
                self._check_all_agents()
            except Exception as e:
                logger.error(f"Health check error: {e}")

            time.sleep(self._check_interval)

    def _check_all_agents(self) -> None:
        """全エージェントのヘルスチェックを実行します。"""
        with self._lock:
            for team_name, agents in self._health_status.items():
                for agent_name, health in agents.items():
                    is_healthy = health.check_health()

                    if not is_healthy and health.is_healthy:
                        # タイムアウト検知
                        health.is_healthy = False

                        event = HealthCheckEvent(
                            event_type="timeout_detected",
                            team_name=team_name,
                            agent_name=agent_name,
                            timestamp=datetime.now(),
                            details={
                                "lastActivity": health.last_activity.isoformat(),
                                "elapsed": (datetime.now() - health.last_activity).total_seconds(),
                            },
                        )

                        self._emit_event(event)
                        logger.warning(
                            f"Agent timeout detected: {team_name}/{agent_name} "
                            f"(inactive for {(datetime.now() - health.last_activity).total_seconds():.0f}s)"
                        )

    def _emit_event(self, event: HealthCheckEvent) -> None:
        """イベントを発行します。

        Args:
            event: ヘルスチェックイベント
        """
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Health check event callback error: {e}")


# シングルトンインスタンス
_health_monitor: AgentHealthMonitor | None = None
_monitor_lock = threading.Lock()


def get_agent_health_monitor() -> AgentHealthMonitor:
    """エージェントヘルスモニターのシングルトンインスタンスを取得します。

    Returns:
        AgentHealthMonitorインスタンス
    """
    global _health_monitor

    with _monitor_lock:
        if _health_monitor is None:
            _health_monitor = AgentHealthMonitor()
        return _health_monitor
