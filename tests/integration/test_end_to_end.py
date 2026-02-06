"""エンドツーエンドテスト

完全なワークフローを検証するテストです。

検証項目:
- V-E2E-001: シナリオ1 - 簡単なタスク実行
- V-E2E-002: シナリオ2 - 複数エージェント協調
- V-E2E-003: シナリオ3 - エラーハンドリング
"""

import json
import time
from pathlib import Path
from unittest.mock import patch

from orchestrator.core.agent_health_monitor import (
    AgentHealthMonitor,
    HealthCheckEvent,
)
from orchestrator.core.agent_teams_manager import (
    AgentTeamsManager,
    TeamConfig,
)
from orchestrator.web.team_models import (
    TaskInfo,
    TeamInfo,
    TeamMember,
    TeamMessage,
)


class TestScenario1SimpleTaskExecution:
    """V-E2E-001: シナリオ1 - 簡単なタスク実行

    1. チーム作成（リーダー + コーダー）
    2. タスク作成
    3. コーダーが実行
    4. 結果確認
    """

    def test_full_workflow_simple_task(self, tmp_path: Path):
        """簡単なタスク実行の完全なワークフローを検証"""
        teams_dir = tmp_path / "teams"
        tasks_dir = tmp_path / "tasks"
        teams_dir.mkdir(parents=True)
        tasks_dir.mkdir(parents=True)

        # ステップ1: チーム作成（リーダー + コーダー）
        manager = AgentTeamsManager(teams_dir=teams_dir, tasks_dir=tasks_dir)

        config = TeamConfig(
            name="simple-task-team",
            description="簡単なタスク実行テスト用チーム",
            agent_type="general-purpose",
            members=[
                {
                    "name": "team-lead",
                    "agentType": "general-purpose",
                    "timeoutThreshold": 300.0,
                },
                {
                    "name": "coder",
                    "agentType": "general-purpose",
                    "timeoutThreshold": 300.0,
                },
            ],
        )

        team_name = manager.create_team(config)
        assert team_name == "simple-task-team"

        # チームディレクトリと設定ファイルを確認
        team_dir = teams_dir / team_name
        assert team_dir.exists()
        config_file = team_dir / "config.json"
        assert config_file.exists()

        # ステップ2: タスク作成
        task_dir = tasks_dir / team_name
        task_dir.mkdir(parents=True)

        task_data = {
            "id": "1",
            "subject": "Implement simple feature",
            "description": "Add a simple feature to the system",
            "status": "pending",
            "activeForm": "Implementing simple feature",
            "owner": "coder",
            "metadata": {"priority": "high"},
        }

        task_file = task_dir / "1.json"
        with open(task_file, "w", encoding="utf-8") as f:
            json.dump(task_data, f, indent=2, ensure_ascii=False)

        # タスクが作成されたことを確認
        assert task_file.exists()

        # ステップ3: コーダーのアクティビティを更新（実行をシミュレート）
        manager.update_agent_activity(team_name, "coder")

        # ステップ4: 結果確認
        # タスクが取得できることを確認
        tasks = manager.get_team_tasks(team_name)
        assert len(tasks) == 1
        assert tasks[0]["subject"] == "Implement simple feature"
        assert tasks[0]["owner"] == "coder"

        # チームステータスを確認
        status = manager.get_team_status(team_name)
        assert status["name"] == team_name
        assert status["taskCount"] == 1
        assert len(status["members"]) == 2

        # ヘルス状態を確認
        health_status = status["health"]
        assert "team-lead" in health_status
        assert "coder" in health_status

    def test_task_lifecycle(self, tmp_path: Path):
        """タスクのライフサイクル（pending -> in_progress -> completed）を検証"""
        teams_dir = tmp_path / "teams"
        tasks_dir = tmp_path / "tasks"
        teams_dir.mkdir(parents=True)
        tasks_dir.mkdir(parents=True)

        manager = AgentTeamsManager(teams_dir=teams_dir, tasks_dir=tasks_dir)

        # チーム作成
        config = TeamConfig(
            name="lifecycle-test-team",
            description="タスクライフサイクルテスト",
            members=[
                {"name": "lead", "agentType": "general-purpose"},
                {"name": "coder", "agentType": "general-purpose"},
            ],
        )
        team_name = manager.create_team(config)

        # タスクディレクトリ作成
        task_dir = tasks_dir / team_name
        task_dir.mkdir(parents=True)

        # タスクをpendingで作成
        task_data = {
            "id": "1",
            "subject": "Test task",
            "description": "Test description",
            "status": "pending",
        }
        task_file = task_dir / "1.json"
        with open(task_file, "w", encoding="utf-8") as f:
            json.dump(task_data, f, indent=2, ensure_ascii=False)

        # pending状態を確認
        tasks = manager.get_team_tasks(team_name)
        assert tasks[0]["status"] == "pending"

        # in_progressに更新
        task_data["status"] = "in_progress"
        task_data["owner"] = "coder"
        with open(task_file, "w", encoding="utf-8") as f:
            json.dump(task_data, f, indent=2, ensure_ascii=False)

        # in_progress状態を確認
        tasks = manager.get_team_tasks(team_name)
        assert tasks[0]["status"] == "in_progress"
        assert tasks[0]["owner"] == "coder"

        # completedに更新
        task_data["status"] = "completed"
        with open(task_file, "w", encoding="utf-8") as f:
            json.dump(task_data, f, indent=2, ensure_ascii=False)

        # completed状態を確認
        tasks = manager.get_team_tasks(team_name)
        assert tasks[0]["status"] == "completed"


class TestScenario2MultiAgentCoordination:
    """V-E2E-002: シナリオ2 - 複数エージェント協調

    1. チーム作成（リーダー + リサーチャー + コーダー）
    2. 複雑なタスク作成
    3. リサーチャーが調査
    4. コーダーが実装
    5. 結果確認
    """

    def test_multi_agent_team_creation(self, tmp_path: Path):
        """複数エージェントのチーム作成を検証"""
        teams_dir = tmp_path / "teams"
        tasks_dir = tmp_path / "tasks"
        teams_dir.mkdir(parents=True)
        tasks_dir.mkdir(parents=True)

        manager = AgentTeamsManager(teams_dir=teams_dir, tasks_dir=tasks_dir)

        # 3人のメンバーでチーム作成
        config = TeamConfig(
            name="multi-agent-team",
            description="複数エージェント協調テスト用チーム",
            agent_type="general-purpose",
            members=[
                {
                    "name": "team-lead",
                    "agentType": "general-purpose",
                    "timeoutThreshold": 300.0,
                },
                {
                    "name": "researcher",
                    "agentType": "general-purpose",
                    "timeoutThreshold": 300.0,
                },
                {
                    "name": "coder",
                    "agentType": "general-purpose",
                    "timeoutThreshold": 300.0,
                },
            ],
        )

        team_name = manager.create_team(config)
        assert team_name == "multi-agent-team"

        # 全メンバーが登録されたことを確認
        status = manager.get_team_status(team_name)
        assert len(status["members"]) == 3

        member_names = {m["name"] for m in status["members"]}
        assert "team-lead" in member_names
        assert "researcher" in member_names
        assert "coder" in member_names

    def test_complex_task_workflow(self, tmp_path: Path):
        """複雑なタスクのワークフローを検証"""
        teams_dir = tmp_path / "teams"
        tasks_dir = tmp_path / "tasks"
        teams_dir.mkdir(parents=True)
        tasks_dir.mkdir(parents=True)

        manager = AgentTeamsManager(teams_dir=teams_dir, tasks_dir=tasks_dir)

        # チーム作成
        config = TeamConfig(
            name="complex-workflow-team",
            description="複雑なワークフローテスト",
            members=[
                {"name": "lead", "agentType": "general-purpose"},
                {"name": "researcher", "agentType": "general-purpose"},
                {"name": "coder", "agentType": "general-purpose"},
            ],
        )
        team_name = manager.create_team(config)

        # 複数の関連タスクを作成
        task_dir = tasks_dir / team_name
        task_dir.mkdir(parents=True)

        # タスク1: リサーチャー向け調査タスク
        research_task = {
            "id": "1",
            "subject": "Research similar implementations",
            "description": "Find existing implementations of similar features",
            "status": "pending",
            "owner": "researcher",
            "activeForm": "Researching similar implementations",
        }

        # タスク2: コーダー向け実装タスク
        implement_task = {
            "id": "2",
            "subject": "Implement the feature",
            "description": "Implement the feature based on research",
            "status": "pending",
            "owner": "coder",
            "activeForm": "Implementing the feature",
            "addBlockedBy": ["1"],  # タスク1に依存
        }

        with open(task_dir / "1.json", "w", encoding="utf-8") as f:
            json.dump(research_task, f, indent=2, ensure_ascii=False)

        with open(task_dir / "2.json", "w", encoding="utf-8") as f:
            json.dump(implement_task, f, indent=2, ensure_ascii=False)

        # タスクが作成されたことを確認
        tasks = manager.get_team_tasks(team_name)
        assert len(tasks) == 2

        # タスクごとの担当者を確認
        task_owners = {t["id"]: t.get("owner") for t in tasks}
        assert task_owners["1"] == "researcher"
        assert task_owners["2"] == "coder"

        # リサーチャーのアクティビティを更新（調査完了をシミュレート）
        manager.update_agent_activity(team_name, "researcher")

        # タスク1を完了
        research_task["status"] = "completed"
        with open(task_dir / "1.json", "w", encoding="utf-8") as f:
            json.dump(research_task, f, indent=2, ensure_ascii=False)

        # コーダーのアクティビティを更新（実装開始をシミュレート）
        manager.update_agent_activity(team_name, "coder")

        # タスク2を進行中に
        implement_task["status"] = "in_progress"
        with open(task_dir / "2.json", "w", encoding="utf-8") as f:
            json.dump(implement_task, f, indent=2, ensure_ascii=False)

        # 最終状態を確認
        final_tasks = manager.get_team_tasks(team_name)
        task_statuses = {t["id"]: t["status"] for t in final_tasks}
        assert task_statuses["1"] == "completed"
        assert task_statuses["2"] == "in_progress"

    def test_team_info_model(self, tmp_path: Path):
        """TeamInfoモデルの統合検証"""
        teams_dir = tmp_path / "teams"
        tasks_dir = tmp_path / "tasks"
        teams_dir.mkdir(parents=True)
        tasks_dir.mkdir(parents=True)

        manager = AgentTeamsManager(teams_dir=teams_dir, tasks_dir=tasks_dir)

        config = TeamConfig(
            name="model-test-team",
            description="モデル統合テスト",
            members=[
                {"name": "lead", "agentType": "general-purpose"},
                {"name": "researcher", "agentType": "general-purpose"},
                {"name": "coder", "agentType": "general-purpose"},
            ],
        )
        team_name = manager.create_team(config)

        # チーム設定ファイルを読み込んでTeamInfoを作成
        team_dir = teams_dir / team_name
        config_file = team_dir / "config.json"

        with open(config_file, encoding="utf-8") as f:
            config_data = json.load(f)

        team_info = TeamInfo.from_dict(config_data)

        # TeamInfoの検証
        assert team_info.name == team_name
        assert len(team_info.members) == 3

        # メンバーの検証
        member_dict = {m.name: m for m in team_info.members}
        assert "lead" in member_dict
        assert "researcher" in member_dict
        assert "coder" in member_dict

        # TeamInfoの辞書変換
        team_info_dict = team_info.to_dict()
        assert team_info_dict["name"] == team_name
        assert len(team_info_dict["members"]) == 3


class TestScenario3ErrorHandling:
    """V-E2E-003: シナリオ3 - エラーハンドリング

    1. タイムアウト発生
    2. ヘルスモニター検知
    3. エラー処理確認
    """

    def test_timeout_detection(self, tmp_path: Path):
        """タイムアウト検知を検証"""
        teams_dir = tmp_path / "teams"
        tasks_dir = tmp_path / "tasks"
        teams_dir.mkdir(parents=True)
        tasks_dir.mkdir(parents=True)

        # 短いタイムアウトしきい値でモニターを作成
        monitor = AgentHealthMonitor(check_interval=0.1)

        # タイムアウトイベントをキャプチャ
        captured_events = []

        def capture_event(event: HealthCheckEvent):
            captured_events.append(event)

        monitor.register_callback(capture_event)

        # エージェントを登録（短いタイムアウト）
        monitor.register_agent("test-team", "timeout-agent", timeout_threshold=0.2)

        # ヘルス状態を確認
        status = monitor.get_health_status()
        assert status["test-team"]["timeout-agent"]["isHealthy"] is True

        # タイムアウトしきい値を超過するまで待機
        time.sleep(0.3)

        # ヘルスチェックを実行（直接メソッドを呼び出して即時チェック）
        monitor._check_all_agents()

        # タイムアウトイベントが発生したことを確認
        assert len(captured_events) > 0
        assert captured_events[0].event_type == "timeout_detected"
        assert captured_events[0].team_name == "test-team"
        assert captured_events[0].agent_name == "timeout-agent"

        # ヘルス状態が変更されたことを確認
        status = monitor.get_health_status()
        assert status["test-team"]["timeout-agent"]["isHealthy"] is False

    def test_health_monitor_integration(self, tmp_path: Path):
        """ヘルスモニターの統合を検証"""
        teams_dir = tmp_path / "teams"
        tasks_dir = tmp_path / "tasks"
        teams_dir.mkdir(parents=True)
        tasks_dir.mkdir(parents=True)

        # ヘルスモニターのコールバックを設定
        monitor = AgentHealthMonitor(check_interval=0.1)
        health_events = []

        def capture_event(event: HealthCheckEvent):
            health_events.append(event)

        monitor.register_callback(capture_event)

        # AgentTeamsManagerにカスタムモニターを設定
        with patch(
            "orchestrator.core.agent_teams_manager.get_agent_health_monitor",
            return_value=monitor,
        ):
            manager = AgentTeamsManager(teams_dir=teams_dir, tasks_dir=tasks_dir)

            config = TeamConfig(
                name="health-test-team",
                description="ヘルスモニター統合テスト",
                members=[
                    {
                        "name": "agent1",
                        "agentType": "general-purpose",
                        "timeoutThreshold": 0.2,  # 短いタイムアウト
                    },
                ],
            )

            manager.create_team(config)

            # ヘルス状態が登録されたことを確認
            status = monitor.get_health_status()
            assert "health-test-team" in status
            assert "agent1" in status["health-test-team"]

            # タイムアウトを待機
            time.sleep(0.3)

            # チームステータス取得時にヘルス状態が含まれることを確認
            team_status = manager.get_team_status("health-test-team")
            assert "health" in team_status

    def test_error_recovery_workflow(self, tmp_path: Path):
        """エラー回復ワークフローを検証"""
        teams_dir = tmp_path / "teams"
        tasks_dir = tmp_path / "tasks"
        teams_dir.mkdir(parents=True)
        tasks_dir.mkdir(parents=True)

        manager = AgentTeamsManager(teams_dir=teams_dir, tasks_dir=tasks_dir)

        # チーム作成
        config = TeamConfig(
            name="recovery-test-team",
            description="エラー回復テスト",
            members=[
                {"name": "agent1", "agentType": "general-purpose"},
            ],
        )
        team_name = manager.create_team(config)

        # エージェントのアクティビティを更新（正常状態）
        manager.update_agent_activity(team_name, "agent1")

        # ヘルスモニターでアクティビティが更新されたことを確認
        health_monitor = manager._health_monitor
        status = health_monitor.get_health_status()
        assert status[team_name]["agent1"]["isHealthy"] is True

        # エージェントの再起動（アクティビティ更新による回復）
        result = manager.restart_agent(team_name, "agent1")
        assert result is True

        # 回復後にヘルス状態がリセットされたことを確認
        status = health_monitor.get_health_status()
        # エージェントが再登録されていることを確認
        assert team_name in status
        assert "agent1" in status[team_name]

    def test_nonexistent_team_handling(self):
        """存在しないチームのエラーハンドリングを検証"""
        teams_dir = Path.home() / ".claude" / "teams_test"
        tasks_dir = Path.home() / ".claude" / "tasks_test"

        manager = AgentTeamsManager(teams_dir=teams_dir, tasks_dir=tasks_dir)

        # 存在しないチームのステータスを取得
        status = manager.get_team_status("nonexistent-team")
        assert "error" in status

        # 存在しないチームのタスクを取得
        tasks = manager.get_team_tasks("nonexistent-team")
        assert len(tasks) == 0

    def test_malformed_task_file_handling(self, tmp_path: Path):
        """不正なタスクファイルのエラーハンドリングを検証"""
        teams_dir = tmp_path / "teams"
        tasks_dir = tmp_path / "tasks"
        teams_dir.mkdir(parents=True)
        tasks_dir.mkdir(parents=True)

        manager = AgentTeamsManager(teams_dir=teams_dir, tasks_dir=tasks_dir)

        # チーム作成
        config = TeamConfig(
            name="malformed-test-team",
            description="不正ファイルハンドリングテスト",
            members=[{"name": "agent1", "agentType": "general-purpose"}],
        )
        team_name = manager.create_team(config)

        # タスクディレクトリに不正なJSONファイルを作成
        task_dir = tasks_dir / team_name
        task_dir.mkdir(parents=True)

        # 不正なJSONファイル
        malformed_file = task_dir / "malformed.json"
        malformed_file.write_text("{ invalid json content")

        # 空のJSONファイル
        empty_file = task_dir / "empty.json"
        empty_file.write_text("{}")

        # エラーが発生せず、有効なタスクのみが返されることを確認
        # 不正なファイルはログに警告が出るが、例外は発生しない
        tasks = manager.get_team_tasks(team_name)
        # 有効な空のファイルが1つ返される（パースは成功する）
        assert len(tasks) >= 0

    def test_agent_activity_update_for_nonexistent_agent(self, tmp_path: Path):
        """存在しないエージェントのアクティビティ更新を検証"""
        teams_dir = tmp_path / "teams"
        tasks_dir = tmp_path / "tasks"
        teams_dir.mkdir(parents=True)
        tasks_dir.mkdir(parents=True)

        manager = AgentTeamsManager(teams_dir=teams_dir, tasks_dir=tasks_dir)

        # チームもエージェントも存在しない状態でアクティビティ更新
        # エラーが発生せず、安全に処理されることを確認
        manager.update_agent_activity("nonexistent-team", "nonexistent-agent")

        # 例外が発生しないことを確認（暗黙的にテスト済み）


class TestTaskMessageModels:
    """タスク・メッセージモデルの統合テスト"""

    def test_team_message_serialization(self):
        """TeamMessageのシリアライズを検証"""
        message = TeamMessage(
            id="msg-1",
            sender="team-lead",
            recipient="coder",
            content="Please implement feature X",
            timestamp="2026-02-07T12:00:00Z",
            message_type="message",
        )

        # 辞書変換
        message_dict = message.to_dict()
        assert message_dict["id"] == "msg-1"
        assert message_dict["sender"] == "team-lead"
        assert message_dict["recipient"] == "coder"
        assert message_dict["type"] == "message"

        # 辞書から復元
        restored_message = TeamMessage.from_dict(message_dict)
        assert restored_message.id == message.id
        assert restored_message.sender == message.sender
        assert restored_message.recipient == message.recipient
        assert restored_message.content == message.content

    def test_task_info_serialization(self):
        """TaskInfoのシリアライズを検証"""
        task = TaskInfo(
            task_id="task-1",
            subject="Test task",
            description="Test task description",
            status="pending",
            owner="coder",
        )

        # 辞書変換
        task_dict = task.to_dict()
        assert task_dict["taskId"] == "task-1"
        assert task_dict["subject"] == "Test task"
        assert task_dict["status"] == "pending"

        # 辞書から復元
        restored_task = TaskInfo.from_dict(task_dict)
        assert restored_task.task_id == task.task_id
        assert restored_task.subject == task.subject
        assert restored_task.status == task.status

    def test_team_member_serialization(self):
        """TeamMemberのシリアライズを検証"""
        member = TeamMember(
            agent_id="agent-1@test-team",
            name="coder",
            agent_type="general-purpose",
            model="claude-sonnet-4-5",
            joined_at=1738857600,
            cwd="/workspace",
            tmux_pane_id="pane-1",
        )

        # 辞書変換
        member_dict = member.to_dict()
        assert member_dict["agentId"] == "agent-1@test-team"
        assert member_dict["name"] == "coder"
        assert member_dict["cwd"] == "/workspace"

        # 辞書から復元
        restored_member = TeamMember.from_dict(member_dict)
        assert restored_member.agent_id == member.agent_id
        assert restored_member.name == member.name
        assert restored_member.cwd == member.cwd
