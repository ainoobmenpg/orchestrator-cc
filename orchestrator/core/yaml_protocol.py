"""YAML通信プロトコルモジュール

このモジュールでは、YAMLベースのエージェント間通信プロトコルを定義します。
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class TaskStatus(str, Enum):
    """タスクの状態列挙型"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class MessageType(str, Enum):
    """メッセージタイプ

    エージェント間通信のメッセージ種類を定義する列挙型です。
    """

    TASK = "task"  # タスク依頼
    INFO = "info"  # 情報通知
    RESULT = "result"  # 結果報告
    ERROR = "error"  # エラー通知


class MessageFormatError(Exception):
    """メッセージフォーマットエラー"""

    pass


@dataclass
class TaskMessage:
    """タスクメッセージ

    エージェント間で送信されるメッセージを表すデータクラスです。

    Attributes:
        id: メッセージID
        from_agent: 送信元エージェント名（例: "grand_boss"）
        to_agent: 送信先エージェント名（例: "middle_manager"）
        type: メッセージタイプ
        content: メッセージ内容
        status: タスク状態
        timestamp: ISO 8601形式のタイムスタンプ
        metadata: 追加メタデータ（オプション）
    """

    id: str
    from_agent: str
    to_agent: str
    type: MessageType
    content: str
    status: TaskStatus = TaskStatus.PENDING
    timestamp: str | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """初期化後の処理"""
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.metadata is None:
            self.metadata = {}

    def to_yaml(self) -> str:
        """YAML形式にシリアライズします。

        Returns:
            YAML形式の文字列
        """
        data = {
            "id": self.id,
            "from": self.from_agent,
            "to": self.to_agent,
            "type": self.type.value,
            "status": self.status.value,
            "content": self.content,
            "timestamp": self.timestamp,
        }
        if self.metadata:
            data["metadata"] = self.metadata
        return yaml.dump(data, allow_unicode=True, sort_keys=False)

    def to_file(self, file_path: Path) -> None:
        """YAMLファイルとして保存します。

        Args:
            file_path: 保存先ファイルパス
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(self.to_yaml(), encoding="utf-8")

    @classmethod
    def from_yaml(cls, yaml_content: str) -> "TaskMessage":
        """YAML形式からデシリアライズします。

        Args:
            yaml_content: YAML形式の文字列

        Returns:
            TaskMessageインスタンス

        Raises:
            MessageFormatError: YAMLフォーマットが不正な場合
        """
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise MessageFormatError(f"YAMLのパースに失敗しました: {e}") from e

        # 必須フィールドのバリデーション
        required_fields = ["id", "from", "to", "type", "status", "content", "timestamp"]
        for field in required_fields:
            if field not in data:
                raise MessageFormatError(f"必須フィールド '{field}' がありません")

        # 文字列の列挙型を変換
        try:
            msg_type = MessageType(data["type"])
            task_status = TaskStatus(data["status"])
        except ValueError as e:
            raise MessageFormatError(f"無効な列挙値: {e}") from e

        return cls(
            id=data["id"],
            from_agent=data["from"],
            to_agent=data["to"],
            type=msg_type,
            status=task_status,
            content=data["content"],
            timestamp=data["timestamp"],
            metadata=data.get("metadata"),
        )

    @classmethod
    def from_file(cls, file_path: Path) -> "TaskMessage":
        """YAMLファイルから読み込みます。

        Args:
            file_path: 読み込み元ファイルパス

        Returns:
            TaskMessageインスタンス

        Raises:
            FileNotFoundError: ファイルが存在しない場合
            MessageFormatError: YAMLフォーマットが不正な場合
        """
        if not file_path.exists():
            raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")

        yaml_content = file_path.read_text(encoding="utf-8")
        return cls.from_yaml(yaml_content)


@dataclass
class AgentStatus:
    """エージェントの状態

    各エージェントの現在の状態を表すデータクラスです。

    Attributes:
        agent_name: エージェント名
        state: エージェントの状態（idle, working, completed, error）
        current_task: 現在のタスク（オプション）
        last_updated: 最終更新時刻（ISO 8601形式）
        statistics: 統計情報
    """

    agent_name: str
    state: str  # idle, working, completed, error
    current_task: str | None = None
    last_updated: str | None = None
    statistics: dict[str, int] | None = None

    def __post_init__(self) -> None:
        """初期化後の処理"""
        if self.last_updated is None:
            self.last_updated = datetime.now().isoformat()
        if self.statistics is None:
            self.statistics = {"tasks_completed": 0}

    def to_yaml(self) -> str:
        """YAML形式にシリアライズします。

        Returns:
            YAML形式の文字列
        """
        data = {
            "agent_name": self.agent_name,
            "state": self.state,
            "last_updated": self.last_updated,
            "statistics": self.statistics,
        }
        if self.current_task:
            data["current_task"] = self.current_task
        return yaml.dump(data, allow_unicode=True, sort_keys=False)

    def to_file(self, file_path: Path) -> None:
        """YAMLファイルとして保存します。

        Args:
            file_path: 保存先ファイルパス
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(self.to_yaml(), encoding="utf-8")

    @classmethod
    def from_yaml(cls, yaml_content: str) -> "AgentStatus":
        """YAML形式からデシリアライズします。

        Args:
            yaml_content: YAML形式の文字列

        Returns:
            AgentStatusインスタンス

        Raises:
            MessageFormatError: YAMLフォーマットが不正な場合
        """
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise MessageFormatError(f"YAMLのパースに失敗しました: {e}") from e

        # 必須フィールドのバリデーション
        required_fields = ["agent_name", "state", "last_updated", "statistics"]
        for field in required_fields:
            if field not in data:
                raise MessageFormatError(f"必須フィールド '{field}' がありません")

        return cls(
            agent_name=data["agent_name"],
            state=data["state"],
            current_task=data.get("current_task"),
            last_updated=data["last_updated"],
            statistics=data["statistics"],
        )

    @classmethod
    def from_file(cls, file_path: Path) -> "AgentStatus":
        """YAMLファイルから読み込みます。

        Args:
            file_path: 読み込み元ファイルパス

        Returns:
            AgentStatusインスタンス

        Raises:
            FileNotFoundError: ファイルが存在しない場合
            MessageFormatError: YAMLフォーマットが不正な場合
        """
        if not file_path.exists():
            raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")

        yaml_content = file_path.read_text(encoding="utf-8")
        return cls.from_yaml(yaml_content)


def generate_message_id() -> str:
    """一意なメッセージIDを生成します。

    Returns:
        メッセージID（タイムスタンプベース）
    """
    return datetime.now().strftime("%Y%m%d%H%M%S%f")
