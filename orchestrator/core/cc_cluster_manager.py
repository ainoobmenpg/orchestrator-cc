"""クラスタ管理モジュール

このモジュールでは、orchestrator-ccクラスタ全体を管理する
CCClusterManagerクラスを定義します。
"""

from pathlib import Path
from typing import Final

import yaml

from orchestrator.core.cc_process_launcher import (
    CCProcessLauncher,
)
from orchestrator.core.cc_process_models import (
    CCClusterConfig,
    CCProcessConfig,
    CCProcessRole,
)
from orchestrator.core.tmux_session_manager import (
    TmuxError,
    TmuxSessionManager,
)


# 例外クラス
class CCClusterError(TmuxError):
    """クラスタ管理に関する基本例外クラス"""

    pass


class CCClusterConfigError(CCClusterError):
    """クラスタ設定ファイルの読み込みエラー"""

    pass


class CCClusterAgentNotFoundError(CCClusterError):
    """指定されたエージェントが見つからない場合の例外"""

    pass


# 定数
CONFIG_PATH_KEY: Final[str] = "personality_prompt_path"
CONFIG_ROLE_KEY: Final[str] = "role"
CONFIG_MARKER_KEY: Final[str] = "marker"
CONFIG_PANE_KEY: Final[str] = "pane_index"


class CCClusterManager:
    """クラスタ全体を管理するクラス

    複数のCCProcessLauncherインスタンスを管理し、
    クラスタ全体の起動・停止・通信を制御します。

    Attributes:
        _config: クラスタ設定
        _tmux: TmuxSessionManagerインスタンス
        _launchers: エージェント名とCCProcessLauncherの辞書
    """

    def __init__(self, config_path: str) -> None:
        """設定ファイルからクラスタマネージャーを初期化します。

        Args:
            config_path: クラスタ設定ファイル（YAML）のパス

        Raises:
            CCClusterConfigError: 設定ファイルの読み込みに失敗した場合
            FileNotFoundError: 設定ファイルが存在しない場合
        """
        # 設定を読み込み
        self._config: CCClusterConfig = self._load_config(config_path)

        # tmuxセッションマネージャーを初期化
        self._tmux: TmuxSessionManager = TmuxSessionManager(
            self._config.session_name
        )

        # エージェントのランチャーを保持する辞書
        self._launchers: dict[str, CCProcessLauncher] = {}

    async def start(self) -> None:
        """クラスタ全体を起動します。

        全エージェントを起動し、初期化完了を待機します。

        Raises:
            CCClusterConfigError: セッションの作成に失敗した場合
            CCProcessLaunchError: いずれかのエージェントの起動に失敗した場合
        """
        # セッションが存在しない場合は作成
        if not self._tmux.session_exists():
            try:
                self._tmux.create_session()
                # 最初のペインはセッション作成時に自動的に作成される
                # 5つのペインを作成するため、適切な分割パターンを使用
                # ┌─────┬─────┐
                # │  0  │  1  │
                # ├─────┼─────┤
                # │  2  │  3  │
                # ├─────┴─────┤
                # │     4      │
                # └───────────┘
                # 垂直分割で2つに
                self._tmux.create_pane(split="h")  # Pane 1
                # 左側を上下分割
                self._tmux.create_pane(split="v", target_pane=0)  # Pane 2
                # 右側を上下分割
                self._tmux.create_pane(split="v", target_pane=1)  # Pane 3
                # 下部を左右統合して1つのペインに
                self._tmux.create_pane(split="v", target_pane=2)  # Pane 4
            except TmuxError as e:
                raise CCClusterConfigError(
                    f"セッションの作成に失敗しました: {e}"
                ) from e

        # 全エージェントを起動
        for agent_config in self._config.agents:
            launcher = CCProcessLauncher(
                agent_config, agent_config.pane_index, self._tmux
            )
            self._launchers[agent_config.name] = launcher
            await launcher.start()

    def connect(self) -> None:
        """既存のtmuxセッションに接続してランチャーを初期化します。

        すでに起動しているクラスタに接続する場合に使用します。
        セッションが存在しない場合はCCClusterConfigErrorを発生させます。

        Raises:
            CCClusterConfigError: セッションが存在しない場合
        """
        if not self._tmux.session_exists():
            raise CCClusterConfigError(
                f"セッション '{self._tmux._session_name}' が存在しません。"
                f"まず start コマンドでクラスタを起動してください。"
            )

        # ランチャーを初期化（プロセスは起動済みと仮定）
        for agent_config in self._config.agents:
            launcher = CCProcessLauncher(
                agent_config, agent_config.pane_index, self._tmux
            )
            launcher.mark_as_running()
            self._launchers[agent_config.name] = launcher

    async def stop(self) -> None:
        """クラスタ全体を停止します。

        全エージェントに停止シグナルを送信します。
        エージェントの停止順序は起動と逆順になります。

        Note:
            このメソッドはtmuxペインを破棄しません。
            セッションを完全に破棄するにはTmuxSessionManagerを使用してください。
        """
        # 起動と逆順で停止
        for agent_config in reversed(self._config.agents):
            if agent_config.name in self._launchers:
                await self._launchers[agent_config.name].stop()

    def get_agent(self, name: str) -> CCProcessLauncher:
        """指定されたエージェントを取得します。

        Args:
            name: エージェント名

        Returns:
            指定されたエージェントのCCProcessLauncherインスタンス

        Raises:
            CCClusterAgentNotFoundError: 指定されたエージェントが存在しない場合
        """
        if name not in self._launchers:
            raise CCClusterAgentNotFoundError(
                f"エージェント '{name}' は存在しません。 "
                f"利用可能なエージェント: {', '.join(self._launchers.keys())}"
            )
        return self._launchers[name]

    def get_launcher(self, agent_name: str) -> CCProcessLauncher:
        """エージェント名に対応するCCProcessLauncherを取得します。

        get_agent()のエイリアスメソッドです。

        Args:
            agent_name: エージェント名

        Returns:
            指定されたエージェントのCCProcessLauncherインスタンス

        Raises:
            CCClusterAgentNotFoundError: 指定されたエージェントが存在しない場合
        """
        return self.get_agent(agent_name)

    async def send_message(
        self, agent_name: str, message: str, timeout: float = 30.0
    ) -> str:
        """指定されたエージェントにメッセージを送信し、応答を取得します。

        Args:
            agent_name: 送信先エージェント名
            message: 送信するメッセージ
            timeout: タイムアウト時間（秒）

        Returns:
            エージェントからの応答

        Raises:
            CCClusterAgentNotFoundError: 指定されたエージェントが存在しない場合
            PaneTimeoutError: 応答がタイムアウトした場合
        """
        launcher = self.get_agent(agent_name)
        return await launcher.send_message(message, timeout=timeout)

    def get_status(self) -> dict:
        """クラスタの状態を取得します。

        Returns:
            クラスタの状態を表す辞書
            {
                "cluster_name": str,
                "session_name": str,
                "session_exists": bool,
                "agents": [
                    {
                        "name": str,
                        "role": str,
                        "running": bool,
                        "restart_count": int,
                        "last_activity": float
                    },
                    ...
                ]
            }
        """
        session_exists = self._tmux.session_exists()
        agents_status = []

        for agent_config in self._config.agents:
            launcher = self._launchers.get(agent_config.name)
            if launcher:
                agents_status.append({
                    "name": agent_config.name,
                    "role": agent_config.role.value,
                    "running": launcher.is_process_alive(),
                    "restart_count": launcher._restart_count,
                    "last_activity": launcher._last_activity_time
                })
            else:
                # ランチャーが未初期化の場合
                agents_status.append({
                    "name": agent_config.name,
                    "role": agent_config.role.value,
                    "running": False,
                    "restart_count": 0,
                    "last_activity": 0.0
                })

        return {
            "cluster_name": self._config.name,
            "session_name": self._config.session_name,
            "session_exists": session_exists,
            "agents": agents_status
        }

    def _load_config(self, path: str) -> CCClusterConfig:
        """YAML設定ファイルを読み込みます。

        Args:
            path: 設定ファイルのパス

        Returns:
            クラスタ設定

        Raises:
            CCClusterConfigError: 設定ファイルの読み込みに失敗した場合
            FileNotFoundError: 設定ファイルが存在しない場合
        """
        config_file = Path(path)

        # config ファイルのディレクトリを基準ディレクトリとして取得
        config_dir = config_file.parent.resolve()

        # ファイルの存在を確認
        if not config_file.exists():
            raise FileNotFoundError(f"設定ファイルが見つかりません: {path}")

        if not config_file.is_file():
            raise CCClusterConfigError(
                f"設定ファイルがファイルではありません: {path}"
            )

        # YAMLファイルを読み込み
        try:
            with open(config_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except OSError as e:
            raise CCClusterConfigError(
                f"設定ファイルの読み込みに失敗しました: {path}"
            ) from e
        except yaml.YAMLError as e:
            raise CCClusterConfigError(
                f"YAMLファイルのパースに失敗しました: {e}"
            ) from e

        # データ構造のバリデーション
        if not isinstance(data, dict):
            raise CCClusterConfigError(
                "設定ファイルのフォーマットが不正です（トップレベルは辞書である必要があります）"
            )

        if "cluster" not in data:
            raise CCClusterConfigError(
                "設定ファイルに 'cluster' キーがありません"
            )

        if "agents" not in data:
            raise CCClusterConfigError(
                "設定ファイルに 'agents' キーがありません"
            )

        cluster_data = data["cluster"]
        agents_data = data["agents"]

        # クラスタ設定を構築
        try:
            cluster_name = cluster_data["name"]
            session_name = cluster_data["session_name"]
            work_dir = cluster_data["work_dir"]
        except KeyError as e:
            raise CCClusterConfigError(
                f"'cluster' セクションに必須キーがありません: {e}"
            ) from e

        # エージェント設定を構築
        agents: list[CCProcessConfig] = []
        for agent_data in agents_data:
            try:
                name = agent_data["name"]
                role_str = agent_data[CONFIG_ROLE_KEY]
                personality_path = agent_data[CONFIG_PATH_KEY]
                marker = agent_data[CONFIG_MARKER_KEY]
                pane_index = agent_data[CONFIG_PANE_KEY]
            except KeyError as e:
                raise CCClusterConfigError(
                    f"エージェント設定に必須キーがありません: {e}"
                ) from e

            # 役割を列挙型に変換
            try:
                role = CCProcessRole(role_str)
            except ValueError as e:
                raise CCClusterConfigError(
                    f"無効な役割が指定されました: {role_str}"
                ) from e

            # 相対パスの場合は config ファイル基準で絶対パス化
            prompt_path = Path(personality_path)
            if not prompt_path.is_absolute():
                prompt_path = (config_dir / personality_path).resolve()
            personality_path = str(prompt_path)

            # オプションフィールドの取得
            wait_time = float(agent_data.get("wait_time", 5.0))
            poll_interval = float(agent_data.get("poll_interval", 0.5))

            # エージェント設定を作成
            agent_config = CCProcessConfig(
                name=name,
                role=role,
                personality_prompt_path=personality_path,
                marker=marker,
                pane_index=pane_index,
                work_dir=work_dir,
                wait_time=wait_time,
                poll_interval=poll_interval,
            )
            agents.append(agent_config)

        return CCClusterConfig(
            name=cluster_name,
            session_name=session_name,
            work_dir=work_dir,
            agents=agents,
        )
