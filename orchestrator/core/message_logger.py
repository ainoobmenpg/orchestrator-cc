"""メッセージログの記録

このモジュールでは、エージェント間通信のログを記録するMessageLoggerクラスを定義します。
"""

import json
import os
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from orchestrator.core.message_models import CCMessage, LogLevel, MessageType


class MessageLogger:
    """メッセージログを記録するクラス

    エージェント間のメッセージ送受信をJSONL形式で記録します。

    Attributes:
        _log_file: ログファイルのパス
        _enabled: ログ記録が有効かどうか
        _log_level: 現在のログレベル
        _max_file_size: ログローテーションの最大ファイルサイズ（バイト）
    """

    def __init__(
        self,
        log_file: str = "logs/messages.jsonl",
        enabled: bool = True,
        log_level: LogLevel = LogLevel.INFO,
        max_file_size: int | None = None,
    ) -> None:
        """MessageLoggerを初期化します。

        Args:
            log_file: ログファイルのパス（デフォルト: "logs/messages.jsonl"）
            enabled: ログ記録を有効にするか（デフォルト: True）
            log_level: ログレベル（デフォルト: INFO）。このレベル以上のログのみ記録されます。
            max_file_size: ログローテーションの最大ファイルサイズ（バイト）。
                          Noneの場合はローテーションしません（デフォルト: None）。
        """
        self._log_file = log_file
        self._enabled = enabled
        self._log_level = log_level
        self._max_file_size = max_file_size

        if self._enabled:
            # ログディレクトリを作成
            log_dir = os.path.dirname(log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)

    def log_send(
        self,
        from_agent: str,
        to_agent: str,
        content: str,
        msg_type: MessageType = MessageType.TASK,
        log_level: LogLevel = LogLevel.INFO,
    ) -> str:
        """メッセージ送信をログに記録します。

        Args:
            from_agent: 送信元エージェント名
            to_agent: 送信先エージェント名
            content: メッセージ内容
            msg_type: メッセージタイプ（デフォルト: TASK）
            log_level: ログレベル（デフォルト: INFO）

        Returns:
            メッセージID（UUID）
        """
        if not self._enabled or log_level.value < self._log_level.value:
            return str(uuid4())

        message = CCMessage(from_agent=from_agent, to_agent=to_agent, content=content)
        return self._log(message, msg_type, log_level)

    def log_receive(
        self,
        from_agent: str,
        to_agent: str,
        content: str,
        msg_type: MessageType = MessageType.RESULT,
        log_level: LogLevel = LogLevel.INFO,
    ) -> str:
        """メッセージ受信をログに記録します。

        Args:
            from_agent: 送信元エージェント名
            to_agent: 送信先エージェント名
            content: メッセージ内容
            msg_type: メッセージタイプ（デフォルト: RESULT）
            log_level: ログレベル（デフォルト: INFO）

        Returns:
            メッセージID（UUID）
        """
        if not self._enabled or log_level.value < self._log_level.value:
            return str(uuid4())

        message = CCMessage(from_agent=from_agent, to_agent=to_agent, content=content)
        return self._log(message, msg_type, log_level)

    def set_log_level(self, log_level: LogLevel) -> None:
        """ログレベルを設定します。

        Args:
            log_level: 新しいログレベル
        """
        self._log_level = log_level

    def get_log_level(self) -> LogLevel:
        """現在のログレベルを取得します。

        Returns:
            現在のログレベル
        """
        return self._log_level

    def _log(self, message: CCMessage, msg_type: MessageType, log_level: LogLevel) -> str:
        """メッセージをログに記録します。

        Args:
            message: メッセージオブジェクト
            msg_type: メッセージタイプ
            log_level: ログレベル

        Returns:
            メッセージID（UUID）
        """
        from orchestrator.core.message_models import MessageLogEntry

        msg_id = str(uuid4())
        timestamp = datetime.now().isoformat()

        entry = MessageLogEntry(
            timestamp=timestamp,
            id=msg_id,
            from_agent=message.from_agent,
            to_agent=message.to_agent,
            type=msg_type.value,
            content=message.content,
            level=log_level.value,
        )

        # コンソールに出力
        level_name = log_level.name
        print(f"[{entry.timestamp}] {level_name:5} {entry.from_agent} → {entry.to_agent} ({entry.type}): {entry.content}")

        # JSONL形式でファイルに保存
        with open(self._log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")

        # 書き込み後にローテーションが必要かチェック
        if self._max_file_size is not None:
            self._rotate_if_needed()

        return msg_id

    def _rotate_if_needed(self) -> None:
        """ログファイルがサイズ制限を超えている場合にローテーションします。

        既存のログファイルをリネームして、新しいログファイルを作成します。
        例: messages.jsonl -> messages.1.jsonl
        """
        assert self._max_file_size is not None, "max_file_size must be set"
        if not os.path.exists(self._log_file):
            return

        file_size = os.path.getsize(self._log_file)
        if file_size >= self._max_file_size:
            # ローテーション番号を決定
            counter = 1
            while True:
                rotated_path = self._get_rotated_path(counter)
                if not os.path.exists(rotated_path):
                    break
                counter += 1

            # 現在のログファイルをリネーム
            os.rename(self._log_file, rotated_path)

    def _get_rotated_path(self, counter: int) -> str:
        """ローテーション後のファイルパスを取得します。

        Args:
            counter: ローテーション番号

        Returns:
            ローテーション後のファイルパス
        """
        # 例: logs/messages.jsonl -> logs/messages.1.jsonl
        path = Path(self._log_file)
        return str(path.with_stem(f"{path.stem}.{counter}"))
