"""APIルート定義

このモジュールでは、REST APIエンドポイントを定義します。
"""

import logging
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from orchestrator.core.agent_health_monitor import AgentHealthMonitor
from orchestrator.core.agent_teams_manager import AgentTeamsManager
from orchestrator.web.personality_generator import PersonalityGenerator
from orchestrator.web.team_models import GlobalState
from orchestrator.web.teams_monitor import TeamsMonitor
from orchestrator.web.thinking_log_handler import ThinkingLogHandler

# ロガーの設定
logger = logging.getLogger(__name__)

# ルーターを作成
router = APIRouter()

# グローバルステートへのアクセサー
_global_state: GlobalState | None = None


def set_global_state(state: GlobalState) -> None:
    """グローバルステートを設定します。

    Args:
        state: グローバルステート
    """
    global _global_state
    _global_state = state


def _get_teams_monitor() -> TeamsMonitor | None:
    """TeamsMonitorを取得します。

    Returns:
        TeamsMonitorインスタンス、未初期化の場合はNone
    """
    return _global_state.teams_monitor if _global_state else None


def _get_thinking_log_handler() -> ThinkingLogHandler | None:
    """ThinkingLogHandlerを取得します。

    Returns:
        ThinkingLogHandlerインスタンス、未初期化の場合はNone
    """
    return _global_state.thinking_log_handler if _global_state else None


def _get_teams_manager() -> AgentTeamsManager | None:
    """AgentTeamsManagerを取得します。

    Returns:
        AgentTeamsManagerインスタンス、未初期化の場合はNone
    """
    return _global_state.teams_manager if _global_state else None


def _get_health_monitor() -> AgentHealthMonitor | None:
    """AgentHealthMonitorを取得します。

    Returns:
        AgentHealthMonitorインスタンス、未初期化の場合はNone
    """
    return _global_state.health_monitor if _global_state else None


# ============================================================================
# Agent Teams APIエンドポイント
# ============================================================================


@router.get("/teams")
async def get_teams() -> dict[str, Any]:
    """チーム一覧を取得します。

    Returns:
        チーム情報のリスト
    """
    teams_monitor = _get_teams_monitor()
    if teams_monitor is None:
        return {"error": "Teams monitor not initialized"}

    return {"teams": teams_monitor.get_teams()}


@router.get("/teams/{team_name}/messages")
async def get_team_messages(team_name: str) -> dict[str, Any]:
    """チームのメッセージ履歴を取得します。

    Args:
        team_name: チーム名

    Returns:
        メッセージのリスト
    """
    teams_monitor = _get_teams_monitor()
    if teams_monitor is None:
        return {"error": "Teams monitor not initialized"}

    return {"teamName": team_name, "messages": teams_monitor.get_team_messages(team_name)}


@router.get("/teams/{team_name}/tasks")
async def get_team_tasks(team_name: str) -> dict[str, Any]:
    """チームのタスクリストを取得します。

    Args:
        team_name: チーム名

    Returns:
        タスクのリスト
    """
    teams_monitor = _get_teams_monitor()
    if teams_monitor is None:
        return {"error": "Teams monitor not initialized"}

    return {"teamName": team_name, "tasks": teams_monitor.get_team_tasks(team_name)}


# ============================================================================
# Agent Teams Management APIエンドポイント
# ============================================================================


@router.get("/teams/{team_name}/status")
async def get_team_status(team_name: str) -> dict[str, Any]:
    """チームの状態を取得します。

    Args:
        team_name: チーム名

    Returns:
        チーム状態
    """
    teams_manager = _get_teams_manager()
    if teams_manager is None:
        return {"error": "Teams manager not initialized"}

    return teams_manager.get_team_status(team_name)


@router.post("/teams/{team_name}/activity")
async def update_agent_activity(team_name: str, agent_name: str) -> dict[str, str]:
    """エージェントのアクティビティを更新します。

    Args:
        team_name: チーム名
        agent_name: エージェント名

    Returns:
        成功メッセージ
    """
    teams_manager = _get_teams_manager()
    if teams_manager is None:
        return {"error": "Teams manager not initialized"}

    teams_manager.update_agent_activity(team_name, agent_name)
    return {"message": "Activity updated"}


@router.get("/health")
async def get_health_status() -> dict[str, Any]:
    """ヘルスモニターの状態を取得します。

    Returns:
        ヘルス状態
    """
    health_monitor = _get_health_monitor()
    if health_monitor is None:
        return {"error": "Health monitor not initialized"}

    return health_monitor.get_health_status()


@router.post("/health/start")
async def start_health_monitoring() -> dict[str, str]:
    """ヘルスモニタリングを開始します。

    Returns:
        成功メッセージ
    """
    health_monitor = _get_health_monitor()
    if health_monitor is None:
        return {"error": "Health monitor not initialized"}

    if health_monitor.is_running():
        return {"message": "Health monitoring already running"}

    health_monitor.start_monitoring()
    return {"message": "Health monitoring started"}


@router.post("/health/stop")
async def stop_health_monitoring() -> dict[str, str]:
    """ヘルスモニタリングを停止します。

    Returns:
        成功メッセージ
    """
    health_monitor = _get_health_monitor()
    if health_monitor is None:
        return {"error": "Health monitor not initialized"}

    if not health_monitor.is_running():
        return {"message": "Health monitoring not running"}

    health_monitor.stop_monitoring()
    return {"message": "Health monitoring stopped"}


# ============================================================================
# 既存のAgent Teams APIエンドポイント
# ============================================================================


@router.get("/teams/{team_name}/thinking")
async def get_team_thinking(team_name: str, agent: str | None = None) -> dict[str, Any]:
    """チームの思考ログを取得します。

    Args:
        team_name: チーム名
        agent: エージェント名でフィルタ（オプション）

    Returns:
        思考ログのリスト
    """
    thinking_log_handler = _get_thinking_log_handler()
    if thinking_log_handler is None:
        return {"error": "Thinking log handler not initialized"}

    logs = thinking_log_handler.get_logs(team_name)

    if agent:
        logs = [log for log in logs if log.get("agentName") == agent]

    return {"teamName": team_name, "agent": agent, "thinking": logs}


@router.post("/teams/monitoring/start")
async def start_teams_monitoring() -> dict[str, str]:
    """Teams監視を開始します。

    Returns:
        成功メッセージ
    """
    teams_monitor = _get_teams_monitor()
    if teams_monitor is None:
        return {"error": "Teams monitor not initialized"}

    if teams_monitor.is_running():
        return {"message": "Teams monitoring already running"}

    teams_monitor.start_monitoring()
    return {"message": "Teams monitoring started"}


@router.post("/teams/monitoring/stop")
async def stop_teams_monitoring() -> dict[str, str]:
    """Teams監視を停止します。

    Returns:
        成功メッセージ
    """
    teams_monitor = _get_teams_monitor()
    if teams_monitor is None:
        return {"error": "Teams monitor not initialized"}

    if not teams_monitor.is_running():
        return {"message": "Teams monitoring not running"}

    teams_monitor.stop_monitoring()
    return {"message": "Teams monitoring stopped"}


@router.get("/")
async def api_info() -> dict[str, Any]:
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


# ============================================================================
# 性格生成 APIエンドポイント
# ============================================================================


class PersonalityRequest(BaseModel):
    """性格生成リクエスト"""

    archetype: str  # アーチタイプ（team-lead, researcher, coder, tester）


@router.post("/personality/generate")
async def generate_personality(request: PersonalityRequest) -> dict[str, Any]:
    """性格パラメータをアーチタイプから生成します。

    Args:
        request: 性格生成リクエスト

    Returns:
        生成された性格パラメータ
    """
    try:
        personality = PersonalityGenerator.from_archetype(request.archetype)

        return {
            "personality": personality.to_dict(),
        }
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"性格生成エラー: {e}")
        return {"error": "Failed to generate personality"}
