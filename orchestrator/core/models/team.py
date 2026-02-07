"""Team models."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TeamConfig:
    """チーム設定

    Attributes:
        name: チーム名
        description: 説明
        agent_type: エージェントタイプ
        members: メンバーリスト
    """

    name: str
    description: str
    agent_type: str = "general-purpose"
    members: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """辞書に変換します。"""
        return {
            "name": self.name,
            "description": self.description,
            "agentType": self.agent_type,
            "members": self.members,
        }
