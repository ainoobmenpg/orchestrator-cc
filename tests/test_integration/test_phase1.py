"""Phase 1の統合テスト

このモジュールでは、CCClusterManagerクラスの統合テストを実装します。
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
import yaml

from orchestrator.core.cc_cluster_manager import (
    CCClusterAgentNotFoundError,
    CCClusterManager,
)


class TestCCClusterManagerIntegration:
    """CCClusterManagerの統合テスト"""

    @pytest.mark.asyncio
    async def test_full_cluster_lifecycle(self, tmp_path):
        """クラスタ全体のライフサイクルをテストする"""
        # テスト用設定ファイルを作成
        config_data = {
            "cluster": {
                "name": "test-cluster",
                "session_name": "test-integration-session",
                "work_dir": "/tmp/test-integration",
            },
            "agents": [
                {
                    "name": "grand_boss",
                    "role": "grand_boss",
                    "personality_prompt_path": "config/personalities/grand_boss.txt",
                    "marker": "GRAND BOSS OK",
                    "pane_index": 0,
                },
                {
                    "name": "middle_manager",
                    "role": "middle_manager",
                    "personality_prompt_path": "config/personalities/middle_manager.txt",
                    "marker": "MIDDLE MANAGER OK",
                    "pane_index": 1,
                },
                {
                    "name": "coding_specialist",
                    "role": "specialist_coding_writing",
                    "personality_prompt_path": "config/personalities/coding_writing_specialist.txt",
                    "marker": "CODING OK",
                    "pane_index": 2,
                },
            ],
        }
        config_file = tmp_path / "test-cluster.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        # モック設定
        with patch("orchestrator.core.cc_cluster_manager.TmuxSessionManager") as MockTmux:
            mock_tmux = Mock()
            mock_tmux.session_exists = Mock(return_value=False)
            mock_tmux.create_session = Mock()
            mock_tmux.create_pane = Mock()

            MockTmux.return_value = mock_tmux

            # エージェントランチャーのモック
            with patch("orchestrator.core.cc_cluster_manager.CCProcessLauncher") as MockLauncher:
                # 各エージェント用のモックを作成
                mock_launchers = {}
                for agent_config in config_data["agents"]:
                    mock_launcher = Mock()
                    mock_launcher.start = AsyncMock()
                    mock_launcher.stop = AsyncMock()
                    mock_launcher.send_message = AsyncMock(return_value=f"Response from {agent_config['name']}")
                    mock_launchers[agent_config["name"]] = mock_launcher

                # モックのside_effectを設定して、適切なモックを返す
                launcher_call_count = [0]
                def get_launcher_side_effect(*args, **kwargs):
                    idx = launcher_call_count[0]
                    launcher_call_count[0] += 1
                    return list(mock_launchers.values())[idx]

                MockLauncher.side_effect = get_launcher_side_effect

                MockLauncher.side_effect = get_launcher_side_effect

                # マネージャーを作成
                manager = CCClusterManager(str(config_file))

                # セッション設定を確認
                assert manager._config.name == "test-cluster"
                assert manager._config.session_name == "test-integration-session"
                assert len(manager._config.agents) == 3

                # クラスタを起動
                await manager.start()

                # セッションとペインが作成されたことを確認
                mock_tmux.create_session.assert_called_once()
                # 3エージェントなので2つの追加ペインが作成される
                assert mock_tmux.create_pane.call_count == 2

                # エージェントが起動されたことを確認
                assert len(manager._launchers) == 3

                # クラスタを停止
                await manager.stop()

    @pytest.mark.asyncio
    async def test_agent_communication(self, tmp_path):
        """エージェント間の通信をテストする"""
        # テスト用設定ファイルを作成
        config_data = {
            "cluster": {
                "name": "test-cluster",
                "session_name": "test-comm-session",
                "work_dir": "/tmp/test-comm",
            },
            "agents": [
                {
                    "name": "agent1",
                    "role": "grand_boss",
                    "personality_prompt_path": "test.txt",
                    "marker": "OK1",
                    "pane_index": 0,
                },
                {
                    "name": "agent2",
                    "role": "middle_manager",
                    "personality_prompt_path": "test.txt",
                    "marker": "OK2",
                    "pane_index": 1,
                },
            ],
        }
        config_file = tmp_path / "test-comm.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        # モック設定
        with patch("orchestrator.core.cc_cluster_manager.TmuxSessionManager") as MockTmux:
            mock_tmux = Mock()
            mock_tmux.session_exists = Mock(return_value=True)
            MockTmux.return_value = mock_tmux

            # エージェントランチャーのモック
            with patch("orchestrator.core.cc_cluster_manager.CCProcessLauncher") as MockLauncher:
                mock_agent1 = Mock()
                mock_agent1.start = AsyncMock()
                mock_agent1.send_message = AsyncMock(return_value="Agent1 response")

                mock_agent2 = Mock()
                mock_agent2.start = AsyncMock()
                mock_agent2.send_message = AsyncMock(return_value="Agent2 response")

                def get_launcher_side_effect(config, pane_index, tmux):
                    if config.name == "agent1":
                        return mock_agent1
                    elif config.name == "agent2":
                        return mock_agent2
                    return Mock()

                MockLauncher.side_effect = get_launcher_side_effect

                # マネージャーを作成して起動
                manager = CCClusterManager(str(config_file))
                await manager.start()

                # agent1にメッセージを送信
                response1 = await manager.send_message("agent1", "Hello agent1")
                assert response1 == "Agent1 response"
                mock_agent1.send_message.assert_called_once_with("Hello agent1", timeout=30.0)

                # agent2にメッセージを送信
                response2 = await manager.send_message("agent2", "Hello agent2")
                assert response2 == "Agent2 response"
                mock_agent2.send_message.assert_called_once_with("Hello agent2", timeout=30.0)

    @pytest.mark.asyncio
    async def test_agent_not_found_error(self, tmp_path):
        """存在しないエージェントを取得しようとするとエラーになる"""
        config_data = {
            "cluster": {
                "name": "test-cluster",
                "session_name": "test-error-session",
                "work_dir": "/tmp/test-error",
            },
            "agents": [
                {
                    "name": "agent1",
                    "role": "grand_boss",
                    "personality_prompt_path": "test.txt",
                    "marker": "OK",
                    "pane_index": 0,
                }
            ],
        }
        config_file = tmp_path / "test-error.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        manager = CCClusterManager(str(config_file))

        # 起動前はエージェントが存在しない
        with pytest.raises(CCClusterAgentNotFoundError):
            manager.get_agent("nonexistent")

    @pytest.mark.asyncio
    async def test_cluster_config_with_actual_file(self, tmp_path):
        """実際の設定ファイル形式でテストする"""
        # 実際の設定ファイルと同じ形式を作成
        config_content = """
cluster:
  name: "orchestrator-cc"
  session_name: "orchestrator-cc"
  work_dir: "/tmp/orchestrator-cc"

agents:
  - name: "grand_boss"
    role: "grand_boss"
    personality_prompt_path: "config/personalities/grand_boss.txt"
    marker: "GRAND BOSS OK"
    pane_index: 0

  - name: "middle_manager"
    role: "middle_manager"
    personality_prompt_path: "config/personalities/middle_manager.txt"
    marker: "MIDDLE MANAGER OK"
    pane_index: 1
"""
        config_file = tmp_path / "test-actual-format.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(config_content)

        # モック設定
        with patch("orchestrator.core.cc_cluster_manager.TmuxSessionManager") as MockTmux:
            mock_tmux = Mock()
            mock_tmux.session_exists = Mock(return_value=True)
            MockTmux.return_value = mock_tmux

            # エージェントランチャーのモック
            with patch("orchestrator.core.cc_cluster_manager.CCProcessLauncher") as MockLauncher:
                mock_launcher = Mock()
                mock_launcher.start = AsyncMock()
                MockLauncher.return_value = mock_launcher

                # マネージャーを作成
                manager = CCClusterManager(str(config_file))

                # 設定が正しく読み込まれたことを確認
                assert manager._config.name == "orchestrator-cc"
                assert manager._config.session_name == "orchestrator-cc"
                assert len(manager._config.agents) == 2
                assert manager._config.agents[0].name == "grand_boss"
                assert manager._config.agents[1].name == "middle_manager"

                # 起動してエージェントが正しく設定されていることを確認
                await manager.start()
                assert "grand_boss" in manager._launchers
                assert "middle_manager" in manager._launchers

    @pytest.mark.asyncio
    async def test_stop_without_start(self, tmp_path):
        """起動前に停止してもエラーにならない"""
        config_data = {
            "cluster": {
                "name": "test-cluster",
                "session_name": "test-stop-session",
                "work_dir": "/tmp/test-stop",
            },
            "agents": [
                {
                    "name": "agent1",
                    "role": "grand_boss",
                    "personality_prompt_path": "test.txt",
                    "marker": "OK",
                    "pane_index": 0,
                }
            ],
        }
        config_file = tmp_path / "test-stop.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        manager = CCClusterManager(str(config_file))

        # 起動前に停止してもエラーにならない（空のループ）
        await manager.stop()

    @pytest.mark.asyncio
    async def test_multiple_start_calls(self, tmp_path):
        """複数回start()を呼び出しても安全に動作する"""
        config_data = {
            "cluster": {
                "name": "test-cluster",
                "session_name": "test-multi-start",
                "work_dir": "/tmp/test-multi",
            },
            "agents": [
                {
                    "name": "agent1",
                    "role": "grand_boss",
                    "personality_prompt_path": "test.txt",
                    "marker": "OK",
                    "pane_index": 0,
                }
            ],
        }
        config_file = tmp_path / "test-multi-start.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        # モック設定
        with patch("orchestrator.core.cc_cluster_manager.TmuxSessionManager") as MockTmux:
            mock_tmux = Mock()
            mock_tmux.session_exists = Mock(return_value=True)
            MockTmux.return_value = mock_tmux

            # エージェントランチャーのモック
            with patch("orchestrator.core.cc_cluster_manager.CCProcessLauncher") as MockLauncher:
                mock_launcher = Mock()
                mock_launcher.start = AsyncMock()
                MockLauncher.return_value = mock_launcher

                manager = CCClusterManager(str(config_file))

                # 1回目の起動
                await manager.start()
                assert len(manager._launchers) == 1

                # 2回目の起動（エージェントが追加される）
                await manager.start()
                # 既存のランチャーが上書きされる
                assert len(manager._launchers) == 1
