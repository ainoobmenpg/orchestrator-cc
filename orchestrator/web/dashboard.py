"""Webダッシュボード FastAPIアプリケーション

このモジュールでは、FastAPIベースのダッシュボードバックエンドを提供します。

機能:
- REST APIエンドポイント（Agent Teams用）
- WebSocketエンドポイント
- TeamsMonitor統合
- リアルタイム状態配信
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from orchestrator.core.agent_health_monitor import AgentHealthMonitor, get_agent_health_monitor
from orchestrator.core.agent_teams_manager import (
    AgentTeamsManager,
    get_agent_teams_manager,
)
from orchestrator.web.message_handler import ChannelManager, WebSocketManager, WebSocketMessageHandler
from orchestrator.web.team_models import GlobalState
from orchestrator.web.teams_monitor import TeamsMonitor
from orchestrator.web.thinking_log_handler import ThinkingLogHandler, get_thinking_log_handler

# ロガーの設定
logger = logging.getLogger(__name__)

# グローバルステート
_global_state: GlobalState = GlobalState()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """アプリケーションのライフサイクル管理

    アプリケーション起動時と終了時の処理を定義します。
    """
    global _global_state

    # 起動時
    logger.info("FastAPIアプリケーションを起動します")

    # WebSocketマネージャーを初期化
    ws_manager = WebSocketManager()
    channel_manager = ChannelManager()
    ws_handler = WebSocketMessageHandler(ws_manager, channel_manager)

    # GlobalStateに設定
    _global_state.ws_manager = ws_manager
    _global_state.channel_manager = channel_manager
    _global_state.ws_handler = ws_handler

    # TeamsMonitorを初期化
    teams_monitor = TeamsMonitor()
    teams_monitor.register_update_callback(_broadcast_teams_update)
    teams_monitor.start_monitoring()
    _global_state.teams_monitor = teams_monitor
    logger.info("Teams monitoring started")

    # ThinkingLogHandlerを初期化
    thinking_log_handler = get_thinking_log_handler()
    thinking_log_handler.register_callback(_broadcast_thinking_log)
    thinking_log_handler.start_monitoring()
    _global_state.thinking_log_handler = thinking_log_handler
    logger.info("Thinking log monitoring started")

    # AgentTeamsManagerを初期化
    teams_manager = get_agent_teams_manager()
    _global_state.teams_manager = teams_manager
    logger.info("AgentTeamsManager initialized")

    # AgentHealthMonitorを初期化
    health_monitor = get_agent_health_monitor()
    health_monitor.register_callback(_on_health_event)
    health_monitor.start_monitoring()
    _global_state.health_monitor = health_monitor
    logger.info("AgentHealthMonitor started")

    yield

    # 終了時
    logger.info("FastAPIアプリケーションを停止します")

    # Teams監視を停止
    if _global_state.teams_monitor and _global_state.teams_monitor.is_running():
        _global_state.teams_monitor.stop_monitoring()

    # 思考ログ監視を停止
    if (
        _global_state.thinking_log_handler
        and _global_state.thinking_log_handler.is_running()
    ):
        _global_state.thinking_log_handler.stop_monitoring()

    # ヘルスモニターを停止
    if _global_state.health_monitor and _global_state.health_monitor.is_running():
        _global_state.health_monitor.stop_monitoring()

    # 全てのWebSocket接続を閉じる
    if _global_state.ws_manager:
        await _global_state.ws_manager.close_all()


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

# パス設定
_frontend_dist_dir = Path(__file__).parent / "frontend" / "dist"
_templates_dir = Path(__file__).parent / "templates"
_static_dir = Path(__file__).parent / "static"

# 旧静的ファイル（開発用・互換性維持）
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


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


# ============================================================================
# REST APIエンドポイント
# ============================================================================

# パス設定
_frontend_dist_dir = Path(__file__).parent / "frontend" / "dist"
_templates_dir = Path(__file__).parent / "templates"
_static_dir = Path(__file__).parent / "static"

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
    if _global_state.ws_manager is None or _global_state.ws_handler is None:
        await websocket.close(code=1011, reason="Server not initialized")
        return

    await _global_state.ws_manager.connect(websocket)

    try:
        # 接続確立メッセージを送信
        await _global_state.ws_manager.send_personal(
            {
                "type": "connected",
                "message": "Connected to Orchestrator CC Dashboard",
            },
            websocket,
        )

        # 初期システムログを送信
        await _global_state.ws_manager.send_personal(
            {
                "type": "system_log",
                "timestamp": None,
                "level": "info",
                "content": "ダッシュボードに接続しました",
            },
            websocket,
        )

        # チーム状態をログに追加
        if _global_state.teams_monitor:
            teams = _global_state.teams_monitor.get_teams()
            await _global_state.ws_manager.send_personal(
                {
                    "type": "system_log",
                    "timestamp": None,
                    "level": "info",
                    "content": f"チーム状態: {len(teams)} チーム稼働中",
                },
                websocket,
            )

        # メッセージ受信ループ
        while True:
            message = await websocket.receive_text()
            await _global_state.ws_handler.handle_message(message, websocket)

    except WebSocketDisconnect:
        _global_state.ws_manager.disconnect(websocket)
        logger.info(f"WebSocket接続が切断されました: {websocket.client}")
    except Exception as e:
        logger.error(f"WebSocketエラーが発生: {e}")
        _global_state.ws_manager.disconnect(websocket)


# ============================================================================
# Agent Teams APIエンドポイント
# ============================================================================


@app.get("/api/teams")
async def get_teams():
    """チーム一覧を取得します。

    Returns:
        チーム情報のリスト
    """
    if _global_state.teams_monitor is None:
        return {"error": "Teams monitor not initialized"}

    return {"teams": _global_state.teams_monitor.get_teams()}


@app.get("/api/teams/{team_name}/messages")
async def get_team_messages(team_name: str):
    """チームのメッセージ履歴を取得します。

    Args:
        team_name: チーム名

    Returns:
        メッセージのリスト
    """
    if _global_state.teams_monitor is None:
        return {"error": "Teams monitor not initialized"}

    return {
        "teamName": team_name,
        "messages": _global_state.teams_monitor.get_team_messages(team_name),
    }


@app.get("/api/teams/{team_name}/tasks")
async def get_team_tasks(team_name: str):
    """チームのタスクリストを取得します。

    Args:
        team_name: チーム名

    Returns:
        タスクのリスト
    """
    if _global_state.teams_monitor is None:
        return {"error": "Teams monitor not initialized"}

    return {
        "teamName": team_name,
        "tasks": _global_state.teams_monitor.get_team_tasks(team_name),
    }


def _on_health_event(event) -> None:
    """ヘルスチェックイベントを処理します。

    Args:
        event: ヘルスチェックイベント
    """
    if _global_state.ws_manager:
        # 非同期でブロードキャスト
        import asyncio

        try:
            asyncio.get_running_loop()
            asyncio.create_task(
                _global_state.ws_manager.broadcast(
                    {
                        "type": "health_event",
                        "event": event.to_dict(),
                    }
                )
            )
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
    if _global_state.teams_manager is None:
        return {"error": "Teams manager not initialized"}

    return _global_state.teams_manager.get_team_status(team_name)


@app.post("/api/teams/{team_name}/activity")
async def update_agent_activity(team_name: str, agent_name: str):
    """エージェントのアクティビティを更新します。

    Args:
        team_name: チーム名
        agent_name: エージェント名

    Returns:
        成功メッセージ
    """
    if _global_state.teams_manager is None:
        return {"error": "Teams manager not initialized"}

    _global_state.teams_manager.update_agent_activity(team_name, agent_name)
    return {"message": "Activity updated"}


@app.get("/api/health")
async def get_health_status():
    """ヘルスモニターの状態を取得します。

    Returns:
        ヘルス状態
    """
    if _global_state.health_monitor is None:
        return {"error": "Health monitor not initialized"}

    return _global_state.health_monitor.get_health_status()


@app.post("/api/health/start")
async def start_health_monitoring():
    """ヘルスモニタリングを開始します。

    Returns:
        成功メッセージ
    """
    if _global_state.health_monitor is None:
        return {"error": "Health monitor not initialized"}

    if _global_state.health_monitor.is_running():
        return {"message": "Health monitoring already running"}

    _global_state.health_monitor.start_monitoring()
    return {"message": "Health monitoring started"}


@app.post("/api/health/stop")
async def stop_health_monitoring():
    """ヘルスモニタリングを停止します。

    Returns:
        成功メッセージ
    """
    if _global_state.health_monitor is None:
        return {"error": "Health monitor not initialized"}

    if not _global_state.health_monitor.is_running():
        return {"message": "Health monitoring not running"}

    _global_state.health_monitor.stop_monitoring()
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

    return {"teamName": team_name, "agent": agent, "thinking": logs}


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


# ============================================================================
# SPA Serving (最後に定義して、他のルートが優先されるようにする)
# ============================================================================


@app.get("/")
async def root():
    """ダッシュボードHTMLを返します（React SPA）"""
    # まず dist/index.html を試す
    if _frontend_dist_dir.exists():
        index_path = _frontend_dist_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)

    # 次に templates/index.html を試す
    index_path = _templates_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)

    # ビルド済みファイルがない場合はメッセージを返す
    return {
        "message": "Orchestrator CC Dashboard - React Build Required",
        "version": "2.0.0",
        "instructions": "Reactアプリをビルドしてください: cd orchestrator/web/frontend && npm install && npm run build",
        "endpoints": {
            "teams": "/api/teams",
            "teams_messages": "/api/teams/{team_name}/messages",
            "teams_tasks": "/api/teams/{team_name}/tasks",
            "teams_thinking": "/api/teams/{team_name}/thinking",
            "teams_status": "/api/teams/{team_name}/status",
            "health": "/api/health",
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
            "teams": "/api/teams",
            "teams_messages": "/api/teams/{team_name}/messages",
            "teams_tasks": "/api/teams/{team_name}/tasks",
            "teams_thinking": "/api/teams/{team_name}/thinking",
            "teams_status": "/api/teams/{team_name}/status",
            "health": "/api/health",
            "websocket": "/ws",
        },
    }


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """React SPAを配信します

    全てのルートをindex.htmlにフォールバックすることで、
    React Routerのクライアントサイドルーティングをサポートします。

    Note: このルートは最後に定義する必要があります（キャッチオール）
    """
    if not _frontend_dist_dir.exists():
        return {"error": "Frontend dist directory not found"}

    # アセットファイルの場合は直接返す
    asset_path = _frontend_dist_dir / full_path
    if asset_path.exists() and asset_path.is_file():
        return FileResponse(asset_path)

    # それ以外の場合はindex.htmlを返す（SPAルーティング）
    index_path = _frontend_dist_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)

    return {
        "message": "Orchestrator CC Dashboard",
        "version": "2.0.0",
        "note": "Reactアプリがビルドされていません。frontendディレクトリで npm run build を実行してください。",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
