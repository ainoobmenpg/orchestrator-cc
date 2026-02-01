"""Claude Code プロセスのデータモデル

このモジュールでは、orchestrator-ccで使用するデータモデルを定義します。
"""

from dataclasses import dataclass
from enum import Enum


class CCProcessRole(str, Enum):
    """エージェントの役割

    各エージェントの役割を定義する列挙型です。
    """

    GRAND_BOSS = "grand_boss"
    MIDDLE_MANAGER = "middle_manager"
    SPECIALIST_CODING_WRITING = "specialist_coding_writing"
    SPECIALIST_RESEARCH_ANALYSIS = "specialist_research_analysis"
    SPECIALIST_TESTING = "specialist_testing"


@dataclass
class CCProcessConfig:
    """エージェントの設定情報

    各エージェントプロセスの設定を保持するデータクラスです。

    Attributes:
        name: エージェント名（例: "grand_boss"）
        role: エージェントの役割
        personality_prompt_path: 性格プロンプトファイルのパス（必須）
        marker: 応答完了マーカー（合言葉、必須）
        pane_index: tmuxペイン番号（0以上、必須）
        work_dir: 作業ディレクトリ
        claude_path: Claude Code実行ファイルのパス
        auto_restart: 異常終了時に自動再起動するか
        max_restarts: 最大再起動回数（0以上）
        wait_time: 初期起動時の追加待機時間（秒）
        poll_interval: ポーリング間隔（秒）
    """

    name: str
    role: CCProcessRole
    personality_prompt_path: str
    marker: str
    pane_index: int
    work_dir: str = "/tmp/orchestrator-cc"
    claude_path: str = "claude"
    auto_restart: bool = True
    max_restarts: int = 3
    wait_time: float = 5.0
    poll_interval: float = 0.5

    def __post_init__(self) -> None:
        """バリデーション"""
        if self.pane_index < 0:
            raise ValueError("pane_indexは0以上である必要があります")
        if self.max_restarts < 0:
            raise ValueError("max_restartsは0以上である必要があります")
        if self.wait_time < 0:
            raise ValueError("wait_timeは0以上である必要があります")
        if self.wait_time > 60.0:
            raise ValueError("wait_timeは60秒以下である必要があります")
        if self.poll_interval <= 0:
            raise ValueError("poll_intervalは0より大きい必要があります")
        if self.poll_interval > 10.0:
            raise ValueError("poll_intervalは10秒以下である必要があります")


@dataclass
class CCClusterConfig:
    """クラスタ全体の設定

    orchestrator-ccクラスタ全体の設定を保持するデータクラスです。

    Attributes:
        name: クラスタ名
        session_name: tmuxセッション名
        work_dir: クラスタの作業ディレクトリ
        agents: エージェント設定のリスト
    """

    name: str
    session_name: str
    work_dir: str
    agents: list[CCProcessConfig]
