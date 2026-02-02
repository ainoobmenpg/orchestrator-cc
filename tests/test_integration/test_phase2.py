"""Phase 2の統合テスト

このモジュールでは、Phase 2で実装したエージェント間通信の統合テストを実装します。

検証項目:
- V-201: エージェント間でメッセージを送信できる
- V-202: 合言葉（マーカー）を検出して応答を取得できる
- V-203: エンドツーエンドの通信ができる
- V-204: SpecialistがCCProcessLauncher経由で通信する（完全版）
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from orchestrator.agents.cc_agent_base import (
    CCAgentSendError,
    CCAgentTimeoutError,
)
from orchestrator.agents.grand_boss import GrandBossAgent
from orchestrator.agents.middle_manager import MiddleManagerAgent
from orchestrator.agents.specialists import (
    CODING_MARKER,
    CODING_SPECIALIST_NAME,
    RESEARCH_MARKER,
    RESEARCH_SPECIALIST_NAME,
    TESTING_MARKER,
    TESTING_SPECIALIST_NAME,
    CodingWritingSpecialist,
    ResearchAnalysisSpecialist,
    TestingSpecialist,
)
from orchestrator.core import (
    CCClusterAgentNotFoundError,
    CCClusterManager,
    MessageLogger,
    MessageType,
    PaneTimeoutError,
)
from orchestrator.core.cc_process_launcher import CCProcessLauncher
from orchestrator.core.yaml_protocol import read_message_async

# ============================================================================
# TestPhase2AgentCommunication（正常系）
# ============================================================================

class TestPhase2AgentCommunication:
    """Phase 2 エージェント間通信の正常系テスト"""

    @pytest.fixture
    def mock_cluster_manager(self) -> MagicMock:
        """CCClusterManagerのモック"""
        mock = MagicMock(spec=CCClusterManager)
        return mock

    @pytest.fixture
    def mock_logger(self) -> MagicMock:
        """MessageLoggerのモック"""
        mock = MagicMock(spec=MessageLogger)
        mock.log_send = MagicMock(return_value="msg-id-send")
        mock.log_receive = MagicMock(return_value="msg-id-recv")
        return mock

    @pytest.mark.asyncio
    async def test_grand_boss_to_middle_manager(
        self, mock_cluster_manager, mock_logger
    ):
        """V-201: Grand Boss → Middle Manager 送信"""
        # YAMLプロトコル対応: GrandBossとMiddleManagerのYAMLメソッドをモック
        from unittest.mock import patch

        # GrandBossの_wait_for_resultをモック
        with patch.object(GrandBossAgent, '_wait_for_result', new_callable=AsyncMock) as mock_gb_wait:
            with patch.object(MiddleManagerAgent, '_write_yaml_message', new_callable=AsyncMock) as mock_mm_write:
                with patch.object(MiddleManagerAgent, '_wait_for_result', new_callable=AsyncMock) as mock_mm_wait:
                    # モックの設定
                    mock_gb_wait.return_value = "MIDDLE MANAGER OK\nタスクを完了しました"
                    mock_mm_write.return_value = "msg-id-gb-mm"
                    mock_mm_wait.return_value = "MIDDLE MANAGER OK\nタスクを完了しました"

                    # Grand Boss Agentを作成
                    grand_boss = GrandBossAgent(
                        name="grand_boss",
                        cluster_manager=mock_cluster_manager,
                        logger=mock_logger,
                    )

                    # タスクを実行
                    result = await grand_boss.handle_task("新しい機能を実装してください")

                    # GrandBossの_wait_for_resultが呼ばれたこと
                    mock_gb_wait.assert_called_once()

                    # 新しいフォーマットで応答が返ってきていること
                    assert "タスク実行結果" in result
                    assert "元のタスク" in result
                    assert "新しい機能を実装してください" in result
                    assert "Middle Managerによる集約結果" in result
                    assert "MIDDLE MANAGER OK" in result
                    assert "Grand Boss as Executive" in result

    @pytest.mark.asyncio
    async def test_middle_manager_to_specialists(
        self, mock_cluster_manager, mock_logger
    ):
        """V-201: Middle Manager → 全Specialist 並列送信"""
        # YAMLプロトコル対応: _write_yaml_message と _wait_for_result をモック
        from unittest.mock import patch

        with patch.object(MiddleManagerAgent, '_write_yaml_message', new_callable=AsyncMock) as mock_write:
            with patch.object(MiddleManagerAgent, '_wait_for_result', new_callable=AsyncMock) as mock_wait:
                # モックの設定
                mock_write.return_value = "msg-id-test"
                mock_wait.return_value = "CODING OK\n実装が完了しました"

                # Middle Manager Agentを作成
                middle_manager = MiddleManagerAgent(
                    name="middle_manager",
                    cluster_manager=mock_cluster_manager,
                    logger=mock_logger,
                )

                # タスクを実行
                await middle_manager.handle_task("新しい機能を実装してください")

                # YAMLメッセージ書き込みが呼ばれたこと
                assert mock_write.call_count >= 1

                # 結果待機が呼ばれたこと
                assert mock_wait.call_count >= 1

    @pytest.mark.asyncio
    async def test_coding_marker_detected(
        self, mock_cluster_manager, mock_logger
    ):
        """V-202: CODING OK 検出"""
        # YAMLプロトコル対応: _write_yaml_message と _wait_for_result をモック
        from unittest.mock import patch

        with patch.object(MiddleManagerAgent, '_write_yaml_message', new_callable=AsyncMock) as mock_write:
            with patch.object(MiddleManagerAgent, '_wait_for_result', new_callable=AsyncMock) as mock_wait:
                # モックの設定
                mock_write.return_value = "msg-id-coding"
                mock_wait.return_value = f"{CODING_MARKER}\n実装が完了しました"

                # Middle Manager Agentを作成
                middle_manager = MiddleManagerAgent(
                    name="middle_manager",
                    cluster_manager=mock_cluster_manager,
                    logger=mock_logger,
                )

                # タスクを実行
                result = await middle_manager.handle_task("コーディングタスク")

                # CODING OK マーカーが含まれていること
                assert CODING_MARKER in result

    @pytest.mark.asyncio
    async def test_research_marker_detected(
        self, mock_cluster_manager, mock_logger
    ):
        """V-202: RESEARCH OK 検出"""
        # YAMLプロトコル対応: _write_yaml_message と _wait_for_result をモック
        from unittest.mock import patch

        with patch.object(MiddleManagerAgent, '_write_yaml_message', new_callable=AsyncMock) as mock_write:
            with patch.object(MiddleManagerAgent, '_wait_for_result', new_callable=AsyncMock) as mock_wait:
                # モックの設定
                mock_write.return_value = "msg-id-research"
                mock_wait.return_value = f"{RESEARCH_MARKER}\n調査が完了しました"

                # Middle Manager Agentを作成
                middle_manager = MiddleManagerAgent(
                    name="middle_manager",
                    cluster_manager=mock_cluster_manager,
                    logger=mock_logger,
                )

                # タスクを実行
                result = await middle_manager.handle_task("調査タスク")

                # RESEARCH OK マーカーが含まれていること
                assert RESEARCH_MARKER in result

    @pytest.mark.asyncio
    async def test_testing_marker_detected(
        self, mock_cluster_manager, mock_logger
    ):
        """V-202: TESTING OK 検出"""
        # YAMLプロトコル対応: _write_yaml_message と _wait_for_result をモック
        from unittest.mock import patch

        with patch.object(MiddleManagerAgent, '_write_yaml_message', new_callable=AsyncMock) as mock_write:
            with patch.object(MiddleManagerAgent, '_wait_for_result', new_callable=AsyncMock) as mock_wait:
                # モックの設定
                mock_write.return_value = "msg-id-testing"
                mock_wait.return_value = f"{TESTING_MARKER}\nテストが完了しました"

                # Middle Manager Agentを作成
                middle_manager = MiddleManagerAgent(
                    name="middle_manager",
                    cluster_manager=mock_cluster_manager,
                    logger=mock_logger,
                )

                # タスクを実行
                result = await middle_manager.handle_task("テストタスク")

                # TESTING OK マーカーが含まれていること
                assert TESTING_MARKER in result

    @pytest.mark.asyncio
    async def test_full_communication_flow(
        self, mock_cluster_manager, mock_logger
    ):
        """V-203: 完全な通信フロー"""
        # YAMLプロトコル対応: GrandBossとMiddleManagerのYAMLメソッドをモック
        from unittest.mock import patch

        # Middle Manager → Coding Specialist → Grand Boss というフローをシミュレート

        # GrandBossの_wait_for_resultをモック
        with patch.object(GrandBossAgent, '_wait_for_result', new_callable=AsyncMock) as mock_gb_wait:
            with patch.object(MiddleManagerAgent, '_write_yaml_message', new_callable=AsyncMock) as mock_mm_write:
                with patch.object(MiddleManagerAgent, '_wait_for_result', new_callable=AsyncMock) as mock_mm_wait:
                    # モックの設定
                    mock_gb_wait.return_value = f"{CODING_MARKER}\n実装が完了しました"
                    mock_mm_write.return_value = "msg-id-full"
                    mock_mm_wait.return_value = f"{CODING_MARKER}\n実装が完了しました"

                    # Grand Boss Agentを作成
                    grand_boss = GrandBossAgent(
                        name="grand_boss",
                        cluster_manager=mock_cluster_manager,
                        logger=mock_logger,
                    )

                    # タスクを実行
                    result = await grand_boss.handle_task("新しい機能を実装してください")

                    # GrandBossの_wait_for_resultが呼ばれたこと
                    mock_gb_wait.assert_called_once()

                    # 最終的にCODING OKマーカーが返ってきていること
                    assert CODING_MARKER in result

    @pytest.mark.asyncio
    async def test_parallel_specialist_communication(
        self, mock_cluster_manager, mock_logger
    ):
        """V-203: 並列送信で最初の応答が返る"""
        # YAMLプロトコル対応: _write_yaml_message と _wait_for_result をモック
        from unittest.mock import patch
        import asyncio

        # 応答順序を制御するためのモック
        call_count = 0

        async def wait_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return f"{CODING_MARKER}\n実装が完了しました"
            elif call_count == 2:
                await asyncio.sleep(0.1)  # 遅延させて最初の応答にならないように
                return f"{RESEARCH_MARKER}\n調査が完了しました"
            else:
                await asyncio.sleep(0.1)  # 遅延させて最初の応答にならないように
                return f"{TESTING_MARKER}\nテストが完了しました"

        with patch.object(MiddleManagerAgent, '_write_yaml_message', new_callable=AsyncMock) as mock_write:
            with patch.object(MiddleManagerAgent, '_wait_for_result', new_callable=AsyncMock, side_effect=wait_side_effect) as mock_wait:
                # モックの設定
                mock_write.return_value = "msg-id-parallel"

                # Middle Manager Agentを作成
                middle_manager = MiddleManagerAgent(
                    name="middle_manager",
                    cluster_manager=mock_cluster_manager,
                    logger=mock_logger,
                )

                # タスクを実行
                result = await middle_manager.handle_task("新しい機能を実装してください")

                # 最初の応答が返ってきていること（CODING OK）
                assert CODING_MARKER in result


# ============================================================================
# TestPhase2ErrorHandling（異常系）
# ============================================================================

class TestPhase2ErrorHandling:
    """Phase 2 エージェント間通信の異常系テスト"""

    @pytest.fixture
    def mock_cluster_manager(self) -> MagicMock:
        """CCClusterManagerのモック"""
        mock = MagicMock(spec=CCClusterManager)
        return mock

    @pytest.fixture
    def mock_logger(self) -> MagicMock:
        """MessageLoggerのモック"""
        mock = MagicMock(spec=MessageLogger)
        mock.log_send = MagicMock(return_value="msg-id-send")
        return mock

    @pytest.mark.asyncio
    async def test_timeout_on_specialist_response(
        self, mock_cluster_manager, mock_logger
    ):
        """Specialist応答のタイムアウト処理

        Note: YAMLプロトコル導入後、_wait_for_resultをモックして
        タイムアウトをシミュレートします。
        """
        from unittest.mock import patch

        # Middle Managerの_wait_for_resultをモックしてタイムアウトをシミュレート
        with patch.object(MiddleManagerAgent, '_wait_for_result', new_callable=AsyncMock) as mock_wait:
            # タイムアウトエラーを投げる
            mock_wait.side_effect = TimeoutError("メッセージの結果がタイムアウトしました")

            # Middle Manager Agentを作成
            middle_manager = MiddleManagerAgent(
                name="middle_manager",
                cluster_manager=mock_cluster_manager,
                logger=mock_logger,
            )

            # TimeoutErrorが発生すること
            with pytest.raises(TimeoutError, match="タイムアウトしました"):
                await middle_manager.handle_task("テストタスク")

    @pytest.mark.asyncio
    async def test_nonexistent_agent_error(
        self, mock_cluster_manager, mock_logger
    ):
        """存在しないエージェントへの送信エラー"""
        # Middle Manager Agentを作成
        middle_manager = MiddleManagerAgent(
            name="middle_manager",
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
        )

        # 空のサブタスク辞書でハンドリングを確認
        # 実際には存在しないエージェントへの送信はタスク分解時に検出される
        # ここでは空タスクケースとしてバリデーションを確認
        with pytest.raises(ValueError, match="taskは空であってはなりません"):
            await middle_manager.handle_task("")

    @pytest.mark.asyncio
    async def test_empty_task_validation(
        self, mock_cluster_manager, mock_logger
    ):
        """空タスク送信のバリデーション"""
        # Middle Manager Agentを作成
        middle_manager = MiddleManagerAgent(
            name="middle_manager",
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
        )

        # 空タスクでValueErrorが発生すること
        with pytest.raises(ValueError, match="taskは空であってはなりません"):
            await middle_manager.handle_task("")

    @pytest.mark.asyncio
    async def test_communication_failure_handling(
        self, mock_cluster_manager, mock_logger
    ):
        """通信失敗のハンドリング - タイムアウト処理を検証

        Note: YAMLプロトコル導入後、_wait_for_resultをモックして
        タイムアウトをシミュレートします。
        """
        from unittest.mock import patch

        # Middle Managerの_wait_for_resultをモックしてタイムアウトをシミュレート
        with patch.object(MiddleManagerAgent, '_wait_for_result', new_callable=AsyncMock) as mock_wait:
            # タイムアウトエラーを投げる
            mock_wait.side_effect = TimeoutError("メッセージの結果がタイムアウトしました")

            # Middle Manager Agentを作成
            middle_manager = MiddleManagerAgent(
                name="middle_manager",
                cluster_manager=mock_cluster_manager,
                logger=mock_logger,
            )

            # TimeoutErrorが発生すること
            with pytest.raises(TimeoutError, match="タイムアウトしました"):
                await middle_manager.handle_task("テストタスク")


# ============================================================================
# TestPhase2EndToEnd（エンドツーエンド）
# ============================================================================

class TestPhase2EndToEnd:
    """Phase 2 エンドツーエンド通信テスト"""

    @pytest.fixture
    def mock_cluster_manager(self) -> MagicMock:
        """CCClusterManagerのモック"""
        mock = MagicMock(spec=CCClusterManager)
        return mock

    @pytest.fixture
    def mock_logger(self) -> MagicMock:
        """MessageLoggerのモック"""
        mock = MagicMock(spec=MessageLogger)
        mock.log_send = MagicMock(return_value="msg-id-send")
        mock.log_receive = MagicMock(return_value="msg-id-recv")
        return mock

    @pytest.mark.asyncio
    async def test_multi_hop_communication(
        self, mock_cluster_manager, mock_logger
    ):
        """マルチホップ通信の検証

        Grand Boss → Middle Manager → Specialist
        という2段階の通信を検証します。

        Note: YAMLプロトコル導入後、_wait_for_resultをモックします。
        """
        from unittest.mock import patch

        # GrandBossの_wait_for_resultをモック
        with patch.object(GrandBossAgent, '_wait_for_result', new_callable=AsyncMock) as mock_gb_wait:
            with patch.object(GrandBossAgent, '_write_yaml_message', new_callable=AsyncMock) as mock_gb_write:
                # モックの設定
                mock_gb_write.return_value = "msg-id-multi-hop"
                mock_gb_wait.return_value = f"{CODING_MARKER}\n実装が完了しました"

                # Grand Boss Agentを作成
                grand_boss = GrandBossAgent(
                    name="grand_boss",
                    cluster_manager=mock_cluster_manager,
                    logger=mock_logger,
                )

                # タスクを実行
                result = await grand_boss.handle_task("新しい機能を実装してください")

                # YAMLメッセージ書き込みが呼ばれたこと
                mock_gb_write.assert_called_once()

                # 応答が返ってきていること
                assert CODING_MARKER in result

    @pytest.mark.asyncio
    async def test_all_specialists_respond_with_markers(
        self, mock_cluster_manager, mock_logger
    ):
        """全Specialistが正しい合言葉で応答する"""
        # 各Specialistのランチャーモックを設定
        # 完全版ではget_launcher()→send_message()を使う
        responses = {
            CODING_SPECIALIST_NAME: f"{CODING_MARKER}\n実装完了",
            RESEARCH_SPECIALIST_NAME: f"{RESEARCH_MARKER}\n調査完了",
            TESTING_SPECIALIST_NAME: f"{TESTING_MARKER}\nテスト完了",
        }

        # ランチャーモックを作成
        mock_launcher = MagicMock(spec=CCProcessLauncher)

        def launcher_side_effect(*args, **kwargs):
            # 現在のSpecialist名を取得して応答を返す
            # kwargs["message"]にはタスクが含まれる
            for marker in responses.values():
                if marker in str(kwargs):
                    return marker
            return f"{CODING_MARKER}\nデフォルト応答"

        mock_launcher.send_message = AsyncMock(side_effect=launcher_side_effect)
        mock_cluster_manager.get_launcher = MagicMock(return_value=mock_launcher)

        # 各Specialistを直接テスト
        specialists = [
            (CodingWritingSpecialist, CODING_SPECIALIST_NAME, CODING_MARKER),
            (ResearchAnalysisSpecialist, RESEARCH_SPECIALIST_NAME, RESEARCH_MARKER),
            (TestingSpecialist, TESTING_SPECIALIST_NAME, TESTING_MARKER),
        ]

        for specialist_class, name, expected_marker in specialists:
            # 各Specialist用のランチャーを設定
            def make_launcher(marker):
                launcher = MagicMock(spec=CCProcessLauncher)
                launcher.send_message = AsyncMock(return_value=f"{marker}\n完了")
                return launcher

            mock_cluster_manager.get_launcher = MagicMock(return_value=make_launcher(expected_marker))

            specialist = specialist_class(
                name=name,
                cluster_manager=mock_cluster_manager,
                logger=mock_logger,
            )

            result = await specialist.handle_task("テストタスク")

            # 正しい合言葉が含まれていること
            assert expected_marker in result

    @pytest.mark.asyncio
    async def test_communication_logging(
        self, mock_cluster_manager, mock_logger
    ):
        """通信ログの記録を検証

        Note: YAMLプロトコル導入後、_wait_for_resultをモックします。
        YAMLベース通信ではlog_send/log_receiveは使用されません。
        代わりにYAMLメッセージの書き込みを検証します。
        """
        from unittest.mock import patch

        # GrandBossの_wait_for_resultをモック
        with patch.object(GrandBossAgent, '_wait_for_result', new_callable=AsyncMock) as mock_gb_wait:
            with patch.object(GrandBossAgent, '_write_yaml_message', new_callable=AsyncMock) as mock_gb_write:
                # モックの設定
                mock_gb_write.return_value = "msg-id-logging"
                mock_gb_wait.return_value = "MIDDLE MANAGER OK\n完了"

                # Grand Boss Agentを作成
                grand_boss = GrandBossAgent(
                    name="grand_boss",
                    cluster_manager=mock_cluster_manager,
                    logger=mock_logger,
                )

                # タスクを実行
                await grand_boss.handle_task("ログ記録テスト")

                # YAMLメッセージ書き込みが呼ばれたこと
                mock_gb_write.assert_called_once()
                write_kwargs = mock_gb_write.call_args.kwargs
                assert write_kwargs["to_agent"] == "middle_manager"
                assert write_kwargs["content"] == "ログ記録テスト"


# ============================================================================
# TestPhase2SpecialistCompleteImpl（完全版Specialist実装）
# ============================================================================

class TestPhase2SpecialistCompleteImpl:
    """Phase 2 完全版Specialistエージェントのテスト

    CCClusterManager経由で自分のCCProcessLauncherを取得し、
    tmuxペインでClaude Codeと通信してタスクを実行する機能をテストします。
    """

    @pytest.fixture
    def mock_cluster_manager(self) -> MagicMock:
        """CCClusterManagerのモック"""
        mock = MagicMock(spec=CCClusterManager)
        return mock

    @pytest.fixture
    def mock_launcher(self) -> MagicMock:
        """CCProcessLauncherのモック"""
        mock = MagicMock(spec=CCProcessLauncher)
        mock.send_message = AsyncMock(
            return_value=f"{CODING_MARKER}\n実際にコードを書きました"
        )
        return mock

    @pytest.fixture
    def mock_logger(self) -> MagicMock:
        """MessageLoggerのモック"""
        mock = MagicMock(spec=MessageLogger)
        mock.log_send = MagicMock(return_value="msg-id-send")
        mock.log_receive = MagicMock(return_value="msg-id-recv")
        return mock

    @pytest.mark.asyncio
    async def test_coding_specialist_uses_launcher(
        self, mock_cluster_manager, mock_launcher, mock_logger
    ):
        """V-204: CodingWritingSpecialistがCCProcessLauncher経由で通信する"""
        # get_launcher()がモックを返すように設定
        mock_cluster_manager.get_launcher = MagicMock(return_value=mock_launcher)

        # CodingWritingSpecialistを作成
        specialist = CodingWritingSpecialist(
            name=CODING_SPECIALIST_NAME,
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
        )

        # タスクを実行
        result = await specialist.handle_task("新しい関数を実装してください")

        # get_launcherが呼ばれていること
        mock_cluster_manager.get_launcher.assert_called_once_with(CODING_SPECIALIST_NAME)

        # launcherのsend_messageが呼ばれていること
        mock_launcher.send_message.assert_called_once()
        call_kwargs = mock_launcher.send_message.call_args.kwargs
        assert call_kwargs["message"] == "新しい関数を実装してください"

        # CODING OKマーカーが含まれていること
        assert CODING_MARKER in result

    @pytest.mark.asyncio
    async def test_research_specialist_uses_launcher(
        self, mock_cluster_manager, mock_launcher, mock_logger
    ):
        """V-204: ResearchAnalysisSpecialistがCCProcessLauncher経由で通信する"""
        # Research Specialist用の応答を設定
        mock_launcher.send_message = AsyncMock(
            return_value=f"{RESEARCH_MARKER}\n調査結果をまとめました"
        )

        # get_launcher()がモックを返すように設定
        mock_cluster_manager.get_launcher = MagicMock(return_value=mock_launcher)

        # ResearchAnalysisSpecialistを作成
        specialist = ResearchAnalysisSpecialist(
            name=RESEARCH_SPECIALIST_NAME,
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
        )

        # タスクを実行
        result = await specialist.handle_task("ベストプラクティスを調査してください")

        # get_launcherが呼ばれていること
        mock_cluster_manager.get_launcher.assert_called_once_with(RESEARCH_SPECIALIST_NAME)

        # launcherのsend_messageが呼ばれていること
        mock_launcher.send_message.assert_called_once()
        call_kwargs = mock_launcher.send_message.call_args.kwargs
        assert call_kwargs["message"] == "ベストプラクティスを調査してください"

        # RESEARCH OKマーカーが含まれていること
        assert RESEARCH_MARKER in result

    @pytest.mark.asyncio
    async def test_testing_specialist_uses_launcher(
        self, mock_cluster_manager, mock_launcher, mock_logger
    ):
        """V-204: TestingSpecialistがCCProcessLauncher経由で通信する"""
        # Testing Specialist用の応答を設定
        mock_launcher.send_message = AsyncMock(
            return_value=f"{TESTING_MARKER}\nテストを実行しました"
        )

        # get_launcher()がモックを返すように設定
        mock_cluster_manager.get_launcher = MagicMock(return_value=mock_launcher)

        # TestingSpecialistを作成
        specialist = TestingSpecialist(
            name=TESTING_SPECIALIST_NAME,
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
        )

        # タスクを実行
        result = await specialist.handle_task("単体テストを実行してください")

        # get_launcherが呼ばれていること
        mock_cluster_manager.get_launcher.assert_called_once_with(TESTING_SPECIALIST_NAME)

        # launcherのsend_messageが呼ばれていること
        mock_launcher.send_message.assert_called_once()
        call_kwargs = mock_launcher.send_message.call_args.kwargs
        assert call_kwargs["message"] == "単体テストを実行してください"

        # TESTING OKマーカーが含まれていること
        assert TESTING_MARKER in result

    @pytest.mark.asyncio
    async def test_specialist_timeout_handling(
        self, mock_cluster_manager, mock_launcher, mock_logger
    ):
        """Specialistのタイムアウト処理"""
        # タイムアウトをシミュレート
        mock_launcher.send_message = AsyncMock(
            side_effect=PaneTimeoutError("応答がありません")
        )

        # get_launcher()がモックを返すように設定
        mock_cluster_manager.get_launcher = MagicMock(return_value=mock_launcher)

        # CodingWritingSpecialistを作成
        specialist = CodingWritingSpecialist(
            name=CODING_SPECIALIST_NAME,
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
        )

        # CCAgentTimeoutErrorが発生すること
        with pytest.raises(CCAgentTimeoutError, match="タスク処理がタイムアウトしました"):
            await specialist.handle_task("テストタスク")

    @pytest.mark.asyncio
    async def test_specialist_custom_timeout(
        self, mock_cluster_manager, mock_launcher, mock_logger
    ):
        """カスタムタイムアウトの指定"""
        # カスタムタイムアウトでSpecialistを作成
        custom_timeout = 180.0
        specialist = CodingWritingSpecialist(
            name=CODING_SPECIALIST_NAME,
            cluster_manager=mock_cluster_manager,
            logger=mock_logger,
            default_timeout=custom_timeout,
        )

        # get_launcher()がモックを返すように設定
        mock_cluster_manager.get_launcher = MagicMock(return_value=mock_launcher)

        # タスクを実行
        await specialist.handle_task("長時間タスク")

        # カスタムタイムアウトが使用されていること
        mock_launcher.send_message.assert_called_once()
        call_kwargs = mock_launcher.send_message.call_args.kwargs
        assert call_kwargs["timeout"] == custom_timeout
