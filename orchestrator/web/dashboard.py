"""Webダッシュボード FastAPIアプリケーション

このモジュールでは、FastAPIベースのダッシュボードバックエンドを提供します。

機能:
- REST APIエンドポイント（Agent Teams用）
- WebSocketエンドポイント
- TeamsMonitor統合
- リアルタイム状態配信

アーキテクチャ:
- APIルート: orchestrator/web/api/routes.py
- WebSocket: orchestrator/web/api/websocket.py
- CORSミドルウェア: orchestrator/web/middleware.py
- SPA配信: orchestrator/web/spa.py
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from orchestrator.core.agent_health_monitor import get_agent_health_monitor
from orchestrator.core.agent_teams_manager import get_agent_teams_manager
from orchestrator.web.api.routes import router
from orchestrator.web.api.routes import set_global_state as set_routes_global_state
from orchestrator.web.api.websocket import (
    set_global_state as set_ws_global_state,
)
from orchestrator.web.api.websocket import websocket_endpoint
from orchestrator.web.message_handler import WebSocketManager, WebSocketMessageHandler
from orchestrator.web.middleware import setup_cors_middleware
from orchestrator.web.team_models import GlobalState
from orchestrator.web.teams_monitor import TeamsMonitor
from orchestrator.web.thinking_log_handler import get_thinking_log_handler

# ロガーの設定
logger = logging.getLogger(__name__)

# グローバルステート
_global_state = GlobalState()

# パス設定
_frontend_dist_dir = Path(__file__).parent / "frontend" / "dist"
_templates_dir = Path(__file__).parent / "templates"
_static_dir = Path(__file__).parent / "static"


# ============================================================================
# ライフサイクル管理
# ============================================================================


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
    ws_handler = WebSocketMessageHandler(ws_manager)
    _global_state.ws_manager = ws_manager
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

    # グローバルステートを各モジュールに設定
    set_routes_global_state(_global_state)
    set_ws_global_state(_global_state)

    yield

    # 終了時
    logger.info("FastAPIアプリケーションを停止します")

    # Teams監視を停止
    if _global_state.teams_monitor and _global_state.teams_monitor.is_running():
        _global_state.teams_monitor.stop_monitoring()

    # 思考ログ監視を停止
    if _global_state.thinking_log_handler and _global_state.thinking_log_handler.is_running():
        _global_state.thinking_log_handler.stop_monitoring()

    # ヘルスモニターを停止
    if _global_state.health_monitor and _global_state.health_monitor.is_running():
        _global_state.health_monitor.stop_monitoring()

    # 全てのWebSocket接続を閉じる
    if _global_state.ws_manager:
        await _global_state.ws_manager.close_all()


# ============================================================================
# ブロードキャストコールバック
# ============================================================================


def _broadcast_teams_update(data: dict) -> None:
    """TeamsMonitorの更新をWebSocketにブロードキャストします。

    Args:
        data: 更新データ
    """
    if _global_state.ws_manager:
        try:
            asyncio.get_running_loop()
            asyncio.create_task(_global_state.ws_manager.broadcast(data))
        except RuntimeError:
            # イベントループが実行中でない場合は無視
            pass


def _broadcast_thinking_log(data: dict) -> None:
    """思考ログの更新をWebSocketにブロードキャストします。

    Args:
        data: 更新データ
    """
    if _global_state.ws_manager:
        try:
            asyncio.get_running_loop()
            asyncio.create_task(_global_state.ws_manager.broadcast(data))
        except RuntimeError:
            # イベントループが実行中でない場合は無視
            pass


def _on_health_event(event) -> None:
    """ヘルスチェックイベントを処理します。

    Args:
        event: ヘルスチェックイベント
    """
    if _global_state.ws_manager:
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
# SPAルート定義
# ============================================================================


spa_router = APIRouter()


@spa_router.get("/", response_model=None)
async def root() -> FileResponse | dict:
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


@spa_router.get("/{full_path:path}", response_model=None)
async def serve_spa(full_path: str) -> FileResponse | dict:
    """React SPAを配信します

    全てのルートをindex.htmlにフォールバックすることで、
    React Routerのクライアントサイドルーティングをサポートします。

    Note: このルートは最後に定義する必要があります（キャッチオール）

    Args:
        full_path: リクエストパス
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


# ============================================================================
# アプリケーション作成
# ============================================================================

# FastAPIアプリケーションを作成
app = FastAPI(
    title="Orchestrator CC Dashboard",
    description="クラスタ管理用Webダッシュボード",
    version="0.1.0",
    lifespan=lifespan,
)

# CORSミドルウェアを設定
setup_cors_middleware(app)

# 旧静的ファイル（開発用・互換性維持）
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

# APIルーターをマウント（最初にマウントして優先させる）
app.include_router(router, prefix="/api")

# APIルートのエイリアス（末尾スラッシュなし）
@app.get("/api", response_model=None)
async def api_info() -> dict:
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

# WebSocketエンドポイントを追加
app.add_websocket_route("/ws", websocket_endpoint)

# SPAルーターをマウント（最後にマウントしてフォールバックとして機能）
# 注意：spa_routerの/{full_path:path}が/apiにマッチしないように、
# /apiルートを個別に定義しています
app.include_router(spa_router)


# ============================================================================
# メインエントリーポイント
# ============================================================================


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
