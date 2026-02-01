"""TmuxSessionManagerのテスト

このモジュールでは、TmuxSessionManagerクラスの単体テストを実装します。
"""

import subprocess
from unittest.mock import patch

import pytest

from orchestrator.core.tmux_session_manager import (
    TmuxCommandError,
    TmuxSessionManager,
    TmuxSessionNotFoundError,
    TmuxTimeoutError,
)


class TestTmuxSessionManagerInit:
    """TmuxSessionManager初期化処理のテスト"""

    def test_init_with_valid_name(self):
        """有効なセッション名で初期化できる"""
        manager = TmuxSessionManager("test-session")
        assert manager._session_name == "test-session"
        assert manager._window_index == 0
        assert manager._next_pane_index == 0

    def test_init_with_empty_name(self):
        """空文字列でValueErrorが送出される"""
        with pytest.raises(ValueError, match="セッション名は空であってはなりません"):
            TmuxSessionManager("")

    def test_init_with_invalid_characters(self):
        """無効な文字でValueErrorが送出される"""
        invalid_names = ["test session", "test.session", "test@session", "test/session"]
        for name in invalid_names:
            with pytest.raises(ValueError, match="セッション名は英数字"):
                TmuxSessionManager(name)

    def test_init_with_hyphen_and_underscore(self):
        """ハイフンとアンダースコアを含む名前で初期化できる"""
        manager = TmuxSessionManager("test-session_123")
        assert manager._session_name == "test-session_123"

    def test_init_with_default_window_index(self):
        """デフォルトのウィンドウインデックスは0"""
        manager = TmuxSessionManager("test-session")
        assert manager._window_index == 0

    def test_init_with_custom_window_index(self):
        """カスタムのウィンドウインデックスを設定できる"""
        manager = TmuxSessionManager("test-session", window_index=2)
        assert manager._window_index == 2


class TestTmuxSessionManagerCreateSession:
    """セッション作成のテスト"""

    def test_create_session_success(self):
        """セッションが正常に作成される"""
        manager = TmuxSessionManager("test-create-success")
        try:
            manager.create_session()
            assert manager.session_exists() is True
        finally:
            # クリーンアップ
            if manager.session_exists():
                manager.kill_session()

    def test_create_session_already_exists(self):
        """既存セッションでRuntimeErrorが送出される"""
        manager = TmuxSessionManager("test-already-exists")
        try:
            manager.create_session()
            with pytest.raises(RuntimeError, match="既に存在します"):
                manager.create_session()
        finally:
            if manager.session_exists():
                manager.kill_session()

    def test_create_session_sets_initial_pane_count(self):
        """セッション作成後のペイン数が1である"""
        manager = TmuxSessionManager("test-initial-panes")
        try:
            manager.create_session()
            assert manager.get_pane_count() == 1
            assert manager._next_pane_index == 0
        finally:
            if manager.session_exists():
                manager.kill_session()


class TestTmuxSessionManagerCreatePane:
    """ペイン作成のテスト"""

    def test_create_pane_horizontal_split(self):
        """水平分割でペインが作成される"""
        manager = TmuxSessionManager("test-horizontal-split")
        try:
            manager.create_session()
            initial_count = manager.get_pane_count()

            pane_index = manager.create_pane(split="h")

            assert pane_index == 0
            assert manager.get_pane_count() == initial_count + 1
            assert manager._next_pane_index == 1
        finally:
            if manager.session_exists():
                manager.kill_session()

    def test_create_pane_vertical_split(self):
        """垂直分割でペインが作成される"""
        manager = TmuxSessionManager("test-vertical-split")
        try:
            manager.create_session()
            initial_count = manager.get_pane_count()

            pane_index = manager.create_pane(split="v")

            assert pane_index == 0
            assert manager.get_pane_count() == initial_count + 1
        finally:
            if manager.session_exists():
                manager.kill_session()

    def test_create_pane_invalid_split(self):
        """無効な分割方向でValueErrorが送出される"""
        manager = TmuxSessionManager("test-invalid-split")
        try:
            manager.create_session()
            with pytest.raises(ValueError, match="splitは'h'または'v'でなければなりません"):
                manager.create_pane(split="x")
        finally:
            if manager.session_exists():
                manager.kill_session()

    def test_create_pane_increments_index(self):
        """ペインインデックスが正しく増加する"""
        manager = TmuxSessionManager("test-increment-index")
        try:
            manager.create_session()

            pane0 = manager.create_pane()
            assert pane0 == 0

            pane1 = manager.create_pane()
            assert pane1 == 1

            pane2 = manager.create_pane()
            assert pane2 == 2
        finally:
            if manager.session_exists():
                manager.kill_session()

    def test_create_pane_session_not_exists(self):
        """セッションがない場合RuntimeErrorが送出される"""
        manager = TmuxSessionManager("test-no-session-pane")
        with pytest.raises(TmuxSessionNotFoundError, match="が存在しません"):
            manager.create_pane()


class TestTmuxSessionManagerSendKeys:
    """キー送信のテスト"""

    def test_send_keys_success(self):
        """キー送信が成功する"""
        manager = TmuxSessionManager("test-send-keys")
        try:
            manager.create_session()
            # 例外が送出されなければ成功
            manager.send_keys(0, "echo hello")
        finally:
            if manager.session_exists():
                manager.kill_session()

    def test_send_keys_invalid_pane_index(self):
        """負のインデックスでValueErrorが送出される"""
        manager = TmuxSessionManager("test-invalid-index-send")
        try:
            manager.create_session()
            with pytest.raises(ValueError, match="pane_indexは0以上でなければなりません"):
                manager.send_keys(-1, "test")
        finally:
            if manager.session_exists():
                manager.kill_session()

    def test_send_keys_session_not_exists(self):
        """セッションがない場合RuntimeErrorが送出される"""
        manager = TmuxSessionManager("test-no-session-send")
        with pytest.raises(TmuxSessionNotFoundError, match="が存在しません"):
            manager.send_keys(0, "test")

    def test_send_keys_with_special_characters(self):
        """特殊文字を含むキー送信が成功する"""
        manager = TmuxSessionManager("test-special-chars")
        try:
            manager.create_session()
            # 特殊文字を含むコマンド
            manager.send_keys(0, 'echo "hello $HOME"')
            # 例外が送出されなければ成功
        finally:
            if manager.session_exists():
                manager.kill_session()


class TestTmuxSessionManagerCapturePane:
    """出力キャプチャのテスト"""

    def test_capture_pane_success(self):
        """出力キャプチャが成功する"""
        manager = TmuxSessionManager("test-capture")
        try:
            manager.create_session()
            output = manager.capture_pane(0)
            assert isinstance(output, str)
            assert len(output) > 0
        finally:
            if manager.session_exists():
                manager.kill_session()

    def test_capture_pane_returns_string(self):
        """文字列が返される"""
        manager = TmuxSessionManager("test-return-string")
        try:
            manager.create_session()
            output = manager.capture_pane(0)
            assert isinstance(output, str)
        finally:
            if manager.session_exists():
                manager.kill_session()

    def test_capture_pane_invalid_pane_index(self):
        """負のインデックスでValueErrorが送出される"""
        manager = TmuxSessionManager("test-invalid-index-capture")
        try:
            manager.create_session()
            with pytest.raises(ValueError, match="pane_indexは0以上でなければなりません"):
                manager.capture_pane(-1)
        finally:
            if manager.session_exists():
                manager.kill_session()

    def test_capture_pane_session_not_exists(self):
        """セッションがない場合RuntimeErrorが送出される"""
        manager = TmuxSessionManager("test-no-session-capture")
        with pytest.raises(TmuxSessionNotFoundError, match="が存在しません"):
            manager.capture_pane(0)

    def test_capture_pane_contains_sent_text(self):
        """送信したテキストが出力に含まれる"""
        manager = TmuxSessionManager("test-contains-text")
        try:
            manager.create_session()
            test_text = "unique-test-string-xyz"
            manager.send_keys(0, f"echo {test_text}")

            # 少し待ってからキャプチャ（コマンド実行を待つ）
            import time
            time.sleep(0.2)

            output = manager.capture_pane(0)
            assert test_text in output
        finally:
            if manager.session_exists():
                manager.kill_session()

    def test_capture_pane_with_start_line(self):
        """開始行を指定してキャプチャできる"""
        manager = TmuxSessionManager("test-start-line")
        try:
            manager.create_session()
            # 複数行の出力を生成
            for i in range(5):
                manager.send_keys(0, f"echo line-{i}")

            import time
            time.sleep(0.2)

            # 後ろから3行目からキャプチャ
            output = manager.capture_pane(0, start_line=-3)
            assert isinstance(output, str)
        finally:
            if manager.session_exists():
                manager.kill_session()

    def test_capture_pane_with_end_line(self):
        """終了行を指定してキャプチャできる"""
        manager = TmuxSessionManager("test-end-line")
        try:
            manager.create_session()
            manager.send_keys(0, "echo test")

            import time
            time.sleep(0.2)

            # 先頭から10行目までキャプチャ
            output = manager.capture_pane(0, end_line=+10)
            assert isinstance(output, str)
        finally:
            if manager.session_exists():
                manager.kill_session()

    def test_capture_pane_with_both_limits(self):
        """開始行と終了行の両方を指定してキャプチャできる"""
        manager = TmuxSessionManager("test-both-limits")
        try:
            manager.create_session()
            manager.send_keys(0, "echo test")

            import time
            time.sleep(0.2)

            # 開始行と終了行の両方を指定
            output = manager.capture_pane(0, start_line=-5, end_line=+10)
            assert isinstance(output, str)
        finally:
            if manager.session_exists():
                manager.kill_session()


class TestTmuxSessionManagerKillSession:
    """セッション破棄のテスト"""

    def test_kill_session_success(self):
        """セッション破棄が成功する"""
        manager = TmuxSessionManager("test-kill-success")
        manager.create_session()
        assert manager.session_exists() is True

        manager.kill_session()
        assert manager.session_exists() is False

    def test_kill_session_not_exists(self):
        """セッションがない場合RuntimeErrorが送出される"""
        manager = TmuxSessionManager("test-kill-no-exists")
        with pytest.raises(TmuxSessionNotFoundError, match="が存在しません"):
            manager.kill_session()

    def test_kill_session_verified(self):
        """破棄後にセッションが存在しない"""
        manager = TmuxSessionManager("test-kill-verified")
        manager.create_session()
        manager.kill_session()
        assert manager.session_exists() is False


class TestTmuxSessionManagerHelperMethods:
    """ヘルパーメソッドのテスト"""

    def test_session_exists_true(self):
        """存在するセッションでTrueが返される"""
        manager = TmuxSessionManager("test-exists-true")
        try:
            manager.create_session()
            assert manager.session_exists() is True
        finally:
            if manager.session_exists():
                manager.kill_session()

    def test_session_exists_false(self):
        """存在しないセッションでFalseが返される"""
        manager = TmuxSessionManager("test-exists-false-nonexistent")
        assert manager.session_exists() is False

    def test_get_pane_count(self):
        """正しいペイン数が返される"""
        manager = TmuxSessionManager("test-pane-count")
        try:
            manager.create_session()
            assert manager.get_pane_count() == 1

            manager.create_pane()
            assert manager.get_pane_count() == 2

            manager.create_pane()
            assert manager.get_pane_count() == 3
        finally:
            if manager.session_exists():
                manager.kill_session()

    def test_get_pane_count_after_create(self):
        """ペイン作成後に数が増加する"""
        manager = TmuxSessionManager("test-count-after-create")
        try:
            manager.create_session()
            initial = manager.get_pane_count()

            manager.create_pane()
            assert manager.get_pane_count() == initial + 1

            manager.create_pane()
            assert manager.get_pane_count() == initial + 2
        finally:
            if manager.session_exists():
                manager.kill_session()


class TestTmuxSessionManagerErrorHandling:
    """エラーハンドリングのテスト"""

    @patch("subprocess.run")
    def test_tmux_command_error_raised_on_failure(self, mock_run):
        """tmuxコマンド失敗時TmuxCommandErrorが送出される"""
        # subprocess.runをモックしてCalledProcessErrorを投げる
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "tmux", stderr="invalid option"
        )

        manager = TmuxSessionManager("test-command-error")

        with pytest.raises(TmuxCommandError, match="tmuxコマンドが失敗しました"):
            manager._run_tmux_command(["--invalid-option"])

    @patch("subprocess.run")
    def test_tmux_timeout_error_raised_on_timeout(self, mock_run):
        """コマンドタイムアウト時TmuxTimeoutErrorが送出される"""
        # subprocess.runをモックしてTimeoutExpiredを投げる
        mock_run.side_effect = subprocess.TimeoutExpired("tmux", 10)

        manager = TmuxSessionManager("test-timeout-error")

        with pytest.raises(TmuxTimeoutError, match="tmuxコマンドがタイムアウトしました"):
            manager._run_tmux_command(["--timeout-option"])

    @patch("subprocess.run")
    def test_tmux_not_installed(self, mock_run):
        """tmuxがインストールされていない場合TmuxCommandErrorが送出される"""
        # subprocess.runをモックしてFileNotFoundErrorを投げる
        mock_run.side_effect = FileNotFoundError

        manager = TmuxSessionManager("test-no-tmux")

        with pytest.raises(TmuxCommandError, match="tmuxがインストールされていません"):
            manager._run_tmux_command(["has-session", "-t", "test"])
