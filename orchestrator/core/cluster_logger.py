"""クラスタ通信ログ永続化モジュール

このモジュールでは、エージェント間通信ログの永続化と検索機能を提供します。
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal


@dataclass
class LogEntry:
    """ログエントリのデータクラス

    Attributes:
        timestamp: タイムスタンプ（ISO 8601形式）
        id: メッセージID
        from_agent: 送信元エージェント名
        to_agent: 送信先エージェント名
        type: メッセージタイプ
        content: メッセージ内容
        level: ログレベル
    """

    timestamp: str
    id: str
    from_agent: str
    to_agent: str
    type: str
    content: str
    level: str

    @classmethod
    def from_dict(cls, data: dict) -> "LogEntry":
        """辞書からLogEntryを作成します。

        Args:
            data: 辞書形式のログエントリ

        Returns:
            LogEntryインスタンス
        """
        return cls(
            timestamp=data.get("timestamp", ""),
            id=data.get("id", ""),
            from_agent=data.get("from_agent", ""),
            to_agent=data.get("to_agent", ""),
            type=data.get("type", ""),
            content=data.get("content", ""),
            level=data.get("level", ""),
        )


@dataclass
class LogFilter:
    """ログフィルタ条件

    Attributes:
        from_agent: 送信元エージェント名でフィルタ（オプション）
        to_agent: 送信先エージェント名でフィルタ（オプション）
        msg_type: メッセージタイプでフィルタ（オプション）
        level: ログレベルでフィルタ（オプション）
        start_time: 開始時刻（ISO 8601形式、オプション）
        end_time: 終了時刻（ISO 8601形式、オプション）
        limit: 最大取得数（オプション）
    """

    from_agent: str | None = None
    to_agent: str | None = None
    msg_type: str | None = None
    level: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    limit: int | None = None


class ClusterLogger:
    """クラスタ通信ログ管理クラス

    エージェント間の通信ログをJSON形式で永続化し、検索・フィルタリング機能を提供します。

    Attributes:
        _log_file: ログファイルのパス
        _log_dir: ログディレクトリのパス
    """

    def __init__(self, log_file: str = "logs/messages.jsonl", log_dir: str = "logs") -> None:
        """ClusterLoggerを初期化します。

        Args:
            log_file: ログファイルのパス（デフォルト: "logs/messages.jsonl"）
            log_dir: ログディレクトリのパス（デフォルト: "logs"）
        """
        self._log_file = log_file
        self._log_dir = Path(log_dir)

    def read_logs(self, log_filter: LogFilter | None = None) -> list[LogEntry]:
        """ログを読み込みます。

        Args:
            log_filter: フィルタ条件（オプション）

        Returns:
            ログエントリのリスト
        """
        entries: list[LogEntry] = []

        # メインのログファイルを読み込み
        log_path = self._log_dir / self._log_file
        if log_path.exists():
            entries.extend(self._read_log_file(log_path))

        # ローテートされたログファイルも読み込み
        for rotated_file in sorted(self._log_dir.glob("*.jsonl")):
            if rotated_file != log_path:
                entries.extend(self._read_log_file(rotated_file))

        # タイムスタンプでソート（古い順）
        entries.sort(key=lambda e: e.timestamp)

        # フィルタ適用
        if log_filter:
            entries = self._apply_filter(entries, log_filter)

        return entries

    def _read_log_file(self, file_path: Path) -> list[LogEntry]:
        """単一のログファイルを読み込みます。

        Args:
            file_path: ログファイルのパス

        Returns:
            ログエントリのリスト
        """
        entries: list[LogEntry] = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            entries.append(LogEntry.from_dict(data))
                        except json.JSONDecodeError:
                            continue
        except FileNotFoundError:
            pass

        return entries

    def _apply_filter(self, entries: list[LogEntry], log_filter: LogFilter) -> list[LogEntry]:
        """フィルタを適用します。

        Args:
            entries: ログエントリのリスト
            log_filter: フィルタ条件

        Returns:
            フィルタ適用後のログエントリのリスト
        """
        filtered = entries

        if log_filter.from_agent:
            filtered = [e for e in filtered if e.from_agent == log_filter.from_agent]

        if log_filter.to_agent:
            filtered = [e for e in filtered if e.to_agent == log_filter.to_agent]

        if log_filter.msg_type:
            filtered = [e for e in filtered if e.type == log_filter.msg_type]

        if log_filter.level:
            filtered = [e for e in filtered if e.level == log_filter.level]

        if log_filter.start_time:
            filtered = [e for e in filtered if e.timestamp >= log_filter.start_time]

        if log_filter.end_time:
            filtered = [e for e in filtered if e.timestamp <= log_filter.end_time]

        if log_filter.limit:
            filtered = filtered[: log_filter.limit]

        return filtered

    def get_stats(self) -> dict[str, int]:
        """ログ統計情報を取得します。

        Returns:
            統計情報の辞書
        """
        entries = self.read_logs()

        stats: dict[str, int] = {
            "total": len(entries),
            "by_agent": {},
            "by_type": {},
            "by_level": {},
        }

        for entry in entries:
            # エージェント別カウント
            stats["by_agent"][entry.from_agent] = stats["by_agent"].get(entry.from_agent, 0) + 1

            # タイプ別カウント
            stats["by_type"][entry.type] = stats["by_type"].get(entry.type, 0) + 1

            # レベル別カウント
            stats["by_level"][entry.level] = stats["by_level"].get(entry.level, 0) + 1

        return stats

    def export_to_json(self, output_path: str, log_filter: LogFilter | None = None) -> None:
        """ログをJSONファイルにエクスポートします。

        Args:
            output_path: 出力ファイルのパス
            log_filter: フィルタ条件（オプション）
        """
        entries = self.read_logs(log_filter)

        data = [
            {
                "timestamp": e.timestamp,
                "id": e.id,
                "from_agent": e.from_agent,
                "to_agent": e.to_agent,
                "type": e.type,
                "content": e.content,
                "level": e.level,
            }
            for e in entries
        ]

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        with open(output, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_recent_logs(self, count: int = 10) -> list[LogEntry]:
        """最近のログを取得します。

        Args:
            count: 取得するログ数（デフォルト: 10）

        Returns:
            最近のログエントリのリスト（新しい順）
        """
        entries = self.read_logs()
        # 新しい順にして先頭から取得
        return list(reversed(entries))[:count]
