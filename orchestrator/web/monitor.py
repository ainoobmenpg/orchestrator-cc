"""ダッシュボード監視統合モジュール

このモジュールでは、ClusterMonitorとダッシュボードの統合機能を提供します。

機能:
- ClusterMonitorのラッパー
- 定期ポーリングとイベント検知
- WebSocket接続への状態配信
- メトリクスのキャッシュ
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


class UpdateType(str, Enum):
    """更新タイプ列挙型"""

    METRICS = "metrics"
    ALERT = "alert"
    STATUS = "status"
    AGENT = "agent"


@dataclass
class MonitorUpdate:
    """監視更新データ

    Attributes:
        type: 更新タイプ
        data: 更新データ
        timestamp: タイムスタンプ
    """

    type: UpdateType
    data: dict
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        """辞書に変換します。

        Returns:
            辞書形式の更新データ
        """
        return {
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp,
        }


class DashboardMonitor:
    """ダッシュボード用監視クラス

    ClusterMonitorをラップし、ダッシュボード向けの機能を提供します。

    Attributes:
        _cluster_monitor: ClusterMonitorインスタンス
        _update_callbacks: 更新通知コールバックのリスト
        _broadcast_interval: ブロードキャスト間隔（秒）
        _monitoring: 監視中フラグ
        _monitor_task: 監視タスク
        _last_update_time: 最終更新時刻
    """

    def __init__(
        self,
        cluster_monitor,  # ClusterMonitor（循環インポート回避）
        broadcast_interval: float = 1.0,
    ) -> None:
        """DashboardMonitorを初期化します。

        Args:
            cluster_monitor: ClusterMonitorインスタンス
            broadcast_interval: ブロードキャスト間隔（秒、デフォルト: 1.0）
        """
        self._cluster_monitor = cluster_monitor
        self._broadcast_interval = broadcast_interval
        self._update_callbacks: list[Callable[[MonitorUpdate], Awaitable[None] | None]] = []
        self._monitoring: bool = False
        self._monitor_task: asyncio.Task[None] | None = None
        self._last_update_time: float = 0.0
        self._last_alert_count: int = 0

    def register_callback(
        self,
        callback: Callable[[MonitorUpdate], Awaitable[None] | None],
    ) -> None:
        """更新通知コールバックを登録します。

        Args:
            callback: 更新時に呼ばれるコールバック関数
        """
        if callback not in self._update_callbacks:
            self._update_callbacks.append(callback)
            logger.debug(f"コールバックを登録しました: {callback}")

    def unregister_callback(
        self,
        callback: Callable[[MonitorUpdate], Awaitable[None] | None],
    ) -> None:
        """更新通知コールバックを解除します。

        Args:
            callback: 解除するコールバック関数
        """
        if callback in self._update_callbacks:
            self._update_callbacks.remove(callback)
            logger.debug(f"コールバックを解除しました: {callback}")

    async def start_monitoring(self) -> None:
        """監視を開始します。"""
        if self._monitoring:
            logger.warning("監視は既に開始されています")
            return

        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("ダッシュボード監視を開始しました")

    async def stop_monitoring(self) -> None:
        """監視を停止します。"""
        if not self._monitoring:
            return

        self._monitoring = False
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._monitor_task

        self._monitor_task = None
        logger.info("ダッシュボード監視を停止しました")

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
                await self._check_and_broadcast()
                await asyncio.sleep(self._broadcast_interval)
        except asyncio.CancelledError:
            logger.debug("監視ループがキャンセルされました")
            raise
        except Exception as e:
            logger.error(f"監視ループでエラーが発生: {e}")
            raise

    async def _check_and_broadcast(self) -> None:
        """変更をチェックしてブロードキャストします。"""
        try:
            # メトリクス更新をチェック
            metrics = self._cluster_monitor.get_metrics()
            if metrics:
                # メトリクス更新をブロードキャスト
                await self._broadcast_update(
                    MonitorUpdate(
                        type=UpdateType.METRICS,
                        data={
                            "total_agents": metrics.total_agents,
                            "running_agents": metrics.running_agents,
                            "idle_agents": metrics.idle_agents,
                            "unhealthy_agents": metrics.unhealthy_agents,
                            "total_restarts": metrics.total_restarts,
                        },
                    )
                )

            # 新しいアラートをチェック
            current_alert_count = len(self._cluster_monitor.get_alerts())
            if current_alert_count > self._last_alert_count:
                new_alerts = self._cluster_monitor.get_alerts()[:current_alert_count - self._last_alert_count]
                for alert in new_alerts:
                    await self._broadcast_update(
                        MonitorUpdate(
                            type=UpdateType.ALERT,
                            data={
                                "level": alert.level.value,
                                "agent_name": alert.agent_name,
                                "message": alert.message,
                                "resolved": alert.resolved,
                            },
                        )
                    )
                self._last_alert_count = current_alert_count

        except Exception as e:
            logger.error(f"ブロードキャストでエラーが発生: {e}")

    async def _broadcast_update(self, update: MonitorUpdate) -> None:
        """登録された全てのコールバックを呼び出します。

        Args:
            update: 更新データ
        """
        for callback in self._update_callbacks:
            try:
                result = callback(update)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"コールバック実行でエラーが発生: {e}")

    async def broadcast_now(self, update: MonitorUpdate) -> None:
        """即座に更新をブロードキャストします。

        Args:
            update: ブロードキャストする更新データ
        """
        await self._broadcast_update(update)

    def get_cluster_status(self) -> dict:
        """クラスタのステータスを取得します。

        Returns:
            クラスタステータスの辞書
        """
        return self._cluster_monitor.get_status_summary()

    def get_metrics(self) -> dict | None:
        """現在のメトリクスを取得します。

        Returns:
            メトリクスの辞書（監視未実行の場合はNone）
        """
        metrics = self._cluster_monitor.get_metrics()
        if metrics is None:
            return None
        return {
            "total_agents": metrics.total_agents,
            "running_agents": metrics.running_agents,
            "idle_agents": metrics.idle_agents,
            "unhealthy_agents": metrics.unhealthy_agents,
            "total_restarts": metrics.total_restarts,
            "timestamp": metrics.timestamp,
        }

    def get_alerts(
        self,
        level: str | None = None,
        resolved: bool | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """アラート履歴を取得します。

        Args:
            level: アラートレベルでフィルタ（オプション）
            resolved: 解決状況でフィルタ（オプション）
            limit: 最大取得件数

        Returns:
            アラートのリスト（辞書形式）
        """
        from orchestrator.core.cluster_monitor import AlertLevel

        alert_level = AlertLevel(level) if level else None
        alerts = self._cluster_monitor.get_alerts(alert_level, resolved, limit)

        return [
            {
                "level": alert.level.value,
                "agent_name": alert.agent_name,
                "message": alert.message,
                "timestamp": alert.timestamp,
                "resolved": alert.resolved,
            }
            for alert in alerts
        ]

    def resolve_alert(self, alert_index: int) -> None:
        """アラートを解決済みにマークします。

        Args:
            alert_index: アラートのインデックス
        """
        self._cluster_monitor.resolve_alert(alert_index)

    def clear_alerts(self) -> None:
        """全てのアラートをクリアします。"""
        self._cluster_manager.clear_alerts()
