"""メッセージ関連のデータモデル

このモジュールでは、エージェント間通信で使用するメッセージデータモデルを定義します。
"""

from dataclasses import dataclass
from enum import Enum


class LogLevel(int, Enum):
    """ログレベル

    ログの出力レベルを定義する列挙型です。値が小さいほど詳細なログです。
    """

    DEBUG = 0  # デバッグ情報
    INFO = 1  # 通常の情報
    WARN = 2  # 警告
    ERROR = 3  # エラー


class MessageType(str, Enum):
    """メッセージタイプ

    エージェント間通信のメッセージ種類を定義する列挙型です。
    """

    TASK = "task"  # タスク依頼
    INFO = "info"  # 情報通知
    RESULT = "result"  # 結果報告
    ERROR = "error"  # エラー通知
    THOUGHT = "thought"  # 思考ログ


@dataclass
class CCMessage:
    """エージェント間のメッセージ

    エージェント間で送信される最小限の情報を保持するデータクラスです。

    Attributes:
        from_agent: 送信元エージェント名（例: "grand_boss"）
        to_agent: 送信先エージェント名（例: "middle_manager"）
        content: メッセージ内容
    """

    from_agent: str
    to_agent: str
    content: str


@dataclass
class MessageLogEntry:
    """メッセージログエントリ

    メッセージの送受信ログを記録するための完全な情報を保持するデータクラスです。

    Attributes:
        timestamp: ISO 8601形式のタイムスタンプ
        id: メッセージID（UUID）
        from_agent: 送信元エージェント名
        to_agent: 送信先エージェント名
        type: メッセージタイプ（task, info, result, error）
        content: メッセージ内容
        level: ログレベル（DEBUG=0, INFO=1, WARN=2, ERROR=3）
    """

    timestamp: str
    id: str
    from_agent: str
    to_agent: str
    type: str
    content: str
    level: int = 1  # デフォルトはINFO
