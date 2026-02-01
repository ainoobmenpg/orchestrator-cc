"""Claude Code プロセス起動モジュール

このモジュールでは、各ペインでClaude Codeプロセスを起動・監視・管理する
CCProcessLauncherクラスを定義します。
"""

import shlex
from pathlib import Path
from typing import Final

from orchestrator.core.cc_process_models import CCProcessConfig
from orchestrator.core.pane_io import (
    PaneIO,
    PaneTimeoutError,
)
from orchestrator.core.tmux_session_manager import (
    TmuxError,
    TmuxSessionManager,
    TmuxSessionNotFoundError,
)


# 例外クラス
class CCProcessError(TmuxError):
    """Claude Codeプロセスに関する基本例外クラス"""

    pass


class CCProcessLaunchError(CCProcessError):
    """プロセス起動失敗時の例外"""

    pass


class CCProcessNotRunningError(CCProcessError):
    """プロセスが実行されていない場合の例外"""

    pass


class CCPersonalityPromptNotFoundError(CCProcessError):
    """性格プロンプトファイルが見つからない場合の例外"""

    pass


class CCPersonalityPromptReadError(CCProcessError):
    """性格プロンプト読み込み失敗時の例外"""

    pass


# 定数
INITIAL_TIMEOUT: Final[float] = 60.0  # 初期化待機のタイムアウト（秒）


class CCProcessLauncher:
    """Claude Codeプロセスを起動・監視・管理するクラス

    各ペインでClaude Codeプロセスを起動し、性格プロンプトを適用して
    エージェントとの通信を管理します。

    Attributes:
        _config: エージェント設定
        _pane_index: tmuxペイン番号
        _tmux: TmuxSessionManagerインスタンス
        _pane_io: PaneIOインスタンス
        _running: プロセス実行中フラグ
        _restart_count: 再起動回数（TODO: auto_restart機能実装時に使用、Issue #11）
    """

    def __init__(
        self,
        config: CCProcessConfig,
        pane_index: int,
        tmux_manager: TmuxSessionManager,
    ) -> None:
        """CCProcessLauncherを初期化します。

        Args:
            config: エージェント設定
            pane_index: tmuxペイン番号
            tmux_manager: TmuxSessionManagerインスタンス

        Raises:
            TypeError: tmux_managerがTmuxSessionManagerでない場合
            ValueError: pane_indexが負の値の場合
        """
        if not isinstance(tmux_manager, TmuxSessionManager):
            raise TypeError("tmux_managerはTmuxSessionManagerのインスタンスである必要があります")

        if pane_index < 0:
            raise ValueError("pane_indexは0以上である必要があります")

        self._config: CCProcessConfig = config
        self._pane_index: int = pane_index
        self._tmux: TmuxSessionManager = tmux_manager
        self._pane_io: PaneIO = PaneIO(tmux_manager)
        self._running: bool = False
        # TODO: auto_restart機能実装時に使用 (Issue #11)
        self._restart_count: int = 0

    async def start(self) -> None:
        """Claude Codeプロセスを起動します。

        性格プロンプトを読み込み、ペインでClaude Codeを起動し、
        初期化完了を待機します。

        Raises:
            CCPersonalityPromptNotFoundError: 性格プロンプトファイルが見つからない場合
            CCPersonalityPromptReadError: 性格プロンプト読み込みに失敗した場合
            CCProcessLaunchError: プロセス起動に失敗した場合
            PaneTimeoutError: 初期化完了マーカーがタイムアウトした場合
            TmuxSessionNotFoundError: セッションが存在しない場合
        """
        if self._running:
            return

        # 性格プロンプトを読み込み
        # TODO: 性格プロンプトの適用方法を検証・実装 (Issue #11)
        # Phase 0の検証では--system-promptオプションは不可だったため
        # 起動後に別の方法で設定する必要がある
        # try:
        #     _ = self._load_personality_prompt()
        # except (CCPersonalityPromptNotFoundError, CCPersonalityPromptReadError):
        #     raise

        # 起動コマンドを構築
        launch_command = self._build_launch_command()

        # コマンドを送信
        try:
            self._tmux.send_keys(self._pane_index, launch_command)
        except TmuxSessionNotFoundError as e:
            raise CCProcessLaunchError(f"セッションが存在しません: {e}") from e

        # 初期化完了マーカーを待機
        try:
            # 空のメッセージを送信してプロンプトを表示（初期化完了確認）
            # 実際にはClaude Codeの起動を待ってから最初のメッセージを送る
            await self._pane_io.get_response(
                self._pane_index,
                self._config.marker,
                timeout=INITIAL_TIMEOUT,
            )
        except PaneTimeoutError as e:
            raise CCProcessLaunchError(
                f"プロセスの初期化がタイムアウトしました "
                f"(marker={self._config.marker}, timeout={INITIAL_TIMEOUT}秒)"
            ) from e

        self._running = True
        # TODO: auto_restart機能実装時に使用 (Issue #11)
        self._restart_count = 0

    def is_running(self) -> bool:
        """プロセスが実行中か確認します。

        Returns:
            実行中の場合True、それ以外の場合False
        """
        return self._running

    async def send_message(self, message: str, timeout: float = 30.0) -> str:
        """メッセージを送信して応答を取得します。

        Args:
            message: 送信するメッセージ
            timeout: タイムアウト時間（秒）

        Returns:
            エージェントからの応答

        Raises:
            ValueError: messageが空の場合
            CCProcessNotRunningError: プロセスが実行されていない場合
            PaneTimeoutError: 応答がタイムアウトした場合
        """
        if not message:
            raise ValueError("messageは空であってはなりません")

        if not self._running:
            raise CCProcessNotRunningError(
                f"プロセス '{self._config.name}' は実行されていません。先にstart()を呼び出してください"
            )

        # メッセージを送信
        self._pane_io.send_message(self._pane_index, message)

        # 応答を取得
        response = await self._pane_io.get_response(
            self._pane_index,
            self._config.marker,
            timeout=timeout,
        )

        return response

    async def stop(self) -> None:
        """プロセスを停止します。

        ペインにCtrl+Cを送信してClaude Codeを停止します。

        Note:
            実際にはtmuxペインは残り、シェルに戻ります。
            完全にペインを破棄するにはTmuxSessionManagerを使用してください。
        """
        if not self._running:
            return

        # Ctrl+Cを送信してプロセスを停止
        self._tmux.send_keys(self._pane_index, "C-c")

        self._running = False

    def _load_personality_prompt(self) -> str:
        """性格プロンプトを読み込みます。

        Returns:
            性格プロンプトの内容

        Raises:
            CCPersonalityPromptNotFoundError: ファイルが見つからない場合
            CCPersonalityPromptReadError: ファイル読み込みに失敗した場合
        """
        prompt_path = Path(self._config.personality_prompt_path)

        # 相対パスの場合はプロジェクトルートからのパスとして解決
        if not prompt_path.is_absolute():
            # カレントワーキングディレクトリを基準に解決
            prompt_path = Path.cwd() / self._config.personality_prompt_path

        # ファイルの存在を確認
        if not prompt_path.exists():
            raise CCPersonalityPromptNotFoundError(
                f"性格プロンプトファイルが見つかりません: {prompt_path}"
            )

        if not prompt_path.is_file():
            raise CCPersonalityPromptNotFoundError(
                f"性格プロンプトがファイルではありません: {prompt_path}"
            )

        # ファイルを読み込み
        try:
            with open(prompt_path, encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            raise CCPersonalityPromptReadError(
                f"性格プロンプトファイルの読み込みに失敗しました: {prompt_path}"
            ) from e

        return content.strip()

    def _build_launch_command(self) -> str:
        """Claude Code起動コマンドを構築します。

        Returns:
            起動コマンド文字列
        """
        # 作業ディレクトリに移動してClaude Codeを起動
        parts = []

        if self._config.work_dir:
            # shlex.quote()でパスをクォート（コマンドインジェクション対策）
            parts.append(f"cd {shlex.quote(self._config.work_dir)}")

        # Claude Codeのパス
        claude_path = self._config.claude_path if self._config.claude_path else "claude"

        # TODO: 性格プロンプトの渡し方を検証 (Issue #11)
        # Phase 0の検証では--system-promptオプションは不可だったため
        # 起動後に別の方法で設定する必要がある
        parts.append(claude_path)

        return " && ".join(parts)
