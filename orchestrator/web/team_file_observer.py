"""Agent Teamsファイル監視ユーティリティ

このモジュールでは、Agent Teams関連のファイルを監視する機能を提供します。
"""

import logging
import threading
import time
from collections.abc import Callable
from pathlib import Path

from watchdog.events import (
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer

logger = logging.getLogger(__name__)


class TeamFileObserver:
    """チームファイル監視クラス

    Agent Teams関連のファイルシステム変更を監視します。

    Attributes:
        _base_dir: 監視対象のベースディレクトリ
        _callbacks: ファイル変更コールバックの辞書
        _observer: watchdog Observerインスタンス
    """

    def __init__(self, base_dir: Path | str = Path.home() / ".claude" / "teams"):
        """TeamFileObserverを初期化します。

        Args:
            base_dir: 監視対象のベースディレクトリ
        """
        self._base_dir = Path(base_dir)
        self._callbacks: dict[str, list[Callable[[str, Path], None]]] = {
            "config_changed": [],
            "inbox_changed": [],
            "task_changed": [],
            "team_created": [],
            "team_deleted": [],
        }
        self._observer: Observer | None = None
        self._lock = threading.Lock()

    def register_callback(
        self, event_type: str, callback: Callable[[str, Path], None]
    ) -> None:
        """ファイル変更コールバックを登録します。

        Args:
            event_type: イベントタイプ（config_changed, inbox_changed, task_changed, team_created, team_deleted）
            callback: コールバック関数（引数: team_name, file_path）
        """
        with self._lock:
            if event_type in self._callbacks:
                self._callbacks[event_type].append(callback)
            else:
                logger.warning(f"Unknown event type: {event_type}")

    def start(self) -> None:
        """ファイル監視を開始します。"""
        if self._observer is not None:
            logger.warning("Observer is already running")
            return

        handler = _TeamFileEventHandler(self._callbacks)
        self._observer = Observer()
        self._observer.schedule(handler, str(self._base_dir), recursive=True)
        self._observer.start()
        logger.info(f"Team file observer started: {self._base_dir}")

    def stop(self) -> None:
        """ファイル監視を停止します。"""
        if self._observer is None:
            return

        self._observer.stop()
        self._observer.join()
        self._observer = None
        logger.info("Team file observer stopped")

    def is_running(self) -> bool:
        """監視中かどうかを返します。

        Returns:
            監視中ならTrue
        """
        return self._observer is not None and self._observer.is_alive()


class _TeamFileEventHandler(FileSystemEventHandler):
    """チームファイルイベントハンドラー

    Attributes:
        _callbacks: イベントコールバックの辞書
    """

    def __init__(self, callbacks: dict[str, list[Callable[[str, Path], None]]]):
        """イベントハンドラーを初期化します。

        Args:
            callbacks: コールバックの辞書
        """
        super().__init__()
        self._callbacks = callbacks
        self._last_event_time: dict[str, float] = {}
        self._debounce_interval = 0.5  # デバウンス間隔（秒）

    def on_created(self, event: FileCreatedEvent) -> None:
        """ファイル作成イベントを処理します。

        Args:
            event: ファイル作成イベント
        """
        if event.is_directory:
            self._handle_team_created(event.src_path)
        else:
            self._handle_file_change("created", event.src_path)

    def on_modified(self, event: FileModifiedEvent) -> None:
        """ファイル変更イベントを処理します。

        Args:
            event: ファイル変更イベント
        """
        if not event.is_directory:
            self._handle_file_change("modified", event.src_path)

    def on_deleted(self, event: FileDeletedEvent) -> None:
        """ファイル削除イベントを処理します。

        Args:
            event: ファイル削除イベント
        """
        if event.is_directory:
            self._handle_team_deleted(event.src_path)

    def _handle_team_created(self, dir_path: str) -> None:
        """チーム作成を処理します。

        Args:
            dir_path: ディレクトリパス
        """
        path = Path(dir_path)
        team_name = path.name

        # チームディレクトリか確認（config.jsonの存在をチェック）
        if (path / "config.json").exists():
            logger.info(f"Team detected: {team_name}")
            self._invoke_callbacks("team_created", team_name, path)

    def _handle_team_deleted(self, dir_path: str) -> None:
        """チーム削除を処理します。

        Args:
            dir_path: ディレクトリパス
        """
        path = Path(dir_path)
        team_name = path.name
        logger.info(f"Team deleted: {team_name}")
        self._invoke_callbacks("team_deleted", team_name, path)

    def _handle_file_change(self, _change_type: str, file_path: str) -> None:
        """ファイル変更を処理します。

        Args:
            _change_type: 変更タイプ（created, modified）
            file_path: ファイルパス
        """
        path = Path(file_path)

        # デバウンス処理
        current_time = time.time()
        last_time = self._last_event_time.get(file_path, 0)

        if current_time - last_time < self._debounce_interval:
            return

        self._last_event_time[file_path] = current_time

        # ファイルパスからチーム名とファイル種別を判定
        parts = path.relative_to(Path.home() / ".claude" / "teams").parts

        if len(parts) < 2:
            return

        team_name = parts[0]

        # config.jsonの変更
        if path.name == "config.json":
            logger.debug(f"Config changed: {team_name}")
            self._invoke_callbacks("config_changed", team_name, path)
            return

        # inboxの変更
        if "inboxes" in parts:
            logger.debug(f"Inbox changed: {team_name}")
            self._invoke_callbacks("inbox_changed", team_name, path)
            return

    def _invoke_callbacks(
        self, event_type: str, team_name: str, file_path: Path
    ) -> None:
        """コールバックを呼び出します。

        Args:
            event_type: イベントタイプ
            team_name: チーム名
            file_path: ファイルパス
        """
        callbacks = self._callbacks.get(event_type, [])
        for callback in callbacks:
            try:
                callback(team_name, file_path)
            except Exception as e:
                logger.error(
                    f"Callback error for {event_type} in {team_name}: {e}"
                )


class TaskFileObserver:
    """タスクファイル監視クラス

    ~/.claude/tasks/ ディレクトリを監視します。

    Attributes:
        _task_dir: タスクディレクトリ
        _callbacks: タスク変更コールバックのリスト
        _observer: watchdog Observerインスタンス
    """

    def __init__(self, task_dir: Path | str = Path.home() / ".claude" / "tasks"):
        """TaskFileObserverを初期化します。

        Args:
            task_dir: タスクディレクトリ
        """
        self._task_dir = Path(task_dir)
        self._callbacks: list[Callable[[str, Path], None]] = []
        self._observer: Observer | None = None
        self._lock = threading.Lock()

    def register_callback(self, callback: Callable[[str, Path], None]) -> None:
        """タスク変更コールバックを登録します。

        Args:
            callback: コールバック関数（引数: team_name, file_path）
        """
        with self._lock:
            self._callbacks.append(callback)

    def start(self) -> None:
        """ファイル監視を開始します。"""
        if self._observer is not None:
            logger.warning("Task observer is already running")
            return

        handler = _TaskFileEventHandler(self._callbacks)
        self._observer = Observer()
        self._observer.schedule(handler, str(self._task_dir), recursive=True)
        self._observer.start()
        logger.info(f"Task file observer started: {self._task_dir}")

    def stop(self) -> None:
        """ファイル監視を停止します。"""
        if self._observer is None:
            return

        self._observer.stop()
        self._observer.join()
        self._observer = None
        logger.info("Task file observer stopped")

    def is_running(self) -> bool:
        """監視中かどうかを返します。

        Returns:
            監視中ならTrue
        """
        return self._observer is not None and self._observer.is_alive()


class _TaskFileEventHandler(FileSystemEventHandler):
    """タスクファイルイベントハンドラー

    Attributes:
        _callbacks: コールバックのリスト
    """

    def __init__(self, callbacks: list[Callable[[str, Path], None]]):
        """イベントハンドラーを初期化します。

        Args:
            callbacks: コールバックのリスト
        """
        super().__init__()
        self._callbacks = callbacks
        self._last_event_time: dict[str, float] = {}
        self._debounce_interval = 0.5

    def on_created(self, event: FileCreatedEvent) -> None:
        """ファイル作成イベントを処理します。"""
        if not event.is_directory:
            self._handle_task_change(event.src_path)

    def on_modified(self, event: FileModifiedEvent) -> None:
        """ファイル変更イベントを処理します。"""
        if not event.is_directory:
            self._handle_task_change(event.src_path)

    def _handle_task_change(self, file_path: str) -> None:
        """タスク変更を処理します。

        Args:
            file_path: ファイルパス
        """
        path = Path(file_path)

        if not path.name.endswith(".json"):
            return

        # デバウンス処理
        current_time = time.time()
        last_time = self._last_event_time.get(file_path, 0)

        if current_time - last_time < self._debounce_interval:
            return

        self._last_event_time[file_path] = current_time

        # パスからチーム名を取得
        try:
            parts = path.relative_to(Path.home() / ".claude" / "tasks").parts
            if len(parts) >= 1:
                team_name = parts[0]
                logger.debug(f"Task changed: {team_name}")
                for callback in self._callbacks:
                    try:
                        callback(team_name, path)
                    except Exception as e:
                        logger.error(f"Task callback error: {e}")
        except ValueError:
            pass
