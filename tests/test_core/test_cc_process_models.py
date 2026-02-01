"""CCProcessModelの単体テスト"""

import pytest

from orchestrator.core.cc_process_models import (
    CCClusterConfig,
    CCProcessConfig,
    CCProcessRole,
)


class TestCCProcessRole:
    """CCProcessRole列挙型のテスト"""

    def test_role_values(self):
        """各役割の値が正しいことを確認"""
        assert CCProcessRole.GRAND_BOSS.value == "grand_boss"
        assert CCProcessRole.MIDDLE_MANAGER.value == "middle_manager"
        assert CCProcessRole.SPECIALIST_CODING_WRITING.value == "specialist_coding_writing"
        assert CCProcessRole.SPECIALIST_RESEARCH_ANALYSIS.value == "specialist_research_analysis"
        assert CCProcessRole.SPECIALIST_TESTING.value == "specialist_testing"

    def test_role_is_string_enum(self):
        """文字列列挙型として振る舞うことを確認"""
        role = CCProcessRole.GRAND_BOSS
        assert isinstance(role.value, str)
        assert role == "grand_boss"


class TestCCProcessConfig:
    """CCProcessConfigのテスト"""

    def test_creation_with_required_fields(self):
        """必須フィールドのみでインスタンスを作成"""
        config = CCProcessConfig(
            name="grand_boss",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="config/personalities/grand_boss.txt",
            marker="GRAND BOSS OK",
            pane_index=0,
        )
        assert config.name == "grand_boss"
        assert config.role == CCProcessRole.GRAND_BOSS
        assert config.personality_prompt_path == "config/personalities/grand_boss.txt"
        assert config.marker == "GRAND BOSS OK"
        assert config.pane_index == 0

    def test_creation_with_all_fields(self):
        """全フィールドを指定してインスタンスを作成"""
        config = CCProcessConfig(
            name="middle_manager",
            role=CCProcessRole.MIDDLE_MANAGER,
            personality_prompt_path="config/personalities/middle_manager.txt",
            marker="MANAGER OK",
            pane_index=1,
            work_dir="/tmp/test",
            claude_path="/usr/local/bin/claude",
            auto_restart=False,
            max_restarts=5,
        )
        assert config.name == "middle_manager"
        assert config.work_dir == "/tmp/test"
        assert config.claude_path == "/usr/local/bin/claude"
        assert config.auto_restart is False
        assert config.max_restarts == 5

    def test_default_values(self):
        """デフォルト値が正しく設定されることを確認"""
        config = CCProcessConfig(
            name="test",
            role=CCProcessRole.SPECIALIST_CODING_WRITING,
            personality_prompt_path="test.txt",
            marker="OK",
            pane_index=2,
        )
        assert config.work_dir == "/tmp/orchestrator-cc"
        assert config.claude_path == "claude"
        assert config.auto_restart is True
        assert config.max_restarts == 3
        assert config.wait_time == 5.0
        assert config.poll_interval == 0.5

    def test_validation_wait_time_negative(self):
        """wait_timeが負の値の場合にValueErrorを送出"""
        with pytest.raises(ValueError, match="wait_timeは0以上である必要があります"):
            CCProcessConfig(
                name="test",
                role=CCProcessRole.MIDDLE_MANAGER,
                personality_prompt_path="test.txt",
                marker="OK",
                pane_index=1,
                wait_time=-1.0,
            )

    def test_validation_wait_time_too_large(self):
        """wait_timeが上限超過の場合にValueErrorを送出"""
        with pytest.raises(ValueError, match="wait_timeは60秒以下である必要があります"):
            CCProcessConfig(
                name="test",
                role=CCProcessRole.MIDDLE_MANAGER,
                personality_prompt_path="test.txt",
                marker="OK",
                pane_index=1,
                wait_time=61.0,
            )

    def test_validation_wait_time_boundary(self):
        """wait_timeの境界値テスト"""
        # 0はOK
        config = CCProcessConfig(
            name="test",
            role=CCProcessRole.MIDDLE_MANAGER,
            personality_prompt_path="test.txt",
            marker="OK",
            pane_index=1,
            wait_time=0.0,
        )
        assert config.wait_time == 0.0

        # 60.0はOK
        config = CCProcessConfig(
            name="test",
            role=CCProcessRole.MIDDLE_MANAGER,
            personality_prompt_path="test.txt",
            marker="OK",
            pane_index=1,
            wait_time=60.0,
        )
        assert config.wait_time == 60.0

    def test_validation_poll_interval_zero(self):
        """poll_intervalが0の場合にValueErrorを送出"""
        with pytest.raises(ValueError, match="poll_intervalは0より大きい必要があります"):
            CCProcessConfig(
                name="test",
                role=CCProcessRole.MIDDLE_MANAGER,
                personality_prompt_path="test.txt",
                marker="OK",
                pane_index=1,
                poll_interval=0.0,
            )

    def test_validation_poll_interval_negative(self):
        """poll_intervalが負の値の場合にValueErrorを送出"""
        with pytest.raises(ValueError, match="poll_intervalは0より大きい必要があります"):
            CCProcessConfig(
                name="test",
                role=CCProcessRole.MIDDLE_MANAGER,
                personality_prompt_path="test.txt",
                marker="OK",
                pane_index=1,
                poll_interval=-0.1,
            )

    def test_validation_poll_interval_too_large(self):
        """poll_intervalが上限超過の場合にValueErrorを送出"""
        with pytest.raises(ValueError, match="poll_intervalは10秒以下である必要があります"):
            CCProcessConfig(
                name="test",
                role=CCProcessRole.MIDDLE_MANAGER,
                personality_prompt_path="test.txt",
                marker="OK",
                pane_index=1,
                poll_interval=10.1,
            )

    def test_validation_poll_interval_boundary(self):
        """poll_intervalの境界値テスト"""
        # 0.1はOK
        config = CCProcessConfig(
            name="test",
            role=CCProcessRole.MIDDLE_MANAGER,
            personality_prompt_path="test.txt",
            marker="OK",
            pane_index=1,
            poll_interval=0.1,
        )
        assert config.poll_interval == 0.1

        # 10.0はOK
        config = CCProcessConfig(
            name="test",
            role=CCProcessRole.MIDDLE_MANAGER,
            personality_prompt_path="test.txt",
            marker="OK",
            pane_index=1,
            poll_interval=10.0,
        )
        assert config.poll_interval == 10.0

    def test_validation_pane_index_negative(self):
        """pane_indexが負の値の場合にValueErrorを送出"""
        with pytest.raises(ValueError, match="pane_indexは0以上である必要があります"):
            CCProcessConfig(
                name="test",
                role=CCProcessRole.MIDDLE_MANAGER,
                personality_prompt_path="test.txt",
                marker="OK",
                pane_index=-1,
            )

    def test_validation_pane_index_zero(self):
        """pane_indexが0の場合は正常に動作"""
        config = CCProcessConfig(
            name="test",
            role=CCProcessRole.MIDDLE_MANAGER,
            personality_prompt_path="test.txt",
            marker="OK",
            pane_index=0,
        )
        assert config.pane_index == 0

    def test_validation_max_restarts_negative(self):
        """max_restartsが負の値の場合にValueErrorを送出"""
        with pytest.raises(ValueError, match="max_restartsは0以上である必要があります"):
            CCProcessConfig(
                name="test",
                role=CCProcessRole.MIDDLE_MANAGER,
                personality_prompt_path="test.txt",
                marker="OK",
                pane_index=1,
                max_restarts=-1,
            )

    def test_validation_max_restarts_zero(self):
        """max_restartsが0の場合は正常に動作"""
        config = CCProcessConfig(
            name="test",
            role=CCProcessRole.MIDDLE_MANAGER,
            personality_prompt_path="test.txt",
            marker="OK",
            pane_index=1,
            max_restarts=0,
        )
        assert config.max_restarts == 0


class TestCCClusterConfig:
    """CCClusterConfigのテスト"""

    def test_creation_with_single_agent(self):
        """単一のエージェントでクラスタ設定を作成"""
        agent = CCProcessConfig(
            name="grand_boss",
            role=CCProcessRole.GRAND_BOSS,
            personality_prompt_path="test.txt",
            marker="OK",
            pane_index=0,
        )
        cluster = CCClusterConfig(
            name="test-cluster",
            session_name="test-session",
            work_dir="/tmp/test",
            agents=[agent],
        )
        assert cluster.name == "test-cluster"
        assert cluster.session_name == "test-session"
        assert cluster.work_dir == "/tmp/test"
        assert len(cluster.agents) == 1
        assert cluster.agents[0].name == "grand_boss"

    def test_creation_with_multiple_agents(self):
        """複数のエージェントでクラスタ設定を作成"""
        agents = [
            CCProcessConfig(
                name="grand_boss",
                role=CCProcessRole.GRAND_BOSS,
                personality_prompt_path="boss.txt",
                marker="BOSS OK",
                pane_index=0,
            ),
            CCProcessConfig(
                name="middle_manager",
                role=CCProcessRole.MIDDLE_MANAGER,
                personality_prompt_path="manager.txt",
                marker="MANAGER OK",
                pane_index=1,
            ),
            CCProcessConfig(
                name="coding_specialist",
                role=CCProcessRole.SPECIALIST_CODING_WRITING,
                personality_prompt_path="coding.txt",
                marker="CODING OK",
                pane_index=2,
            ),
        ]
        cluster = CCClusterConfig(
            name="multi-cluster",
            session_name="multi-session",
            work_dir="/tmp/multi",
            agents=agents,
        )
        assert len(cluster.agents) == 3
        assert cluster.agents[0].pane_index == 0
        assert cluster.agents[1].pane_index == 1
        assert cluster.agents[2].pane_index == 2

    def test_creation_with_empty_agents(self):
        """空のエージェントリストでクラスタ設定を作成"""
        cluster = CCClusterConfig(
            name="empty-cluster",
            session_name="empty-session",
            work_dir="/tmp/empty",
            agents=[],
        )
        assert len(cluster.agents) == 0
