"""YAMLファイル監視モジュール

このモジュールでは、YAMLファイルの変更を監視して
コールバックを呼び出す機能を提供します。
"""

import asyncio
from pathlib import Path
from typing import Awaitable, Callable

from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer


class YAMLFileHandler(FileSystemEventHandler):
    """YAMLファイル変更イベントハンドラ

    YAMLファイルの変更を検出してコールバックを呼び出します。
    """

    def __init__(
        self,
        callback: Callable[[str], Awaitable[None] | None],
        filter_pattern: str = ".yaml",
    ) -> None:
        """YAMLFileHandlerを初期化します。

        Args:
            callback: ファイル変更時に呼び出されるコールバック関数
            filter_pattern: 監視するファイルのパターン（デフォルト: ".yaml"）
        """
        self.callback = callback
        self.filter_pattern = filter_pattern

    def on_modified(self, event: FileSystemEvent) -> None:
        """ファイル変更イベントを処理します。

        Args:
            event: ファイルシステムイベント
        """
        if not event.is_directory and self.filter_pattern in event.src_path:
            # コールバックが非同期か同期的かを判定
            result = self.callback(event.src_path)
            if asyncio.iscoroutine(result):
                # 非同期コールバックの場合はイベントループで実行
                loop = asyncio.get_event_loop()
                loop.create_task(result)  # type: ignore[arg-type]


class YAMLMonitor:
    """YAMLファイル監視クラス

    指定されたディレクトリ内のYAMLファイルを監視し、
    変更が検出されたときにコールバックを呼び出します。
    """

    def __init__(
        self,
        watch_dir: str | Path,
        callback: Callable[[str], Awaitable[None] | None],
        filter_pattern: str = ".yaml",
    ) -> None:
        """YAMLMonitorを初期化します。

        Args:
            watch_dir: 監視するディレクトリパス
            callback: ファイル変更時に呼び出されるコールバック関数
            filter_pattern: 監視するファイルのパターン（デフォルト: ".yaml"）
        """
        self._watch_dir = Path(watch_dir)
        self._callback = callback
        self._filter_pattern = filter_pattern
        self._observer: Observer | None = None

    def start(self) -> None:
        """監視を開始します。

        Note:
            このメソッドはブロックしません。監視は別スレッドで実行されます。
        """
        # ディレクトリが存在しない場合は作成
        self._watch_dir.mkdir(parents=True, exist_ok=True)

        # オブザーバーを作成
        self._observer = Observer()
        handler = YAMLFileHandler(self._callback, self._filter_pattern)
        self._observer.schedule(
            handler, str(self._watch_dir), recursive=False
        )
        self._observer.start()

    def stop(self) -> None:
        """監視を停止します。"""
        if self._observer is not None:
            self._observer.stop()
            self._observer.join()
            self._observer = None

    def is_running(self) -> bool:
        """監視が実行中か確認します。

        Returns:
            実行中の場合True、それ以外の場合False
        """
        return self._observer is not None and self._observer.is_alive()

    async def watch_async(
        self,
        check_interval: float = 1.0,
        stop_condition: Callable[[], bool] | None = None,
    ) -> None:
        """非同期で監視を実行します。

        Args:
            check_interval: 監視状態のチェック間隔（秒）
            stop_condition: 停止条件を返す関数（オプション）
        """
        self.start()

        try:
            while self.is_running():
                await asyncio.sleep(check_interval)

                if stop_condition is not None and stop_condition():
                    break
        finally:
            self.stop()


class MultiPathYAMLMonitor:
    """複数パスのYAMLファイル監視クラス

    複数のディレクトリやファイルを同時に監視します。
    """

    def __init__(
        self,
        watch_paths: list[str | Path],
        callback: Callable[[str], Awaitable[None] | None],
        filter_pattern: str = ".yaml",
    ) -> None:
        """MultiPathYAMLMonitorを初期化します。

        Args:
            watch_paths: 監視するパスのリスト（ディレクトリまたはファイル）
            callback: ファイル変更時に呼び出されるコールバック関数
            filter_pattern: 監視するファイルのパターン（デフォルト: ".yaml"）
        """
        self._watch_paths = [Path(p) for p in watch_paths]
        self._callback = callback
        self._filter_pattern = filter_pattern
        self._monitors: list[YAMLMonitor] = []

    def start_all(self) -> None:
        """全てのパスの監視を開始します。"""
        for watch_path in self._watch_paths:
            if watch_path.is_dir():
                monitor = YAMLMonitor(watch_path, self._callback, self._filter_pattern)
            else:
                # 単一ファイルの場合は親ディレクトリを監視
                monitor = YAMLMonitor(
                    watch_path.parent,
                    self._callback,
                    watch_path.name,
                )
            monitor.start()
            self._monitors.append(monitor)

    def stop_all(self) -> None:
        """全ての監視を停止します。"""
        for monitor in self._monitors:
            monitor.stop()
        self._monitors.clear()

    def is_running(self) -> bool:
        """いずれかの監視が実行中か確認します。

        Returns:
            いずれかが実行中の場合True、全て停止している場合False
        """
        return any(m.is_running() for m in self._monitors)

    async def watch_async(
        self,
        check_interval: float = 1.0,
        stop_condition: Callable[[], bool] | None = None,
    ) -> None:
        """非同期で監視を実行します。

        Args:
            check_interval: 監視状態のチェック間隔（秒）
            stop_condition: 停止条件を返す関数（オプション）
        """
        self.start_all()

        try:
            while self.is_running():
                await asyncio.sleep(check_interval)

                if stop_condition is not None and stop_condition():
                    break
        finally:
            self.stop_all()
