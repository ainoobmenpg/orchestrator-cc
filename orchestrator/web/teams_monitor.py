"""Agent Teams監視モジュール

このモジュールでは、Agent Teamsの監視と可視化を行うTeamsMonitorクラスを提供します。
"""

import logging
<<<<<<< HEAD
=======
import threading
>>>>>>> main
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any

<<<<<<< HEAD
=======
from orchestrator.core.tmux_session_manager import TmuxSessionManager
>>>>>>> main
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
<<<<<<< HEAD
        _thinking_polling_active: 思考ログポーリング中フラグ（現在は未使用）
=======
        _tmux_manager: tmuxセッションマネージャー（オプション）
        _thinking_polling_active: 思考ログポーリング中フラグ
>>>>>>> main
    """

    def __init__(self, tmux_session_name: str | None = None):
        """TeamsMonitorを初期化します。

        Args:
<<<<<<< HEAD
            tmux_session_name: この引数は互換性のために残されていますが、
                              現在は使用されていません（ファイルベースの思考ログを使用）。
=======
            tmux_session_name: tmuxセッション名（指定すると思考ログキャプチャを有効化）
>>>>>>> main
        """
        self._teams: dict[str, TeamInfo] = {}
        self._messages: dict[str, list[TeamMessage]] = defaultdict(list)
        self._tasks: dict[str, list[TaskInfo]] = defaultdict(list)
        self._thinking_logs: dict[str, list[ThinkingLog]] = defaultdict(list)
        self._file_observer = TeamFileObserver()
        self._task_observer = TaskFileObserver()
        self._update_callbacks: list[Callable[[dict[str, Any]], None]] = []
<<<<<<< HEAD
        self._thinking_polling_active = False
        self._thinking_polling_interval = 2.0  # 秒

        # tmux_session_name引数は互換性のために残されていますが、使用しません
        if tmux_session_name:
            logger.debug(
                f"tmux_session_name '{tmux_session_name}' was provided but is not used "
                "(thinking logs are now file-based)"
            )
=======
        self._tmux_manager: TmuxSessionManager | None = None
        self._thinking_polling_active = False
        self._thinking_polling_interval = 2.0  # 秒

        if tmux_session_name:
            try:
                self._tmux_manager = TmuxSessionManager(tmux_session_name)
                logger.info(f"TmuxSessionManager initialized: {tmux_session_name}")
            except Exception as e:
                logger.warning(f"Failed to initialize TmuxSessionManager: {e}")
>>>>>>> main

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

<<<<<<< HEAD
    def register_update_callback(self, callback: Callable[[dict[str, Any]], None]) -> None:
=======
    def register_update_callback(
        self, callback: Callable[[dict[str, Any]], None]
    ) -> None:
>>>>>>> main
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

<<<<<<< HEAD
        # 思考ログポーリングはファイルベースに移行したため開始しない
        # （tmux依存削除）
=======
        # 思考ログポーリングを開始（tmuxマネージャーがある場合）
        if self._tmux_manager:
            self._start_thinking_polling()
>>>>>>> main

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

<<<<<<< HEAD
            self._broadcast(
                {
                    "type": "team_created",
                    "teamName": team_name,
                    "team": team_info.to_dict(),
                }
            )
=======
            self._broadcast({
                "type": "team_created",
                "teamName": team_name,
                "team": team_info.to_dict(),
            })
>>>>>>> main
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

<<<<<<< HEAD
        self._broadcast(
            {
                "type": "team_deleted",
                "teamName": team_name,
            }
        )
=======
        self._broadcast({
            "type": "team_deleted",
            "teamName": team_name,
        })
>>>>>>> main
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

<<<<<<< HEAD
            self._broadcast(
                {
                    "type": "team_updated",
                    "teamName": team_name,
                    "team": team_info.to_dict(),
                }
            )
=======
            self._broadcast({
                "type": "team_updated",
                "teamName": team_name,
                "team": team_info.to_dict(),
            })
>>>>>>> main
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
<<<<<<< HEAD
            self._broadcast(
                {
                    "type": "team_message",
                    "teamName": team_name,
                    "message": latest_message.to_dict(),
                }
            )
=======
            self._broadcast({
                "type": "team_message",
                "teamName": team_name,
                "message": latest_message.to_dict(),
            })
>>>>>>> main

        logger.debug(f"Inbox changed: {team_name}")

    def _on_task_changed(self, team_name: str, _path: Path) -> None:
        """タスク変更イベントを処理します。

        Args:
            team_name: チーム名
            _path: タスクファイルパス
        """
        tasks = load_team_tasks(team_name)
        self._tasks[team_name] = tasks

<<<<<<< HEAD
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
        tmuxへの依存は削除されています。ThinkingLogHandlerを通じて
        ファイルから思考ログが読み込まれます。
        """
        # tmuxへの依存削除により、このメソッドは何もしません
        # 思考ログはThinkingLogHandlerを通じてファイルベースで処理されます
        logger.debug("Thinking polling is now file-based (tmux dependency removed)")

    def _capture_thinking(self) -> None:
        """思考ログをキャプチャします。

        注意: tmux依存は削除されました。思考ログはファイルベースの
        ThinkingLogHandlerを通じて処理されます。
        """
        # tmuxへの依存削除により、このメソッドは何もしません
        pass
=======
        self._broadcast({
            "type": "tasks_updated",
            "teamName": team_name,
            "tasks": [task.to_dict() for task in tasks],
        })
        logger.debug(f"Tasks changed: {team_name}")

    def _start_thinking_polling(self) -> None:
        """思考ログポーリングを開始します。"""

        def poll_loop():
            self._thinking_polling_active = True

            while self._thinking_polling_active:
                try:
                    self._capture_thinking()
                except Exception as e:
                    logger.error(f"Thinking capture error: {e}")

                import time
                time.sleep(self._thinking_polling_interval)

        thread = threading.Thread(target=poll_loop, daemon=True)
        thread.start()
        logger.info("Thinking polling started")

    def _capture_thinking(self) -> None:
        """tmuxペインから思考ログをキャプチャします。"""
        if not self._tmux_manager:
            return

        for team_name, team_info in self._teams.items():
            try:
                for member in team_info.members:
                    # ペイン番号を取得（メタデータ等から推定）
                    # ここでは簡易的にメンバー名からマッピング
                    pane_index = self._get_pane_index_for_member(team_name, member)

                    if pane_index is not None:
                        # 最近の100行を取得
                        output = self._tmux_manager.capture_pane(
                            pane_index, start_line=-100
                        )

                        # 思考ログをパース
                        logs = ThinkingLog.from_pane_output(member.name, output)

                        # 新しいログのみを追加
                        existing_contents = {
                            log.content for log in self._thinking_logs[team_name]
                        }

                        for log in logs:
                            if log.content not in existing_contents:
                                self._thinking_logs[team_name].append(log)

                                # ブロードキャスト
                                self._broadcast({
                                    "type": "thinking_log",
                                    "teamName": team_name,
                                    "log": log.to_dict(),
                                })

            except Exception as e:
                logger.debug(f"Failed to capture thinking for {team_name}: {e}")

    def _get_pane_index_for_member(
        self, _team_name: str, member
    ) -> int | None:
        """メンバーに対応するペイン番号を取得します。

        Args:
            _team_name: チーム名
            member: チームメンバー

        Returns:
            ペイン番号、不明な場合はNone
        """
        # 現在の実装では固定のマッピングを使用
        # 将来的にはconfig.json等から取得可能にする
        member_pane_map = {
            "team-lead": 0,
            "researcher": 1,
            "coder": 2,
            "tester": 3,
        }

        return member_pane_map.get(member.name)
>>>>>>> main

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
