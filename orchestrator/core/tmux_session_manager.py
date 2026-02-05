"""tmuxセッション管理モジュール

このモジュールでは、tmuxセッションの作成・管理を行うTmuxSessionManagerクラスを定義します。
"""

import re
import subprocess
import threading
from typing import Final

# 定数
COMMAND_TIMEOUT: Final[int] = 10  # tmuxコマンドのタイムアウト（秒）


class TmuxError(RuntimeError):
    """tmux操作に関する基本例外クラス"""

    pass


class TmuxSessionNotFoundError(TmuxError):
    """セッションが見つからない場合の例外"""

    pass


class TmuxCommandError(TmuxError):
    """tmuxコマンド実行失敗時の例外"""

    pass


class TmuxTimeoutError(TmuxError):
    """tmuxコマンドタイムアウト時の例外"""

    pass


class TmuxSessionManager:
    """tmuxセッションの作成・管理を行うクラス

    tmuxセッションの作成、ペインの分割、コマンド送信、出力キャプチャなどの機能を提供します。

    Attributes:
        _session_name: tmuxセッション名
        _window_index: ウィンドウインデックス（デフォルト: 0）
        _next_pane_index: 次に作成するペイン番号
        _lock: tmuxコマンド実行の排他ロック（並列実行時の競合回避）
    """

    # クラスレベルのロック（すべてのインスタンスで共有）
    _lock: threading.Lock = threading.Lock()

    def __init__(self, session_name: str, window_index: int = 0) -> None:
        """TmuxSessionManagerを初期化します。

        Args:
            session_name: tmuxセッション名
            window_index: ウィンドウインデックス（デフォルト: 0）
                         将来の複数ウィンドウ対応時に使用

        Raises:
            ValueError: セッション名が空の場合、または無効な文字を含む場合
        """
        if not session_name:
            raise ValueError("セッション名は空であってはなりません")

        # tmuxのセッション名に使用できる文字は英数字、ハイフン、アンダースコアのみ
        if not re.match(r"^[a-zA-Z0-9_-]+$", session_name):
            raise ValueError("セッション名は英数字、ハイフン、アンダースコアのみ使用できます")

        self._session_name: str = session_name
        self._window_index: int = window_index
        self._next_pane_index: int = 0

    def _run_tmux_command(self, args: list[str]) -> str:
        """tmuxコマンドを実行し、出力を返します。

        並列実行時の競合を回避するため、クラスレベルのロックを使用して
        tmuxコマンドの実行を直列化します。

        Args:
            args: tmuxコマンドの引数リスト

        Returns:
            コマンドの標準出力

        Raises:
            TmuxTimeoutError: コマンドがタイムアウトした場合
            TmuxCommandError: コマンドが失敗した場合
        """
        with TmuxSessionManager._lock:
            try:
                result = subprocess.run(
                    ["tmux"] + args,
                    capture_output=True,
                    text=True,
                    timeout=COMMAND_TIMEOUT,
                    check=True,
                )
                return result.stdout
            except subprocess.TimeoutExpired as e:
                raise TmuxTimeoutError(f"tmuxコマンドがタイムアウトしました: {e}") from e
            except subprocess.CalledProcessError as e:
                raise TmuxCommandError(f"tmuxコマンドが失敗しました: {e.stderr}") from e
            except FileNotFoundError as e:
                raise TmuxCommandError("tmuxがインストールされていません") from e

    def session_exists(self) -> bool:
        """セッションが存在するか確認します。

        Returns:
            セッションが存在すればTrue、なければFalse
        """
        try:
            self._run_tmux_command(["has-session", "-t", self._session_name])
            return True
        except TmuxCommandError:
            return False

    def create_session(self, width: int = 200, height: int = 50) -> None:
        """新しいtmuxセッションを作成します。

        Args:
            width: セッションの幅（文字数、デフォルト: 200）
            height: セッションの高さ（行数、デフォルト: 50）

        Raises:
            RuntimeError: セッションが既に存在する場合
            TmuxCommandError: tmuxコマンドが失敗した場合
            TmuxTimeoutError: コマンドがタイムアウトした場合
        """
        if self.session_exists():
            raise RuntimeError(f"セッション '{self._session_name}' は既に存在します")

        self._run_tmux_command(
            [
                "new-session",
                "-d",
                "-s",
                self._session_name,
                "-x",
                str(width),
                "-y",
                str(height),
            ]
        )

        # セッションが正常に作成されたことを確認
        if not self.session_exists():
            raise TmuxError(f"セッション '{self._session_name}' の作成に失敗しました")

    def create_pane(self, split: str = "h", target_pane: int | None = None) -> int:
        """新しいペインを作成し、ペイン番号を返します。

        Args:
            split: 分割方向（"h": 水平分割/左右、 "v": 垂直分割/上下）
            target_pane: 分割対象のペイン番号（Noneの場合はウィンドウ全体）

        Returns:
            作成されたペイン番号（0, 1, 2, ...）

        Raises:
            ValueError: splitが"h"または"v"でない場合
            RuntimeError: セッションが存在しない場合
            TmuxCommandError: tmuxコマンドが失敗した場合
            TmuxTimeoutError: コマンドがタイムアウトした場合
        """
        if split not in ("h", "v"):
            raise ValueError("splitは'h'または'v'でなければなりません")

        if not self.session_exists():
            raise TmuxSessionNotFoundError(f"セッション '{self._session_name}' が存在しません")

        # ターゲットを設定
        if target_pane is not None:
            target = f"{self._session_name}:{self._window_index}.{target_pane}"
        else:
            target = f"{self._session_name}:{self._window_index}"

        self._run_tmux_command(
            [
                "split-window",
                f"-{split}",
                "-t",
                target,
            ]
        )

        pane_index = self._next_pane_index
        self._next_pane_index += 1
        return pane_index

    def send_keys(self, pane_index: int, keys: str) -> None:
        """指定したペインにキー入力を送信します。

        注意:
            tmux send-keysはシェルを介さずに直接キー入力を送信するため、
            シェルインジェクションのリスクはありません。スペース、クォート、
            その他の特殊文字はそのままペインに入力されます。

        Args:
            pane_index: ペイン番号（0以上）
            keys: 送信するキー文字列

        Raises:
            ValueError: pane_indexが負の値の場合
            RuntimeError: セッションが存在しない場合
            TmuxCommandError: tmuxコマンドが失敗した場合
            TmuxTimeoutError: コマンドがタイムアウトした場合
        """
        if pane_index < 0:
            raise ValueError("pane_indexは0以上でなければなりません")

        if not self.session_exists():
            raise TmuxSessionNotFoundError(f"セッション '{self._session_name}' が存在しません")

        target = f"{self._session_name}:{self._window_index}.{pane_index}"

        # メッセージを送信
        self._run_tmux_command(
            [
                "send-keys",
                "-t",
                target,
                "-l",  # リテラルモード（特殊文字をそのまま入力）
                keys,
            ]
        )

        # Enterキーを送信
        self._run_tmux_command(
            [
                "send-keys",
                "-t",
                target,
                "C-m",  # Enterキー（Carriage Return）
            ]
        )

    def capture_pane(
        self, pane_index: int, start_line: int | None = None, end_line: int | None = None
    ) -> str:
        """指定したペインの出力をキャプチャします。

        Args:
            pane_index: ペイン番号（0以上）
            start_line: 開始行（負の値で後ろから数える、例: -100で後ろから100行目から）
                        Noneの場合、tmuxのデフォルト（履歴の先頭）を使用
            end_line: 終了行（正の値で先頭から数える、例: +100で先頭から100行目まで）
                     Noneの場合、tmuxのデフォルト（現在の行）を使用

        Returns:
            ペインの出力（改行区切りの文字列）

        Raises:
            ValueError: pane_indexが負の値の場合
            RuntimeError: セッションが存在しない場合
            TmuxCommandError: tmuxコマンドが失敗した場合
            TmuxTimeoutError: コマンドがタイムアウトした場合
        """
        if pane_index < 0:
            raise ValueError("pane_indexは0以上でなければなりません")

        if not self.session_exists():
            raise TmuxSessionNotFoundError(f"セッション '{self._session_name}' が存在しません")

        target = f"{self._session_name}:{self._window_index}.{pane_index}"
        args = [
            "capture-pane",
            "-t",
            target,
            "-p",
        ]

        # オプション引数を追加
        if start_line is not None:
            args.extend(["-S", str(start_line)])
        if end_line is not None:
            args.extend(["-E", str(end_line)])

        output = self._run_tmux_command(args)

        return output

    def send_tmux_key(self, pane_index: int, key: str) -> None:
        """tmuxキーをペインに送信します。

        send_keys() とは異なり、文字列入力ではなく制御キーを送信します。

        Args:
            pane_index: ペイン番号（0以上）
            key: tmuxキー（例: "C-c", "C-d", "Enter"）

        Raises:
            ValueError: pane_indexが負の値、またはkeyが空の場合
            TmuxSessionNotFoundError: セッションが存在しない場合
            TmuxCommandError: tmuxコマンドが失敗した場合
            TmuxTimeoutError: コマンドがタイムアウトした場合
        """
        if pane_index < 0:
            raise ValueError("pane_indexは0以上でなければなりません")

        if not key:
            raise ValueError("keyは空であってはなりません")

        if not self.session_exists():
            raise TmuxSessionNotFoundError(f"セッション '{self._session_name}' が存在しません")

        target = f"{self._session_name}:{self._window_index}.{pane_index}"

        # tmux send-keys -t {target} {key} （-l なしでキーとして送信）
        self._run_tmux_command(
            [
                "send-keys",
                "-t",
                target,
                key,
            ]
        )

    def get_pane_count(self) -> int:
        """現在のペイン数を取得します。

        Returns:
            現在のペイン数

        Raises:
            RuntimeError: セッションが存在しない場合
            TmuxCommandError: tmuxコマンドが失敗した場合
            TmuxTimeoutError: コマンドがタイムアウトした場合
            ValueError: 出力を整数に変換できない場合
        """
        if not self.session_exists():
            raise TmuxSessionNotFoundError(f"セッション '{self._session_name}' が存在しません")

        target = f"{self._session_name}:{self._window_index}"
        output = self._run_tmux_command(
            [
                "display-message",
                "-t",
                target,
                "-p",
                "#{window_panes}",
            ]
        )

        try:
            return int(output.strip())
        except ValueError as e:
            raise ValueError(f"ペイン数を整数に変換できません: {output}") from e

    def kill_session(self) -> None:
        """tmuxセッションを破棄します。

        Raises:
            RuntimeError: セッションが存在しない場合
            TmuxCommandError: tmuxコマンドが失敗した場合
            TmuxTimeoutError: コマンドがタイムアウトした場合
        """
        if not self.session_exists():
            raise TmuxSessionNotFoundError(f"セッション '{self._session_name}' が存在しません")

        self._run_tmux_command(
            [
                "kill-session",
                "-t",
                self._session_name,
            ]
        )

        # セッションが正常に破棄されたことを確認
        if self.session_exists():
            raise TmuxError(f"セッション '{self._session_name}' の破棄に失敗しました")
