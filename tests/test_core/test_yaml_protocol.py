"""yaml_protocolモジュールのユニットテスト"""

from pathlib import Path
import tempfile

import pytest

from orchestrator.core.yaml_protocol import (
    AgentStatus,
    MessageFormatError,
    MessageType,
    TaskMessage,
    TaskStatus,
    generate_message_id,
)


class TestTaskMessage:
    """TaskMessageクラスのテスト"""

    def test_init(self) -> None:
        """初期化テスト"""
        msg = TaskMessage(
            id="msg-001",
            from_agent="grand_boss",
            to_agent="middle_manager",
            type=MessageType.TASK,
            content="テストタスク",
        )

        assert msg.id == "msg-001"
        assert msg.from_agent == "grand_boss"
        assert msg.to_agent == "middle_manager"
        assert msg.type == MessageType.TASK
        assert msg.content == "テストタスク"
        assert msg.status == TaskStatus.PENDING
        assert msg.timestamp is not None
        assert msg.metadata == {}

    def test_to_yaml(self) -> None:
        """YAMLシリアライゼーションテスト"""
        msg = TaskMessage(
            id="msg-002",
            from_agent="middle_manager",
            to_agent="coding_writing_specialist",
            type=MessageType.TASK,
            content="実装してください",
        )

        yaml_str = msg.to_yaml()

        assert "id: msg-002" in yaml_str
        assert "from: middle_manager" in yaml_str
        assert "to: coding_writing_specialist" in yaml_str
        assert "type: task" in yaml_str
        assert "status: pending" in yaml_str
        assert "content:" in yaml_str
        assert "実装してください" in yaml_str

    def test_from_yaml(self) -> None:
        """YAMLデシリアライゼーションテスト"""
        yaml_content = """
id: msg-003
from: research_analysis_specialist
to: middle_manager
type: result
status: completed
content: |
  調査結果です
timestamp: 2026-02-01T10:00:00
"""
        msg = TaskMessage.from_yaml(yaml_content)

        assert msg.id == "msg-003"
        assert msg.from_agent == "research_analysis_specialist"
        assert msg.to_agent == "middle_manager"
        assert msg.type == MessageType.RESULT
        assert msg.status == TaskStatus.COMPLETED
        # contentは改行を含む場合があるのでトリムして比較
        assert msg.content.strip() == "調査結果です"
        # YAMLがtimestampをdatetimeとしてパースする場合がある
        assert str(msg.timestamp) == "2026-02-01 10:00:00" or msg.timestamp == "2026-02-01T10:00:00"

    def test_from_yaml_with_metadata(self) -> None:
        """メタデータ付きのYAMLデシリアライゼーションテスト"""
        yaml_content = """
id: msg-004
from: testing_specialist
to: middle_manager
type: error
status: failed
content: |
  テスト失敗
timestamp: 2026-02-01T11:00:00
metadata:
  error_code: 500
  retry_count: 3
"""
        msg = TaskMessage.from_yaml(yaml_content)

        assert msg.id == "msg-004"
        assert msg.type == MessageType.ERROR
        assert msg.status == TaskStatus.FAILED
        assert msg.metadata == {"error_code": 500, "retry_count": 3}

    def test_from_yaml_invalid_format(self) -> None:
        """不正なYAMLフォーマットのテスト"""
        with pytest.raises(MessageFormatError):
            TaskMessage.from_yaml("invalid yaml content [[")

    def test_from_yaml_missing_required_field(self) -> None:
        """必須フィールド欠如のテスト"""
        yaml_content = """
id: msg-005
from: grand_boss
to: middle_manager
# typeが欠如
status: pending
content: テスト
"""
        with pytest.raises(MessageFormatError):
            TaskMessage.from_yaml(yaml_content)

    def test_from_yaml_invalid_enum_value(self) -> None:
        """無効な列挙値のテスト"""
        yaml_content = """
id: msg-006
from: grand_boss
to: middle_manager
type: invalid_type
status: pending
content: テスト
timestamp: 2026-02-01T10:00:00
"""
        with pytest.raises(MessageFormatError):
            TaskMessage.from_yaml(yaml_content)

    def test_to_file_and_from_file(self) -> None:
        """ファイル書き込み・読み込みテスト"""
        msg = TaskMessage(
            id="msg-007",
            from_agent="middle_manager",
            to_agent="grand_boss",
            type=MessageType.RESULT,
            content="完了しました",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_message.yaml"

            # ファイルに書き込み
            msg.to_file(file_path)
            assert file_path.exists()

            # ファイルから読み込み
            loaded_msg = TaskMessage.from_file(file_path)

            assert loaded_msg.id == msg.id
            assert loaded_msg.from_agent == msg.from_agent
            assert loaded_msg.to_agent == msg.to_agent
            assert loaded_msg.type == msg.type
            assert loaded_msg.content == msg.content

    def test_from_file_not_found(self) -> None:
        """ファイルが存在しない場合のテスト"""
        with pytest.raises(FileNotFoundError):
            TaskMessage.from_file(Path("/nonexistent/path/file.yaml"))


class TestAgentStatus:
    """AgentStatusクラスのテスト"""

    def test_init(self) -> None:
        """初期化テスト"""
        status = AgentStatus(
            agent_name="grand_boss",
            state="idle",
        )

        assert status.agent_name == "grand_boss"
        assert status.state == "idle"
        assert status.current_task is None
        assert status.last_updated is not None
        assert status.statistics == {"tasks_completed": 0}

    def test_init_with_current_task(self) -> None:
        """current_task付きの初期化テスト"""
        status = AgentStatus(
            agent_name="middle_manager",
            state="working",
            current_task="タスクを分解中",
        )

        assert status.current_task == "タスクを分解中"

    def test_to_yaml(self) -> None:
        """YAMLシリアライゼーションテスト"""
        status = AgentStatus(
            agent_name="coding_writing_specialist",
            state="working",
            current_task="実装中",
        )

        yaml_str = status.to_yaml()

        assert "agent_name: coding_writing_specialist" in yaml_str
        assert "state: working" in yaml_str
        assert "current_task: 実装中" in yaml_str

    def test_to_yaml_no_current_task(self) -> None:
        """current_taskがない場合のYAMLシリアライゼーションテスト"""
        status = AgentStatus(
            agent_name="research_analysis_specialist",
            state="idle",
        )

        yaml_str = status.to_yaml()

        assert "current_task:" not in yaml_str

    def test_from_yaml(self) -> None:
        """YAMLデシリアライゼーションテスト"""
        yaml_content = """
agent_name: testing_specialist
state: working
current_task: テスト実行中
last_updated: 2026-02-01T10:00:00
statistics:
  tasks_completed: 5
"""
        status = AgentStatus.from_yaml(yaml_content)

        assert status.agent_name == "testing_specialist"
        assert status.state == "working"
        assert status.current_task == "テスト実行中"
        assert status.statistics == {"tasks_completed": 5}

    def test_from_yaml_no_current_task(self) -> None:
        """current_taskがない場合のYAMLデシリアライゼーションテスト"""
        yaml_content = """
agent_name: grand_boss
state: idle
last_updated: 2026-02-01T10:00:00
statistics:
  tasks_completed: 10
"""
        status = AgentStatus.from_yaml(yaml_content)

        assert status.current_task is None

    def test_to_file_and_from_file(self) -> None:
        """ファイル書き込み・読み込みテスト"""
        status = AgentStatus(
            agent_name="middle_manager",
            state="working",
            current_task="タスク管理中",
            statistics={"tasks_completed": 15},
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_status.yaml"

            # ファイルに書き込み
            status.to_file(file_path)
            assert file_path.exists()

            # ファイルから読み込み
            loaded_status = AgentStatus.from_file(file_path)

            assert loaded_status.agent_name == status.agent_name
            assert loaded_status.state == status.state
            assert loaded_status.current_task == status.current_task
            assert loaded_status.statistics == status.statistics


class TestGenerateMessageId:
    """generate_message_id関数のテスト"""

    def test_generate_message_id(self) -> None:
        """メッセージID生成テスト"""
        msg_id = generate_message_id()

        assert isinstance(msg_id, str)
        assert len(msg_id) > 0
        # タイムスタンプベースなので、異なる時刻で呼び出すと異なるIDになる
        import time

        time.sleep(0.01)
        msg_id2 = generate_message_id()
        assert msg_id != msg_id2
