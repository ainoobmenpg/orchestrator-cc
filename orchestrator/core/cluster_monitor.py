"""クラスタ監視モジュール

このモジュールでは、クラスタ全体の状態を監視するClusterMonitorクラスを定義します。

機能:
- エージェントの状態監視（実行中、アイドル、エラーなど）
- タスクの進捗監視
- リソース使用状況の監視
- アラート通知（異常検知時）
"""

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from contextlib import suppress
from dataclasses import dataclass, field
from enum import Enum

# ロガーの設定
logger = logging.getLogger(__name__)


class AgentHealthStatus(str, Enum):
    """エージェントのヘルス状態列挙型"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class AlertLevel(str, Enum):
    """アラートレベル列挙型"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AgentState:
    """エージェントの状態

    Attributes:
        name: エージェント名
        is_running: 実行中フラグ
        last_activity: 最終アクティビティ時刻（Unixタイムスタンプ）
        restart_count: 再起動回数
        health_status: ヘルス状態
        current_task_id: 現在処理中のタスクID
        error_message: エラーメッセージ（ある場合）
    """

    name: str
    is_running: bool
    last_activity: float
    restart_count: int
    health_status: AgentHealthStatus = AgentHealthStatus.HEALTHY
    current_task_id: str | None = None
    error_message: str | None = None


@dataclass
class ClusterMetrics:
    """クラスタのメトリクス

    Attributes:
        total_agents: エージェント総数
        running_agents: 実行中のエージェント数
        idle_agents: アイドル状態のエージェント数
        unhealthy_agents: 異常状態のエージェント数
        total_restarts: 総再起動回数
        timestamp: 計測時刻
    """

    total_agents: int
    running_agents: int
    idle_agents: int
    unhealthy_agents: int
    total_restarts: int
    timestamp: float = field(default_factory=time.time)


@dataclass
class Alert:
    """アラート情報

    Attributes:
        level: アラートレベル
        agent_name: 対象エージェント名
        message: アラートメッセージ
        timestamp: 発生時刻
        resolved: 解決済みフラグ
    """

    level: AlertLevel
    agent_name: str
    message: str
    timestamp: float = field(default_factory=time.time)
    resolved: bool = False


class ClusterMonitor:
    """クラスタ全体を監視するクラス

    エージェントの状態を定期的にチェックし、
    異常を検知した場合はアラートを通知します。

    Attributes:
        _cluster_manager: CCClusterManagerインスタンス
        _check_interval: 監視間隔（秒）
        _agent_timeout: エージェント応答タイムアウト（秒）
        _max_idle_time: 最大アイドル時間（秒、超過でdegraded判定）
        _monitoring: 監視中フラグ
        _monitor_task: 監視タスク
        _alerts: アラート履歴
        _alert_callback: アラート通知コールバック
    """

    def __init__(
        self,
        cluster_manager,  # CCClusterManager（循環インポート回避）
        check_interval: float = 5.0,
        agent_timeout: float = 60.0,
        max_idle_time: float = 300.0,
        alert_callback: Callable[[Alert], Awaitable[None] | None] | None = None,
    ) -> None:
        """ClusterMonitorを初期化します。

        Args:
            cluster_manager: CCClusterManagerインスタンス
            check_interval: 監視間隔（秒、デフォルト: 5.0）
            agent_timeout: エージェント応答タイムアウト（秒、デフォルト: 60.0）
            max_idle_time: 最大アイドル時間（秒、デフォルト: 300.0）
            alert_callback: アラート通知コールバック（オプション）
        """
        self._cluster_manager = cluster_manager
        self._check_interval = check_interval
        self._agent_timeout = agent_timeout
        self._max_idle_time = max_idle_time
        self._monitoring: bool = False
        self._monitor_task: asyncio.Task[None] | None = None
        self._alerts: list[Alert] = []
        self._alert_callback = alert_callback
        self._last_metrics: ClusterMetrics | None = None

    def start(self) -> None:
        """監視を開始します。"""
        if self._monitoring:
            logger.warning("監視は既に開始されています")
            return

        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info(f"クラスタ監視を開始しました（間隔: {self._check_interval}秒）")

    async def stop_async(self) -> None:
        """監視を停止します（非同期版）。"""
        if not self._monitoring:
            return

        self._monitoring = False
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._monitor_task

        self._monitor_task = None
        logger.info("クラスタ監視を停止しました")

    def stop(self) -> None:
        """監視を停止します。"""
        if not self._monitoring:
            return

        # イベントループが実行中かチェック
        try:
            loop = asyncio.get_running_loop()
            # 実行中の場合は非同期版の呼び出しをスケジュール
            loop.create_task(self.stop_async())
        except RuntimeError:
            # 実行中のループがない場合は同期的に実行
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.stop_async())
            loop.close()

    def is_running(self) -> bool:
        """監視が実行中か確認します。

        Returns:
            実行中の場合True、それ以外の場合False
        """
        return self._monitoring

    async def _monitor_loop(self) -> None:
        """監視ループ"""
        try:
            while self._monitoring:
                await self._check_cluster_health()
                await asyncio.sleep(self._check_interval)
        except asyncio.CancelledError:
            logger.debug("監視ループがキャンセルされました")
            raise
        except Exception as e:
            logger.error(f"監視ループでエラーが発生: {e}")
            raise

    async def _check_cluster_health(self) -> None:
        """クラスタのヘルスチェックを実行します。"""
        try:
            # ステータスを取得
            status = self._cluster_manager.get_status()
            current_time = time.time()

            # メトリクスを計算
            total_agents = len(status["agents"])
            running_agents = sum(1 for a in status["agents"] if a["running"])
            idle_agents = 0
            unhealthy_agents = 0
            total_restarts = sum(a["restart_count"] for a in status["agents"])

            # 各エージェントの状態をチェック
            for agent_status in status["agents"]:
                agent_name = agent_status["name"]
                is_running = agent_status["running"]
                last_activity = agent_status["last_activity"]
                restart_count = agent_status["restart_count"]

                # アイドル判定（最終アクティビティからの経過時間）
                if is_running and last_activity > 0:
                    idle_time = current_time - last_activity
                    if idle_time > self._max_idle_time:
                        idle_agents += 1
                        await self._create_alert(
                            AlertLevel.WARNING,
                            agent_name,
                            f"エージェントが長時間アイドル状態です（{idle_time:.0f}秒）",
                        )

                # 異常判定
                if not is_running:
                    unhealthy_agents += 1
                    await self._create_alert(
                        AlertLevel.ERROR,
                        agent_name,
                        "エージェントが実行されていません",
                    )
                elif restart_count > 3:
                    unhealthy_agents += 1
                    await self._create_alert(
                        AlertLevel.WARNING,
                        agent_name,
                        f"再起動回数が多いです（{restart_count}回）",
                    )

            # メトリクスを更新
            self._last_metrics = ClusterMetrics(
                total_agents=total_agents,
                running_agents=running_agents,
                idle_agents=idle_agents,
                unhealthy_agents=unhealthy_agents,
                total_restarts=total_restarts,
            )

        except Exception as e:
            logger.error(f"ヘルスチェックでエラーが発生: {e}")

    async def _create_alert(
        self, level: AlertLevel, agent_name: str, message: str
    ) -> None:
        """アラートを作成して通知します。

        Args:
            level: アラートレベル
            agent_name: 対象エージェント名
            message: アラートメッセージ
        """
        alert = Alert(level=level, agent_name=agent_name, message=message)
        self._alerts.append(alert)

        # コールバックがあれば実行
        if self._alert_callback:
            try:
                result = self._alert_callback(alert)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"アラートコールバックでエラーが発生: {e}")

        logger.warning(f"[{level.value.upper()}] {agent_name}: {message}")

    def get_metrics(self) -> ClusterMetrics | None:
        """現在のメトリクスを取得します。

        Returns:
            現在のメトリクス（監視未実行の場合はNone）
        """
        return self._last_metrics

    def get_alerts(
        self,
        level: AlertLevel | None = None,
        resolved: bool | None = None,
        limit: int = 100,
    ) -> list[Alert]:
        """アラート履歴を取得します。

        Args:
            level: アラートレベルでフィルタ（オプション）
            resolved: 解決状況でフィルタ（オプション）
            limit: 最大取得件数

        Returns:
            アラートのリスト
        """
        alerts = self._alerts

        if level is not None:
            alerts = [a for a in alerts if a.level == level]
        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]

        # 新しい順にソートして返す
        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)[:limit]

    def resolve_alert(self, alert_index: int) -> None:
        """アラートを解決済みにマークします。

        Args:
            alert_index: アラートのインデックス（get_alerts()で取得したリストのインデックス）
        """
        alerts = self.get_alerts(resolved=False)
        if 0 <= alert_index < len(alerts):
            alerts[alert_index].resolved = True
            logger.info(f"アラートを解決済みにマークしました: {alerts[alert_index].message}")

    def clear_alerts(self) -> None:
        """全てのアラートをクリアします。"""
        self._alerts.clear()
        logger.info("全てのアラートをクリアしました")

    async def check_now(self) -> ClusterMetrics:
        """即座にヘルスチェックを実行します。

        Returns:
            現在のメトリクス
        """
        await self._check_cluster_health()
        if self._last_metrics is None:
            raise RuntimeError("メトリクスの取得に失敗しました")
        return self._last_metrics

    def get_status_summary(self) -> dict:
        """監視ステータスのサマリーを取得します。

        Returns:
            ステータスサマリー
        """
        return {
            "monitoring": self._monitoring,
            "check_interval": self._check_interval,
            "agent_timeout": self._agent_timeout,
            "max_idle_time": self._max_idle_time,
            "total_alerts": len(self._alerts),
            "unresolved_alerts": len([a for a in self._alerts if not a.resolved]),
            "last_metrics": (
                {
                    "total_agents": self._last_metrics.total_agents,
                    "running_agents": self._last_metrics.running_agents,
                    "idle_agents": self._last_metrics.idle_agents,
                    "unhealthy_agents": self._last_metrics.unhealthy_agents,
                    "total_restarts": self._last_metrics.total_restarts,
                }
                if self._last_metrics
                else None
            ),
        }
