"""Webダッシュボード FastAPIアプリケーション

このモジュールでは、FastAPIベースのダッシュボードバックエンドを提供します。

機能:
- REST APIエンドポイント
- WebSocketエンドポイント
- ClusterMonitor統合
- リアルタイム状態配信
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from orchestrator.core.cc_cluster_manager import (
    CCClusterConfigError,
    CCClusterManager,
)
from orchestrator.core.cluster_monitor import ClusterMonitor
from orchestrator.web.message_handler import WebSocketManager, WebSocketMessageHandler
from orchestrator.web.monitor import DashboardMonitor, MonitorUpdate
from orchestrator.web.teams_monitor import TeamsMonitor
from orchestrator.web.thinking_log_handler import ThinkingLogHandler, get_thinking_log_handler
from orchestrator.core.agent_teams_manager import AgentTeamsManager, TeamConfig, get_agent_teams_manager
from orchestrator.core.agent_health_monitor import AgentHealthMonitor, get_agent_health_monitor

# ロガーの設定
logger = logging.getLogger(__name__)

# グローバルインスタンス
_cluster_manager: CCClusterManager | None = None
_cluster_monitor: ClusterMonitor | None = None
_dashboard_monitor: DashboardMonitor | None = None
_ws_manager: WebSocketManager | None = None
_ws_handler: WebSocketMessageHandler | None = None
_teams_monitor: TeamsMonitor | None = None
_thinking_log_handler: ThinkingLogHandler | None = None
_teams_manager: AgentTeamsManager | None = None
_health_monitor: AgentHealthMonitor | None = None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """アプリケーションのライフサイクル管理

    アプリケーション起動時と終了時の処理を定義します。
    """
    global _cluster_manager, _cluster_monitor, _dashboard_monitor, _ws_manager, _ws_handler, _teams_monitor, _thinking_log_handler

    # 起動時
    logger.info("FastAPIアプリケーションを起動します")

    # WebSocketマネージャーを初期化
    _ws_manager = WebSocketManager()
    _ws_handler = WebSocketMessageHandler(_ws_manager)

    # ステータスハンドラーを設定
    _ws_handler.set_status_handler(
        lambda data, ws: _handle_get_status(data, ws)
    )

    # TeamsMonitorを初期化
    _teams_monitor = TeamsMonitor()
    _teams_monitor.register_update_callback(_broadcast_teams_update)
    _teams_monitor.start_monitoring()
    logger.info("Teams monitoring started")

    # ThinkingLogHandlerを初期化
    _thinking_log_handler = get_thinking_log_handler()
    _thinking_log_handler.register_callback(_broadcast_thinking_log)
    _thinking_log_handler.start_monitoring()
    logger.info("Thinking log monitoring started")

    # AgentTeamsManagerを初期化
    _teams_manager = get_agent_teams_manager()
    logger.info("AgentTeamsManager initialized")

    # AgentHealthMonitorを初期化
    _health_monitor = get_agent_health_monitor()
    _health_monitor.register_callback(_on_health_event)
    _health_monitor.start_monitoring()
    logger.info("AgentHealthMonitor started")

    yield

    # 終了時
    logger.info("FastAPIアプリケーションを停止します")

    # ダッシュボード監視を停止
    if _dashboard_monitor and _dashboard_monitor.is_running():
        await _dashboard_monitor.stop_monitoring()

    # Teams監視を停止
    if _teams_monitor and _teams_monitor.is_running():
        _teams_monitor.stop_monitoring()

    # 思考ログ監視を停止
    if _thinking_log_handler and _thinking_log_handler.is_running():
        _thinking_log_handler.stop_monitoring()

    # ヘルスモニターを停止
    if _health_monitor and _health_monitor.is_running():
        _health_monitor.stop_monitoring()

    # 全てのWebSocket接続を閉じる
    if _ws_manager:
        await _ws_manager.close_all()


# FastAPIアプリケーションを作成
app = FastAPI(
    title="Orchestrator CC Dashboard",
    description="クラスタ管理用Webダッシュボード",
    version="0.1.0",
    lifespan=lifespan,
)

# CORSミドルウェアを設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 開発環境では全許可、本番では制限すること
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静的ファイルを配信
_static_dir = Path(__file__).parent / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


def initialize(
    config_path: str = "config/cc-cluster.yaml",
) -> None:
    """ダッシュボードを初期化します。

    Args:
        config_path: クラスタ設定ファイルのパス（デフォルト: config/cc-cluster.yaml）
    """
    global _cluster_manager, _cluster_monitor, _dashboard_monitor

    # クラスタマネージャーを初期化
    _cluster_manager = CCClusterManager(config_path)

    # 既存のクラスタに接続（自動再起動は無効化）
    try:
        _cluster_manager.connect(auto_restart=False)
        logger.info("既存のクラスタに接続しました")
    except CCClusterConfigError as e:
        logger.warning(f"既存のクラスタへの接続に失敗しました: {e}")
        # 接続失敗しても続行（ダッシュボード単体で動作可能）

    # クラスタ監視を初期化
    _cluster_monitor = ClusterMonitor(_cluster_manager)

    # ダッシュボード監視を初期化
    _dashboard_monitor = DashboardMonitor(_cluster_monitor)

    # コールバックを登録（WebSocketブロードキャスト）
    _dashboard_monitor.register_callback(_broadcast_to_websockets)


async def _broadcast_to_websockets(update: MonitorUpdate) -> None:
    """MonitorUpdateをWebSocket接続にブロードキャストします。

    Args:
        update: 監視更新データ
    """
    if _ws_manager:
        await _ws_manager.broadcast(update.to_dict())


def _broadcast_teams_update(data: dict) -> None:
    """TeamsMonitorの更新をWebSocketにブロードキャストします。

    Args:
        data: 更新データ
    """
    if _ws_manager:
        # 非同期でブロードキャスト
        import asyncio
        try:
            asyncio.get_running_loop()
            asyncio.create_task(_ws_manager.broadcast(data))
        except RuntimeError:
            # イベントループが実行中でない場合は無視
            pass


def _broadcast_thinking_log(data: dict) -> None:
    """思考ログの更新をWebSocketにブロードキャストします。

    Args:
        data: 更新データ
    """
    if _ws_manager:
        # 非同期でブロードキャスト
        import asyncio
        try:
            asyncio.get_running_loop()
            asyncio.create_task(_ws_manager.broadcast(data))
        except RuntimeError:
            # イベントループが実行中でない場合は無視
            pass


async def _handle_get_status(_data: dict, websocket: WebSocket) -> None:
    """ステータス取得リクエストを処理します。

    Args:
        _data: リクエストデータ（未使用）
        websocket: WebSocket接続
    """
    if _dashboard_monitor:
        await _ws_manager.send_personal(
            {
                "type": "status",
                "data": _dashboard_monitor.get_cluster_status(),
            },
            websocket
        )


# ============================================================================
# REST APIエンドポイント
# ============================================================================

# テンプレートディレクトリのパス
_templates_dir = Path(__file__).parent / "templates"
_static_dir = Path(__file__).parent / "static"


@app.get("/")
async def root():
    """ダッシュボードHTMLを返します"""
    index_path = _templates_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {
        "message": "Orchestrator CC Dashboard API",
        "version": "0.1.0",
        "endpoints": {
            "status": "/api/status",
            "metrics": "/api/metrics",
            "alerts": "/api/alerts",
            "agents": "/api/agents",
            "websocket": "/ws",
        },
    }


@app.get("/api")
async def api_info():
    """API情報を返します"""
    return {
        "message": "Orchestrator CC Dashboard API",
        "version": "0.1.0",
        "endpoints": {
            "status": "/api/status",
            "metrics": "/api/metrics",
            "alerts": "/api/alerts",
            "agents": "/api/agents",
            "websocket": "/ws",
        },
    }


@app.get("/api/status")
async def get_status():
    """クラスタの状態を取得します。

    Returns:
        クラスタステータスの辞書
    """
    if _dashboard_monitor is None:
        return {"error": "Dashboard not initialized"}

    return _dashboard_monitor.get_cluster_status()


@app.get("/api/metrics")
async def get_metrics():
    """現在のメトリクスを取得します。

    Returns:
        メトリクスの辞書（監視未実行の場合はnull）
    """
    if _dashboard_monitor is None:
        return {"error": "Dashboard not initialized"}

    metrics = _dashboard_monitor.get_metrics()
    if metrics is None:
        return {"metrics": None}

    return {"metrics": metrics}


@app.get("/api/alerts")
async def get_alerts(
    level: str | None = Query(None, description="アラートレベルでフィルタ"),
    resolved: bool | None = Query(None, description="解決状況でフィルタ"),
    limit: int = Query(100, description="最大取得件数", ge=1, le=1000),
):
    """アラート履歴を取得します。

    Args:
        level: アラートレベルでフィルタ（オプション）
        resolved: 解決状況でフィルタ（オプション）
        limit: 最大取得件数（デフォルト: 100）

    Returns:
        アラートのリスト
    """
    if _dashboard_monitor is None:
        return {"error": "Dashboard not initialized"}

    alerts = _dashboard_monitor.get_alerts(level, resolved, limit)
    return {"alerts": alerts}


@app.post("/api/alerts/{alert_index}/resolve")
async def resolve_alert(alert_index: int):
    """アラートを解決済みにマークします。

    Args:
        alert_index: アラートのインデックス

    Returns:
        成功メッセージ
    """
    if _dashboard_monitor is None:
        return {"error": "Dashboard not initialized"}

    try:
        _dashboard_monitor.resolve_alert(alert_index)
        return {"message": f"Alert {alert_index} resolved"}
    except Exception as e:
        return {"error": str(e)}


@app.delete("/api/alerts")
async def clear_alerts():
    """全てのアラートをクリアします。

    Returns:
        成功メッセージ
    """
    if _dashboard_monitor is None:
        return {"error": "Dashboard not initialized"}

    try:
        _dashboard_monitor.clear_alerts()
        return {"message": "All alerts cleared"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/agents")
async def get_agents():
    """エージェント一覧を取得します。

    Returns:
        エージェント情報のリスト
    """
    if _cluster_manager is None:
        return {"error": "Cluster manager not initialized"}

    status = _cluster_manager.get_status()
    return {"agents": status["agents"]}


@app.post("/api/monitoring/start")
async def start_monitoring():
    """監視を開始します。

    Returns:
        成功メッセージ
    """
    if _dashboard_monitor is None:
        return {"error": "Dashboard not initialized"}

    if _dashboard_monitor.is_running():
        return {"message": "Monitoring already running"}

    await _dashboard_monitor.start_monitoring()
    return {"message": "Monitoring started"}


@app.post("/api/monitoring/stop")
async def stop_monitoring():
    """監視を停止します。

    Returns:
        成功メッセージ
    """
    if _dashboard_monitor is None:
        return {"error": "Dashboard not initialized"}

    if not _dashboard_monitor.is_running():
        return {"message": "Monitoring not running"}

    await _dashboard_monitor.stop_monitoring()
    return {"message": "Monitoring stopped"}


@app.post("/api/cluster/restart")
async def restart_cluster():
    """クラスタを再起動します。

    全エージェントを停止した後、再度起動します。

    Returns:
        成功メッセージまたはエラーメッセージ
    """
    if _cluster_manager is None:
        return {"error": "Cluster manager not initialized"}

    try:
        # システムログを配信
        if _ws_manager:
            await _ws_manager.broadcast({
                "type": "cluster_event",
                "event": "cluster_restart_start",
            })

        # 監視を一時停止
        monitoring_was_running = (
            _dashboard_monitor is not None and _dashboard_monitor.is_running()
        )
        if monitoring_was_running:
            await _dashboard_monitor.stop_monitoring()

        # クラスタを再起動
        await _cluster_manager.restart()

        # 監視を再開
        if monitoring_was_running and _dashboard_monitor:
            await _dashboard_monitor.start_monitoring()

        # システムログを配信（成功）
        if _ws_manager:
            await _ws_manager.broadcast({
                "type": "cluster_event",
                "event": "cluster_restart_complete",
            })

        return {"message": "Cluster restarted successfully"}
    except Exception as e:
        logger.error(f"Cluster restart error: {e}")
        # システムログを配信（失敗）
        if _ws_manager:
            await _ws_manager.broadcast({
                "type": "cluster_event",
                "event": "cluster_restart_failed",
                "data": {"error": str(e)},
            })
        return {"error": f"Failed to restart cluster: {str(e)}"}


@app.post("/api/cluster/shutdown")
async def shutdown_cluster():
    """クラスタをシャットダウンします。

    全エージェントを停止し、tmuxセッションを削除します。

    Returns:
        成功メッセージまたはエラーメッセージ
    """
    if _cluster_manager is None:
        return {"error": "Cluster manager not initialized"}

    try:
        # システムログを配信
        if _ws_manager:
            await _ws_manager.broadcast({
                "type": "cluster_event",
                "event": "cluster_stop",
            })

        # 監視を停止
        if _dashboard_monitor is not None and _dashboard_monitor.is_running():
            await _dashboard_monitor.stop_monitoring()

        # クラスタをシャットダウン
        await _cluster_manager.shutdown()

        return {"message": "Cluster shut down successfully"}
    except Exception as e:
        logger.error(f"Cluster shutdown error: {e}")
        return {"error": f"Failed to shutdown cluster: {str(e)}"}


# ============================================================================
# WebSocketエンドポイント
# ============================================================================


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    _token: str | None = Query(None, description="認証トークン（オプション）"),
):
    """WebSocketエンドポイント

    クライアントからの接続を受け入れ、リアルタイム更新を配信します。

    Args:
        websocket: WebSocket接続オブジェクト
        _token: 認証トークン（将来的な実装用）
    """
    if _ws_manager is None or _ws_handler is None:
        await websocket.close(code=1011, reason="Server not initialized")
        return

    await _ws_manager.connect(websocket)

    try:
        # 接続確立メッセージを送信
        await _ws_manager.send_personal(
            {
                "type": "connected",
                "message": "Connected to Orchestrator CC Dashboard",
            },
            websocket
        )

        # 初期システムログを送信
        await _ws_manager.send_personal(
            {
                "type": "system_log",
                "timestamp": None,
                "level": "info",
                "content": "ダッシュボードに接続しました",
            },
            websocket
        )

        # クラスタ状態をログに追加
        if _cluster_manager:
            status = _cluster_manager.get_status()
            running_agents = sum(1 for a in status.get("agents", []) if a.get("running"))
            await _ws_manager.send_personal(
                {
                    "type": "system_log",
                    "timestamp": None,
                    "level": "info",
                    "content": f"クラスタ状態: {status.get('cluster_name', 'unknown')} (エージェント: {running_agents}/{len(status.get('agents', []))} 実行中)",
                },
                websocket
            )

        # メッセージ受信ループ
        while True:
            message = await websocket.receive_text()
            await _ws_handler.handle_message(message, websocket)

    except WebSocketDisconnect:
        _ws_manager.disconnect(websocket)
        logger.info(f"WebSocket接続が切断されました: {websocket.client}")
    except Exception as e:
        logger.error(f"WebSocketエラーが発生: {e}")
        _ws_manager.disconnect(websocket)


# ============================================================================
# Agent Teams APIエンドポイント
# ============================================================================


@app.get("/api/teams")
async def get_teams():
    """チーム一覧を取得します。

    Returns:
        チーム情報のリスト
    """
    if _teams_monitor is None:
        return {"error": "Teams monitor not initialized"}

    return {"teams": _teams_monitor.get_teams()}


@app.get("/api/teams/{team_name}/messages")
async def get_team_messages(team_name: str):
    """チームのメッセージ履歴を取得します。

    Args:
        team_name: チーム名

    Returns:
        メッセージのリスト
    """
    if _teams_monitor is None:
        return {"error": "Teams monitor not initialized"}

    return {
        "teamName": team_name,
        "messages": _teams_monitor.get_team_messages(team_name)
    }


@app.get("/api/teams/{team_name}/tasks")
async def get_team_tasks(team_name: str):
    """チームのタスクリストを取得します。

    Args:
        team_name: チーム名

    Returns:
        タスクのリスト
    """
    if _teams_monitor is None:
        return {"error": "Teams monitor not initialized"}

    return {
        "teamName": team_name,
        "tasks": _teams_monitor.get_team_tasks(team_name)
    }


def _on_health_event(event) -> None:
    """ヘルスチェックイベントを処理します。

    Args:
        event: ヘルスチェックイベント
    """
    if _ws_manager:
        # 非同期でブロードキャスト
        import asyncio
        try:
            asyncio.get_running_loop()
            asyncio.create_task(_ws_manager.broadcast({
                "type": "health_event",
                "event": event.to_dict(),
            }))
        except RuntimeError:
            pass


# ============================================================================
# Agent Teams Management APIエンドポイント
# ============================================================================


@app.get("/api/teams/{team_name}/status")
async def get_team_status(team_name: str):
    """チームの状態を取得します。

    Args:
        team_name: チーム名

    Returns:
        チーム状態
    """
    if _teams_manager is None:
        return {"error": "Teams manager not initialized"}

    return _teams_manager.get_team_status(team_name)


@app.post("/api/teams/{team_name}/activity")
async def update_agent_activity(team_name: str, agent_name: str):
    """エージェントのアクティビティを更新します。

    Args:
        team_name: チーム名
        agent_name: エージェント名

    Returns:
        成功メッセージ
    """
    if _teams_manager is None:
        return {"error": "Teams manager not initialized"}

    _teams_manager.update_agent_activity(team_name, agent_name)
    return {"message": "Activity updated"}


@app.get("/api/health")
async def get_health_status():
    """ヘルスモニターの状態を取得します。

    Returns:
        ヘルス状態
    """
    if _health_monitor is None:
        return {"error": "Health monitor not initialized"}

    return _health_monitor.get_health_status()


@app.post("/api/health/start")
async def start_health_monitoring():
    """ヘルスモニタリングを開始します。

    Returns:
        成功メッセージ
    """
    if _health_monitor is None:
        return {"error": "Health monitor not initialized"}

    if _health_monitor.is_running():
        return {"message": "Health monitoring already running"}

    _health_monitor.start_monitoring()
    return {"message": "Health monitoring started"}


@app.post("/api/health/stop")
async def stop_health_monitoring():
    """ヘルスモニタリングを停止します。

    Returns:
        成功メッセージ
    """
    if _health_monitor is None:
        return {"error": "Health monitor not initialized"}

    if not _health_monitor.is_running():
        return {"message": "Health monitoring not running"}

    _health_monitor.stop_monitoring()
    return {"message": "Health monitoring stopped"}


# ============================================================================
# 既存のAgent Teams APIエンドポイント
# ============================================================================


@app.get("/api/teams/{team_name}/thinking")
async def get_team_thinking(team_name: str, agent: str | None = None):
    """チームの思考ログを取得します。

    Args:
        team_name: チーム名
        agent: エージェント名でフィルタ（オプション）

    Returns:
        思考ログのリスト
    """
    if _thinking_log_handler is None:
        return {"error": "Thinking log handler not initialized"}

    logs = _thinking_log_handler.get_logs(team_name)

    if agent:
        logs = [log for log in logs if log.get("agentName") == agent]

    return {
        "teamName": team_name,
        "agent": agent,
        "thinking": logs
    }


@app.post("/api/teams/monitoring/start")
async def start_teams_monitoring():
    """Teams監視を開始します。

    Returns:
        成功メッセージ
    """
    if _teams_monitor is None:
        return {"error": "Teams monitor not initialized"}

    if _teams_monitor.is_running():
        return {"message": "Teams monitoring already running"}

    _teams_monitor.start_monitoring()
    return {"message": "Teams monitoring started"}


@app.post("/api/teams/monitoring/stop")
async def stop_teams_monitoring():
    """Teams監視を停止します。

    Returns:
        成功メッセージ
    """
    if _teams_monitor is None:
        return {"error": "Teams monitor not initialized"}

    if not _teams_monitor.is_running():
        return {"message": "Teams monitoring not running"}

    _teams_monitor.stop_monitoring()
    return {"message": "Teams monitoring stopped"}
