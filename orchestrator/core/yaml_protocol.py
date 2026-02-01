"""YAML通信プロトコル

このモジュールでは、エージェント間通信で使用するYAMLベースの
データモデルとプロトコルを定義します。
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class MessageType(str, Enum):
    """メッセージタイプ

    エージェント間で送信されるメッセージの種類を表します。
    """

    TASK = "task"
    INFO = "info"
    RESULT = "result"
    ERROR = "error"


class MessageStatus(str, Enum):
    """メッセージステータス

    メッセージの処理状態を表します。
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentState(str, Enum):
    """エージェント状態

    エージェントの現在の状態を表します。
    """

    IDLE = "idle"
    WORKING = "working"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class TaskMessage:
    """タスクメッセージ

    エージェント間で送信されるメッセージを表すデータクラスです。

    Attributes:
        id: メッセージID
        from: 送信元エージェント名
        to: 送信先エージェント名
        type: メッセージタイプ
        status: メッセージステータス
        content: メッセージ内容
        timestamp: タイムスタンプ（ISO 8601形式）
        metadata: 追加メタデータ
    """

    id: str
    from: str
    to: str
    type: MessageType
    status: MessageStatus
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """辞書に変換します。

        Returns:
            辞書形式のメッセージデータ
        """
        return {
            "id": self.id,
            "from": self.from,
            "to": self.to,
            "type": self.type.value,
            "status": self.status.value,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    def to_yaml(self, path: Path | str) -> None:
        """YAMLファイルに書き込みます。

        Args:
            path: 書き込み先のファイルパス
        """
        path_obj = Path(path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)

        with open(path_obj, "w", encoding="utf-8") as f:
            yaml.dump(self.to_dict(), f, allow_unicode=True, default_flow_style=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskMessage":
        """辞書からインスタンスを作成します。

        Args:
            data: 辞書形式のメッセージデータ

        Returns:
            TaskMessageインスタンス
        """
        return cls(
            id=data["id"],
            from=data["from"],
            to=data["to"],
            type=MessageType(data["type"]),
            status=MessageStatus(data["status"]),
            content=data["content"],
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_yaml(cls, path: Path | str) -> "TaskMessage":
        """YAMLファイルから読み込みます。

        Args:
            path: 読み込み元のファイルパス

        Returns:
            TaskMessageインスタンス
        """
        path_obj = Path(path)

        with open(path_obj, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return cls.from_dict(data)


@dataclass
class AgentStatus:
    """エージェントステータス

    エージェントの現在の状態を表すデータクラスです。

    Attributes:
        agent_name: エージェント名
        state: エージェント状態
        current_task: 現在処理中のタスクID
        last_updated: 最終更新時刻（ISO 8601形式）
        statistics: 統計情報
    """

    agent_name: str
    state: AgentState
    current_task: str | None
    last_updated: str
    statistics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """辞書に変換します。

        Returns:
            辞書形式のステータスデータ
        """
        return {
            "agent_name": self.agent_name,
            "state": self.state.value,
            "current_task": self.current_task,
            "last_updated": self.last_updated,
            "statistics": self.statistics,
        }

    def to_yaml(self, path: Path | str) -> None:
        """YAMLファイルに書き込みます。

        Args:
            path: 書き込み先のファイルパス
        """
        path_obj = Path(path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)

        with open(path_obj, "w", encoding="utf-8") as f:
            yaml.dump(self.to_dict(), f, allow_unicode=True, default_flow_style=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentStatus":
        """辞書からインスタンスを作成します。

        Args:
            data: 辞書形式のステータスデータ

        Returns:
            AgentStatusインスタンス
        """
        return cls(
            agent_name=data["agent_name"],
            state=AgentState(data["state"]),
            current_task=data.get("current_task"),
            last_updated=data["last_updated"],
            statistics=data.get("statistics", {}),
        )

    @classmethod
    def from_yaml(cls, path: Path | str) -> "AgentStatus":
        """YAMLファイルから読み込みます。

        Args:
            path: 読み込み元のファイルパス

        Returns:
            AgentStatusインスタンス
        """
        path_obj = Path(path)

        with open(path_obj, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return cls.from_dict(data)


async def read_message_async(path: Path | str) -> TaskMessage | None:
    """非同期でメッセージを読み込みます。

    Args:
        path: 読み込み元のファイルパス

    Returns:
        TaskMessageインスタンス。ファイルが存在しない場合はNone。
    """
    path_obj = Path(path)

    if not path_obj.exists():
        return None

    # I/Oをブロックしないようにスレッドプールで実行
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, TaskMessage.from_yaml, path_obj)


async def write_message_async(message: TaskMessage, path: Path | str) -> None:
    """非同期でメッセージを書き込みます。

    Args:
        message: 書き込むメッセージ
        path: 書き込み先のファイルパス
    """
    # I/Oをブロックしないようにスレッドプールで実行
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, message.to_yaml, path)


async def read_status_async(path: Path | str) -> AgentStatus | None:
    """非同期でステータスを読み込みます。

    Args:
        path: 読み込み元のファイルパス

    Returns:
        AgentStatusインスタンス。ファイルが存在しない場合はNone。
    """
    path_obj = Path(path)

    if not path_obj.exists():
        return None

    # I/Oをブロックしないようにスレッドプールで実行
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, AgentStatus.from_yaml, path_obj)


async def write_status_async(status: AgentStatus, path: Path | str) -> None:
    """非同期でステータスを書き込みます。

    Args:
        status: 書き込むステータス
        path: 書き込み先のファイルパス
    """
    # I/Oをブロックしないようにスレッドプールで実行
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, status.to_yaml, path)
