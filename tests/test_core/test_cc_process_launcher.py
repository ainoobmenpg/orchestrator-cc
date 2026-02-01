"""CCProcessLauncherのテスト

このモジュールでは、CCProcessLauncherクラスの単体テストを実装します。
"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from orchestrator.core.cc_process_launcher import (
    INITIAL_TIMEOUT,
    CCPersonalityPromptNotFoundError,
    CCPersonalityPromptReadError,
    CCProcessLauncher,
    CCProcessLaunchError,
    CCProcessNotRunningError,
)
from orchestrator.core.cc_process_models import CCProcessConfig, CCProcessRole
from orchestrator.core.pane_io import PaneTimeoutError
from orchestrator.core.tmux_session_manager import TmuxSessionManager


class TestCCProcessLauncherInit:
    """CCProcessLauncher初期化処理のテスト"""

    def test_init_with_valid_params(self):
        """有効なパラメータで初期化できる"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="config/personalities/test.txt",
            marker="TEST OK",
            pane_index=0,
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)

        assert launcher._config is config
        assert launcher._pane_index == 0
        assert launcher._tmux is mock_tmux
        assert launcher._running is False
        assert launcher._restart_count == 0

    def test_init_with_invalid_tmux_manager_raises_type_error(self):
        """無効なtmux_managerでTypeErrorが送出される"""
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="config/personalities/test.txt",
            marker="TEST OK",
            pane_index=0,
        )

        with pytest.raises(TypeError, match="TmuxSessionManagerのインスタンス"):
            CCProcessLauncher(config, 0, "not_a_manager")  # type: ignore[arg-type]

    def test_init_with_negative_pane_index_raises_value_error(self):
        """負のpane_indexでValueErrorが送出される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="config/personalities/test.txt",
            marker="TEST OK",
            pane_index=0,
        )

        with pytest.raises(ValueError, match="pane_indexは0以上"):
            CCProcessLauncher(config, -1, mock_tmux)

    def test_init_stores_config_reference(self):
        """configが正しく保存される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="config/personalities/test.txt",
            marker="TEST OK",
            pane_index=0,
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)

        assert launcher._config is config
        assert launcher._config.name == "test_agent"


class TestCCProcessLauncherLoadPrompt:
    """性格プロンプト読み込みのテスト"""

    def test_load_prompt_with_absolute_path(self, tmp_path):
        """絶対パスで読み込みが成功する"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path=str(tmp_path / "test.txt"),
            marker="TEST OK",
            pane_index=0,
        )

        # テストファイルを作成
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test personality prompt", encoding="utf-8")

        launcher = CCProcessLauncher(config, 0, mock_tmux)

        prompt = launcher._load_personality_prompt()

        assert prompt == "Test personality prompt"

    def test_load_prompt_with_relative_path(self, tmp_path):
        """相対パスで読み込みが成功する"""
        mock_tmux = Mock(spec=TmuxSessionManager)

        # カレントディレクトリにテストファイルを作成
        test_file = Path.cwd() / "test_prompt.txt"
        test_file.write_text("Relative path prompt", encoding="utf-8")

        try:
            config = CCProcessConfig(
                name="test_agent",
                role=CCProcessRole.GRAND_BOSS,
                personality_prompt_path="test_prompt.txt",
                marker="TEST OK",
                pane_index=0,
            )

            launcher = CCProcessLauncher(config, 0, mock_tmux)

            prompt = launcher._load_personality_prompt()

            assert prompt == "Relative path prompt"
        finally:
            # クリーンアップ
            if test_file.exists():
                test_file.unlink()

    def test_load_prompt_file_not_found_raises_error(self):
        """ファイル不存在でCCPersonalityPromptNotFoundErrorが送出される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="/nonexistent/path.txt",
            marker="TEST OK",
            pane_index=0,
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)

        with pytest.raises(
            CCPersonalityPromptNotFoundError, match="性格プロンプトファイルが見つかりません"
        ):
            launcher._load_personality_prompt()

    def test_load_prompt_path_is_directory_raises_error(self, tmp_path):
        """パスがディレクトリの場合にエラーが送出される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path=str(tmp_path),  # ディレクトリ
            marker="TEST OK",
            pane_index=0,
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)

        with pytest.raises(
            CCPersonalityPromptNotFoundError, match="性格プロンプトがファイルではありません"
        ):
            launcher._load_personality_prompt()

    def test_load_prompt_read_error_raises_cc_personality_prompt_read_error(self, tmp_path):
        """読み込みエラーでCCPersonalityPromptReadErrorが送出される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path=str(tmp_path / "test.txt"),
            marker="TEST OK",
            pane_index=0,
        )

        # 読み取り不可のファイルを作成
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content", encoding="utf-8")

        # パーミッションを変更して読み取り不可にする（Unix系のみ）
        try:
            test_file.chmod(0o000)

            launcher = CCProcessLauncher(config, 0, mock_tmux)

            with pytest.raises(
                CCPersonalityPromptReadError, match="性格プロンプトファイルの読み込みに失敗しました"
            ):
                launcher._load_personality_prompt()
        finally:
            # クリーンアップ（パーミッションを戻して削除）
            try:
                test_file.chmod(0o644)
                test_file.unlink()
            except Exception:
                pass

    def test_load_prompt_content_is_stripped(self, tmp_path):
        """内容の先頭・末尾の空白が除去される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path=str(tmp_path / "test.txt"),
            marker="TEST OK",
            pane_index=0,
        )

        # 前後に空白を含むファイルを作成
        test_file = tmp_path / "test.txt"
        test_file.write_text("  \n\nTest prompt\n  \n", encoding="utf-8")

        launcher = CCProcessLauncher(config, 0, mock_tmux)

        prompt = launcher._load_personality_prompt()

        assert prompt == "Test prompt"


class TestCCProcessLauncherStart:
    """プロセス起動のテスト"""

    @pytest.mark.asyncio
    async def test_start_success(self):
        """正常起動でis_running()がTrueになる"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="config/personalities/test.txt",
            marker="TEST OK",
            pane_index=0,
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)

        # モックの設定
        with patch.object(launcher, "_load_personality_prompt", return_value="Test prompt"):
            launcher._pane_io.get_response = AsyncMock(return_value="Response with TEST OK")

            await launcher.start()

            assert launcher.is_running() is True
            launcher._pane_io.get_response.assert_called_once_with(
                0, "TEST OK", timeout=INITIAL_TIMEOUT
            )

    @pytest.mark.asyncio
    async def test_start_calls_send_keys(self):
        """send_keysが呼び出されることを確認"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="config/personalities/test.txt",
            marker="TEST OK",
            pane_index=0,
            work_dir="/tmp/test",
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)

        with patch.object(launcher, "_load_personality_prompt", return_value="Test prompt"):
            launcher._pane_io.get_response = AsyncMock(return_value="Response with TEST OK")

            await launcher.start()

            # send_keysが起動コマンドで呼ばれることを確認
            mock_tmux.send_keys.assert_called()
            call_args = mock_tmux.send_keys.call_args
            assert call_args[0][0] == 0  # pane_index
            assert "cd /tmp/test" in call_args[0][1]  # work_dirを含む

    @pytest.mark.asyncio
    async def test_start_waits_for_marker(self):
        """マーカー待機でget_responseが呼ばれることを確認"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="config/personalities/test.txt",
            marker="TEST OK",
            pane_index=0,
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)

        with patch.object(launcher, "_load_personality_prompt", return_value="Test prompt"):
            launcher._pane_io.get_response = AsyncMock(return_value="Response with TEST OK")

            await launcher.start()

            # get_responseがマーカー付きで呼ばれることを確認
            launcher._pane_io.get_response.assert_called_once_with(
                0, "TEST OK", timeout=INITIAL_TIMEOUT
            )

    @pytest.mark.asyncio
    async def test_start_sets_running_flag(self):
        """起動成功で_runningフラグがTrueになる"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="config/personalities/test.txt",
            marker="TEST OK",
            pane_index=0,
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)

        with patch.object(launcher, "_load_personality_prompt", return_value="Test prompt"):
            launcher._pane_io.get_response = AsyncMock(return_value="Response with TEST OK")

            await launcher.start()

            assert launcher._running is True

    @pytest.mark.skip(reason="プロンプト読み込み処理はまだ実装されていません")
    @pytest.mark.asyncio
    async def test_start_prompt_not_found_raises_error(self):
        """プロンプトファイル不在でエラーが送出される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="/nonexistent/path.txt",
            marker="TEST OK",
            pane_index=0,
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)

        with pytest.raises(CCPersonalityPromptNotFoundError):
            await launcher.start()

    @pytest.mark.asyncio
    async def test_start_timeout_raises_cc_process_launch_error(self):
        """タイムアウトでCCProcessLaunchErrorが送出される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="config/personalities/test.txt",
            marker="TEST OK",
            pane_index=0,
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)

        with patch.object(launcher, "_load_personality_prompt", return_value="Test prompt"):
            # タイムアウトさせる
            launcher._pane_io.get_response = AsyncMock(side_effect=PaneTimeoutError("Timeout"))

            with pytest.raises(
                CCProcessLaunchError, match="プロセスの初期化がタイムアウトしました"
            ):
                await launcher.start()

    @pytest.mark.asyncio
    async def test_start_when_already_running_does_nothing(self):
        """既に実行中の場合は何もしない"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="config/personalities/test.txt",
            marker="TEST OK",
            pane_index=0,
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)
        launcher._running = True

        # 既に実行中なので何も呼ばれない
        launcher._pane_io.get_response = AsyncMock(return_value="Response")

        await launcher.start()

        # get_responseは呼ばれない
        launcher._pane_io.get_response.assert_not_called()


class TestCCProcessLauncherIsRunning:
    """状態確認のテスト"""

    def test_is_running_after_start(self):
        """起動後にTrueを返す"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="config/personalities/test.txt",
            marker="TEST OK",
            pane_index=0,
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)
        launcher._running = True

        assert launcher.is_running() is True

    def test_is_running_initially(self):
        """初期状態でFalseを返す"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="config/personalities/test.txt",
            marker="TEST OK",
            pane_index=0,
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)

        assert launcher.is_running() is False

    def test_is_running_after_stop(self):
        """停止後にFalseを返す"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="config/personalities/test.txt",
            marker="TEST OK",
            pane_index=0,
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)
        launcher._running = True
        launcher._running = False

        assert launcher.is_running() is False


class TestCCProcessLauncherSendMessage:
    """メッセージ送信のテスト"""

    @pytest.mark.asyncio
    async def test_send_message_success(self):
        """正常送信で応答が返る"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="config/personalities/test.txt",
            marker="TEST OK",
            pane_index=0,
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)
        launcher._running = True

        launcher._pane_io.send_message = Mock()
        launcher._pane_io.get_response = AsyncMock(return_value="Test response")

        response = await launcher.send_message("Hello")

        assert response == "Test response"
        launcher._pane_io.send_message.assert_called_once_with(0, "Hello")

    @pytest.mark.asyncio
    async def test_send_message_empty_message_raises_value_error(self):
        """空メッセージでValueErrorが送出される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="config/personalities/test.txt",
            marker="TEST OK",
            pane_index=0,
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)
        launcher._running = True

        with pytest.raises(ValueError, match="messageは空であってはなりません"):
            await launcher.send_message("")

    @pytest.mark.asyncio
    async def test_send_message_not_running_raises_cc_process_not_running_error(self):
        """未起動状態でCCProcessNotRunningErrorが送出される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="config/personalities/test.txt",
            marker="TEST OK",
            pane_index=0,
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)
        launcher._running = False

        with pytest.raises(
            CCProcessNotRunningError, match="プロセス 'test_agent' は実行されていません"
        ):
            await launcher.send_message("Hello")

    @pytest.mark.asyncio
    async def test_send_message_timeout_raises_pane_timeout_error(self):
        """タイムアウトでPaneTimeoutErrorが送出される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="config/personalities/test.txt",
            marker="TEST OK",
            pane_index=0,
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)
        launcher._running = True

        launcher._pane_io.send_message = Mock()
        launcher._pane_io.get_response = AsyncMock(side_effect=PaneTimeoutError("Timeout"))

        with pytest.raises(PaneTimeoutError):
            await launcher.send_message("Hello")

    @pytest.mark.asyncio
    async def test_send_message_with_custom_timeout(self):
        """カスタムタイムアウトが使用されることを確認"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="config/personalities/test.txt",
            marker="TEST OK",
            pane_index=0,
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)
        launcher._running = True

        launcher._pane_io.send_message = Mock()
        launcher._pane_io.get_response = AsyncMock(return_value="Test response")

        await launcher.send_message("Hello", timeout=45.0)

        launcher._pane_io.get_response.assert_called_once_with(0, "TEST OK", timeout=45.0)


class TestCCProcessLauncherStop:
    """プロセス停止のテスト"""

    @pytest.mark.asyncio
    async def test_stop_success(self):
        """正常停止でis_running()がFalseになる"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="config/personalities/test.txt",
            marker="TEST OK",
            pane_index=0,
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)
        launcher._running = True

        await launcher.stop()

        assert launcher.is_running() is False
        mock_tmux.send_keys.assert_called_once_with(0, "C-c")

    @pytest.mark.asyncio
    async def test_stop_sends_ctrl_c(self):
        """Ctrl+Cが送信されることを確認"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="config/personalities/test.txt",
            marker="TEST OK",
            pane_index=0,
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)
        launcher._running = True

        await launcher.stop()

        mock_tmux.send_keys.assert_called_once_with(0, "C-c")

    @pytest.mark.asyncio
    async def test_stop_when_not_running_does_nothing(self):
        """未起動状態では何もしない"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="config/personalities/test.txt",
            marker="TEST OK",
            pane_index=0,
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)
        launcher._running = False

        await launcher.stop()

        # send_keysは呼ばれない
        mock_tmux.send_keys.assert_not_called()


class TestCCProcessLauncherBuildCommand:
    """コマンド構築のテスト"""

    def test_build_command_default(self):
        """デフォルト設定でclaudeコマンドが構築される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="config/personalities/test.txt",
            marker="TEST OK",
            pane_index=0,
            work_dir="",
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)

        command = launcher._build_launch_command()

        assert command == "claude"

    def test_build_command_with_work_dir(self):
        """作業ディレクトリ指定でcdコマンドが含まれる"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="config/personalities/test.txt",
            marker="TEST OK",
            pane_index=0,
            work_dir="/tmp/test",
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)

        command = launcher._build_launch_command()

        assert "cd /tmp/test" in command
        assert "claude" in command

    def test_build_command_with_custom_path(self):
        """カスタムclaudeパスが使用される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="config/personalities/test.txt",
            marker="TEST OK",
            pane_index=0,
            claude_path="/custom/path/to/claude",
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)

        command = launcher._build_launch_command()

        assert "/custom/path/to/claude" in command

    def test_build_command_with_both_work_dir_and_custom_path(self):
        """作業ディレクトリとカスタムパスの両方が含まれる"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="config/personalities/test.txt",
            marker="TEST OK",
            pane_index=0,
            work_dir="/tmp/test",
            claude_path="/custom/path/to/claude",
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)

        command = launcher._build_launch_command()

        assert command == "cd /tmp/test && /custom/path/to/claude"


class TestCCProcessLauncherErrorHandling:
    """エラーハンドリングのテスト"""

    def test_exception_hierarchy(self):
        """例外クラスがTmuxErrorを継承していることを確認"""
        from orchestrator.core.tmux_session_manager import TmuxError

        assert issubclass(CCProcessLaunchError, TmuxError)
        assert issubclass(CCProcessNotRunningError, TmuxError)
        assert issubclass(CCPersonalityPromptNotFoundError, TmuxError)
        assert issubclass(CCPersonalityPromptReadError, TmuxError)

    def test_custom_exceptions_are_raiseable(self):
        """カスタム例外が正常に送出できることを確認"""
        with pytest.raises(CCProcessLaunchError):
            raise CCProcessLaunchError("Test error")

        with pytest.raises(CCProcessNotRunningError):
            raise CCProcessNotRunningError("Test error")

        with pytest.raises(CCPersonalityPromptNotFoundError):
            raise CCPersonalityPromptNotFoundError("Test error")

        with pytest.raises(CCPersonalityPromptReadError):
            raise CCPersonalityPromptReadError("Test error")
