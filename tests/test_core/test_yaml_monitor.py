"""yaml_monitorモジュールのユニットテスト"""

import tempfile
from pathlib import Path
from threading import Thread
from time import sleep
from typing import Callable
from unittest.mock import Mock

import pytest

from orchestrator.core.yaml_monitor import (
    StatusMonitor,
    YAMLFileHandler,
    YAMLMonitor,
)


class TestYAMLFileHandler:
    """YAMLFileHandlerクラスのテスト"""

    def test_init(self) -> None:
        """初期化テスト"""
        callback: Callable[[Path], None] = Mock()
        handler = YAMLFileHandler(on_file_changed=callback)

        assert handler._on_file_changed is callback
        assert handler._debounce_seconds == 0.5

    def test_init_with_custom_debounce(self) -> None:
        """カスタムデバウンス時間での初期化テスト"""
        callback: Callable[[Path], None] = Mock()
        handler = YAMLFileHandler(on_file_changed=callback, debounce_seconds=1.0)

        assert handler._debounce_seconds == 1.0

    def test_on_created_yaml_file(self, tmp_path: Path) -> None:
        """YAMLファイル作成イベントのテスト"""
        callback = Mock()
        handler = YAMLFileHandler(on_file_changed=callback, debounce_seconds=0.1)

        # YAMLファイルを作成
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("test: content")

        # イベントをシミュレート
        from watchdog.events import FileCreatedEvent

        event = FileCreatedEvent(str(yaml_file))
        handler.on_created(event)

        # 少し待機してデバウンスを通過させる
        sleep(0.2)

        # コールバックが呼ばれたことを確認
        callback.assert_called_once_with(yaml_file)

    def test_on_modified_yaml_file(self, tmp_path: Path) -> None:
        """YAMLファイル変更イベントのテスト"""
        callback = Mock()
        handler = YAMLFileHandler(on_file_changed=callback, debounce_seconds=0.1)

        # YAMLファイルを作成
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("test: content")

        # イベントをシミュレート
        from watchdog.events import FileModifiedEvent

        event = FileModifiedEvent(str(yaml_file))
        handler.on_modified(event)

        # 少し待機してデバウンスを通過させる
        sleep(0.2)

        # コールバックが呼ばれたことを確認
        callback.assert_called_once_with(yaml_file)

    def test_ignores_non_yaml_files(self, tmp_path: Path) -> None:
        """非YAMLファイルを無視するテスト"""
        callback = Mock()
        handler = YAMLFileHandler(on_file_changed=callback, debounce_seconds=0.1)

        # 非YAMLファイルを作成
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("not yaml")

        # イベントをシミュレート
        from watchdog.events import FileCreatedEvent

        event = FileCreatedEvent(str(txt_file))
        handler.on_created(event)

        sleep(0.2)

        # コールバックが呼ばれていないことを確認
        callback.assert_not_called()

    def test_ignores_directory_events(self, tmp_path: Path) -> None:
        """ディレクトリイベントを無視するテスト"""
        callback = Mock()
        handler = YAMLFileHandler(on_file_changed=callback, debounce_seconds=0.1)

        # ディレクトリを作成
        dir_path = tmp_path / "test_dir"
        dir_path.mkdir()

        # イベントをシミュレート
        from watchdog.events import DirCreatedEvent

        event = DirCreatedEvent(str(dir_path))
        handler.on_created(event)

        sleep(0.2)

        # コールバックが呼ばれていないことを確認
        callback.assert_not_called()

    def test_debounce_rapid_events(self, tmp_path: Path) -> None:
        """連続イベントのデバウンステスト"""
        callback = Mock()
        handler = YAMLFileHandler(on_file_changed=callback, debounce_seconds=0.3)

        # YAMLファイルを作成
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text("test: content")

        from watchdog.events import FileModifiedEvent

        # 連続してイベントを発火
        for _ in range(3):
            handler.on_modified(FileModifiedEvent(str(yaml_file)))

        # デバウンス期間待機
        sleep(0.5)

        # 1回のみ呼ばれるべき（デバウンス効果）
        assert callback.call_count == 1


class TestYAMLMonitor:
    """YAMLMonitorクラスのテスト"""

    def test_init(self, tmp_path: Path) -> None:
        """初期化テスト"""
        queue_dir = tmp_path / "queue"
        queue_dir.mkdir()

        callback: Callable[[Path], None] = Mock()
        monitor = YAMLMonitor(queue_dir=queue_dir, notification_callback=callback)

        assert monitor._queue_dir == queue_dir
        assert monitor._notification_callback is callback

    def test_init_nonexistent_directory(self) -> None:
        """存在しないディレクトリでの初期化テスト"""
        callback: Callable[[Path], None] = Mock()

        with pytest.raises(FileNotFoundError):
            YAMLMonitor(
                queue_dir=Path("/nonexistent/directory"),
                notification_callback=callback,
            )

    def test_init_file_path(self, tmp_path: Path) -> None:
        """ファイルパスでの初期化テスト"""
        file_path = tmp_path / "file.txt"
        file_path.write_text("test")

        callback: Callable[[Path], None] = Mock()

        with pytest.raises(NotADirectoryError):
            YAMLMonitor(queue_dir=file_path, notification_callback=callback)

    def test_start_and_stop(self, tmp_path: Path) -> None:
        """開始・停止テスト"""
        queue_dir = tmp_path / "queue"
        queue_dir.mkdir()

        callback: Callable[[Path], None] = Mock()
        monitor = YAMLMonitor(queue_dir=queue_dir, notification_callback=callback)

        # 開始
        monitor.start()
        assert monitor.is_running()

        # 停止
        monitor.stop()
        assert not monitor.is_running()

    def test_start_already_started(self, tmp_path: Path) -> None:
        """既に開始されている状態での開始テスト"""
        queue_dir = tmp_path / "queue"
        queue_dir.mkdir()

        callback: Callable[[Path], None] = Mock()
        monitor = YAMLMonitor(queue_dir=queue_dir, notification_callback=callback)

        monitor.start()

        with pytest.raises(RuntimeError):
            monitor.start()

        monitor.stop()

    def test_context_manager(self, tmp_path: Path) -> None:
        """コンテキストマネージャーテスト"""
        queue_dir = tmp_path / "queue"
        queue_dir.mkdir()

        callback: Callable[[Path], None] = Mock()

        with YAMLMonitor(queue_dir=queue_dir, notification_callback=callback) as monitor:
            assert monitor.is_running()

        # コンテキスト終了後に停止している
        assert not monitor.is_running()

    def test_file_change_detection(self, tmp_path: Path) -> None:
        """ファイル変更検知テスト"""
        queue_dir = tmp_path / "queue"
        queue_dir.mkdir()

        callback = Mock()

        monitor = YAMLMonitor(
            queue_dir=queue_dir,
            notification_callback=callback,
            debounce_seconds=0.1,
        )
        monitor.start()

        try:
            # YAMLファイルを作成
            yaml_file = queue_dir / "test.yaml"
            yaml_file.write_text("""id: msg-001
from: grand_boss
to: middle_manager
type: task
status: pending
content: テストタスク
timestamp: 2026-02-01T10:00:00
""")

            # 少し待機してオブザーバーがイベントを処理するのを待つ
            sleep(0.5)

            # コールバックが呼ばれたことを確認
            callback.assert_called()

        finally:
            monitor.stop()

    def test_on_file_changed_with_valid_yaml(self, tmp_path: Path) -> None:
        """有効なYAMLファイルでの変更時コールバックテスト"""
        from orchestrator.core.yaml_protocol import TaskMessage

        queue_dir = tmp_path / "queue"
        queue_dir.mkdir()

        callback = Mock()

        monitor = YAMLMonitor(queue_dir=queue_dir, notification_callback=callback)

        # 有効なYAMLファイルを作成
        yaml_file = queue_dir / "test.yaml"
        valid_yaml = """
id: msg-001
from: grand_boss
to: middle_manager
type: task
status: pending
content: テストタスク
timestamp: 2026-02-01T10:00:00
"""
        yaml_file.write_text(valid_yaml)

        # ファイル変更イベントをシミュレート
        monitor._on_file_changed(yaml_file)

        # コールバックがTaskMessageと共に呼ばれたことを確認
        callback.assert_called_once()
        args = callback.call_args[0]
        assert isinstance(args[0], TaskMessage)
        assert args[1] == yaml_file

    def test_on_file_changed_with_invalid_yaml(self, tmp_path: Path, caplog) -> None:
        """無効なYAMLファイルでの変更時コールバックテスト"""
        import logging

        queue_dir = tmp_path / "queue"
        queue_dir.mkdir()

        callback = Mock()

        monitor = YAMLMonitor(queue_dir=queue_dir, notification_callback=callback)

        # 無効なYAMLファイルを作成
        yaml_file = queue_dir / "test.yaml"
        yaml_file.write_text("invalid yaml content [[")

        # ファイル変更イベントをシミュレート
        with caplog.at_level(logging.ERROR):
            monitor._on_file_changed(yaml_file)

        # コールバックが呼ばれていないことを確認
        callback.assert_not_called()


class TestStatusMonitor:
    """StatusMonitorクラスのテスト"""

    def test_init(self, tmp_path: Path) -> None:
        """初期化テスト"""
        status_dir = tmp_path / "status"
        status_dir.mkdir()

        callback: Callable[[], None] = Mock()
        monitor = StatusMonitor(status_dir=status_dir, update_callback=callback)

        assert monitor._status_dir == status_dir
        assert monitor._update_callback is callback

    def test_start_and_stop(self, tmp_path: Path) -> None:
        """開始・停止テスト"""
        status_dir = tmp_path / "status"
        status_dir.mkdir()

        callback: Callable[[], None] = Mock()
        monitor = StatusMonitor(status_dir=status_dir, update_callback=callback)

        # 開始
        monitor.start()
        assert monitor.is_running()

        # 停止
        monitor.stop()
        assert not monitor.is_running()

    def test_context_manager(self, tmp_path: Path) -> None:
        """コンテキストマネージャーテスト"""
        status_dir = tmp_path / "status"
        status_dir.mkdir()

        callback: Callable[[], None] = Mock()

        with StatusMonitor(status_dir=status_dir, update_callback=callback) as monitor:
            assert monitor.is_running()

        assert not monitor.is_running()
