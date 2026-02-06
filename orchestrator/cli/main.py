"""orchestrator-cc CLI

このモジュールでは、コマンドラインインターフェースを提供します。
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import typer

from orchestrator.core.agent_health_monitor import get_agent_health_monitor
from orchestrator.core.agent_teams_manager import TeamConfig, get_agent_teams_manager
from orchestrator.web.teams_monitor import TeamsMonitor
from orchestrator.web.thinking_log_handler import get_thinking_log_handler

app = typer.Typer(
    help="orchestrator-cc CLI - Agent Teams管理ツール",
    add_completion=False,
)


@app.command()
def create_team(
    name: str = typer.Argument(..., help="チーム名"),
    description: str = typer.Option(..., "--description", "-d", help="チームの説明"),
    agent_type: str = typer.Option(
        "general-purpose",
        "--agent-type",
        "-t",
        help="エージェントタイプ（デフォルト: general-purpose）",
    ),
    members_file: Path = typer.Option(
        None,
        "--members",
        "-m",
        help="メンバー定義ファイル（JSON形式）",
        exists=True,
    ),
) -> None:
    """新しいチームを作成します。

    チーム設定ファイルを作成し、メンバーをヘルスモニターに登録します。
    """
    manager = get_agent_teams_manager()

    # メンバーリストの作成
    members: list[dict[str, Any]] = []

    if members_file:
        # ファイルからメンバーを読み込み
        with open(members_file, encoding="utf-8") as f:
            members_data = json.load(f)
            if isinstance(members_data, list):
                members = members_data
            else:
                members = members_data.get("members", [])
    else:
        # デフォルトメンバー
        members = [
            {"name": "team-lead", "agentType": "general-purpose", "timeoutThreshold": 300.0},
        ]

    # チーム設定を作成
    config = TeamConfig(
        name=name,
        description=description,
        agent_type=agent_type,
        members=members,
    )

    # チームを作成
    team_name = manager.create_team(config)

    typer.echo(f"チーム '{team_name}' を作成しました")
    typer.echo(f"  説明: {description}")
    typer.echo(f"  エージェントタイプ: {agent_type}")
    typer.echo(f"  メンバー数: {len(members)}")


@app.command()
def delete_team(
    team_name: str = typer.Argument(..., help="削除するチーム名"),
) -> None:
    """チームを削除します。

    チームの設定ファイルとタスクを削除します。
    """
    manager = get_agent_teams_manager()

    if not manager.delete_team(team_name):
        typer.echo(f"エラー: チーム '{team_name}' が見つかりません", err=True)
        raise typer.Exit(1)

    typer.echo(f"チーム '{team_name}' を削除しました")


@app.command()
def list_teams(
    json_output: bool = typer.Option(False, "--json", help="JSON形式で出力"),
) -> None:
    """チーム一覧を表示します。

    登録されている全チームの情報を表示します。
    """
    monitor = TeamsMonitor()
    teams = monitor.get_teams()

    if json_output:
        typer.echo(json.dumps(teams, ensure_ascii=False, indent=2))
        return

    if not teams:
        typer.echo("チームが見つかりませんでした")
        return

    typer.echo(f"\n{'=' * 60}")
    typer.echo(f"チーム一覧 ({len(teams)}件)")
    typer.echo(f"{'=' * 60}\n")

    for team in teams:
        created_at = datetime.fromtimestamp(team.get("createdAt", 0) / 1000).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        typer.echo(f"📁 {team['name']}")
        typer.echo(f"   説明: {team.get('description', 'N/A')}")
        typer.echo(f"   作成日時: {created_at}")
        typer.echo(f"   メンバー数: {len(team.get('members', []))}")
        typer.echo()


@app.command()
def team_status(
    team_name: str = typer.Argument(..., help="チーム名"),
    json_output: bool = typer.Option(False, "--json", help="JSON形式で出力"),
) -> None:
    """チームの状態を表示します。

    指定したチームの詳細な状態情報を表示します。
    """
    manager = get_agent_teams_manager()
    status = manager.get_team_status(team_name)

    if "error" in status:
        typer.echo(f"エラー: {status['error']}", err=True)
        raise typer.Exit(1)

    if json_output:
        typer.echo(json.dumps(status, ensure_ascii=False, indent=2))
        return

    typer.echo(f"\n{'=' * 60}")
    typer.echo(f"チーム: {status['name']}")
    typer.echo(f"{'=' * 60}")
    typer.echo(f"説明: {status.get('description', 'N/A')}")
    typer.echo(f"タスク数: {status.get('taskCount', 0)}")
    typer.echo()

    typer.echo("メンバー:")
    for member in status.get("members", []):
        typer.echo(f"  - {member.get('name', 'unknown')}")
        typer.echo(f"    タイプ: {member.get('agentType', 'N/A')}")
        typer.echo(f"    モデル: {member.get('model', 'N/A')}")

    typer.echo()


@app.command()
def team_messages(
    team_name: str = typer.Argument(..., help="チーム名"),
    limit: int = typer.Option(10, "--limit", "-l", help="表示数（デフォルト: 10）"),
    json_output: bool = typer.Option(False, "--json", help="JSON形式で出力"),
) -> None:
    """チームのメッセージを表示します。

    チーム内のメッセージ履歴を表示します。
    """
    monitor = TeamsMonitor()
    messages = monitor.get_team_messages(team_name)

    if not messages:
        typer.echo(f"チーム '{team_name}' のメッセージが見つかりませんでした")
        return

    # 制限を適用
    messages = messages[-limit:] if limit > 0 else messages

    if json_output:
        typer.echo(json.dumps(messages, ensure_ascii=False, indent=2))
        return

    typer.echo(f"\n{'=' * 60}")
    typer.echo(f"チーム '{team_name}' のメッセージ ({len(messages)}件)")
    typer.echo(f"{'=' * 60}\n")

    for msg in messages:
        timestamp = msg.get("timestamp", "N/A")
        sender = msg.get("sender", "unknown")
        content = msg.get("content", "")
        msg_type = msg.get("type", "info")

        type_icons = {
            "task": "📋",
            "result": "✅",
            "thought": "💭",
            "error": "❌",
            "info": "ℹ️",
        }
        icon = type_icons.get(msg_type, "📝")

        typer.echo(f"{icon} [{timestamp}] {sender}")
        content_preview = content[:80] + "..." if len(content) > 80 else content
        typer.echo(f"   {content_preview}")
        typer.echo()


@app.command()
def team_tasks(
    team_name: str = typer.Argument(..., help="チーム名"),
    status_filter: str = typer.Option(None, "--status", "-s", help="ステータスでフィルタ"),
    json_output: bool = typer.Option(False, "--json", help="JSON形式で出力"),
) -> None:
    """チームのタスクを表示します。

    チーム内のタスクリストを表示します。
    """
    monitor = TeamsMonitor()
    tasks = monitor.get_team_tasks(team_name)

    if not tasks:
        typer.echo(f"チーム '{team_name}' のタスクが見つかりませんでした")
        return

    # ステータスでフィルタ
    if status_filter:
        tasks = [t for t in tasks if t.get("status") == status_filter]

    if json_output:
        typer.echo(json.dumps(tasks, ensure_ascii=False, indent=2))
        return

    typer.echo(f"\n{'=' * 60}")
    typer.echo(f"チーム '{team_name}' のタスク ({len(tasks)}件)")
    typer.echo(f"{'=' * 60}\n")

    status_order = ["in_progress", "pending", "completed", "deleted"]
    grouped: dict[str, list[dict[str, Any]]] = {s: [] for s in status_order}

    for task in tasks:
        task_status = task.get("status", "pending")
        if task_status not in grouped:
            grouped[task_status] = []
        grouped[task_status].append(task)

    status_icons = {
        "pending": "⏳",
        "in_progress": "🔄",
        "completed": "✅",
        "deleted": "🗑️",
    }

    for status in status_order:
        tasks_in_status = grouped.get(status, [])
        if not tasks_in_status:
            continue

        icon = status_icons.get(status, "📝")
        typer.echo(f"{icon} {status.upper()} ({len(tasks_in_status)}件)")
        typer.echo("-" * 60)

        for task in tasks_in_status:
            task_id = task.get("id", "unknown")
            subject = task.get("subject", task.get("description", ""))
            owner = task.get("owner", "unassigned")
            active_form = task.get("activeForm", subject)

            typer.echo(f"  [{task_id}] {active_form}")
            typer.echo(f"    担当: {owner}")
            typer.echo()


@app.command()
def health(
    team_name: str = typer.Option(
        None, "--team", "-t", help="チーム名（指定しない場合は全チーム）"
    ),
    json_output: bool = typer.Option(False, "--json", help="JSON形式で出力"),
) -> None:
    """ヘルスステータスを表示します。

    エージェントのヘルス状態を表示します。
    """
    monitor = get_agent_health_monitor()
    health_status = monitor.get_health_status()

    if team_name:
        if team_name not in health_status:
            typer.echo(f"エラー: チーム '{team_name}' のヘルス情報が見つかりません", err=True)
            raise typer.Exit(1)
        health_status = {team_name: health_status[team_name]}

    if json_output:
        typer.echo(json.dumps(health_status, ensure_ascii=False, indent=2))
        return

    typer.echo(f"\n{'=' * 60}")
    typer.echo("ヘルスステータス")
    typer.echo(f"{'=' * 60}\n")

    for t_name, agents in health_status.items():
        typer.echo(f"🏠 チーム: {t_name}")

        for agent_name, status_info in agents.items():
            is_healthy = status_info.get("isHealthy", True)
            elapsed = status_info.get("elapsed", 0.0)
            last_activity = status_info.get("lastActivity", "N/A")
            threshold = status_info.get("timeoutThreshold", 300.0)

            status_icon = "🟢" if is_healthy else "🔴"
            typer.echo(f"  {status_icon} {agent_name}")
            typer.echo(f"     状態: {'健全' if is_healthy else 'タイムアウト'}")
            typer.echo(f"     経過時間: {elapsed:.1f}秒 / {threshold:.0f}秒")
            typer.echo(f"     最終アクティビティ: {last_activity}")
            typer.echo()


@app.command()
def show_logs(
    team_name: str = typer.Argument(..., help="チーム名"),
    agent: str = typer.Option(None, "--agent", "-a", help="エージェント名でフィルタ"),
    limit: int = typer.Option(20, "--limit", "-l", help="表示数（デフォルト: 20）"),
    follow: bool = typer.Option(False, "--follow", "-f", help="リアルタイム監視"),
    json_output: bool = typer.Option(False, "--json", help="JSON形式で出力"),
) -> None:
    """チームの思考ログを表示します。

    チーム内のエージェントの思考ログを表示します。
    """
    handler = get_thinking_log_handler()
    logs = handler.get_logs(team_name)

    if not logs:
        typer.echo(f"チーム '{team_name}' の思考ログが見つかりませんでした")
        return

    # エージェントでフィルタ
    if agent:
        logs = [log for log in logs if log.get("agentName") == agent]

    # 制限を適用
    logs = logs[-limit:] if limit > 0 else logs

    if json_output:
        typer.echo(json.dumps(logs, ensure_ascii=False, indent=2))
        return

    typer.echo(f"\n{'=' * 60}")
    typer.echo(f"チーム '{team_name}' の思考ログ ({len(logs)}件)")
    if agent:
        typer.echo(f"エージェント: {agent}")
    typer.echo(f"{'=' * 60}\n")

    def _display_logs(logs_to_display: list[dict[str, Any]]) -> None:
        """ログを表示するヘルパー関数"""
        for log in logs_to_display:
            agent_name = log.get("agentName", "unknown")
            timestamp = log.get("timestamp", "")
            content = log.get("content", "")
            category = log.get("category", "thinking")

            # カテゴリに応じたアイコン
            category_icons = {
                "thinking": "💭",
                "planning": "📋",
                "decision": "🎯",
                "question": "❓",
                "error": "❌",
            }
            icon = category_icons.get(category, "📝")

            typer.echo(f"{icon} [{timestamp}] {agent_name}")
            content_preview = content[:100] + "..." if len(content) > 100 else content
            typer.echo(f"   {content_preview}")
            typer.echo()

    _display_logs(logs)

    # リアルタイム監視モード
    if follow:
        typer.echo("リアルタイム監視中... (Ctrl+C で終了)", err=True)
        displayed_log_ids = {log.get("id") for log in logs if log.get("id")}

        try:
            while True:
                time.sleep(1)
                new_logs = handler.get_logs(team_name)

                # エージェントでフィルタ
                if agent:
                    new_logs = [log for log in new_logs if log.get("agentName") == agent]

                # 新しいログのみを表示
                fresh_logs = [log for log in new_logs if log.get("id") not in displayed_log_ids]
                if fresh_logs:
                    for log in fresh_logs:
                        if log.get("id"):
                            displayed_log_ids.add(log["id"])
                    _display_logs(fresh_logs)

        except KeyboardInterrupt:
            typer.echo("\n監視を終了しました", err=True)


@app.command()
def team_activity(
    team_name: str = typer.Argument(..., help="チーム名"),
    json_output: bool = typer.Option(False, "--json", help="JSON形式で出力"),
) -> None:
    """チームのアクティビティ概要を表示します。

    チームのメッセージ、タスク、思考ログの概要を表示します。
    """
    monitor = TeamsMonitor()
    handler = get_thinking_log_handler()

    # チーム情報を取得
    teams = monitor.get_teams()
    team_info = next((t for t in teams if t["name"] == team_name), None)

    if not team_info:
        typer.echo(f"エラー: チーム '{team_name}' が見つかりません", err=True)
        raise typer.Exit(1)

    # 各種データを取得
    messages = monitor.get_team_messages(team_name)
    tasks = monitor.get_team_tasks(team_name)
    thinking_logs = handler.get_logs(team_name)

    activity = {
        "teamName": team_name,
        "description": team_info.get("description", ""),
        "messageCount": len(messages),
        "taskCount": len(tasks),
        "thinkingLogCount": len(thinking_logs),
        "memberCount": len(team_info.get("members", [])),
        "tasksByStatus": {},
        "latestActivity": None,
    }

    # タスクをステータス別に集計
    for task in tasks:
        status = task.get("status", "pending")
        activity["tasksByStatus"][status] = activity["tasksByStatus"].get(status, 0) + 1

    # 最新アクティビティを特定
    latest_timestamp = None
    latest_type = None

    for msg in messages:
        ts = msg.get("timestamp", "")
        if ts and (not latest_timestamp or ts > latest_timestamp):
            latest_timestamp = ts
            latest_type = "message"

    for log in thinking_logs:
        ts = log.get("timestamp", "")
        if ts and (not latest_timestamp or ts > latest_timestamp):
            latest_timestamp = ts
            latest_type = "thinking"

    activity["latestActivity"] = {
        "type": latest_type,
        "timestamp": latest_timestamp,
    }

    if json_output:
        typer.echo(json.dumps(activity, ensure_ascii=False, indent=2))
        return

    typer.echo(f"\n{'=' * 60}")
    typer.echo(f"チーム: {team_name}")
    typer.echo(f"{'=' * 60}")
    typer.echo(f"説明: {activity['description']}")
    typer.echo(f"メンバー数: {activity['memberCount']}")
    typer.echo()

    typer.echo("📊 アクティビティ概要:")
    typer.echo(f"  メッセージ数: {activity['messageCount']}")
    typer.echo(f"  タスク数: {activity['taskCount']}")
    typer.echo(f"  思考ログ数: {activity['thinkingLogCount']}")
    typer.echo()

    if activity["tasksByStatus"]:
        typer.echo("📋 タスクステータス:")
        status_labels = {
            "pending": "待機中",
            "in_progress": "進行中",
            "completed": "完了",
            "deleted": "削除",
        }
        for status, count in activity["tasksByStatus"].items():
            label = status_labels.get(status, status)
            typer.echo(f"  {label}: {count}件")
        typer.echo()

    if activity["latestActivity"]["timestamp"]:
        typer.echo("🕐 最新アクティビティ:")
        typer.echo(f"  タイプ: {activity['latestActivity']['type'] or 'N/A'}")
        typer.echo(f"  時刻: {activity['latestActivity']['timestamp']}")
        typer.echo()


def main() -> None:
    """メインエントリーポイント"""
    app()


if __name__ == "__main__":
    main()
