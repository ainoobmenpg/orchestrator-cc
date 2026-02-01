"""ダッシュボード管理モジュール

このモジュールでは、ステータスYAMLファイルを読み込み、
ダッシュボード（Markdown）を自動更新する機能を提供します。
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from orchestrator.core.yaml_protocol import AgentStatus

logger = logging.getLogger(__name__)


class DashboardManager:
    """ダッシュボード管理クラス

    status/agents/以下のYAMLファイルを読み込み、
    dashboard.mdを自動更新します。
    """

    # エージェントの表示名
    AGENT_DISPLAY_NAMES = {
        "grand_boss": "Grand Boss",
        "middle_manager": "Middle Manager",
        "coding_writing_specialist": "Coding & Writing Specialist",
        "research_analysis_specialist": "Research & Analysis Specialist",
        "testing_specialist": "Testing Specialist",
    }

    def __init__(self, status_dir: Path, dashboard_path: Path) -> None:
        """DashboardManagerを初期化します。

        Args:
            status_dir: ステータスYAMLファイルのディレクトリパス
            dashboard_path: ダッシュボードの出力先ファイルパス
        """
        self._status_dir = Path(status_dir)
        self._dashboard_path = Path(dashboard_path)

        # ディレクトリの存在確認・作成
        self._status_dir.mkdir(parents=True, exist_ok=True)
        self._dashboard_path.parent.mkdir(parents=True, exist_ok=True)

    async def update_dashboard(self) -> None:
        """ダッシュボードを更新します。"""
        try:
            # 全エージェントのステータスを読み込み
            agent_statuses = self._load_agent_statuses()

            # ダッシュボードを生成
            dashboard_content = self._generate_dashboard(agent_statuses)

            # ファイルに書き込み
            self._dashboard_path.write_text(dashboard_content, encoding="utf-8")

            logger.info(f"ダッシュボードを更新しました: {self._dashboard_path}")
        except Exception as e:
            logger.error(f"ダッシュボードの更新に失敗しました: {e}")

    def _load_agent_statuses(self) -> dict[str, dict[str, Any]]:
        """全エージェントのステータスを読み込みます。

        Returns:
            エージェント名とステータス情報の辞書
        """
        statuses: dict[str, dict[str, Any]] = {}

        for agent_name in self.AGENT_DISPLAY_NAMES:
            status_file = self._status_dir / f"{agent_name}.yaml"

            if status_file.exists():
                try:
                    agent_status = AgentStatus.from_file(status_file)
                    statuses[agent_name] = {
                        "agent_name": agent_status.agent_name,
                        "state": agent_status.state,
                        "current_task": agent_status.current_task,
                        "last_updated": agent_status.last_updated,
                        "statistics": agent_status.statistics,
                    }
                except Exception as e:
                    logger.warning(f"ステータスファイルの読み込みに失敗しました: {status_file}, {e}")
                    # デフォルト値を設定
                    statuses[agent_name] = self._get_default_status(agent_name)
            else:
                # ファイルが存在しない場合はデフォルト値
                statuses[agent_name] = self._get_default_status(agent_name)

        return statuses

    def _get_default_status(self, agent_name: str) -> dict[str, Any]:
        """デフォルトのステータス情報を取得します。

        Args:
            agent_name: エージェント名

        Returns:
            デフォルトステータス情報
        """
        return {
            "agent_name": agent_name,
            "state": "idle",
            "current_task": None,
            "last_updated": datetime.now().isoformat(),
            "statistics": {"tasks_completed": 0},
        }

    def _generate_dashboard(self, agent_statuses: dict[str, dict[str, Any]]) -> str:
        """ダッシュボードのMarkdownを生成します。

        Args:
            agent_statuses: エージェントのステータス情報

        Returns:
            Markdown形式のダッシュボード内容
        """
        lines = []

        # ヘッダー
        lines.append("# orchestrator-cc ダッシュボード\n")
        lines.append(f"**最終更新**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append("---\n")

        # サマリー
        lines.append("## 📊 サマリー\n")
        summary = self._generate_summary(agent_statuses)
        lines.extend(summary)
        lines.append("\n---\n")

        # エージェントステータス
        lines.append("## 👥 エージェントステータス\n")

        for agent_name, display_name in self.AGENT_DISPLAY_NAMES.items():
            status = agent_statuses.get(agent_name, self._get_default_status(agent_name))
            lines.append(self._generate_agent_section(agent_name, display_name, status))
            lines.append("")

        # フッター
        lines.append("---\n")
        lines.append("*このダッシュボードは自動更新されています*\n")

        return "\n".join(lines)

    def _generate_summary(self, agent_statuses: dict[str, dict[str, Any]]) -> list[str]:
        """サマリーセクションを生成します。

        Args:
            agent_statuses: エージェントのステータス情報

        Returns:
            サマリーの行リスト
        """
        lines = []

        # 状態ごとのカウント
        state_counts = {
            "idle": 0,
            "working": 0,
            "completed": 0,
            "error": 0,
        }

        total_tasks = 0

        for status in agent_statuses.values():
            state = status.get("state", "idle")
            if state in state_counts:
                state_counts[state] += 1

            stats = status.get("statistics", {})
            total_tasks += stats.get("tasks_completed", 0)

        lines.append(f"- **総完了タスク数**: {total_tasks}\n")
        lines.append(f"- **アイドル中**: {state_counts['idle']}\n")
        lines.append(f"- **作業中**: {state_counts['working']}\n")
        lines.append(f"- **完了**: {state_counts['completed']}\n")
        lines.append(f"- **エラー**: {state_counts['error']}\n")

        return lines

    def _generate_agent_section(
        self,
        _agent_name: str,
        display_name: str,
        status: dict[str, Any],
    ) -> str:
        """エージェントセクションを生成します。

        Args:
            agent_name: エージェント名
            display_name: 表示名
            status: ステータス情報

        Returns:
            エージェントセクションのMarkdown
        """
        state = status.get("state", "idle")
        state_emoji = self._get_state_emoji(state)
        current_task = status.get("current_task")
        last_updated = status.get("last_updated", "")
        statistics = status.get("statistics", {})
        tasks_completed = statistics.get("tasks_completed", 0)

        lines = []
        lines.append(f"### {state_emoji} {display_name}\n")
        lines.append(f"- **状態**: `{state}`\n")

        if current_task:
            lines.append(f"- **現在のタスク**: {current_task}\n")
        else:
            lines.append("- **現在のタスク**: なし\n")

        lines.append(f"- **完了タスク数**: {tasks_completed}\n")

        if last_updated:
            try:
                dt = datetime.fromisoformat(last_updated)
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                lines.append(f"- **最終更新**: {formatted_time}\n")
            except Exception:
                lines.append(f"- **最終更新**: {last_updated}\n")

        return "".join(lines)

    def _get_state_emoji(self, state: str) -> str:
        """状態に対応する絵文字を取得します。

        Args:
            state: 状態文字列

        Returns:
            絵文字
        """
        emoji_map = {
            "idle": "💤",
            "working": "⚙️",
            "completed": "✅",
            "error": "❌",
        }
        return emoji_map.get(state, "❓")


class DashboardManagerError(Exception):
    """ダッシュボード管理エラー"""

    pass


class StatusFileReadError(DashboardManagerError):
    """ステータスファイル読み込みエラー"""

    pass


class DashboardWriteError(DashboardManagerError):
    """ダッシュボード書き込みエラー"""

    pass
