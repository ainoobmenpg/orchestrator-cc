"""YAMLファイル監視モジュール

このモジュールでは、YAMLファイルの変更を監視する機能を提供します。
watchdogを使用してファイルシステムイベントを監視します。
"""

import logging
import threading
import time
from collections.abc import Callable
from pathlib import Path

from watchdog.events import FileCreatedEvent, FileModifiedEvent, FileSystemEventHandler
from watchdog.observers import Observer

from orchestrator.core.yaml_protocol import TaskMessage

logger = logging.getLogger(__name__)


class YAMLFileHandler(FileSystemEventHandler):
    """YAMLファイルイベントハンドラー

    YAMLファイルの作成・変更イベントを検知し、コールバックを呼び出します。
    """

    def __init__(
        self,
        on_file_changed: Callable[[Path], None],
        debounce_seconds: float = 0.5,
    ) -> None:
        """YAMLFileHandlerを初期化します。

        Args:
            on_file_changed: ファイル変更時のコールバック関数
            debounce_seconds: デバウンス時間（秒）。同じファイルの連続したイベントをまとめる
        """
        self._on_file_changed = on_file_changed
        self._debounce_seconds = debounce_seconds
        self._last_event_time: dict[str, float] = {}
        self._lock = threading.Lock()

    def on_created(self, event: FileCreatedEvent) -> None:
        """ファイル作成イベントを処理します。

        Args:
            event: ファイル作成イベント
        """
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if not self._is_yaml_file(file_path):
            return

        self._handle_event(file_path)

    def on_modified(self, event: FileModifiedEvent) -> None:
        """ファイル変更イベントを処理します。

        Args:
            event: ファイル変更イベント
        """
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if not self._is_yaml_file(file_path):
            return

        self._handle_event(file_path)

    def _is_yaml_file(self, file_path: Path) -> bool:
        """YAMLファイルかどうかを判定します。

        Args:
            file_path: ファイルパス

        Returns:
            YAMLファイルの場合True
        """
        return file_path.suffix in (".yaml", ".yml")

    def _handle_event(self, file_path: Path) -> None:
        """ファイルイベントを処理します（デバウンス付き）。

        Args:
            file_path: ファイルパス
        """
        file_key = str(file_path)
        current_time = time.time()

        with self._lock:
            last_time = self._last_event_time.get(file_key, 0)
            if current_time - last_time < self._debounce_seconds:
                # デバウンス期間内の場合は無視
                return

            self._last_event_time[file_key] = current_time

        logger.info(f"YAMLファイル変更を検知: {file_path}")
        self._on_file_changed(file_path)


class YAMLMonitor:
    """YAMLファイル監視クラス

    指定されたディレクトリ内のYAMLファイルの変更を監視し、
    変更時にコールバックを呼び出します。
    """

    def __init__(
        self,
        queue_dir: Path,
        notification_callback: Callable[[TaskMessage, Path], None],
        debounce_seconds: float = 0.5,
    ) -> None:
        """YAMLMonitorを初期化します。

        Args:
            queue_dir: 監視するディレクトリパス
            notification_callback: メッセージ検知時のコールバック関数
                                (TaskMessage, ファイルパス) を引数に取る
            debounce_seconds: デバウンス時間（秒）
        """
        self._queue_dir = Path(queue_dir)
        self._notification_callback = notification_callback
        self._debounce_seconds = debounce_seconds

        # ディレクトリの存在確認
        if not self._queue_dir.exists():
            raise FileNotFoundError(f"監視ディレクトリが存在しません: {self._queue_dir}")

        if not self._queue_dir.is_dir():
            raise NotADirectoryError(f"監視パスはディレクトリである必要があります: {self._queue_dir}")

        # オブザーバーとハンドラー
        self._observer: Observer | None = None
        self._handler: YAMLFileHandler | None = None

    def _on_file_changed(self, file_path: Path) -> None:
        """ファイル変更時のコールバック

        YAMLファイルを読み込み、通知コールバックを呼び出します。

        Args:
            file_path: 変更されたファイルパス
        """
        try:
            # YAMLファイルを読み込み
            message = TaskMessage.from_file(file_path)
            logger.info(
                f"メッセージを検知: {message.from_agent} -> {message.to_agent} "
                f"(type={message.type}, status={message.status})"
            )

            # 通知コールバックを呼び出し
            self._notification_callback(message, file_path)
        except FileNotFoundError:
            logger.warning(f"ファイルが見つかりません（既に削除された可能性があります）: {file_path}")
        except Exception as e:
            logger.error(f"ファイル変更の処理中にエラーが発生しました: {e}")

    def start(self) -> None:
        """監視を開始します。

        Raises:
            RuntimeError: 既に監視が開始されている場合
        """
        if self._observer is not None:
            raise RuntimeError("監視は既に開始されています")

        logger.info(f"YAML監視を開始します: {self._queue_dir}")

        # ハンドラーを作成
        self._handler = YAMLFileHandler(
            on_file_changed=self._on_file_changed,
            debounce_seconds=self._debounce_seconds,
        )

        # オブザーバーを作成して開始
        self._observer = Observer()
        self._observer.schedule(self._handler, str(self._queue_dir), recursive=False)
        self._observer.start()

    def stop(self) -> None:
        """監視を停止します。"""
        if self._observer is None:
            return

        logger.info("YAML監視を停止します")

        self._observer.stop()
        self._observer.join()
        self._observer = None
        self._handler = None

    def is_running(self) -> bool:
        """監視が実行中かどうかを確認します。

        Returns:
            実行中の場合True
        """
        return self._observer is not None and self._observer.is_alive()

    def __enter__(self) -> "YAMLMonitor":
        """コンテキストマネージャーとして使用する場合のエントリー"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        """コンテキストマネージャーとして使用する場合のイグジット"""
        self.stop()


class StatusMonitor:
    """ステータスファイル監視クラス

    status/agents/ディレクトリ内のステータスYAMLファイルの変更を監視し、
    ダッシュボード更新のコールバックを呼び出します。
    """

    def __init__(
        self,
        status_dir: Path,
        update_callback: Callable[[], None],
        debounce_seconds: float = 0.5,
    ) -> None:
        """StatusMonitorを初期化します。

        Args:
            status_dir: 監視するステータスディレクトリパス
            update_callback: ステータス更新時のコールバック関数
            debounce_seconds: デバウンス時間（秒）
        """
        self._status_dir = Path(status_dir)
        self._update_callback = update_callback
        self._debounce_seconds = debounce_seconds

        # ディレクトリの存在確認
        if not self._status_dir.exists():
            raise FileNotFoundError(f"ステータスディレクトリが存在しません: {self._status_dir}")

        if not self._status_dir.is_dir():
            raise NotADirectoryError(
                f"ステータスパスはディレクトリである必要があります: {self._status_dir}"
            )

        # オブザーバーとハンドラー
        self._observer: Observer | None = None
        self._handler: YAMLFileHandler | None = None

    def start(self) -> None:
        """監視を開始します。

        Raises:
            RuntimeError: 既に監視が開始されている場合
        """
        if self._observer is not None:
            raise RuntimeError("監視は既に開始されています")

        logger.info(f"ステータス監視を開始します: {self._status_dir}")

        # ハンドラーを作成
        self._handler = YAMLFileHandler(
            on_file_changed=lambda _: self._update_callback(),
            debounce_seconds=self._debounce_seconds,
        )

        # オブザーバーを作成して開始
        self._observer = Observer()
        self._observer.schedule(self._handler, str(self._status_dir), recursive=True)
        self._observer.start()

    def stop(self) -> None:
        """監視を停止します。"""
        if self._observer is None:
            return

        logger.info("ステータス監視を停止します")

        self._observer.stop()
        self._observer.join()
        self._observer = None
        self._handler = None

    def is_running(self) -> bool:
        """監視が実行中かどうかを確認します。

        Returns:
            実行中の場合True
        """
        return self._observer is not None and self._observer.is_alive()

    def __enter__(self) -> "StatusMonitor":
        """コンテキストマネージャーとして使用する場合のエントリー"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        """コンテキストマネージャーとして使用する場合のイグジット"""
        self.stop()
