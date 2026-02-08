"""Agent Teamsデータモデル定義

このモジュールでは、Agent Teams監視用のデータモデルを定義します。
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class MessageCategory(str, Enum):
    """メッセージのカテゴリ"""

    ACTION = "action"
    THINKING = "thinking"
    EMOTION = "emotion"


class EmotionType(str, Enum):
    """感情タイプ"""

    CONFUSION = "confusion"
    SATISFACTION = "satisfaction"
    FOCUS = "focus"
    CONCERN = "concern"
    NEUTRAL = "neutral"


@dataclass
class TeamMember:
    """チームメンバー情報

    Attributes:
        agent_id: エージェントID
        name: 名前
        agent_type: エージェントタイプ
        model: モデル名
        joined_at: 参加日時
        cwd: 作業ディレクトリ
    """

    agent_id: str
    name: str
    agent_type: str
    model: str
    joined_at: int
    cwd: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TeamMember":
        """辞書からTeamMemberを作成します。"""
        return cls(
            agent_id=data.get("agentId", ""),
            name=data.get("name", ""),
            agent_type=data.get("agentType", ""),
            model=data.get("model", ""),
            joined_at=data.get("joinedAt", 0),
            cwd=data.get("cwd", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        """辞書に変換します。"""
        return {
            "agentId": self.agent_id,
            "name": self.name,
            "agentType": self.agent_type,
            "model": self.model,
            "joinedAt": self.joined_at,
            "cwd": self.cwd,
        }


@dataclass
class TeamInfo:
    """チーム情報

    Attributes:
        name: チーム名
        description: 説明
        created_at: 作成日時
        lead_agent_id: リードエージェントID
        lead_session_id: リードセッションID
        members: メンバーのリスト
    """

    name: str
    description: str
    created_at: int
    lead_agent_id: str
    lead_session_id: str
    members: list[TeamMember] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TeamInfo":
        """辞書からTeamInfoを作成します。"""
        members = [TeamMember.from_dict(m) for m in data.get("members", [])]
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            created_at=data.get("createdAt", 0),
            lead_agent_id=data.get("leadAgentId", ""),
            lead_session_id=data.get("leadSessionId", ""),
            members=members,
        )

    def to_dict(self) -> dict[str, Any]:
        """辞書に変換します。"""
        return {
            "name": self.name,
            "description": self.description,
            "createdAt": self.created_at,
            "leadAgentId": self.lead_agent_id,
            "leadSessionId": self.lead_session_id,
            "members": [m.to_dict() for m in self.members],
        }


@dataclass
class TeamMessage:
    """チームメッセージ

    Attributes:
        id: メッセージID
        sender: 送信者名
        recipient: 受信者名（空の場合は全体）
        content: メッセージ内容
        timestamp: タイムスタンプ
        message_type: メッセージタイプ
        summary: メッセージの要約（inboxファイル用）
        color: メッセージの色（inboxファイル用）
        read: 既読かどうか（inboxファイル用）
    """

    id: str = ""
    sender: str = ""
    recipient: str = ""
    content: str = ""
    timestamp: str = ""
    message_type: str = "message"
    summary: str = ""
    color: str = ""
    read: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TeamMessage":
        """辞書からTeamMessageを作成します。

        inboxファイル形式（from, text, summary, color, read）と
        標準形式（sender, content, id, recipient, type）の両方に対応します。
        """
        return cls(
            id=data.get("id", ""),
            # inbox形式の "from" を標準形式の "sender" にマッピング
            sender=data.get("sender", "") or data.get("from", ""),
            recipient=data.get("recipient", ""),
            # inbox形式の "text" を標準形式の "content" にマッピング
            content=data.get("content", "") or data.get("text", ""),
            timestamp=data.get("timestamp", ""),
            message_type=data.get("type", "message"),
            # inbox形式の追加フィールド
            summary=data.get("summary", ""),
            color=data.get("color", ""),
            read=data.get("read", False),
        )

    def to_dict(self) -> dict[str, Any]:
        """辞書に変換します。"""
        return {
            "id": self.id,
            "sender": self.sender,
            "recipient": self.recipient,
            "content": self.content,
            "text": self.content,  # inbox形式との互換性
            "timestamp": self.timestamp,
            "type": self.message_type,
            "summary": self.summary,
            "color": self.color,
            "read": self.read,
        }


@dataclass
class ThinkingLog:
    """思考ログ

    エージェントの思考プロセスを表現します。

    Attributes:
        agent_name: エージェント名
        content: 内容
        timestamp: タイムスタンプ
        category: カテゴリ（行動・思考・感情）
        emotion: 感情タイプ（カテゴリがemotionの場合）
    """

    agent_name: str
    content: str
    timestamp: str
    category: MessageCategory = MessageCategory.THINKING
    emotion: EmotionType = EmotionType.NEUTRAL

    def to_dict(self) -> dict[str, Any]:
        """辞書に変換します。"""
        return {
            "agentName": self.agent_name,
            "content": self.content,
            "timestamp": self.timestamp,
            "category": self.category.value,
            "emotion": self.emotion.value,
        }


@dataclass
class TaskInfo:
    """タスク情報

    Attributes:
        task_id: タスクID
        subject: タイトル
        description: 説明
        status: ステータス
        owner: 担当者
    """

    task_id: str
    subject: str
    description: str
    status: str
    owner: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskInfo":
        """辞書からTaskInfoを作成します。"""
        return cls(
            task_id=data.get("taskId", data.get("id", "")),
            subject=data.get("subject", ""),
            description=data.get("description", ""),
            status=data.get("status", "pending"),
            owner=data.get("owner", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        """辞書に変換します。"""
        return {
            "taskId": self.task_id,
            "subject": self.subject,
            "description": self.description,
            "status": self.status,
            "owner": self.owner,
        }


def _classify_message_category(content: str) -> MessageCategory:
    """メッセージ内容からカテゴリを分類します。

    Args:
        content: メッセージ内容

    Returns:
        メッセージカテゴリ
    """
    content_lower = content.lower()

    # 行動パターン
    action_patterns = [
        "tool used:",
        "reading file",
        "writing file",
        "editing file",
        "running command",
        "bash:",
        "read:",
        "edit:",
        "write:",
    ]

    # 思考パターン
    thinking_patterns = [
        "let me",
        "i need to",
        "based on",
        "i'll",
        "first",
        "next",
        "then",
        "let's",
        "analyzing",
        "checking",
        "planning",
    ]

    # 感情パターン
    emotion_patterns = [
        "confused",
        "unclear",
        "uncertain",
        "success",
        "complete",
        "solved",
        "error",
        "problem",
        "issue",
        "concern",
    ]

    for pattern in action_patterns:
        if pattern in content_lower:
            return MessageCategory.ACTION

    for pattern in thinking_patterns:
        if pattern in content_lower:
            return MessageCategory.THINKING

    for pattern in emotion_patterns:
        if pattern in content_lower:
            return MessageCategory.EMOTION

    return MessageCategory.THINKING


def _detect_emotion(content: str) -> EmotionType:
    """メッセージ内容から感情を検出します。

    Args:
        content: メッセージ内容

    Returns:
        感情タイプ
    """
    content_lower = content.lower()

    # 困惑
    if any(w in content_lower for w in ["confused", "unclear", "uncertain", "don't know", "?"]):
        return EmotionType.CONFUSION

    # 満足
    if any(w in content_lower for w in ["success", "complete", "solved", "done", "finished"]):
        return EmotionType.SATISFACTION

    # 関心
    if any(w in content_lower for w in ["error", "problem", "issue", "fail", "wrong"]):
        return EmotionType.CONCERN

    # フォーカス
    if any(w in content_lower for w in ["checking", "verifying", "analyzing", "focus"]):
        return EmotionType.FOCUS

    return EmotionType.NEUTRAL


def load_team_config(team_path: Path) -> TeamInfo | None:
    """チーム設定ファイルを読み込みます。

    Args:
        team_path: チームディレクトリのパス

    Returns:
        TeamInfo、読み込み失敗時はNone
    """
    config_path = team_path / "config.json"
    try:
        with open(config_path, encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"Loaded config.json from {config_path}: {data.get('name', 'unknown')}")
        return TeamInfo.from_dict(data)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load config from {config_path}: {e}")
        return None


def load_team_messages(team_path: Path) -> list[TeamMessage]:
    """チームのメッセージinboxを読み込みます。

    Args:
        team_path: チームディレクトリのパス

    Returns:
        TeamMessageのリスト
    """
    messages: list[TeamMessage] = []
    inbox_dir = team_path / "inboxes"

    if not inbox_dir.exists():
        return messages

    for inbox_file in inbox_dir.glob("*.json"):
        try:
            with open(inbox_file, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                for msg_data in data:
                    messages.append(TeamMessage.from_dict(msg_data))
            elif isinstance(data, dict):
                messages.append(TeamMessage.from_dict(data))
        except (FileNotFoundError, json.JSONDecodeError):
            continue

    return messages


def load_team_tasks(team_name: str) -> list[TaskInfo]:
    """チームのタスクを読み込みます。

    Args:
        team_name: チーム名

    Returns:
        TaskInfoのリスト
    """
    tasks: list[TaskInfo] = []
    task_dir = Path.home() / ".claude" / "tasks" / team_name

    if not task_dir.exists():
        return tasks

    for task_file in task_dir.glob("*.json"):
        try:
            with open(task_file, encoding="utf-8") as f:
                data = json.load(f)
            tasks.append(TaskInfo.from_dict(data))
        except (FileNotFoundError, json.JSONDecodeError):
            continue

    return tasks


# ============================================================================
# グローバルステート管理
# ============================================================================


@dataclass
class GlobalState:
    """ダッシュボードアプリケーションのグローバルステート

    各モジュール間で共有する状態を管理します。

    Attributes:
        ws_manager: WebSocketマネージャー
        ws_handler: WebSocketメッセージハンドラー
        teams_monitor: Teams監視モジュール
        thinking_log_handler: 思考ログハンドラー
        teams_manager: AgentTeamsManager
        health_monitor: ヘルスモニター
        event_loop: イベントループ（スレッドセーフなブロードキャスト用）
    """

    ws_manager: Any | None = None
    ws_handler: Any | None = None
    teams_monitor: Any | None = None
    thinking_log_handler: Any | None = None
    teams_manager: Any | None = None
    health_monitor: Any | None = None
    event_loop: Any | None = None
