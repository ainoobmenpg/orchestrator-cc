"""SPA配信ロジック

このモジュールでは、シングルページアプリケーション（SPA）の配信機能を提供します。
"""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

# ルーターを作成
spa_router = APIRouter()

# パス設定
_frontend_dist_dir = Path(__file__).parent / "frontend" / "dist"
_templates_dir = Path(__file__).parent / "templates"


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
