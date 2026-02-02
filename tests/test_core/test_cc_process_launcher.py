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
    async def test_launch_cc_in_pane_success(self):
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
            launcher._wait_for_prompt_ready = AsyncMock(return_value=True)

            await launcher.launch_cc_in_pane()

            assert launcher.is_process_alive() is True
            launcher._pane_io.get_response.assert_called_once_with(
                0, "TEST OK", timeout=INITIAL_TIMEOUT, poll_interval=0.5
            )

    @pytest.mark.asyncio
    async def test_launch_cc_in_pane_uses_custom_poll_interval(self):
        """カスタムpoll_intervalが使用される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="config/personalities/test.txt",
            marker="TEST OK",
            pane_index=0,
            poll_interval=0.3,
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)

        with patch.object(launcher, "_load_personality_prompt", return_value="Test prompt"):
            launcher._pane_io.get_response = AsyncMock(return_value="Response with TEST OK")
            launcher._wait_for_prompt_ready = AsyncMock(return_value=True)

            await launcher.launch_cc_in_pane()

            launcher._pane_io.get_response.assert_called_once_with(
                0, "TEST OK", timeout=INITIAL_TIMEOUT, poll_interval=0.3
            )

    @pytest.mark.asyncio
    async def test_launch_cc_in_pane_waits_for_wait_time(self):
        """wait_timeの分だけ追加待機する"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="config/personalities/test.txt",
            marker="TEST OK",
            pane_index=0,
            wait_time=0.1,
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)

        with patch.object(launcher, "_load_personality_prompt", return_value="Test prompt"):
            launcher._pane_io.get_response = AsyncMock(return_value="Response with TEST OK")
            launcher._wait_for_prompt_ready = AsyncMock(return_value=True)

            await launcher.launch_cc_in_pane()

            assert launcher.is_process_alive() is True

    @pytest.mark.asyncio
    async def test_launch_cc_in_pane_calls_send_keys(self):
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
            launcher._wait_for_prompt_ready = AsyncMock(return_value=True)

            await launcher.launch_cc_in_pane()

            # send_keysが起動コマンドで呼ばれることを確認
            mock_tmux.send_keys.assert_called()
            call_args = mock_tmux.send_keys.call_args
            assert call_args[0][0] == 0  # pane_index
            assert "cd /tmp/test" in call_args[0][1]  # work_dirを含む

    @pytest.mark.asyncio
    async def test_launch_cc_in_pane_waits_for_marker(self):
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
            launcher._wait_for_prompt_ready = AsyncMock(return_value=True)

            await launcher.launch_cc_in_pane()

            # get_responseがマーカー付きで呼ばれることを確認
            launcher._pane_io.get_response.assert_called_once_with(
                0, "TEST OK", timeout=INITIAL_TIMEOUT, poll_interval=0.5
            )

    @pytest.mark.asyncio
    async def test_launch_cc_in_pane_sets_running_flag(self):
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
            launcher._wait_for_prompt_ready = AsyncMock(return_value=True)

            await launcher.launch_cc_in_pane()

            assert launcher._running is True

    @pytest.mark.asyncio
    async def test_launch_cc_in_pane_prompt_not_found_raises_error(self):
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
            await launcher.launch_cc_in_pane()

    @pytest.mark.asyncio
    async def test_launch_cc_in_pane_timeout_raises_cc_process_launch_error(self):
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
                await launcher.launch_cc_in_pane()

    @pytest.mark.asyncio
    async def test_launch_cc_in_pane_when_already_running_does_nothing(self):
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

        await launcher.launch_cc_in_pane()

        # get_responseは呼ばれない
        launcher._pane_io.get_response.assert_not_called()


class TestCCProcessLauncherIsRunning:
    """状態確認のテスト"""

    def test_is_process_alive_after_start(self):
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

        assert launcher.is_process_alive() is True

    def test_is_process_alive_initially(self):
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

        assert launcher.is_process_alive() is False

    def test_is_process_alive_after_stop(self):
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

        assert launcher.is_process_alive() is False


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
    async def test_terminate_process_success(self):
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

        await launcher.terminate_process()

        assert launcher.is_process_alive() is False
        mock_tmux.send_keys.assert_called_once_with(0, "C-c")

    @pytest.mark.asyncio
    async def test_terminate_process_sends_ctrl_c(self):
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

        await launcher.terminate_process()

        mock_tmux.send_keys.assert_called_once_with(0, "C-c")

    @pytest.mark.asyncio
    async def test_terminate_process_when_not_running_does_nothing(self):
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

        await launcher.terminate_process()

        # send_keysは呼ばれない
        mock_tmux.send_keys.assert_not_called()


class TestCCProcessLauncherBuildCommand:
    """コマンド構築のテスト"""

    def test_build_command_includes_system_prompt(self, tmp_path):
        """--system-promptオプションが含まれる"""
        mock_tmux = Mock(spec=TmuxSessionManager)

        # テスト用プロンプトファイルを作成
        prompt_file = tmp_path / "test_prompt.txt"
        prompt_file.write_text("You are a test agent.", encoding="utf-8")

        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path=str(prompt_file),
            marker="TEST OK",
            pane_index=0,
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)

        command = launcher._build_launch_command()

        assert "--system-prompt" in command
        assert "You are a test agent." in command

    def test_build_command_with_work_dir(self, tmp_path):
        """作業ディレクトリ指定でcdコマンドが含まれる"""
        mock_tmux = Mock(spec=TmuxSessionManager)

        # テスト用プロンプトファイルを作成
        prompt_file = tmp_path / "test_prompt.txt"
        prompt_file.write_text("Test prompt", encoding="utf-8")

        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path=str(prompt_file),
            marker="TEST OK",
            pane_index=0,
            work_dir="/tmp/test",
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)

        command = launcher._build_launch_command()

        assert "cd /tmp/test" in command
        assert "--system-prompt" in command

    def test_build_command_with_custom_path(self, tmp_path):
        """カスタムclaudeパスが使用される"""
        mock_tmux = Mock(spec=TmuxSessionManager)

        # テスト用プロンプトファイルを作成
        prompt_file = tmp_path / "test_prompt.txt"
        prompt_file.write_text("Test prompt", encoding="utf-8")

        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path=str(prompt_file),
            marker="TEST OK",
            pane_index=0,
            claude_path="/custom/path/to/claude",
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)

        command = launcher._build_launch_command()

        assert "/custom/path/to/claude" in command
        assert "--system-prompt" in command

    def test_build_command_with_both_work_dir_and_custom_path(self, tmp_path):
        """作業ディレクトリとカスタムパスの両方が含まれる"""
        mock_tmux = Mock(spec=TmuxSessionManager)

        # テスト用プロンプトファイルを作成
        prompt_file = tmp_path / "test_prompt.txt"
        prompt_file.write_text("Test prompt", encoding="utf-8")

        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path=str(prompt_file),
            marker="TEST OK",
            pane_index=0,
            work_dir="/tmp/test",
            claude_path="/custom/path/to/claude",
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)

        command = launcher._build_launch_command()

        assert "cd /tmp/test" in command
        assert "/custom/path/to/claude" in command
        assert "--system-prompt" in command

    def test_build_command_escapes_single_quotes_in_prompt(self, tmp_path):
        """プロンプト内のシングルクォートがエスケープされる"""
        mock_tmux = Mock(spec=TmuxSessionManager)

        # シングルクォートを含むプロンプトファイル
        prompt_file = tmp_path / "test_prompt.txt"
        prompt_file.write_text("I'm a test agent's prompt.", encoding="utf-8")

        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path=str(prompt_file),
            marker="TEST OK",
            pane_index=0,
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)

        command = launcher._build_launch_command()

        # シングルクォートがエスケープされていることを確認
        assert "'\\''" in command or "I\\'m" in command


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


class TestCCProcessLauncherWaitForPromptReady:
    """プロンプト準備完了待機のテスト"""

    @pytest.mark.asyncio
    async def test_wait_for_prompt_ready_success(self):
        """プロンプト検出成功でTrueが返る"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="config/personalities/test.txt",
            marker="TEST OK",
            pane_index=0,
            poll_interval=0.05,  # 短くしてテストを高速化
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)

        # プロンプトパターンを含む出力をモック（start_line引数を許容）
        def mock_capture(pane_index, start_line):
            return "Some output\n> "

        mock_tmux.capture_pane = Mock(side_effect=mock_capture)

        result = await launcher._wait_for_prompt_ready(timeout=0.5)

        assert result is True
        # capture_paneが呼ばれたことを確認
        mock_tmux.capture_pane.assert_called()

    @pytest.mark.asyncio
    async def test_wait_for_prompt_ready_timeout(self):
        """プロンプト検出タイムアウトでFalseが返る"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="config/personalities/test.txt",
            marker="TEST OK",
            pane_index=0,
            poll_interval=0.1,
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)

        # プロンプトパターンを含まない出力をモック
        def mock_capture(pane_index, start_line):
            return "Some output without prompt"

        mock_tmux.capture_pane = Mock(side_effect=mock_capture)

        result = await launcher._wait_for_prompt_ready(timeout=0.3)

        assert result is False

    @pytest.mark.asyncio
    async def test_wait_for_prompt_ready_checks_last_lines(self):
        """直近10行をチェックすることを確認"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="config/personalities/test.txt",
            marker="TEST OK",
            pane_index=0,
            poll_interval=0.05,
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)

        # 最後の行にプロンプトがある出力
        output = "\n".join([f"Line {i}" for i in range(20)] + ["Last line > "])

        def mock_capture(pane_index, start_line):
            return output

        mock_tmux.capture_pane = Mock(side_effect=mock_capture)

        result = await launcher._wait_for_prompt_ready(timeout=0.5)

        assert result is True

    @pytest.mark.asyncio
    async def test_wait_for_prompt_ready_detects_prompt_pattern(self):
        """プロンプトパターン"> "を正しく検出する"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="config/personalities/test.txt",
            marker="TEST OK",
            pane_index=0,
            poll_interval=0.05,
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)

        # 様々なプロンプトパターンをテスト
        test_cases = [
            ("Some text\n> ", True),           # 行末にプロンプト
            ("Line 1\nLine 2\n> ", True),      # 複数行後にプロンプト
            ("No prompt here", False),         # プロンプトなし
            ("Prompt with spaces:  >  ", True),  # スペース付きプロンプト
        ]

        for output, expected in test_cases:
            def mock_capture(pane_index, start_line, out=output):
                return out

            mock_tmux.capture_pane = Mock(side_effect=mock_capture)
            result = await launcher._wait_for_prompt_ready(timeout=0.5)
            assert result is expected, f"Failed for: {output!r}, expected {expected}, got {result}"


class TestCCProcessLauncherGetAllProcessesStatus:
    """全プロセス状態取得のテスト"""

    def test_get_all_processes_status_returns_dict(self):
        """辞書型で返ることを確認"""
        result = CCProcessLauncher.get_all_processes_status()

        assert isinstance(result, dict)

    def test_get_all_processes_status_includes_registered_processes(self):
        """登録されたプロセスが含まれることを確認"""
        mock_tmux = Mock(spec=TmuxSessionManager)

        # 複数のプロセスを作成
        config1 = CCProcessConfig(
            name="agent1",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="config/personalities/test.txt",
            marker="TEST1",
            pane_index=0,
        )
        config2 = CCProcessConfig(
            name="agent2",
            role=CCProcessRole.MIDDLE_MANAGER,
            personality_prompt_path="config/personalities/test.txt",
            marker="TEST2",
            pane_index=1,
        )

        launcher1 = CCProcessLauncher(config1, 0, mock_tmux)
        _ = CCProcessLauncher(config2, 1, mock_tmux)

        # プロセス1を実行中に設定
        launcher1._running = True

        result = CCProcessLauncher.get_all_processes_status()

        assert result["agent1"] is True
        assert result["agent2"] is False

    def test_get_all_processes_status_with_running_processes(self):
        """実行中のプロセスの状態を正しく取得"""
        mock_tmux = Mock(spec=TmuxSessionManager)

        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="config/personalities/test.txt",
            marker="TEST",
            pane_index=0,
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)
        launcher._running = True

        result = CCProcessLauncher.get_all_processes_status()

        assert result["test_agent"] is True

    def test_get_all_processes_status_after_terminate(self):
        """終了後のプロセスがレジストリから削除されることを確認"""
        mock_tmux = Mock(spec=TmuxSessionManager)

        config = CCProcessConfig(
            name="test_agent",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="config/personalities/test.txt",
            marker="TEST",
            pane_index=0,
        )

        launcher = CCProcessLauncher(config, 0, mock_tmux)
        launcher._running = True

        # 終了前にプロセスが含まれることを確認
        result_before = CCProcessLauncher.get_all_processes_status()
        assert "test_agent" in result_before

        # terminate_processを呼び出す（同期メソッドとして実装）
        launcher._running = False
        CCProcessLauncher._process_registry.pop(config.name, None)

        # 終了後にプロセスが含まれないことを確認
        result_after = CCProcessLauncher.get_all_processes_status()
        assert "test_agent" not in result_after
