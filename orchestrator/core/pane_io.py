"""ペイン入出力モジュール

このモジュールでは、tmuxペインへの入出力処理を行うPaneIOクラスを定義します。
"""

import asyncio
import re
import time
from typing import Final

from orchestrator.core.tmux_session_manager import (
    TmuxError,
    TmuxSessionManager,
)

# 定数
DEFAULT_TIMEOUT: Final[float] = 30.0  # デフォルトタイムアウト（秒）
DEFAULT_POLL_INTERVAL: Final[float] = 0.5  # デフォルトポーリング間隔（秒）
CAPTURE_HISTORY_LINES: Final[int] = -100  # キャプチャ時に取得する履歴行数


class PaneTimeoutError(TmuxError):
    """ペイン応答のタイムアウト例外

    指定されたタイムアウト時間内に合言葉が検出されなかった場合に送出されます。
    """

    pass


class PaneIO:
    """tmuxペインへの入出力処理を行うクラス

    TmuxSessionManagerをラップし、エージェントとの通信に特化した機能を提供します。
    メッセージ送信、合言葉検出による応答取得、出力のパース処理を行います。

    Attributes:
        _tmux: TmuxSessionManagerインスタンス
    """

    def __init__(self, tmux_manager: TmuxSessionManager) -> None:
        """PaneIOを初期化します。

        Args:
            tmux_manager: TmuxSessionManagerインスタンス

        Raises:
            TypeError: tmux_managerがTmuxSessionManagerでない場合
        """
        if not isinstance(tmux_manager, TmuxSessionManager):
            raise TypeError("tmux_managerはTmuxSessionManagerのインスタンスである必要があります")
        self._tmux: TmuxSessionManager = tmux_manager

    def send_message(self, pane_index: int, message: str) -> None:
        """メッセージをペインに送信します。

        シェルインジェクションのリスクはありませんが、tmuxの制御文字
        （Enterキーなど）との衝突を回避するためのエスケープ処理を行います。

        Args:
            pane_index: ペイン番号（0以上）
            message: 送信するメッセージ文字列

        Raises:
            ValueError: pane_indexが負の値、またはmessageが空の場合
            TmuxSessionNotFoundError: セッションが存在しない場合
            TmuxCommandError: tmuxコマンドが失敗した場合
            TmuxTimeoutError: コマンドがタイムアウトした場合
        """
        if pane_index < 0:
            raise ValueError("pane_indexは0以上でなければなりません")
        if not message:
            raise ValueError("messageは空であってはなりません")

        # エスケープ処理（基本的にはtmux send-keysはそのまま入力される）
        escaped_message = self._escape_message(message)

        # TmuxSessionManagerを通じて送信
        self._tmux.send_keys(pane_index, escaped_message)

    def _escape_message(self, message: str) -> str:
        """メッセージのエスケープ処理を行います。

        Args:
            message: 生のメッセージ

        Returns:
            エスケープ処理済みのメッセージ
        """
        # 基本的にはtmux send-keysはそのまま入力されるので、
        # 現時点ではエスケープ処理は不要
        # 将来の拡張用にメソッドとして分離
        return message

    # ============================================================
    # エイリアスメソッド（PjM指定名）
    # ============================================================

    def send_input(self, pane_index: int, message: str) -> None:
        """メッセージをペインに送信します（send_messageのエイリアス）。

        PjM指定のメソッド名です。send_messageと同じ機能を提供します。

        Args:
            pane_index: ペイン番号（0以上）
            message: 送信するメッセージ文字列

        Raises:
            ValueError: pane_indexが負の値、またはmessageが空の場合
            TmuxSessionNotFoundError: セッションが存在しない場合
            TmuxCommandError: tmuxコマンドが失敗した場合
            TmuxTimeoutError: コマンドがタイムアウトした場合
        """
        self.send_message(pane_index, message)

    async def get_response(
        self,
        pane_index: int,
        expected_marker: str,
        timeout: float = DEFAULT_TIMEOUT,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
    ) -> str:
        """合言葉（マーカー）を検出して応答を取得します。

        指定された合言葉がペイン出力に現れるまでポーリングし、検出された時点で
        応答を返します。タイムアウトまでに合言葉が検出されない場合は例外を送出します。

        Args:
            pane_index: ペイン番号（0以上）
            expected_marker: 検出する合言葉（例: "MIDDLE MANAGER OK"）
            timeout: タイムアウト時間（秒）、デフォルト30.0秒
            poll_interval: ポーリング間隔（秒）、デフォルト0.5秒

        Returns:
            パースされた応答文字列（プロンプト行を除去）

        Raises:
            ValueError: pane_indexが負の値、またはexpected_markerが空の場合
            PaneTimeoutError: タイムアウトまでに合言葉が検出されなかった場合
            TmuxSessionNotFoundError: セッションが存在しない場合
            TmuxCommandError: tmuxコマンドが失敗した場合
            TmuxTimeoutError: tmuxコマンドがタイムアウトした場合
        """
        if pane_index < 0:
            raise ValueError("pane_indexは0以上でなければなりません")
        if not expected_marker:
            raise ValueError("expected_markerは空であってはなりません")

        start_time = time.time()
        previous_output = ""

        while time.time() - start_time < timeout:
            # 現在の出力を取得
            raw_output = self._tmux.capture_pane(
                pane_index,
                start_line=CAPTURE_HISTORY_LINES,
            )

            # 出力が変化したか確認
            if raw_output != previous_output:
                previous_output = raw_output

                # 合言葉を検出
                if expected_marker in raw_output:
                    return self._parse_response(raw_output, expected_marker)

            # 次のポーリングまで待機
            await asyncio.sleep(poll_interval)

        # タイムアウト
        raise PaneTimeoutError(
            f"合言葉 '{expected_marker}' がタイムアウトまでに検出されませんでした "
            f"(timeout={timeout}秒)"
        )

    def _parse_response(self, raw_output: str, marker: str) -> str:
        """生の出力をパースして応答のみを抽出します。

        プロンプト行（ユーザー入力部分）を除去し、エージェントの応答のみを抽出します。
        また、合言葉以降の出力も除去します。

        Args:
            raw_output: tmux capture-paneで取得した生の出力
            marker: 合言葉（応答完了のマーカー）

        Returns:
            パースされた応答文字列
        """
        lines = raw_output.split("\n")
        response_lines = []
        marker_found = False

        for line in lines:
            # 合言葉が含まれる行を見つけたらそこまで
            if marker in line:
                marker_found = True
                break

            response_lines.append(line)

        # 合言葉が見つからなかった場合のフォールバック
        if not marker_found and marker in raw_output:
            # パース失敗時の簡易フォールバック
            return raw_output

        # プロンプト行を除去
        cleaned_lines = []
        for line in response_lines:
            # シェルプロンプトっぽい行をスキップ
            if self._is_prompt_line(line):
                continue
            cleaned_lines.append(line)

        # 先頭と末尾の空白行を削除
        result = "\n".join(cleaned_lines).strip()
        return result

    def _is_prompt_line(self, line: str) -> bool:
        """シェルプロンプト行かどうかを判定します。

        Args:
            line: 判定する行

        Returns:
            プロンプト行の場合True、それ以外の場合False
        """
        stripped = line.strip()
        if not stripped:
            return False

        # 一般的なシェルプロンプトパターン
        # 例: "user@host:~$", "user@host:~$ command", "$", "$ command", ">", "> "
        prompt_patterns = [
            r"^[\w\-]+@[\w\-]+:.*[\$%#>]\s",  # user@host:path$ command
            r"^[\w\-]+@[\w\-]+:.*[\$%#>]$",  # user@host:path$
            r"^[\$%#>]\s",  # $ command, # command, > command
            r"^[\$%#>]$",  # 単一のプロンプト文字
        ]

        for pattern in prompt_patterns:
            if re.match(pattern, stripped):
                return True

        return False

    # ============================================================
    # エイリアスメソッド（PjM指定名） - 非同期
    # ============================================================

    async def get_output(
        self,
        pane_index: int,
        expected_marker: str,
        timeout: float = DEFAULT_TIMEOUT,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
    ) -> str:
        """合言葉（マーカー）を検出して応答を取得します（get_responseのエイリアス）。

        PjM指定のメソッド名です。get_responseと同じ機能を提供します。

        Args:
            pane_index: ペイン番号（0以上）
            expected_marker: 検出する合言葉（例: "MIDDLE MANAGER OK"）
            timeout: タイムアウト時間（秒）、デフォルト30.0秒
            poll_interval: ポーリング間隔（秒）、デフォルト0.5秒

        Returns:
            パースされた応答文字列（プロンプト行を除去）

        Raises:
            ValueError: pane_indexが負の値、またはexpected_markerが空の場合
            PaneTimeoutError: タイムアウトまでに合言葉が検出されなかった場合
            TmuxSessionNotFoundError: セッションが存在しない場合
            TmuxCommandError: tmuxコマンドが失敗した場合
            TmuxTimeoutError: tmuxコマンドがタイムアウトした場合
        """
        return await self.get_response(pane_index, expected_marker, timeout, poll_interval)

    async def wait_for_response(
        self,
        pane_index: int,
        expected_marker: str,
        timeout: float = DEFAULT_TIMEOUT,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
    ) -> str:
        """合言葉（マーカー）を検出して応答を取得します（get_outputのエイリアス）。

        PjM指定のメソッド名です。待機動作を強調するエイリアスです。
        get_output/get_responseと同じ機能を提供します。

        Args:
            pane_index: ペイン番号（0以上）
            expected_marker: 検出する合言葉（例: "MIDDLE MANAGER OK"）
            timeout: タイムアウト時間（秒）、デフォルト30.0秒
            poll_interval: ポーリング間隔（秒）、デフォルト0.5秒

        Returns:
            パースされた応答文字列（プロンプト行を除去）

        Raises:
            ValueError: pane_indexが負の値、またはexpected_markerが空の場合
            PaneTimeoutError: タイムアウトまでに合言葉が検出されなかった場合
            TmuxSessionNotFoundError: セッションが存在しない場合
            TmuxCommandError: tmuxコマンドが失敗した場合
            TmuxTimeoutError: tmuxコマンドがタイムアウトした場合
        """
        return await self.get_output(pane_index, expected_marker, timeout, poll_interval)

    # ============================================================
    # 新規メソッド（PjM指定）
    # ============================================================

    def clear_pane(self, pane_index: int) -> None:
        """ペインの画面をクリアします。

        tmuxのclearコマンドを送信して、ペインの画面をクリアします。

        Args:
            pane_index: ペイン番号（0以上）

        Raises:
            ValueError: pane_indexが負の値の場合
            TmuxSessionNotFoundError: セッションが存在しない場合
            TmuxCommandError: tmuxコマンドが失敗した場合
            TmuxTimeoutError: コマンドがタイムアウトした場合
        """
        if pane_index < 0:
            raise ValueError("pane_indexは0以上でなければなりません")

        # clearコマンドを送信
        self._tmux.send_keys(pane_index, "clear")

    def is_ready(self, pane_index: int, prompt_char: str = ">") -> bool:
        """ペインがコマンド受信可能な状態か確認します。

        プロンプトが表示されているかを判定して、ペインが準備完了状態かを確認します。

        Args:
            pane_index: ペイン番号（0以上）
            prompt_char: プロンプト文字（デフォルト: ">"、Claude Codeのプロンプト）

        Returns:
            プロンプトが表示されている場合True、それ以外の場合False

        Raises:
            ValueError: pane_indexが負の値の場合
            TmuxSessionNotFoundError: セッションが存在しない場合
            TmuxCommandError: tmuxコマンドが失敗した場合
            TmuxTimeoutError: コマンドがタイムアウトした場合
        """
        if pane_index < 0:
            raise ValueError("pane_indexは0以上でなければなりません")

        # 現在の出力を取得
        raw_output = self._tmux.capture_pane(
            pane_index,
            start_line=CAPTURE_HISTORY_LINES,
        )

        # 直近の行を確認
        lines = raw_output.split("\n")
        # 直近10行を確認（プロンプトは末尾付近にあるはず）
        for line in reversed(lines[-10:]):
            # 末尾のスペースを削除してチェック
            if line.rstrip().endswith(prompt_char):
                return True

        return False
