"""Specialistエージェントの単体テスト

このモジュールでは、3種類のSpecialistエージェントクラスの単体テストを実装します。
- CodingWritingSpecialist
- ResearchAnalysisSpecialist
- TestingSpecialist
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from orchestrator.agents.specialists import (
    CODING_MARKER,
    CODING_SPECIALIST_NAME,
    DEFAULT_TASK_TIMEOUT,
    RESEARCH_MARKER,
    RESEARCH_SPECIALIST_NAME,
    TESTING_MARKER,
    TESTING_SPECIALIST_NAME,
    CodingWritingSpecialist,
    ResearchAnalysisSpecialist,
    TestingSpecialist,
)
from orchestrator.core import CCClusterManager, CCProcessLauncher, MessageLogger

# ============================================================================
# Test CodingWritingSpecialist
# ============================================================================

class TestCodingWritingSpecialistInit:
    """CodingWritingSpecialist初期化処理のテスト"""

    @pytest.fixture
    def mock_cluster_manager(self) -> MagicMock:
        """CCClusterManagerのモック"""
        mock = MagicMock(spec=CCClusterManager)
        return mock

    @pytest.fixture
    def mock_logger(self) -> MagicMock:
        """MessageLoggerのモック"""
        mock = MagicMock(spec=MessageLogger)
        return mock

    def test_init_with_valid_parameters(self, mock_cluster_manager, mock_logger):
        """正常なパラメータで初期化が成功すること"""
        agent = CodingWritingSpecialist(
            name=CODING_SPECIALIST_NAME,
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
        )

        assert agent._get_name() == CODING_SPECIALIST_NAME
        assert agent._cluster_manager is mock_cluster_manager
        assert agent._logger is mock_logger

    def test_init_with_default_logger(self, mock_cluster_manager):
        """loggerを省略した場合、新規MessageLoggerが作成されること"""
        agent = CodingWritingSpecialist(
            name=CODING_SPECIALIST_NAME,
            cluster_manager=mock_cluster_manager,
        )

        assert agent._get_name() == CODING_SPECIALIST_NAME
        assert isinstance(agent._logger, MessageLogger)
        assert agent._default_timeout == DEFAULT_TASK_TIMEOUT

    def test_init_with_custom_timeout(self, mock_cluster_manager, mock_logger):
        """カスタムタイムアウトを指定した場合、それが設定されること"""
        custom_timeout = 180.0
        agent = CodingWritingSpecialist(
            name=CODING_SPECIALIST_NAME,
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
            default_timeout=custom_timeout,
        )

        assert agent._default_timeout == custom_timeout

    def test_init_with_invalid_name(self, mock_cluster_manager):
        """nameが正しくない場合、ValueErrorが発生すること"""
        with pytest.raises(ValueError, match=f"nameは'{CODING_SPECIALIST_NAME}'である必要があります"):
            CodingWritingSpecialist(
                name="research_analysis_specialist",
                cluster_manager=mock_cluster_manager,
            )

    def test_init_with_invalid_cluster_manager(self):
        """cluster_managerがCCClusterManagerでない場合、TypeErrorが発生すること"""
        with pytest.raises(TypeError, match="cluster_managerはCCClusterManagerのインスタンス"):
            CodingWritingSpecialist(
                name=CODING_SPECIALIST_NAME,
                cluster_manager="not_a_manager",  # type: ignore[arg-type]
            )


class TestCodingWritingSpecialistHandleTask:
    """handle_task正常系のテスト"""

    @pytest.fixture
    def mock_cluster_manager(self) -> MagicMock:
        """CCClusterManagerのモック"""
        mock = MagicMock(spec=CCClusterManager)
        # get_launcher()がモックランチャーを返すように設定
        mock_launcher = MagicMock(spec=CCProcessLauncher)
        mock_launcher.send_message = AsyncMock(
            return_value=f"{CODING_MARKER}\nタスクを完了しました"
        )
        mock.get_launcher = MagicMock(return_value=mock_launcher)
        return mock

    @pytest.fixture
    def mock_logger(self) -> MagicMock:
        """MessageLoggerのモック"""
        mock = MagicMock(spec=MessageLogger)
        return mock

    @pytest.fixture
    def agent(self, mock_cluster_manager, mock_logger) -> CodingWritingSpecialist:
        """CodingWritingSpecialistインスタンス"""
        return CodingWritingSpecialist(
            name=CODING_SPECIALIST_NAME,
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
        )

    @pytest.mark.asyncio
    async def test_handle_task_returns_response(self, agent):
        """タスク処理が成功し、応答が返されること"""
        result = await agent.handle_task("ユーザー認証機能を実装してください")

        assert CODING_MARKER in result

    @pytest.mark.asyncio
    async def test_handle_task_with_complex_task(self, agent):
        """複雑なタスクでも正しく処理できること"""
        complex_task = """
        以下の機能を実装してください：
        1. ユーザー認証
        2. パスワードリセット
        3. ドキュメント作成
        """
        result = await agent.handle_task(complex_task)

        assert CODING_MARKER in result

    @pytest.mark.asyncio
    async def test_handle_task_with_multilingual_task(self, agent):
        """多言語のタスクでも正しく処理できること"""
        result = await agent.handle_task("Implement user authentication")

        assert CODING_MARKER in result


class TestCodingWritingSpecialistHandleTaskErrors:
    """handle_task異常系のテスト"""

    @pytest.fixture
    def mock_cluster_manager(self) -> MagicMock:
        """CCClusterManagerのモック"""
        mock = MagicMock(spec=CCClusterManager)
        return mock

    @pytest.fixture
    def mock_logger(self) -> MagicMock:
        """MessageLoggerのモック"""
        mock = MagicMock(spec=MessageLogger)
        return mock

    @pytest.fixture
    def agent(self, mock_cluster_manager, mock_logger) -> CodingWritingSpecialist:
        """CodingWritingSpecialistインスタンス"""
        return CodingWritingSpecialist(
            name=CODING_SPECIALIST_NAME,
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
        )

    @pytest.mark.asyncio
    async def test_handle_task_with_empty_task(self, agent):
        """空のタスクの場合、ValueErrorが発生すること"""
        with pytest.raises(ValueError, match="taskは空であってはなりません"):
            await agent.handle_task("")

    @pytest.mark.asyncio
    async def test_handle_task_with_whitespace_task(self, agent):
        """空白のみのタスクの場合、ValueErrorが発生すること"""
        with pytest.raises(ValueError, match="taskは空であってはなりません"):
            await agent.handle_task("   ")


# ============================================================================
# Test ResearchAnalysisSpecialist
# ============================================================================

class TestResearchAnalysisSpecialistInit:
    """ResearchAnalysisSpecialist初期化処理のテスト"""

    @pytest.fixture
    def mock_cluster_manager(self) -> MagicMock:
        """CCClusterManagerのモック"""
        mock = MagicMock(spec=CCClusterManager)
        return mock

    @pytest.fixture
    def mock_logger(self) -> MagicMock:
        """MessageLoggerのモック"""
        mock = MagicMock(spec=MessageLogger)
        return mock

    def test_init_with_valid_parameters(self, mock_cluster_manager, mock_logger):
        """正常なパラメータで初期化が成功すること"""
        agent = ResearchAnalysisSpecialist(
            name=RESEARCH_SPECIALIST_NAME,
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
        )

        assert agent._get_name() == RESEARCH_SPECIALIST_NAME
        assert agent._cluster_manager is mock_cluster_manager
        assert agent._logger is mock_logger

    def test_init_with_default_logger(self, mock_cluster_manager):
        """loggerを省略した場合、新規MessageLoggerが作成されること"""
        agent = ResearchAnalysisSpecialist(
            name=RESEARCH_SPECIALIST_NAME,
            cluster_manager=mock_cluster_manager,
        )

        assert agent._get_name() == RESEARCH_SPECIALIST_NAME
        assert isinstance(agent._logger, MessageLogger)
        assert agent._default_timeout == DEFAULT_TASK_TIMEOUT

    def test_init_with_custom_timeout(self, mock_cluster_manager, mock_logger):
        """カスタムタイムアウトを指定した場合、それが設定されること"""
        custom_timeout = 200.0
        agent = ResearchAnalysisSpecialist(
            name=RESEARCH_SPECIALIST_NAME,
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
            default_timeout=custom_timeout,
        )

        assert agent._default_timeout == custom_timeout

    def test_init_with_invalid_name(self, mock_cluster_manager):
        """nameが正しくない場合、ValueErrorが発生すること"""
        with pytest.raises(ValueError, match=f"nameは'{RESEARCH_SPECIALIST_NAME}'である必要があります"):
            ResearchAnalysisSpecialist(
                name="coding_writing_specialist",
                cluster_manager=mock_cluster_manager,
            )

    def test_init_with_invalid_cluster_manager(self):
        """cluster_managerがCCClusterManagerでない場合、TypeErrorが発生すること"""
        with pytest.raises(TypeError, match="cluster_managerはCCClusterManagerのインスタンス"):
            ResearchAnalysisSpecialist(
                name=RESEARCH_SPECIALIST_NAME,
                cluster_manager="not_a_manager",  # type: ignore[arg-type]
            )


class TestResearchAnalysisSpecialistHandleTask:
    """handle_task正常系のテスト"""

    @pytest.fixture
    def mock_cluster_manager(self) -> MagicMock:
        """CCClusterManagerのモック"""
        mock = MagicMock(spec=CCClusterManager)
        # get_launcher()がモックランチャーを返すように設定
        mock_launcher = MagicMock(spec=CCProcessLauncher)
        mock_launcher.send_message = AsyncMock(
            return_value=f"{RESEARCH_MARKER}\nタスクを完了しました"
        )
        mock.get_launcher = MagicMock(return_value=mock_launcher)
        return mock

    @pytest.fixture
    def mock_logger(self) -> MagicMock:
        """MessageLoggerのモック"""
        mock = MagicMock(spec=MessageLogger)
        return mock

    @pytest.fixture
    def agent(self, mock_cluster_manager, mock_logger) -> ResearchAnalysisSpecialist:
        """ResearchAnalysisSpecialistインスタンス"""
        return ResearchAnalysisSpecialist(
            name=RESEARCH_SPECIALIST_NAME,
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
        )

    @pytest.mark.asyncio
    async def test_handle_task_returns_response(self, agent):
        """タスク処理が成功し、応答が返されること"""
        result = await agent.handle_task("ベストプラクティスを調査してください")

        assert RESEARCH_MARKER in result

    @pytest.mark.asyncio
    async def test_handle_task_with_complex_task(self, agent):
        """複雑なタスクでも正しく処理できること"""
        complex_task = """
        以下について調査してください：
        1. FastAPIのベストプラクティス
        2. 非同期処理の実装方法
        3. テスト戦略
        """
        result = await agent.handle_task(complex_task)

        assert RESEARCH_MARKER in result

    @pytest.mark.asyncio
    async def test_handle_task_with_analysis_task(self, agent):
        """分析タスクでも正しく処理できること"""
        result = await agent.handle_task("コードベースを分析して改善点を特定してください")

        assert RESEARCH_MARKER in result


class TestResearchAnalysisSpecialistHandleTaskErrors:
    """handle_task異常系のテスト"""

    @pytest.fixture
    def mock_cluster_manager(self) -> MagicMock:
        """CCClusterManagerのモック"""
        mock = MagicMock(spec=CCClusterManager)
        return mock

    @pytest.fixture
    def mock_logger(self) -> MagicMock:
        """MessageLoggerのモック"""
        mock = MagicMock(spec=MessageLogger)
        return mock

    @pytest.fixture
    def agent(self, mock_cluster_manager, mock_logger) -> ResearchAnalysisSpecialist:
        """ResearchAnalysisSpecialistインスタンス"""
        return ResearchAnalysisSpecialist(
            name=RESEARCH_SPECIALIST_NAME,
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
        )

    @pytest.mark.asyncio
    async def test_handle_task_with_empty_task(self, agent):
        """空のタスクの場合、ValueErrorが発生すること"""
        with pytest.raises(ValueError, match="taskは空であってはなりません"):
            await agent.handle_task("")

    @pytest.mark.asyncio
    async def test_handle_task_with_whitespace_task(self, agent):
        """空白のみのタスクの場合、ValueErrorが発生すること"""
        with pytest.raises(ValueError, match="taskは空であってはなりません"):
            await agent.handle_task("   ")


# ============================================================================
# Test TestingSpecialist
# ============================================================================

class TestTestingSpecialistInit:
    """TestingSpecialist初期化処理のテスト"""

    @pytest.fixture
    def mock_cluster_manager(self) -> MagicMock:
        """CCClusterManagerのモック"""
        mock = MagicMock(spec=CCClusterManager)
        return mock

    @pytest.fixture
    def mock_logger(self) -> MagicMock:
        """MessageLoggerのモック"""
        mock = MagicMock(spec=MessageLogger)
        return mock

    def test_init_with_valid_parameters(self, mock_cluster_manager, mock_logger):
        """正常なパラメータで初期化が成功すること"""
        agent = TestingSpecialist(
            name=TESTING_SPECIALIST_NAME,
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
        )

        assert agent._get_name() == TESTING_SPECIALIST_NAME
        assert agent._cluster_manager is mock_cluster_manager
        assert agent._logger is mock_logger

    def test_init_with_default_logger(self, mock_cluster_manager):
        """loggerを省略した場合、新規MessageLoggerが作成されること"""
        agent = TestingSpecialist(
            name=TESTING_SPECIALIST_NAME,
            cluster_manager=mock_cluster_manager,
        )

        assert agent._get_name() == TESTING_SPECIALIST_NAME
        assert isinstance(agent._logger, MessageLogger)
        assert agent._default_timeout == DEFAULT_TASK_TIMEOUT

    def test_init_with_custom_timeout(self, mock_cluster_manager, mock_logger):
        """カスタムタイムアウトを指定した場合、それが設定されること"""
        custom_timeout = 150.0
        agent = TestingSpecialist(
            name=TESTING_SPECIALIST_NAME,
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
            default_timeout=custom_timeout,
        )

        assert agent._default_timeout == custom_timeout

    def test_init_with_invalid_name(self, mock_cluster_manager):
        """nameが正しくない場合、ValueErrorが発生すること"""
        with pytest.raises(ValueError, match=f"nameは'{TESTING_SPECIALIST_NAME}'である必要があります"):
            TestingSpecialist(
                name="coding_writing_specialist",
                cluster_manager=mock_cluster_manager,
            )

    def test_init_with_invalid_cluster_manager(self):
        """cluster_managerがCCClusterManagerでない場合、TypeErrorが発生すること"""
        with pytest.raises(TypeError, match="cluster_managerはCCClusterManagerのインスタンス"):
            TestingSpecialist(
                name=TESTING_SPECIALIST_NAME,
                cluster_manager="not_a_manager",  # type: ignore[arg-type]
            )


class TestTestingSpecialistHandleTask:
    """handle_task正常系のテスト"""

    @pytest.fixture
    def mock_cluster_manager(self) -> MagicMock:
        """CCClusterManagerのモック"""
        mock = MagicMock(spec=CCClusterManager)
        # get_launcher()がモックランチャーを返すように設定
        mock_launcher = MagicMock(spec=CCProcessLauncher)
        mock_launcher.send_message = AsyncMock(
            return_value=f"{TESTING_MARKER}\nタスクを完了しました"
        )
        mock.get_launcher = MagicMock(return_value=mock_launcher)
        return mock

    @pytest.fixture
    def mock_logger(self) -> MagicMock:
        """MessageLoggerのモック"""
        mock = MagicMock(spec=MessageLogger)
        return mock

    @pytest.fixture
    def agent(self, mock_cluster_manager, mock_logger) -> TestingSpecialist:
        """TestingSpecialistインスタンス"""
        return TestingSpecialist(
            name=TESTING_SPECIALIST_NAME,
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
        )

    @pytest.mark.asyncio
    async def test_handle_task_returns_response(self, agent):
        """タスク処理が成功し、応答が返されること"""
        result = await agent.handle_task("単体テストを実行してください")

        assert TESTING_MARKER in result

    @pytest.mark.asyncio
    async def test_handle_task_with_complex_task(self, agent):
        """複雑なタスクでも正しく処理できること"""
        complex_task = """
        以下のテストを実行してください：
        1. 単体テスト
        2. 統合テスト
        3. カバレッジ計測
        """
        result = await agent.handle_task(complex_task)

        assert TESTING_MARKER in result

    @pytest.mark.asyncio
    async def test_handle_task_with_quality_check_task(self, agent):
        """品質チェックタスクでも正しく処理できること"""
        result = await agent.handle_task("コードの品質チェックを実施してください")

        assert TESTING_MARKER in result


class TestTestingSpecialistHandleTaskErrors:
    """handle_task異常系のテスト"""

    @pytest.fixture
    def mock_cluster_manager(self) -> MagicMock:
        """CCClusterManagerのモック"""
        mock = MagicMock(spec=CCClusterManager)
        return mock

    @pytest.fixture
    def mock_logger(self) -> MagicMock:
        """MessageLoggerのモック"""
        mock = MagicMock(spec=MessageLogger)
        return mock

    @pytest.fixture
    def agent(self, mock_cluster_manager, mock_logger) -> TestingSpecialist:
        """TestingSpecialistインスタンス"""
        return TestingSpecialist(
            name=TESTING_SPECIALIST_NAME,
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
        )

    @pytest.mark.asyncio
    async def test_handle_task_with_empty_task(self, agent):
        """空のタスクの場合、ValueErrorが発生すること"""
        with pytest.raises(ValueError, match="taskは空であってはなりません"):
            await agent.handle_task("")

    @pytest.mark.asyncio
    async def test_handle_task_with_whitespace_task(self, agent):
        """空白のみのタスクの場合、ValueErrorが発生すること"""
        with pytest.raises(ValueError, match="taskは空であってはなりません"):
            await agent.handle_task("   ")


# ============================================================================
# Test Specialist Agent Constants
# ============================================================================

class TestSpecialistAgentConstants:
    """Specialistエージェント定数のテスト"""

    def test_coding_specialist_name_constant(self):
        """CODING_SPECIALIST_NAME定数が正しいこと"""
        assert CODING_SPECIALIST_NAME == "specialist_coding_writing"

    def test_research_specialist_name_constant(self):
        """RESEARCH_SPECIALIST_NAME定数が正しいこと"""
        assert RESEARCH_SPECIALIST_NAME == "specialist_research_analysis"

    def test_testing_specialist_name_constant(self):
        """TESTING_SPECIALIST_NAME定数が正しいこと"""
        assert TESTING_SPECIALIST_NAME == "specialist_testing"

    def test_coding_marker_constant(self):
        """CODING_MARKER定数が正しいこと"""
        assert CODING_MARKER == "CODING OK"

    def test_research_marker_constant(self):
        """RESEARCH_MARKER定数が正しいこと"""
        assert RESEARCH_MARKER == "RESEARCH OK"

    def test_testing_marker_constant(self):
        """TESTING_MARKER定数が正しいこと"""
        assert TESTING_MARKER == "TESTING OK"

    def test_default_task_timeout_constant(self):
        """DEFAULT_TASK_TIMEOUT定数が正しいこと"""
        assert DEFAULT_TASK_TIMEOUT == 120.0
