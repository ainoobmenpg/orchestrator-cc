"""orchestrator-cc カスタム例外クラス定義

このモジュールでは、アプリケーションで使用するカスタム例外クラスを定義します。

エラーコード一覧:
- TEAM_NOT_FOUND: チームが見つからない
- TASK_NOT_FOUND: タスクが見つからない
- AGENT_NOT_FOUND: エージェントが見つからない
- INITIALIZATION_ERROR: 初期化エラー
- CONFIGURATION_ERROR: 設定エラー
- VALIDATION_ERROR: バリデーションエラー
"""

from typing import Any


class OrchestratorException(Exception):
    """orchestrator-cc の基底例外クラス

    すべてのカスタム例外はこのクラスを継承します。

    Attributes:
        message: エラーメッセージ
        error_code: エラーコード
        details: エラーの詳細情報（オプション）
    """

    def __init__(
        self,
        message: str,
        error_code: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """例外を初期化します。

        Args:
            message: エラーメッセージ
            error_code: エラーコード
            details: エラーの詳細情報（オプション）
        """
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """例外を辞書形式に変換します。

        Returns:
            例外情報を含む辞書
        """
        return {
            "error_code": self.error_code,
            "message": str(self),
            "details": self.details,
        }


class TeamNotFound(OrchestratorException):
    """チームが見つからない場合の例外"""

    def __init__(self, team_name: str) -> None:
        """例外を初期化します。

        Args:
            team_name: 見つからないチーム名
        """
        super().__init__(
            message=f"Team '{team_name}' not found",
            error_code="TEAM_NOT_FOUND",
            details={"team_name": team_name},
        )


class TaskNotFound(OrchestratorException):
    """タスクが見つからない場合の例外"""

    def __init__(self, task_id: str) -> None:
        """例外を初期化します。

        Args:
            task_id: 見つからないタスクID
        """
        super().__init__(
            message=f"Task '{task_id}' not found",
            error_code="TASK_NOT_FOUND",
            details={"task_id": task_id},
        )


class AgentNotFound(OrchestratorException):
    """エージェントが見つからない場合の例外"""

    def __init__(self, agent_id: str) -> None:
        """例外を初期化します。

        Args:
            agent_id: 見つからないエージェントID
        """
        super().__init__(
            message=f"Agent '{agent_id}' not found",
            error_code="AGENT_NOT_FOUND",
            details={"agent_id": agent_id},
        )


class InitializationError(OrchestratorException):
    """初期化エラー"""

    def __init__(self, component: str, reason: str) -> None:
        """例外を初期化します。

        Args:
            component: 初期化に失敗したコンポーネント名
            reason: 失敗の理由
        """
        super().__init__(
            message=f"Failed to initialize {component}: {reason}",
            error_code="INITIALIZATION_ERROR",
            details={"component": component, "reason": reason},
        )


class ConfigurationError(OrchestratorException):
    """設定エラー"""

    def __init__(self, setting_name: str, reason: str) -> None:
        """例外を初期化します。

        Args:
            setting_name: 設定項目名
            reason: エラーの理由
        """
        super().__init__(
            message=f"Invalid configuration for '{setting_name}': {reason}",
            error_code="CONFIGURATION_ERROR",
            details={"setting_name": setting_name, "reason": reason},
        )


class ValidationError(OrchestratorException):
    """バリデーションエラー"""

    def __init__(self, field: str, reason: str) -> None:
        """例外を初期化します。

        Args:
            field: バリデーションに失敗したフィールド名
            reason: エラーの理由
        """
        super().__init__(
            message=f"Validation failed for '{field}': {reason}",
            error_code="VALIDATION_ERROR",
            details={"field": field, "reason": reason},
        )


class ChannelError(OrchestratorException):
    """チャンネル関連エラー"""

    def __init__(self, channel_name: str, reason: str) -> None:
        """例外を初期化します。

        Args:
            channel_name: チャンネル名
            reason: エラーの理由
        """
        super().__init__(
            message=f"Channel error for '{channel_name}': {reason}",
            error_code="CHANNEL_ERROR",
            details={"channel_name": channel_name, "reason": reason},
        )
