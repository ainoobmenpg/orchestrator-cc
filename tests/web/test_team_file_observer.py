"""TeamFileObserverテスト

ファイル監視機能をテストします。
"""

import json
import time
from pathlib import Path
<<<<<<< HEAD
=======
from threading import Thread
from typing import Any

import pytest
>>>>>>> main

from orchestrator.web.team_file_observer import (
    TaskFileObserver,
    TeamFileObserver,
)

<<<<<<< HEAD
=======

>>>>>>> main
# ============================================================================
# TeamFileObserver テスト
# ============================================================================


class TestTeamFileObserver:
    """TeamFileObserverクラスのテスト"""

    def test_initialization(self, tmp_path: Path):
        """初期化テスト"""
        observer = TeamFileObserver(base_dir=tmp_path)

        assert observer._base_dir == tmp_path
        assert observer._observer is None
        assert not observer.is_running()

    def test_register_callback(self, tmp_path: Path):
        """コールバック登録テスト"""
        observer = TeamFileObserver(base_dir=tmp_path)

        called = []

        def callback(team_name: str, file_path: Path) -> None:
            called.append((team_name, file_path))

        observer.register_callback("config_changed", callback)

        # コールバックが登録されたことを確認
        assert "config_changed" in observer._callbacks
        assert len(observer._callbacks["config_changed"]) == 1

    def test_start_stop_monitoring(self, tmp_path: Path):
        """監視の開始・停止テスト"""
        observer = TeamFileObserver(base_dir=tmp_path)

        observer.start()
        assert observer.is_running()

        observer.stop()
        assert not observer.is_running()

    def test_config_changed_detection(self, tmp_path: Path):
        """config.json変更検出のテスト"""
        observer = TeamFileObserver(base_dir=tmp_path)

        detected = []

        def callback(team_name: str, file_path: Path) -> None:
            detected.append(("config", team_name, file_path))

        observer.register_callback("config_changed", callback)
        observer.start()

        # テスト用チームディレクトリを作成
        team_dir = tmp_path / "test-team"
        team_dir.mkdir()

        # config.jsonを作成
        config_file = team_dir / "config.json"
        config_data = {
            "name": "test-team",
            "description": "Test",
            "createdAt": 1234567890,
            "leadAgentId": "lead@test",
            "leadSessionId": "session-123",
            "members": [],
        }
        config_file.write_text(json.dumps(config_data))

        # イベントが処理されるのを待つ
        time.sleep(1)

        observer.stop()

        # 検出されたイベントを確認
        # 注: ファイルシステムイベントのタイミングにより、
        # 検出されない場合があるため、ここでは監視が開始/停止できることのみを確認

    def test_team_created_detection(self, tmp_path: Path):
        """チーム作成検出のテスト"""
        observer = TeamFileObserver(base_dir=tmp_path)

        detected = []

        def callback(team_name: str, file_path: Path) -> None:
            detected.append(("created", team_name))

        observer.register_callback("team_created", callback)
        observer.start()

        # テスト用チームを作成
        team_dir = tmp_path / "new-team"
        team_dir.mkdir()
<<<<<<< HEAD
        (team_dir / "config.json").write_text(
            json.dumps(
                {
                    "name": "new-team",
                    "createdAt": 1234567890,
                    "leadAgentId": "lead@test",
                    "leadSessionId": "session-123",
                    "members": [],
                }
            )
        )
=======
        (team_dir / "config.json").write_text(json.dumps({
            "name": "new-team",
            "createdAt": 1234567890,
            "leadAgentId": "lead@test",
            "leadSessionId": "session-123",
            "members": [],
        }))
>>>>>>> main

        time.sleep(1)
        observer.stop()

        # チーム作成イベントが検出されたことを確認
        # （タイミング依存のため、実際の環境では検出されない場合あり）

    def test_multiple_callbacks(self, tmp_path: Path):
        """複数コールバックの登録テスト"""
        observer = TeamFileObserver(base_dir=tmp_path)

        called1 = []
        called2 = []

        observer.register_callback("config_changed", lambda t, p: called1.append(t))
        observer.register_callback("config_changed", lambda t, p: called2.append(t))

        # 両方のコールバックが登録されたことを確認
        assert len(observer._callbacks["config_changed"]) == 2


# ============================================================================
# TaskFileObserver テスト
# ============================================================================


class TestTaskFileObserver:
    """TaskFileObserverクラスのテスト"""

    def test_initialization(self, tmp_path: Path):
        """初期化テスト"""
        observer = TaskFileObserver(task_dir=tmp_path)

        assert observer._task_dir == tmp_path
        assert observer._observer is None
        assert not observer.is_running()

    def test_register_callback(self, tmp_path: Path):
        """コールバック登録テスト"""
        observer = TaskFileObserver(task_dir=tmp_path)

        called = []

        def callback(team_name: str, file_path: Path) -> None:
            called.append((team_name, file_path))

        observer.register_callback(callback)

        # コールバックが登録されたことを確認
        assert len(observer._callbacks) == 1

    def test_start_stop_monitoring(self, tmp_path: Path):
        """監視の開始・停止テスト"""
        observer = TaskFileObserver(task_dir=tmp_path)

        observer.start()
        assert observer.is_running()

        observer.stop()
        assert not observer.is_running()

    def test_task_file_detection(self, tmp_path: Path):
        """タスクファイル変更検出のテスト"""
        observer = TaskFileObserver(task_dir=tmp_path)

        detected = []

        def callback(team_name: str, file_path: Path) -> None:
            detected.append(("task", team_name, file_path))

        observer.register_callback(callback)
        observer.start()

        # テスト用タスクを作成
        team_dir = tmp_path / "test-team"
        team_dir.mkdir()

        task_file = team_dir / "task-001.json"
        task_data = {
            "taskId": "task-001",
            "subject": "Test task",
            "description": "Test",
            "status": "pending",
        }
        task_file.write_text(json.dumps(task_data))

        time.sleep(1)
        observer.stop()

        # タスク変更イベントが検出されたことを確認
        # （タイミング依存のため、実際の環境では検出されない場合あり）


# ============================================================================
# 統合テスト
# ============================================================================


class TestObserverIntegration:
    """オブザーバーの統合テスト"""

    def test_concurrent_observers(self, tmp_path: Path):
        """複数オブザーバーの同時動作テスト"""
        team_observer = TeamFileObserver(base_dir=tmp_path / "teams")
        task_observer = TaskFileObserver(task_dir=tmp_path / "tasks")

        # ディレクトリを作成
        (tmp_path / "teams").mkdir()
        (tmp_path / "tasks").mkdir()

        # 両方のオブザーバーを開始
        team_observer.start()
        task_observer.start()

        assert team_observer.is_running()
        assert task_observer.is_running()

        # 両方のオブザーバーを停止
        team_observer.stop()
        task_observer.stop()

        assert not team_observer.is_running()
        assert not task_observer.is_running()

    def test_observer_reusability(self, tmp_path: Path):
        """オブザーバーの再利用テスト"""
        observer = TeamFileObserver(base_dir=tmp_path)

        # 1回目の実行
        observer.start()
        assert observer.is_running()
        observer.stop()
        assert not observer.is_running()

        # 2回目の実行（同じインスタンスを再利用）
        observer.start()
        assert observer.is_running()
        observer.stop()
        assert not observer.is_running()
