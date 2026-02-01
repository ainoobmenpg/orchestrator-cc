"""Middle Managerエージェント

このモジュールでは、タスク分解とSpecialistの取りまとめを行うMiddle Managerエージェントを定義します。
"""

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Final

from orchestrator.agents.cc_agent_base import CCAgentBase
from orchestrator.core.yaml_protocol import (
    AgentState,
    MessageStatus,
    MessageType as YAMLMessageType,
    TaskMessage,
    read_message_async,
)
from orchestrator.core.task_tracker import TaskTracker, TaskStatus

if TYPE_CHECKING:
    from orchestrator.core.cc_cluster_manager import CCClusterManager
    from orchestrator.core.message_logger import MessageLogger

# 定数
CODING_SPECIALIST_NAME: Final[str] = "specialist_coding_writing"
RESEARCH_SPECIALIST_NAME: Final[str] = "specialist_research_analysis"
TESTING_SPECIALIST_NAME: Final[str] = "specialist_testing"
DEFAULT_TASK_TIMEOUT: Final[float] = 120.0
YAML_POLL_INTERVAL: Final[float] = 1.0  # YAML確認間隔（秒）

GRAND_BOSS_NAME: Final[str] = "grand_boss"

# タスク分解のためのキーワードパターン
TASK_PATTERNS: Final[dict[str, list[str]]] = {
    CODING_SPECIALIST_NAME: [
        "実装",
        "コード",
        "関数",
        "クラス",
        "プログラム",
        "コーディング",
        "開発",
        "feature",
    ],
    RESEARCH_SPECIALIST_NAME: [
        "調査",
        "リサーチ",
        "ベストプラクティス",
        "方法",
        "分析",
        "研究",
        "research",
    ],
    TESTING_SPECIALIST_NAME: [
        "テスト",
        "検証",
        "確認",
        "チェック",
        "品質",
        "test",
        "verify",
    ],
}


class MiddleManagerAgent(CCAgentBase):
    """Middle Managerエージェント

    orchestrator-ccプロジェクトの中間管理職として、Grand Bossから
    タスクを受領し、各Specialistに割り当てて結果を集約します。

    Attributes:
        _name: エージェント名（"middle_manager"固定）
        _cluster_manager: CCClusterManagerインスタンス
        _logger: MessageLoggerインスタンス
        _default_timeout: デフォルトのタイムアウト時間（秒）

    Example:
        >>> from orchestrator.core import CCClusterManager
        >>> cluster = CCClusterManager("config/cc-cluster.yaml")
        >>> agent = MiddleManagerAgent("middle_manager", cluster_manager=cluster)
        >>> result = await agent.handle_task("新しい機能を実装してください")
        >>> print(result)
    """

    def __init__(
        self,
        name: str,
        cluster_manager: "CCClusterManager",
        logger: "MessageLogger | None" = None,
        default_timeout: float = DEFAULT_TASK_TIMEOUT,
    ) -> None:
        """MiddleManagerAgentを初期化します。

        Args:
            name: エージェント名（"middle_manager"である必要があります）
            cluster_manager: CCClusterManagerインスタンス
            logger: MessageLoggerインスタンス（Noneの場合は新規作成）
            default_timeout: デフォルトのタイムアウト時間（秒）

        Raises:
            ValueError: nameが"middle_manager"でない場合
            TypeError: cluster_managerがCCClusterManagerでない場合
        """
        # nameのバリデーション
        if name != "middle_manager":
            raise ValueError(f"nameは'middle_manager'である必要があります: {name}")

        # 親クラスを初期化
        super().__init__(name, cluster_manager, logger, default_timeout)

        # タスク追跡機能を初期化
        self._task_tracker = TaskTracker()

    async def handle_task(self, task: str) -> str:
        """タスクを処理します。

        Grand Bossからのタスクを受領し、分解して各Specialistに割り当て、結果を集約して返します。
        YAMLベースの通信を使用します。

        Args:
            task: Grand Bossからのタスク内容

        Returns:
            処理結果（各Specialistの結果を集約したもの）

        Raises:
            ValueError: taskが空の場合
            CCAgentSendError: Specialistへの送信に失敗した場合
            CCAgentTimeoutError: Specialistからの応答がタイムアウトした場合
            CCClusterAgentNotFoundError: Specialistが存在しない場合

        Note:
            - タスクは空であってはなりません
            - タイムアウトはインスタンスのdefault_timeoutを使用します
            - タスク分解→割り振り→集約のフローで処理します
        """
        if not task or not task.strip():
            raise ValueError("taskは空であってはなりません")

        # ステータスをWORKINGに更新
        await self._update_status(AgentState.WORKING, current_task="grand_boss_task")

        # 1. タスクを分解
        subtasks = self._decompose_task(task)
        self.log_thought(f"タスクを分解しました: {list(subtasks.keys())}")

        # 2. 各SpecialistにYAMLで割り振り
        results = await self._assign_tasks_yaml(subtasks)

        # 3. 結果を集約
        aggregated = await self._aggregate_results(results)
        self.log_thought("結果を集約しました")

        # ステータスをIDLEに戻す
        await self._update_status(
            AgentState.IDLE,
            statistics={"tasks_completed": 1, "subtasks_delegated": len(subtasks)}
        )

        return aggregated

    async def _assign_tasks_yaml(self, subtasks: dict[str, list[str]]) -> dict[str, str]:
        """各SpecialistにYAMLでタスクを割り振り、結果を収集します。

        Args:
            subtasks: Specialist名からサブタスクリストへの辞書

        Returns:
            Specialist名から結果への辞書

        Raises:
            CCAgentSendError: いずれかのSpecialistへの送信に失敗した場合
            CCAgentTimeoutError: Specialistからの応答がタイムアウトした場合
        """
        results: dict[str, str] = {}
        msg_ids: list[str] = []

        # 各Specialistにタスクを割り振り
        for specialist, task_list in subtasks.items():
            if not task_list:
                continue

            # 複数タスクがある場合は結合
            combined_task = "\n".join(task_list)

            # YAMLメッセージを送信
            msg_id = await self._write_yaml_message(
                to_agent=specialist,
                content=combined_task,
                msg_type=YAMLMessageType.TASK,
            )
            msg_ids.append(msg_id)
            self.log_thought(f"{specialist} にタスクを送信: {msg_id}")

        # 全ての結果を待機
        for msg_id in msg_ids:
            result = await self._wait_for_result(msg_id, timeout=self._default_timeout)
            # 送信元エージェントを特定（簡易実装）
            for specialist in [CODING_SPECIALIST_NAME, RESEARCH_SPECIALIST_NAME, TESTING_SPECIALIST_NAME]:
                # 結果からどのSpecialistかを推定
                results[specialist] = result

        return results

    async def _wait_for_result(self, msg_id: str, timeout: float) -> str:
        """YAMLメッセージの結果を待ちます。

        Args:
            msg_id: 待機するメッセージID
            timeout: タイムアウト時間（秒）

        Returns:
            結果の内容

        Raises:
            TimeoutError: タイムアウトした場合
        """
        start_time = asyncio.get_event_loop().time()

        while asyncio.get_event_loop().time() - start_time < timeout:
            # 各Specialistからの結果メッセージを確認
            for specialist in [CODING_SPECIALIST_NAME, RESEARCH_SPECIALIST_NAME, TESTING_SPECIALIST_NAME]:
                result_path = Path("queue") / f"{specialist}_to_{self._name}.yaml"
                message = await read_message_async(result_path)
                if message and message.status == MessageStatus.COMPLETED:
                    return message.content

            await asyncio.sleep(YAML_POLL_INTERVAL)

        raise TimeoutError(f"メッセージ {msg_id} の結果がタイムアウトしました")

    async def check_and_process_yaml_messages(self) -> None:
        """YAMLメッセージを確認して処理します。

        Grand Bossからのタスクメッセージを確認して処理します。
        """
        messages = await self._check_and_process_messages()

        for message in messages:
            if message.type == YAMLMessageType.TASK:
                self.log_thought(f"タスクを受信しました: {message.id}")
                # タスクを処理
                try:
                    result = await self.handle_task(message.content)
                    # 結果を返信
                    await self._write_yaml_message(
                        to_agent=GRAND_BOSS_NAME,
                        content=result,
                        msg_type=YAMLMessageType.RESULT,
                    )
                except Exception as e:
                    # エラーを返信
                    await self._write_yaml_message(
                        to_agent=GRAND_BOSS_NAME,
                        content=f"エラーが発生: {e}",
                        msg_type=YAMLMessageType.ERROR,
                    )

    async def run_yaml_loop(self) -> None:
        """YAMLメッセージ監視ループを実行します。

        定期的にYAMLメッセージを確認して処理します。
        """
        while True:
            try:
                await self.check_and_process_yaml_messages()
            except Exception as e:
                self.log_thought(f"YAML処理でエラーが発生: {e}")
            await asyncio.sleep(YAML_POLL_INTERVAL)

    def _decompose_task(self, task: str) -> dict[str, list[str]]:
        """タスクを各Specialist向けのサブタスクに分解します。

        キーワードパターンマッチングに基づいて、タスクを適切なSpecialistに割り振ります。
        どのSpecialistにもマッチしない場合は、全Specialistに同じタスクを送信します。

        Args:
            task: 分解するタスク内容

        Returns:
            Specialist名からサブタスクリストへの辞書
        """
        subtasks: dict[str, list[str]] = {
            CODING_SPECIALIST_NAME: [],
            RESEARCH_SPECIALIST_NAME: [],
            TESTING_SPECIALIST_NAME: [],
        }

        # キーワードパターンマッチング
        for specialist, keywords in TASK_PATTERNS.items():
            for keyword in keywords:
                if keyword in task:
                    subtasks[specialist].append(f"{keyword}に関連するタスク: {task}")
                    break

        # どのSpecialistにもマッチしない場合は全員に送信
        if all(len(tasks) == 0 for tasks in subtasks.values()):
            for specialist in subtasks.keys():
                subtasks[specialist].append(task)

        return subtasks

    async def _assign_tasks(self, subtasks: dict[str, list[str]]) -> dict[str, str]:
        """各Specialistにタスクを割り振り、結果を収集します。

        Args:
            subtasks: Specialist名からサブタスクリストへの辞書

        Returns:
            Specialist名から結果への辞書

        Raises:
            CCAgentSendError: いずれかのSpecialistへの送信に失敗した場合
            CCAgentTimeoutError: Specialistからの応答がタイムアウトした場合
            CCClusterAgentNotFoundError: Specialistが存在しない場合
        """
        results: dict[str, str] = {}

        # 各Specialistにタスクを割り振り
        for specialist, task_list in subtasks.items():
            if not task_list:
                continue

            # 複数タスクがある場合は結合
            combined_task = "\n".join(task_list)

            try:
                # タスク追跡に登録
                for task_desc in task_list:
                    subtask = self._task_tracker.create_subtask(task_desc, specialist)
                    self._task_tracker.update_status(subtask.id, TaskStatus.IN_PROGRESS)

                # メッセージを送信して応答を取得
                response = await self.send_to(
                    to_agent=specialist,
                    message=combined_task,
                    timeout=self._default_timeout,
                )

                results[specialist] = response

                # タスク追跡を完了に更新
                for task_desc in task_list:
                    subtask = self._task_tracker.get_subtasks_by_agent(specialist)[-1]
                    self._task_tracker.update_status(subtask.id, TaskStatus.COMPLETED, response)

            except Exception as e:
                # エラーが発生した場合はFAILEDに更新
                for task_desc in task_list:
                    subtask = self._task_tracker.get_subtasks_by_agent(specialist)[-1]
                    self._task_tracker.update_status(subtask.id, TaskStatus.FAILED, str(e))
                raise

        return results

    async def _aggregate_results(self, results: dict[str, str]) -> str:
        """各Specialistからの結果を集約します。

        Args:
            results: Specialist名から結果への辞書

        Returns:
            集約された結果文字列
        """
        if not results:
            return "結果がありませんでした"

        # 結果をSpecialistごとに分割
        sections: list[str] = []

        for specialist in [CODING_SPECIALIST_NAME, RESEARCH_SPECIALIST_NAME, TESTING_SPECIALIST_NAME]:
            if specialist in results:
                # Specialist名を読みやすい形式に変換
                specialist_name = specialist.replace("_", " ").title()
                sections.append(f"## {specialist_name}\n\n{results[specialist]}")

        # 進捗サマリーを追加
        summary = self._task_tracker.get_summary()

        return f"# Middle Managerによる集約結果\n\n進捗: {summary}\n\n" + "\n\n".join(sections)

    async def _forward_to_specialists(self, task: str) -> str:
        """全Specialistにタスクを転送し、最初の応答を返します。

        全Specialist（Coding、Research、Testing）に並列でタスクを送信し、
        最初に応答が返ってきたものを結果として返します。
        残りのリクエストはキャンセルされます。

        Args:
            task: 転送するタスク内容

        Returns:
            最初に応答したSpecialistからの応答

        Raises:
            CCAgentSendError: いずれかのSpecialistへの送信に失敗した場合
            CCAgentTimeoutError: 全Specialistからの応答がタイムアウトした場合
            CCClusterAgentNotFoundError: Specialistが存在しない場合
        """
        # 全Specialistに並列送信（Taskとして作成）
        tasks = [
            asyncio.create_task(
                self.send_to(to_agent=CODING_SPECIALIST_NAME, message=task, timeout=self._default_timeout)
            ),
            asyncio.create_task(
                self.send_to(to_agent=RESEARCH_SPECIALIST_NAME, message=task, timeout=self._default_timeout)
            ),
            asyncio.create_task(
                self.send_to(to_agent=TESTING_SPECIALIST_NAME, message=task, timeout=self._default_timeout)
            ),
        ]

        # 最初の完了を待つ
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

        # 待機中のタスクをキャンセル
        for t in pending:
            t.cancel()

        # 最初の応答を返す
        return done.pop().result()
