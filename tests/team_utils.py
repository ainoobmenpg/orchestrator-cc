"""TeamCreate機能テスト用ユーティリティ

このモジュールでは、TeamCreate機能をテストするためのユーティリティ関数を提供します。

主な機能:
- テスト用のモックチーム作成
- テスト用のモックタスク作成
- テスト後のクリーンアップ
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from orchestrator.core.models.team import TeamConfig


def create_mock_team_config(
    team_name: str,
    description: str = "Test team",
    agent_type: str = "general-purpose",
    members: list[dict[str, Any]] | None = None,
) -> TeamConfig:
    """テスト用のモックTeamConfigを作成します。

    Args:
        team_name: チーム名
        description: チーム説明（デフォルト: "Test team"）
        agent_type: エージェントタイプ（デフォルト: "general-purpose"）
        members: メンバーリスト（デフォルト: team-leadのみ）

    Returns:
        TeamConfigインスタンス

    Examples:
        >>> config = create_mock_team_config("test-team")
        >>> config.name
        'test-team'
        >>> config.description
        'Test team'
    """
    if members is None:
        members = [
            {
                "name": "team-lead",
                "agentType": agent_type,
                "model": "claude-opus-4-6",
                "timeoutThreshold": 300.0,
            },
        ]

    return TeamConfig(
        name=team_name,
        description=description,
        agent_type=agent_type,
        members=members,
    )


def create_mock_task(
    task_id: str,
    subject: str,
    description: str = "",
    status: str = "pending",
    owner: str = "",
    blocked_by: list[str] | None = None,
) -> dict[str, Any]:
    """テスト用のモックタスクを作成します。

    Args:
        task_id: タスクID
        subject: タスク件名
        description: タスク詳細説明（デフォルト: 空文字）
        status: タスクステータス（デフォルト: "pending"）
        owner: タスク所有者（デフォルト: 空文字）
        blocked_by: ブロックしているタスクIDリスト（デフォルト: 空リスト）

    Returns:
        タスク情報の辞書

    Examples:
        >>> task = create_mock_task("task-1", "Test task")
        >>> task["id"]
        'task-1'
        >>> task["subject"]
        'Test task'
    """
    return {
        "id": task_id,
        "subject": subject,
        "description": description,
        "status": status,
        "owner": owner,
        "blockedBy": blocked_by or [],
        "blocks": [],
    }


def create_mock_task_file(
    team_name: str,
    task_id: str,
    tasks_dir: Path,
    task_data: dict[str, Any] | None = None,
) -> Path:
    """テスト用のタスクファイルを作成します。

    Args:
        team_name: チーム名
        task_id: タスクID
        tasks_dir: タスクディレクトリ
        task_data: タスクデータ（指定しない場合はデフォルト値を使用）

    Returns:
        作成されたタスクファイルのパス

    Examples:
        一時ディレクトリを作成してタスクファイルを作成:
        >>> import tempfile
        >>> tmpdir = Path(tempfile.mkdtemp())
        >>> tasks_dir = tmpdir / "tasks"
        >>> task_file = create_mock_task_file("test-team", "task-1", tasks_dir)
        >>> task_file.exists()
        True
        >>> import shutil
        >>> shutil.rmtree(tmpdir)
    """
    team_tasks_dir = tasks_dir / team_name
    team_tasks_dir.mkdir(parents=True, exist_ok=True)

    if task_data is None:
        task_data = create_mock_task(
            task_id=task_id,
            subject=f"Test task {task_id}",
            description=f"Description for task {task_id}",
        )

    task_file = team_tasks_dir / f"{task_id}.json"
    with open(task_file, "w", encoding="utf-8") as f:
        json.dump(task_data, f, indent=2, ensure_ascii=False)

    return task_file


def cleanup_test_teams(
    teams_dir: Path,
    team_names: list[str] | None = None,
) -> int:
    """テスト用のチームディレクトリをクリーンアップします。

    Args:
        teams_dir: チームディレクトリ
        team_names: 削除するチーム名リスト（指定しない場合は全チームを削除）

    Returns:
        削除したチーム数

    Examples:
        一時ディレクトリを作成してチームをクリーンアップ:
        >>> import tempfile
        >>> tmpdir = Path(tempfile.mkdtemp())
        >>> teams_dir = tmpdir / "teams"
        >>> teams_dir.mkdir(parents=True)
        >>> (teams_dir / "test-team").mkdir()
        >>> count = cleanup_test_teams(teams_dir, ["test-team"])
        >>> count
        1
        >>> import shutil
        >>> shutil.rmtree(tmpdir)
    """
    if not teams_dir.exists():
        return 0

    count = 0
    if team_names is None:
        # 全チームを削除
        for team_dir in teams_dir.iterdir():
            if team_dir.is_dir():
                shutil.rmtree(team_dir)
                count += 1
    else:
        # 指定されたチームのみ削除
        for team_name in team_names:
            team_dir = teams_dir / team_name
            if team_dir.exists():
                shutil.rmtree(team_dir)
                count += 1

    return count


def cleanup_test_tasks(
    tasks_dir: Path,
    team_names: list[str] | None = None,
) -> int:
    """テスト用のタスクディレクトリをクリーンアップします。

    Args:
        tasks_dir: タスクディレクトリ
        team_names: 削除するチーム名リスト（指定しない場合は全チームのタスクを削除）

    Returns:
        削除したタスクディレクトリ数

    Examples:
        一時ディレクトリを作成してタスクをクリーンアップ:
        >>> import tempfile
        >>> tmpdir = Path(tempfile.mkdtemp())
        >>> tasks_dir = tmpdir / "tasks"
        >>> tasks_dir.mkdir(parents=True)
        >>> (tasks_dir / "test-team").mkdir()
        >>> count = cleanup_test_tasks(tasks_dir, ["test-team"])
        >>> count
        1
        >>> import shutil
        >>> shutil.rmtree(tmpdir)
    """
    if not tasks_dir.exists():
        return 0

    count = 0
    if team_names is None:
        # 全チームのタスクを削除
        for team_dir in tasks_dir.iterdir():
            if team_dir.is_dir():
                shutil.rmtree(team_dir)
                count += 1
    else:
        # 指定されたチームのタスクのみ削除
        for team_name in team_names:
            team_dir = tasks_dir / team_name
            if team_dir.exists():
                shutil.rmtree(team_dir)
                count += 1

    return count


def cleanup_test_data(
    teams_dir: Path,
    tasks_dir: Path,
    team_names: list[str] | None = None,
) -> dict[str, int]:
    """テスト用のチーム・タスクデータを一括クリーンアップします。

    Args:
        teams_dir: チームディレクトリ
        tasks_dir: タスクディレクトリ
        team_names: 削除するチーム名リスト（指定しない場合は全チームを削除）

    Returns:
        削除数の辞書 {"teams": int, "tasks": int}

    Examples:
        一時ディレクトリを作成してテストデータをクリーンアップ:
        >>> import tempfile
        >>> tmpdir = Path(tempfile.mkdtemp())
        >>> teams_dir = tmpdir / "teams"
        >>> tasks_dir = tmpdir / "tasks"
        >>> teams_dir.mkdir(parents=True)
        >>> tasks_dir.mkdir(parents=True)
        >>> (teams_dir / "test-team").mkdir()
        >>> (tasks_dir / "test-team").mkdir()
        >>> result = cleanup_test_data(teams_dir, tasks_dir, ["test-team"])
        >>> result["teams"]
        1
        >>> result["tasks"]
        1
        >>> import shutil
        >>> shutil.rmtree(tmpdir)
    """
    teams_count = cleanup_test_teams(teams_dir, team_names)
    tasks_count = cleanup_test_tasks(tasks_dir, team_names)

    return {"teams": teams_count, "tasks": tasks_count}


def create_test_team_directory(
    teams_dir: Path,
    team_name: str,
    config: dict[str, Any] | None = None,
) -> Path:
    """テスト用のチームディレクトリを直接作成します。

    AgentTeamsManagerを使用せずに、テスト用にディレクトリ構造を作成する場合に使用します。

    Args:
        teams_dir: チームディレクトリ
        team_name: チーム名
        config: config.jsonに書き込む内容（指定しない場合はデフォルト値を使用）

    Returns:
        作成されたチームディレクトリのパス

    Examples:
        一時ディレクトリを作成してチームディレクトリを作成:
        >>> import tempfile
        >>> tmpdir = Path(tempfile.mkdtemp())
        >>> teams_dir = tmpdir / "teams"
        >>> team_dir = create_test_team_directory(teams_dir, "test-team")
        >>> team_dir.exists()
        True
        >>> import shutil
        >>> shutil.rmtree(tmpdir)
    """
    team_dir = teams_dir / team_name
    team_dir.mkdir(parents=True, exist_ok=True)

    if config is None:
        config = {
            "name": team_name,
            "description": f"Test team: {team_name}",
            "createdAt": 0,
            "leadAgentId": f"team-lead@{team_name}",
            "leadSessionId": f"session-{team_name}",
            "members": [
                {
                    "agentId": f"team-lead@{team_name}",
                    "name": "team-lead",
                    "agentType": "general-purpose",
                    "model": "claude-opus-4-6",
                    "joinedAt": 0,
                    "cwd": str(Path.cwd()),
                    "subscriptions": [],
                    "planModeRequired": False,
                },
            ],
        }

    config_file = team_dir / "config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    return team_dir


__all__ = [
    "create_mock_team_config",
    "create_mock_task",
    "create_mock_task_file",
    "cleanup_test_teams",
    "cleanup_test_tasks",
    "cleanup_test_data",
    "create_test_team_directory",
]
