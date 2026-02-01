"""PaneIOのテスト

このモジュールでは、PaneIOクラスの単体テストを実装します。
"""

from unittest.mock import Mock

import pytest

from orchestrator.core.pane_io import (
    PaneIO,
    PaneTimeoutError,
)
from orchestrator.core.tmux_session_manager import (
    TmuxSessionManager,
    TmuxSessionNotFoundError,
)


class TestPaneIOInit:
    """PaneIO初期化処理のテスト"""

    def test_init_with_valid_tmux_manager(self):
        """有効なTmuxSessionManagerで初期化できる"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        pane_io = PaneIO(mock_tmux)
        assert pane_io._tmux is mock_tmux

    def test_init_with_invalid_type(self):
        """無効な型でTypeErrorが送出される"""
        with pytest.raises(TypeError, match="TmuxSessionManagerのインスタンス"):
            PaneIO("not_a_manager")

    def test_init_stores_tmux_reference(self):
        """TmuxSessionManagerが正しく保存される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        pane_io = PaneIO(mock_tmux)
        assert pane_io._tmux is mock_tmux


class TestPaneIOSendMessage:
    """send_messageメソッドのテスト"""

    def test_send_message_success(self):
        """メッセージ送信が成功する"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        pane_io = PaneIO(mock_tmux)

        pane_io.send_message(0, "test message")

        mock_tmux.send_keys.assert_called_once_with(0, "test message")

    def test_send_message_with_special_characters(self):
        """特殊文字を含むメッセージが正常に送信される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        pane_io = PaneIO(mock_tmux)

        special_message = "test with !@#$%^&*() characters"
        pane_io.send_message(0, special_message)

        mock_tmux.send_keys.assert_called_once_with(0, special_message)

    def test_send_message_with_quotes(self):
        """クォートを含むメッセージが正常に送信される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        pane_io = PaneIO(mock_tmux)

        quoted_message = 'test with "double" and \'single\' quotes'
        pane_io.send_message(0, quoted_message)

        mock_tmux.send_keys.assert_called_once_with(0, quoted_message)

    def test_send_message_with_unicode(self):
        """Unicode文字を含むメッセージが正常に送信される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        pane_io = PaneIO(mock_tmux)

        unicode_message = "test with 日本語 and 🎉 emoji"
        pane_io.send_message(0, unicode_message)

        mock_tmux.send_keys.assert_called_once_with(0, unicode_message)

    def test_send_message_with_multiline(self):
        """複数行メッセージが正常に送信される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        pane_io = PaneIO(mock_tmux)

        multiline_message = "line1\nline2\nline3"
        pane_io.send_message(0, multiline_message)

        mock_tmux.send_keys.assert_called_once_with(0, multiline_message)

    def test_send_message_empty_message_raises_value_error(self):
        """空文字列でValueErrorが送出される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        pane_io = PaneIO(mock_tmux)

        with pytest.raises(ValueError, match="messageは空であってはなりません"):
            pane_io.send_message(0, "")

    def test_send_message_invalid_pane_index_raises_value_error(self):
        """負のペインインデックスでValueErrorが送出される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        pane_io = PaneIO(mock_tmux)

        with pytest.raises(ValueError, match="pane_indexは0以上"):
            pane_io.send_message(-1, "test")

    def test_send_message_session_not_exists_raises_error(self):
        """セッションが存在しない場合TmuxSessionNotFoundErrorが送出される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        mock_tmux.send_keys.side_effect = TmuxSessionNotFoundError("session not found")
        pane_io = PaneIO(mock_tmux)

        with pytest.raises(TmuxSessionNotFoundError):
            pane_io.send_message(0, "test")


class TestPaneIOGetResponse:
    """get_responseメソッドのテスト"""

    @pytest.mark.asyncio
    async def test_get_response_success(self):
        """応答取得が成功する"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        # 合言葉を含む出力を返す
        mock_tmux.capture_pane.return_value = "Response content\nMIDDLE MANAGER OK\n"
        pane_io = PaneIO(mock_tmux)

        response = await pane_io.get_response(0, "MIDDLE MANAGER OK", timeout=1.0)

        assert isinstance(response, str)
        # 合言葉以降が除去されている
        assert "MIDDLE MANAGER OK" not in response
        mock_tmux.capture_pane.assert_called()

    @pytest.mark.asyncio
    async def test_get_response_with_timeout(self):
        """タイムアウト指定でPaneTimeoutErrorが送出される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        # 合言葉を含まない出力を返し続ける
        mock_tmux.capture_pane.return_value = "waiting...\n"
        pane_io = PaneIO(mock_tmux)

        with pytest.raises(PaneTimeoutError, match="合言葉.*タイムアウト"):
            await pane_io.get_response(0, "MARKER", timeout=0.5)

    @pytest.mark.asyncio
    async def test_get_response_marker_detected(self):
        """合言葉検出時に応答が返される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        # 最初は合言葉なし、その後に合言葉あり
        mock_tmux.capture_pane.side_effect = [
            "waiting...\n",
            "waiting...\n",
            "Response here\nMARKER\n",
        ]
        pane_io = PaneIO(mock_tmux)

        response = await pane_io.get_response(0, "MARKER", timeout=2.0)

        assert "Response here" in response
        assert "MARKER" not in response

    @pytest.mark.asyncio
    async def test_get_response_invalid_pane_index_raises_value_error(self):
        """負のペインインデックスでValueErrorが送出される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        pane_io = PaneIO(mock_tmux)

        with pytest.raises(ValueError, match="pane_indexは0以上"):
            await pane_io.get_response(-1, "MARKER")

    @pytest.mark.asyncio
    async def test_get_response_empty_marker_raises_value_error(self):
        """空の合言葉でValueErrorが送出される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        pane_io = PaneIO(mock_tmux)

        with pytest.raises(ValueError, match="expected_markerは空"):
            await pane_io.get_response(0, "")

    @pytest.mark.asyncio
    async def test_get_response_session_not_exists_raises_error(self):
        """セッションが存在しない場合TmuxSessionNotFoundErrorが送出される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        mock_tmux.capture_pane.side_effect = TmuxSessionNotFoundError("session not found")
        pane_io = PaneIO(mock_tmux)

        with pytest.raises(TmuxSessionNotFoundError):
            await pane_io.get_response(0, "MARKER", timeout=0.5)

    @pytest.mark.asyncio
    async def test_get_response_default_parameters(self):
        """デフォルトパラメータが正しく設定される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        mock_tmux.capture_pane.return_value = "OK\nMARKER\n"
        pane_io = PaneIO(mock_tmux)

        response = await pane_io.get_response(0, "MARKER")

        # デフォルト値が使用されている
        assert isinstance(response, str)


class TestPaneIOParseResponse:
    """_parse_responseメソッドのテスト"""

    def test_parse_response_removes_prompt_lines(self):
        """プロンプト行が除去される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        pane_io = PaneIO(mock_tmux)

        raw_output = "user@host:~$ test message\nResponse\nMARKER\n"
        result = pane_io._parse_response(raw_output, "MARKER")

        # プロンプト行が除去されている
        assert "user@host" not in result
        assert "Response" in result
        assert "MARKER" not in result

    def test_parse_response_extracts_before_marker(self):
        """合言葉前のみが抽出される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        pane_io = PaneIO(mock_tmux)

        raw_output = "Response content\nMARKER\nAfter marker\n"
        result = pane_io._parse_response(raw_output, "MARKER")

        assert "Response content" in result
        assert "After marker" not in result

    def test_parse_response_empty_output(self):
        """空の出力で空文字列が返される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        pane_io = PaneIO(mock_tmux)

        result = pane_io._parse_response("", "MARKER")

        assert result == ""

    def test_parse_response_with_multiline_output(self):
        """複数行出力が正しくパースされる"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        pane_io = PaneIO(mock_tmux)

        raw_output = "Line 1\nLine 2\nLine 3\nMARKER\n"
        result = pane_io._parse_response(raw_output, "MARKER")

        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result
        assert "MARKER" not in result

    def test_parse_response_removes_simple_prompt(self):
        """単純なプロンプト（$, #, >）が除去される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        pane_io = PaneIO(mock_tmux)

        # $ プロンプト
        raw_output = "$ command\nResponse\nMARKER\n"
        result = pane_io._parse_response(raw_output, "MARKER")
        assert "$ command" not in result or result.count("$") == 0

        # > プロンプト
        raw_output = "> command\nResponse\nMARKER\n"
        result = pane_io._parse_response(raw_output, "MARKER")
        assert ">" not in result or result.count(">") == 0


class TestPaneIOIsPromptLine:
    """_is_prompt_lineメソッドのテスト"""

    def test_is_prompt_line_with_user_host_format(self):
        """user@host:path形式がプロンプトと判定される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        pane_io = PaneIO(mock_tmux)

        assert pane_io._is_prompt_line("user@host:~$") is True
        assert pane_io._is_prompt_line("user@host:/path/to/dir#") is True

    def test_is_prompt_line_with_simple_prompt(self):
        """単純なプロンプト文字が判定される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        pane_io = PaneIO(mock_tmux)

        assert pane_io._is_prompt_line("$") is True
        assert pane_io._is_prompt_line("#") is True
        assert pane_io._is_prompt_line(">") is True

    def test_is_prompt_line_with_continuation(self):
        """プロンプト継続が判定される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        pane_io = PaneIO(mock_tmux)

        assert pane_io._is_prompt_line("> more input") is True

    def test_is_prompt_line_with_normal_text(self):
        """通常のテキストがプロンプトではないと判定される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        pane_io = PaneIO(mock_tmux)

        assert pane_io._is_prompt_line("This is normal text") is False
        assert pane_io._is_prompt_line("Response content") is False

    def test_is_prompt_line_with_empty_line(self):
        """空行がプロンプトではないと判定される"""
        mock_tmux = Mock(spec=TmuxSessionManager)
        pane_io = PaneIO(mock_tmux)

        assert pane_io._is_prompt_line("") is False
        assert pane_io._is_prompt_line("   ") is False
