"""Agent Teamsマネージャーモジュール

このモジュールでは、Agent Teamsの作成・管理・タスク操作を提供します。
"""

import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from orchestrator.core.agent_health_monitor import (
    HealthCheckEvent,
    get_agent_health_monitor,
)
from orchestrator.core.models import TeamConfig

logger = logging.getLogger(__name__)


class AgentTeamsManager:
    """Agent Teamsマネージャー

    Agent Teamsの作成・管理・タスク操作を提供します。

    Attributes:
        _health_monitor: ヘルスモニター
        _teams_dir: チームディレクトリ
        _tasks_dir: タスクディレクトリ
    """

    def __init__(
        self,
        teams_dir: Path | None = None,
        tasks_dir: Path | None = None,
    ):
        """AgentTeamsManagerを初期化します。

        Args:
            teams_dir: チームディレクトリ（デフォルト: ~/.claude/teams）
            tasks_dir: タスクディレクトリ（デフォルト: ~/.claude/tasks）
        """
        self._health_monitor = get_agent_health_monitor()
        self._teams_dir = Path(teams_dir or Path.home() / ".claude" / "teams")
        self._tasks_dir = Path(tasks_dir or Path.home() / ".claude" / "tasks")

        # ディレクトリを作成
        self._teams_dir.mkdir(parents=True, exist_ok=True)
        self._tasks_dir.mkdir(parents=True, exist_ok=True)

        # ヘルスモニターにイベントコールバックを登録
        self._health_monitor.register_callback(self._on_health_event)

    def create_team(self, config: TeamConfig) -> str:
        """チームを作成します。

        注: このメソッドはチーム設定ファイルを作成するだけです。
        実際のチーム作成はClaude CodeのTeamCreateツールを使用してください。

        Args:
            config: チーム設定

        Returns:
            チーム名
        """
        team_dir = self._teams_dir / config.name

        if team_dir.exists():
            logger.warning(f"Team directory already exists: {config.name}")
            return config.name

        # チームディレクトリを作成
        team_dir.mkdir(parents=True, exist_ok=True)

        # config.jsonを作成
        config_data = {
            "name": config.name,
            "description": config.description,
            "createdAt": int(datetime.now().timestamp() * 1000),
            "leadAgentId": f"team-lead@{config.name}",
            "leadSessionId": f"session-{config.name}",
            "members": [
                {
                    "agentId": f"{member.get('name', 'unknown')}@{config.name}",
                    "name": member.get("name", "unknown"),
                    "agentType": member.get("agentType", "general-purpose"),
                    "model": member.get("model", "claude-sonnet-4-5-20250929"),
                    "joinedAt": int(datetime.now().timestamp() * 1000),
                    "tmuxPaneId": "",
                    "cwd": str(Path.cwd()),
                    "subscriptions": [],
                    "planModeRequired": member.get("planModeRequired", False),
                }
                for member in config.members
            ],
        }

        config_file = team_dir / "config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Team config created: {config.name}")

        # メンバーをヘルスモニターに登録
        for member in config.members:
            member_name = member.get("name", "unknown")
            self._health_monitor.register_agent(
                team_name=config.name,
                agent_name=member_name,
                timeout_threshold=member.get("timeoutThreshold", 300.0),
            )

        return config.name

    def delete_team(self, team_name: str) -> bool:
        """チームを削除します。

        Args:
            team_name: チーム名

        Returns:
            成功ならTrue
        """
        team_dir = self._teams_dir / team_name

        if not team_dir.exists():
            logger.warning(f"Team directory not found: {team_name}")
            return False

        # チームディレクトリを削除
        import shutil

        shutil.rmtree(team_dir)

        # タスクディレクトリも削除
        task_dir = self._tasks_dir / team_name
        if task_dir.exists():
            shutil.rmtree(task_dir)

        logger.info(f"Team deleted: {team_name}")
        return True

    def get_team_tasks(self, team_name: str) -> list[dict[str, Any]]:
        """チームのタスクリストを取得します。

        Args:
            team_name: チーム名

        Returns:
            タスクのリスト
        """
        tasks: list[dict[str, Any]] = []
        task_dir = self._tasks_dir / team_name

        if not task_dir.exists():
            return tasks

        for task_file in task_dir.glob("*.json"):
            try:
                with open(task_file, encoding="utf-8") as f:
                    data = json.load(f)
                tasks.append(data)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to read task file {task_file}: {e}")

        return tasks

    def get_team_status(self, team_name: str) -> dict[str, Any]:
        """チームの状態を取得します。

        Args:
            team_name: チーム名

        Returns:
            チーム状態の辞書
        """
        team_dir = self._teams_dir / team_name

        if not team_dir.exists():
            return {"error": "Team not found"}

        # config.jsonを読み込み
        config_file = team_dir / "config.json"
        try:
            with open(config_file, encoding="utf-8") as f:
                config_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            return {"error": f"Failed to read config: {e}"}

        # タスクリストを取得
        tasks = self.get_team_tasks(team_name)

        # ヘルス状態を取得
        health_status = self._health_monitor.get_health_status()
        team_health = health_status.get(team_name, {})

        return {
            "name": team_name,
            "description": config_data.get("description", ""),
            "members": config_data.get("members", []),
            "taskCount": len(tasks),
            "tasks": tasks,
            "health": team_health,
        }

    def update_agent_activity(self, team_name: str, agent_name: str) -> None:
        """エージェントのアクティビティを更新します。

        Args:
            team_name: チーム名
            agent_name: エージェント名
        """
        self._health_monitor.update_activity(team_name, agent_name)

    def restart_agent(self, team_name: str, agent_name: str) -> bool:
        """エージェントを再起動します。

        注: このメソッドはヘルス状態をリセットするだけです。
        実際の再起動はClaude CodeのTeamDelete/TeamCreateツールを使用してください。

        Args:
            team_name: チーム名
            agent_name: エージェント名

        Returns:
            成功ならTrue
        """
        # アクティビティを更新してヘルス状態をリセット
        self._health_monitor.update_activity(team_name, agent_name)

        logger.info(f"Agent activity updated: {team_name}/{agent_name}")
        return True

    def _on_health_event(self, event: HealthCheckEvent) -> None:
        """ヘルスチェックイベントを処理します。

        Args:
            event: ヘルスチェックイベント
        """
        if event.event_type == "timeout_detected":
            logger.warning(
                f"Agent timeout: {event.team_name}/{event.agent_name} - considering restart"
            )
            # TODO: 自動再起動ロジックを実装
            # 現在はログ出力のみ


# シングルトンインスタンス
_teams_manager: AgentTeamsManager | None = None
_manager_lock = threading.Lock()


def get_agent_teams_manager() -> AgentTeamsManager:
    """Agent Teamsマネージャーのシングルトンインスタンスを取得します。

    Returns:
        AgentTeamsManagerインスタンス
    """
    global _teams_manager

    with _manager_lock:
        if _teams_manager is None:
            _teams_manager = AgentTeamsManager()
        return _teams_manager


__all__ = ["AgentTeamsManager", "TeamConfig", "get_agent_teams_manager"]
