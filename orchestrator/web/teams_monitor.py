"""Agent Teams監視モジュール

このモジュールでは、Agent Teamsの監視と可視化を行うTeamsMonitorクラスを提供します。
"""

import logging
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any

from orchestrator.web.team_file_observer import TaskFileObserver, TeamFileObserver
from orchestrator.web.team_models import (
    TaskInfo,
    TeamInfo,
    TeamMessage,
    ThinkingLog,
    load_team_config,
    load_team_messages,
    load_team_tasks,
)

logger = logging.getLogger(__name__)


class TeamsMonitor:
    """Agent Teams監視クラス

    チームの状態、メッセージ、タスク、思考ログを監視し、
    WebSocketを通じてクライアントに配信します。

    Attributes:
        _teams: チーム情報の辞書（チーム名 -> TeamInfo）
        _messages: チームメッセージの辞書（チーム名 -> メッセージリスト）
        _tasks: タスク情報の辞書（チーム名 -> タスクリスト）
        _thinking_logs: 思考ログの辞書（チーム名 -> ログリスト）
        _file_observer: ファイル監視オブザーバー
        _task_observer: タスク監視オブザーバー
        _update_callbacks: 更新コールバックのリスト
        _thinking_polling_active: 思考ログポーリング中フラグ（現在は未使用）
    """

    def __init__(self) -> None:
        """TeamsMonitorを初期化します。"""
        self._teams: dict[str, TeamInfo] = {}
        self._messages: dict[str, list[TeamMessage]] = defaultdict(list)
        self._tasks: dict[str, list[TaskInfo]] = defaultdict(list)
        self._thinking_logs: dict[str, list[ThinkingLog]] = defaultdict(list)
        self._file_observer = TeamFileObserver()
        self._task_observer = TaskFileObserver()
        self._update_callbacks: list[Callable[[dict[str, Any]], None]] = []
        self._thinking_polling_active = False
        self._thinking_polling_interval = 2.0  # 秒

        # 既存のチームを読み込み
        self._load_existing_teams()

    def _load_existing_teams(self) -> None:
        """既存のチームを読み込みます。"""
        teams_dir = Path.home() / ".claude" / "teams"

        if not teams_dir.exists():
            return

        for team_dir in teams_dir.iterdir():
            if not team_dir.is_dir():
                continue

            team_name = team_dir.name
            team_info = load_team_config(team_dir)

            if team_info:
                self._teams[team_name] = team_info
                self._messages[team_name] = load_team_messages(team_dir)
                self._tasks[team_name] = load_team_tasks(team_name)
                logger.info(f"Loaded existing team: {team_name}")

    def register_update_callback(self, callback: Callable[[dict[str, Any]], None]) -> None:
        """更新コールバックを登録します。

        Args:
            callback: コールバック関数（更新データを辞書で受け取る）
        """
        self._update_callbacks.append(callback)

    def start_monitoring(self) -> None:
        """監視を開始します。"""
        # コールバックを登録
        self._file_observer.register_callback("config_changed", self._on_config_changed)
        self._file_observer.register_callback("inbox_changed", self._on_inbox_changed)
        self._file_observer.register_callback("team_created", self._on_team_created)
        self._file_observer.register_callback("team_deleted", self._on_team_deleted)
        self._task_observer.register_callback(self._on_task_changed)

        # オブザーバーを開始
        self._file_observer.start()
        self._task_observer.start()

        logger.info("Teams monitoring started")

    def stop_monitoring(self) -> None:
        """監視を停止します。"""
        self._file_observer.stop()
        self._task_observer.stop()
        self._thinking_polling_active = False
        logger.info("Teams monitoring stopped")

    def is_running(self) -> bool:
        """監視中かどうかを返します。

        Returns:
            監視中ならTrue
        """
        return self._file_observer.is_running()

    def get_teams(self) -> list[dict[str, Any]]:
        """チーム一覧を取得します。

        Returns:
            チーム情報の辞書リスト
        """
        return [team.to_dict() for team in self._teams.values()]

    def get_team_messages(self, team_name: str) -> list[dict[str, Any]]:
        """チームのメッセージを取得します。

        Args:
            team_name: チーム名

        Returns:
            メッセージの辞書リスト
        """
        messages = self._messages.get(team_name, [])
        return [msg.to_dict() for msg in messages]

    def get_team_tasks(self, team_name: str) -> list[dict[str, Any]]:
        """チームのタスクを取得します。

        Args:
            team_name: チーム名

        Returns:
            タスクの辞書リスト
        """
        tasks = self._tasks.get(team_name, [])
        return [task.to_dict() for task in tasks]

    def get_team_thinking(self, team_name: str) -> list[dict[str, Any]]:
        """チームの思考ログを取得します。

        Args:
            team_name: チーム名

        Returns:
            思考ログの辞書リスト
        """
        logs = self._thinking_logs.get(team_name, [])
        return [log.to_dict() for log in logs]

    def _on_team_created(self, team_name: str, path: Path) -> None:
        """チーム作成イベントを処理します。

        Args:
            team_name: チーム名
            path: チームディレクトリパス
        """
        team_info = load_team_config(path)
        if team_info:
            self._teams[team_name] = team_info
            self._messages[team_name] = load_team_messages(path)
            self._tasks[team_name] = load_team_tasks(team_name)

            self._broadcast(
                {
                    "type": "team_created",
                    "teamName": team_name,
                    "team": team_info.to_dict(),
                }
            )
            logger.info(f"Team created event processed: {team_name}")

    def _on_team_deleted(self, team_name: str, _path: Path) -> None:
        """チーム削除イベントを処理します。

        Args:
            team_name: チーム名
            _path: チームディレクトリパス
        """
        if team_name in self._teams:
            del self._teams[team_name]
        if team_name in self._messages:
            del self._messages[team_name]
        if team_name in self._tasks:
            del self._tasks[team_name]
        if team_name in self._thinking_logs:
            del self._thinking_logs[team_name]

        self._broadcast(
            {
                "type": "team_deleted",
                "teamName": team_name,
            }
        )
        logger.info(f"Team deleted event processed: {team_name}")

    def _on_config_changed(self, team_name: str, path: Path) -> None:
        """config.json変更イベントを処理します。

        Args:
            team_name: チーム名
            path: config.jsonパス
        """
        team_dir = path.parent
        team_info = load_team_config(team_dir)

        if team_info:
            self._teams[team_name] = team_info

            self._broadcast(
                {
                    "type": "team_updated",
                    "teamName": team_name,
                    "team": team_info.to_dict(),
                }
            )
            logger.debug(f"Config changed: {team_name}")

    def _on_inbox_changed(self, team_name: str, path: Path) -> None:
        """inbox変更イベントを処理します。

        Args:
            team_name: チーム名
            path: inboxファイルパス
        """
        team_dir = path.parent.parent
        messages = load_team_messages(team_dir)
        self._messages[team_name] = messages

        # 新しいメッセージのみを送信
        if messages:
            latest_message = messages[-1]
            self._broadcast(
                {
                    "type": "team_message",
                    "teamName": team_name,
                    "message": latest_message.to_dict(),
                }
            )

        logger.debug(f"Inbox changed: {team_name}")

    def _on_task_changed(self, team_name: str, _path: Path) -> None:
        """タスク変更イベントを処理します。

        Args:
            team_name: チーム名
            _path: タスクファイルパス
        """
        tasks = load_team_tasks(team_name)
        self._tasks[team_name] = tasks

        self._broadcast(
            {
                "type": "tasks_updated",
                "teamName": team_name,
                "tasks": [task.to_dict() for task in tasks],
            }
        )
        logger.debug(f"Tasks changed: {team_name}")

    def _start_thinking_polling(self) -> None:
        """思考ログポーリングを開始します。

        注意: この機能はファイルベースの思考ログを使用するため、
        ThinkingLogHandlerを通じてファイルから思考ログが読み込まれます。
        """
        # 思考ログはThinkingLogHandlerを通じてファイルベースで処理されます
        logger.debug("Thinking polling is now file-based")

    def _capture_thinking(self) -> None:
        """思考ログをキャプチャします。

        注意: 思考ログはファイルベースのThinkingLogHandlerを通じて処理されます。
        """
        pass

    def _broadcast(self, data: dict[str, Any]) -> None:
        """更新を全コールバックに通知します。

        Args:
            data: 送信するデータ
        """
        for callback in self._update_callbacks:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Broadcast callback error: {e}")
