"""思考ログハンドラーモジュール

このモジュールでは、Agent Teamsからの思考ログを収集・配信する機能を提供します。
"""

import json
import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from watchdog.events import (
    DirCreatedEvent,
    DirModifiedEvent,
    FileCreatedEvent,
    FileModifiedEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer
from watchdog.observers.api import BaseObserver

logger = logging.getLogger(__name__)


@dataclass
class ThinkingLogEntry:
    """思考ログエントリ

    Attributes:
        agent_name: エージェント名
        content: 内容
        timestamp: タイムスタンプ
        category: カテゴリ
        emotion: 感情タイプ
        team_name: チーム名
    """

    agent_name: str
    content: str
    timestamp: str
    category: str = "thinking"
    emotion: str = "neutral"
    team_name: str = ""

    def to_dict(self) -> dict[str, Any]:
        """辞書に変換します。"""
        return {
            "agentName": self.agent_name,
            "content": self.content,
            "timestamp": self.timestamp,
            "category": self.category,
            "emotion": self.emotion,
            "teamName": self.team_name,
        }


class ThinkingLogHandler:
    """思考ログハンドラー

    Agent Teamsから送信される思考ログを収集・配信します。

    Attributes:
        _logs: チームごとの思考ログ
        _callbacks: 更新コールバックのリスト
        _observer: watchdog Observerインスタンス
        _log_dir: ログディレクトリ
    """

    def __init__(self, log_dir: Path | str | None = None):
        """ThinkingLogHandlerを初期化します。

        Args:
            log_dir: ログディレクトリ（指定しない場合はデフォルトを使用）
        """
        if log_dir is None:
            log_dir = Path.home() / ".claude" / "thinking-logs"

        self._logs: dict[str, list[ThinkingLogEntry]] = {}
        self._callbacks: list[Callable[[dict[str, Any]], None]] = []
        self._observer: BaseObserver | None = None
        self._log_dir = Path(log_dir)
        self._lock = threading.Lock()

        # ログディレクトリを作成
        self._log_dir.mkdir(parents=True, exist_ok=True)

        # 既存のログを読み込み
        self._load_existing_logs()

    def _load_existing_logs(self) -> None:
        """既存のログを読み込みます。"""
        if not self._log_dir.exists():
            return

        for log_file in self._log_dir.glob("*.jsonl"):
            try:
                with open(log_file, encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            entry = ThinkingLogEntry(
                                agent_name=data.get("agentName", ""),
                                content=data.get("content", ""),
                                timestamp=data.get("timestamp", ""),
                                category=data.get("category", "thinking"),
                                emotion=data.get("emotion", "neutral"),
                                team_name=data.get("teamName", ""),
                            )
                            team_name = entry.team_name or "default"
                            if team_name not in self._logs:
                                self._logs[team_name] = []
                            self._logs[team_name].append(entry)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to load log file {log_file}: {e}")

    def register_callback(self, callback: Callable[[dict[str, Any]], None]) -> None:
        """更新コールバックを登録します。

        Args:
            callback: コールバック関数（思考ログデータを辞書で受け取る）
        """
        with self._lock:
            self._callbacks.append(callback)

    def start_monitoring(self) -> None:
        """ログ監視を開始します。"""
        if self._observer is not None:
            logger.warning("Thinking log observer is already running")
            return

        handler = _ThinkingLogEventHandler(self._on_log_entry)
        self._observer = Observer()
        self._observer.schedule(handler, str(self._log_dir), recursive=True)
        self._observer.start()
        logger.info(f"Thinking log monitoring started: {self._log_dir}")

    def stop_monitoring(self) -> None:
        """ログ監視を停止します。"""
        if self._observer is None:
            return

        self._observer.stop()
        self._observer.join()
        self._observer = None
        logger.info("Thinking log monitoring stopped")

    def is_running(self) -> bool:
        """監視中かどうかを返します。

        Returns:
            監視中ならTrue
        """
        return self._observer is not None and self._observer.is_alive()

    def get_logs(self, team_name: str) -> list[dict[str, Any]]:
        """チームの思考ログを取得します。

        Args:
            team_name: チーム名

        Returns:
            思考ログの辞書リスト
        """
        logs = self._logs.get(team_name, [])
        return [log.to_dict() for log in logs]

    def add_log(self, entry: ThinkingLogEntry) -> None:
        """思考ログを追加します。

        Args:
            entry: 思考ログエントリ
        """
        team_name = entry.team_name or "default"

        with self._lock:
            if team_name not in self._logs:
                self._logs[team_name] = []

            # 重複チェック
            existing_contents = {log.content for log in self._logs[team_name]}
            if entry.content not in existing_contents:
                self._logs[team_name].append(entry)

                # ログファイルに書き込み
                self._write_log_to_file(entry)

                # コールバックを呼び出し
                for callback in self._callbacks:
                    try:
                        callback({
                            "type": "thinking_log",
                            "teamName": team_name,
                            "log": entry.to_dict(),
                        })
                    except Exception as e:
                        logger.error(f"Thinking log callback error: {e}")

    def _write_log_to_file(self, entry: ThinkingLogEntry) -> None:
        """ログをファイルに書き込みます。

        Args:
            entry: 思考ログエントリ
        """
        team_name = entry.team_name or "default"
        log_file = self._log_dir / f"{team_name}.jsonl"

        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
        except OSError as e:
            logger.error(f"Failed to write log to file: {e}")

    def _on_log_entry(self, entry: ThinkingLogEntry) -> None:
        """ログエントリを処理します。

        Args:
            entry: 思考ログエントリ
        """
        self.add_log(entry)


class _ThinkingLogEventHandler(FileSystemEventHandler):
    """思考ログファイルイベントハンドラー

    Attributes:
        _on_log_entry: ログエントリコールバック
    """

    def __init__(self, on_log_entry: Callable[[ThinkingLogEntry], None]):
        """イベントハンドラーを初期化します。

        Args:
            on_log_entry: ログエントリコールバック
        """
        super().__init__()
        self._on_log_entry = on_log_entry
        self._last_event_time: dict[str, float] = {}
        self._debounce_interval = 0.5

    def on_created(self, event: FileCreatedEvent | DirCreatedEvent) -> None:
        """ファイル作成イベントを処理します。"""
        if not event.is_directory:
            self._handle_log_file(str(event.src_path))

    def on_modified(self, event: FileModifiedEvent | DirModifiedEvent) -> None:
        """ファイル変更イベントを処理します。"""
        if not event.is_directory:
            self._handle_log_file(str(event.src_path))

    def _handle_log_file(self, file_path: str) -> None:
        """ログファイルを処理します。

        Args:
            file_path: ファイルパス
        """
        path = Path(file_path)

        if not path.name.endswith(".jsonl"):
            return

        # デバウンス処理
        current_time = time.time()
        last_time = self._last_event_time.get(file_path, 0)

        if current_time - last_time < self._debounce_interval:
            return

        self._last_event_time[file_path] = current_time

        # 新しいエントリを読み込み
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        entry = ThinkingLogEntry(
                            agent_name=data.get("agentName", ""),
                            content=data.get("content", ""),
                            timestamp=data.get("timestamp", ""),
                            category=data.get("category", "thinking"),
                            emotion=data.get("emotion", "neutral"),
                            team_name=data.get("teamName", ""),
                        )
                        self._on_log_entry(entry)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Failed to read log file {path}: {e}")


# シングルトンインスタンス
_thinking_log_handler: ThinkingLogHandler | None = None
_handler_lock = threading.Lock()


def get_thinking_log_handler() -> ThinkingLogHandler:
    """思考ログハンドラーのシングルトンインスタンスを取得します。

    Returns:
        ThinkingLogHandlerインスタンス
    """
    global _thinking_log_handler

    with _handler_lock:
        if _thinking_log_handler is None:
            _thinking_log_handler = ThinkingLogHandler()
        return _thinking_log_handler


def send_thinking_log(
    agent_name: str,
    content: str,
    team_name: str = "default",
    category: str = "thinking",
    emotion: str = "neutral",
) -> None:
    """思考ログを送信します。

    この関数は、エージェントから呼び出されて思考ログを記録します。

    Args:
        agent_name: エージェント名
        content: 思考内容
        team_name: チーム名
        category: カテゴリ
        emotion: 感情タイプ
    """
    handler = get_thinking_log_handler()

    entry = ThinkingLogEntry(
        agent_name=agent_name,
        content=content,
        timestamp=datetime.now().isoformat(),
        category=category,
        emotion=emotion,
        team_name=team_name,
    )

    handler.add_log(entry)
