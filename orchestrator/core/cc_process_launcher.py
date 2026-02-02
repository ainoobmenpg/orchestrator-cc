"""Claude Code プロセス起動モジュール

このモジュールでは、各ペインでClaude Codeプロセスを起動・監視・管理する
CCProcessLauncherクラスを定義します。
"""

import asyncio
import logging
import shlex
import time
from pathlib import Path
from typing import Final
from weakref import WeakValueDictionary

# ロガーの設定
logger = logging.getLogger(__name__)

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
CAPTURE_HISTORY_LINES: Final[int] = -100  # キャプチャ時に取得する履歴行数
RESTART_CHECK_INTERVAL: Final[float] = 5.0  # 再起動監視のチェック間隔（秒）


class CCProcessLauncher:
    """Claude Codeプロセスを起動・監視・管理するクラス

    各ペインでClaude Codeプロセスを起動し、性格プロンプトを適用して
    エージェントとの通信を管理します。

    クラス変数:
        _process_registry: 全プロセスの登録簿（プロセス名 -> インスタンス）

    Attributes:
        _config: エージェント設定
        _pane_index: tmuxペイン番号
        _tmux: TmuxSessionManagerインスタンス
        _pane_io: PaneIOインスタンス
        _running: プロセス実行中フラグ
        _restart_count: 再起動回数
        _monitor_task: 自動再起動監視タスク
        _last_activity_time: 最終アクティビティ時刻
    """

    # クラスレベルのプロセスレジストリ
    # WeakValueDictionaryを使用して、インスタンスがGCされたら自動削除
    _process_registry: WeakValueDictionary[str, "CCProcessLauncher"] = (
        WeakValueDictionary()
    )

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
        self._restart_count: int = 0
        self._monitor_task: asyncio.Task[None] | None = None
        self._last_activity_time: float = time.time()

        # プロセスレジストリに登録（同じ名前のプロセスがあれば上書き）
        CCProcessLauncher._process_registry[config.name] = self

    async def launch_cc_in_pane(self, is_restart: bool = False) -> None:
        """Claude Codeプロセスを起動します。

        性格プロンプトを読み込み、ペインでClaude Codeを起動し、
        初期化完了を待機します。

        Args:
            is_restart: 再起動の場合True（再起動回数をリセットしない）

        Raises:
            CCPersonalityPromptNotFoundError: 性格プロンプトファイルが見つからない場合
            CCPersonalityPromptReadError: 性格プロンプト読み込みに失敗した場合
            CCProcessLaunchError: プロセス起動に失敗した場合
            PaneTimeoutError: 初期化完了マーカーがタイムアウトした場合
            TmuxSessionNotFoundError: セッションが存在しない場合
        """
        if self._running:
            return

        # 性格プロンプトを読み込み（ファイルの存在チェック）
        try:
            _ = self._load_personality_prompt()
        except (CCPersonalityPromptNotFoundError, CCPersonalityPromptReadError):
            raise

        # 起動コマンドを構築
        launch_command = self._build_launch_command()

        # コマンドを送信
        try:
            self._tmux.send_keys(self._pane_index, launch_command)
        except TmuxSessionNotFoundError as e:
            raise CCProcessLaunchError(f"セッションが存在しません: {e}") from e

        # Enterキーを押してコマンドを実行
        try:
            self._tmux.send_keys(self._pane_index, "Enter")
        except TmuxSessionNotFoundError as e:
            raise CCProcessLaunchError(f"セッションが存在しません: {e}") from e

        # Claude Code起動待機（起動コマンド実行後の初期化時間）
        await asyncio.sleep(12.0)

        # プロンプト準備完了を確認（Claude Codeが起動してプロンプトが表示されているか）
        if not await self._wait_for_prompt_ready(timeout=60.0):
            raise CCProcessLaunchError(
                f"プロセス '{self._config.name}' のプロンプト起動を確認できませんでした"
            )

        # 起動後の追加待機（Claude Codeの完全な初期化を待つ）
        await asyncio.sleep(self._config.wait_time)

        self._running = True
        # 初期起動時のみ再起動回数をリセット（再起動時はカウントを維持）
        if not is_restart:
            self._restart_count = 0
        self._last_activity_time = time.time()
        logger.info(f"プロセス '{self._config.name}' を起動しました（ペイン: {self._pane_index}）")

        # 自動再起動監視を開始（有効な場合）
        if self._config.auto_restart:
            self.start_auto_restart_monitor()

    def is_process_alive(self) -> bool:
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
                f"プロセス '{self._config.name}' は実行されていません。先にlaunch_cc_in_pane()を呼び出してください"
            )

        # メッセージを送信
        self._pane_io.send_message(self._pane_index, message)

        # 応答を取得
        response = await self._pane_io.get_response(
            self._pane_index,
            self._config.marker,
            timeout=timeout,
        )

        # アクティビティ時刻を更新
        self._last_activity_time = time.time()

        return response

    async def terminate_process(self) -> None:
        """プロセスを停止します。

        ペインにCtrl+Cを送信してClaude Codeを停止します。

        Note:
            実際にはtmuxペインは残り、シェルに戻ります。
            完全にペインを破棄するにはTmuxSessionManagerを使用してください。
        """
        if not self._running:
            return

        # 監視タスクを停止
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

        # Ctrl+Cを送信してプロセスを停止
        self._tmux.send_keys(self._pane_index, "C-c")

        self._running = False

        # プロセスレジストリから削除
        CCProcessLauncher._process_registry.pop(self._config.name, None)
        logger.info(f"プロセス '{self._config.name}' を停止しました")

    @classmethod
    def get_all_processes_status(cls) -> dict[str, bool]:
        """全プロセスの状態を取得します。

        Returns:
            プロセス名 -> 生存状況 の辞書
            例: {"grand_boss": True, "middle_manager": True, "specialist_coding": False}

        Note:
            このメソッドはクラスメソッドです。インスタンス化せずに呼び出せます。
        """
        return {
            name: launcher.is_process_alive()
            for name, launcher in cls._process_registry.items()
        }

    def mark_as_running(self) -> None:
        """既存のプロセスが実行中としてマークします。

        すでにtmuxペインで起動しているプロセスに接続する場合に使用します。
        このメソッドを呼び出すと、プロセスレジストリにも登録されます。

        Note: 自動再起動監視は開始しません。接続先のプロセスは既に実行中と仮定します。
        """
        self._running = True
        self._restart_count = 0
        self._last_activity_time = time.time()
        # プロセスレジストリに登録
        CCProcessLauncher._process_registry[self._config.name] = self

        # Note: 自動再起動監視は開始しません（connect()メソッドから呼ばれる場合）

    async def _wait_for_prompt_ready(self, timeout: float = 10.0) -> bool:
        """Claude Codeのプロンプトが表示されていることを確認します。

        Args:
            timeout: タイムアウト時間（秒）

        Returns:
            プロンプト検出に成功した場合True
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            raw_output = self._tmux.capture_pane(
                self._pane_index,
                start_line=CAPTURE_HISTORY_LINES,
            )

            # Claude Codeのプロンプトパターンを検出
            lines = raw_output.split("\n")
            # 直近10行を確認
            for line in reversed(lines[-10:]):
                # 末尾のスペースを削除してチェック
                # Claude Code v2.xのプロンプトは ❯ で始まる
                stripped = line.strip()
                if stripped.endswith(">") or "❯" in stripped:
                    return True

            await asyncio.sleep(self._config.poll_interval)

        return False

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

        # 性格プロンプトを読み込んで--system-promptに渡す
        # Phase 0.5の検証により、tmux方式では--system-promptが使用可能
        personality_prompt = self._load_personality_prompt()
        # 改行をスペースに置換（1行のコマンドとして渡すため）
        single_line_prompt = personality_prompt.replace("\n", " ").replace("\r", " ")
        # シングルクォートをエスケープ
        escaped_prompt = single_line_prompt.replace("'", "'\\''")
        parts.append(f"{claude_path} --dangerously-skip-permissions --system-prompt '{escaped_prompt}'")

        return " && ".join(parts)

    # === 自動再起動機能 ===

    def start_auto_restart_monitor(self) -> None:
        """自動再起動監視を開始します。

        バックグラウンドでプロセスの死活監視タスクを起動します。
        """
        if self._monitor_task is None or self._monitor_task.done():
            self._monitor_task = asyncio.create_task(self._auto_restart_monitor())
            logger.info(
                f"プロセス '{self._config.name}' の自動再起動監視を開始しました "
                f"(上限: {self._config.max_restarts}回)"
            )

    async def _auto_restart_monitor(self) -> None:
        """プロセス監視ループ

        定期的にプロセスの状態を確認し、クラッシュしている場合は自動的に再起動します。
        """
        try:
            while self._running:
                await asyncio.sleep(RESTART_CHECK_INTERVAL)

                # プロセスの生存確認
                if not await self._check_process_alive():
                    logger.warning(f"プロセス '{self._config.name}' がクラッシュを検出しました")
                    await self._attempt_restart()
        except asyncio.CancelledError:
            logger.debug(f"プロセス '{self._config.name}' の監視タスクがキャンセルされました")
            raise

    async def _check_process_alive(self) -> bool:
        """プロセスが生存しているか確認します。

        Returns:
            生存している場合True、それ以外の場合False
        """
        try:
            # tmuxペインのキャプチャを取得してプロセスを確認
            raw_output = self._tmux.capture_pane(
                self._pane_index,
                start_line=CAPTURE_HISTORY_LINES,
            )

            # Claude Codeのプロンプトパターンを検出
            lines = raw_output.split("\n")
            for line in reversed(lines[-10:]):
                # Claude Code v2.xのプロンプトは ❯ で始まる
                stripped = line.strip()
                if stripped.endswith(">") or "❯" in stripped:
                    return True

            # プロンプトが見つからない場合はクラッシュとみなす
            return False
        except Exception as e:
            logger.error(f"プロセス生存確認中にエラーが発生: {e}")
            return False

    async def _attempt_restart(self) -> None:
        """プロセスの再起動を試みます。

        再起動回数の上限をチェックし、上限内であれば再起動します。
        """
        if not self._should_restart():
            logger.error(
                f"プロセス '{self._config.name}' の再起動回数が上限に達しました "
                f"({self._restart_count}/{self._config.max_restarts})"
            )
            self._running = False
            return

        self._restart_count += 1
        logger.info(
            f"プロセス '{self._config.name}' を再起動します "
            f"({self._restart_count}/{self._config.max_restarts}回目)"
        )

        # プロセスを停止してから再起動
        self._running = False

        try:
            # プロセスを強制終了
            self._tmux.send_keys(self._pane_index, "C-c")
            await asyncio.sleep(1.0)

            # プロセスを再起動（is_restart=Trueでカウントを維持）
            await self.launch_cc_in_pane(is_restart=True)
            logger.info(f"プロセス '{self._config.name}' の再起動が完了しました")
        except Exception as e:
            logger.error(f"プロセス '{self._config.name}' の再起動に失敗しました: {e}")
            self._running = False

    def _should_restart(self) -> bool:
        """再起動すべきか判定します。

        Returns:
            再起動すべき場合True、それ以外の場合False
        """
        return (
            self._config.auto_restart
            and self._restart_count < self._config.max_restarts
        )

    async def restart_process(self) -> None:
        """プロセスを手動で再起動します。

        監視タスクを一時停止し、プロセスを強制終了してから再起動します。

        Raises:
            CCProcessLaunchError: 再起動に失敗した場合
        """
        logger.info(f"プロセス '{self._config.name}' を手動再起動します")

        # 監視タスクを一時停止
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

        # プロセスを強制終了
        self._running = False
        self._tmux.send_keys(self._pane_index, "C-c")
        await asyncio.sleep(1.0)

        # 再起動回数をリセットして起動
        self._restart_count = 0
        await self.launch_cc_in_pane()

        logger.info(f"プロセス '{self._config.name}' の手動再起動が完了しました")
