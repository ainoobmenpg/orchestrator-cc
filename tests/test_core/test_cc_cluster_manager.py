"""CCClusterManagerのテスト

このモジュールでは、CCClusterManagerクラスの単体テストを実装します。
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
import yaml

from orchestrator.core.cc_cluster_manager import (
    CCClusterAgentNotFoundError,
    CCClusterConfigError,
    CCClusterManager,
)
from orchestrator.core.tmux_session_manager import TmuxError


class TestCCClusterManagerInit:
    """CCClusterManager初期化処理のテスト"""

    def test_init_with_valid_config(self, tmp_path):
        """有効な設定ファイルで初期化できる"""
        # テスト用設定ファイルを作成
        config_data = {
            "cluster": {
                "name": "test-cluster",
                "session_name": "test-session",
                "work_dir": "/tmp/test",
            },
            "agents": [
                {
                    "name": "agent1",
                    "role": "grand_boss",
                    "personality_prompt_path": "config/personalities/test.txt",
                    "marker": "OK",
                    "pane_index": 0,
                }
            ],
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        manager = CCClusterManager(str(config_file))

        assert manager._config.name == "test-cluster"
        assert manager._config.session_name == "test-session"
        assert manager._config.work_dir == "/tmp/test"
        assert len(manager._config.agents) == 1
        assert manager._config.agents[0].name == "agent1"

    def test_init_with_nonexistent_file_raises_error(self, tmp_path):
        """存在しないファイルでFileNotFoundErrorが送出される"""
        config_file = tmp_path / "nonexistent.yaml"

        with pytest.raises(FileNotFoundError, match="設定ファイルが見つかりません"):
            CCClusterManager(str(config_file))

    def test_init_with_invalid_yaml_raises_error(self, tmp_path):
        """無効なYAMLでCCClusterConfigErrorが送出される"""
        config_file = tmp_path / "invalid.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            f.write("{invalid yaml content")

        with pytest.raises(CCClusterConfigError, match="YAMLファイルのパースに失敗しました"):
            CCClusterManager(str(config_file))

    def test_init_with_missing_cluster_key_raises_error(self, tmp_path):
        """'cluster'キーがない場合CCClusterConfigErrorが送出される"""
        config_data = {"agents": []}
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        with pytest.raises(CCClusterConfigError, match="'cluster' キーがありません"):
            CCClusterManager(str(config_file))

    def test_init_with_missing_agents_key_raises_error(self, tmp_path):
        """'agents'キーがない場合CCClusterConfigErrorが送出される"""
        config_data = {
            "cluster": {
                "name": "test",
                "session_name": "test-session",
                "work_dir": "/tmp/test",
            }
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        with pytest.raises(CCClusterConfigError, match="'agents' キーがありません"):
            CCClusterManager(str(config_file))

    def test_init_with_missing_cluster_field_raises_error(self, tmp_path):
        """clusterセクションに必須フィールドがない場合CCClusterConfigErrorが送出される"""
        config_data = {
            "cluster": {
                "name": "test",
                # session_nameが欠落
                "work_dir": "/tmp/test",
            },
            "agents": [],
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        with pytest.raises(CCClusterConfigError, match="必須キーがありません"):
            CCClusterManager(str(config_file))

    def test_init_with_invalid_role_raises_error(self, tmp_path):
        """無効な役割でCCClusterConfigErrorが送出される"""
        config_data = {
            "cluster": {
                "name": "test",
                "session_name": "test-session",
                "work_dir": "/tmp/test",
            },
            "agents": [
                {
                    "name": "agent1",
                    "role": "invalid_role",
                    "personality_prompt_path": "test.txt",
                    "marker": "OK",
                    "pane_index": 0,
                }
            ],
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        with pytest.raises(CCClusterConfigError, match="無効な役割が指定されました"):
            CCClusterManager(str(config_file))


class TestCCClusterManagerLoadConfig:
    """設定読み込みのテスト"""

    def test_load_config_with_multiple_agents(self, tmp_path):
        """複数のエージェント設定を読み込める"""
        config_data = {
            "cluster": {
                "name": "test-cluster",
                "session_name": "test-session",
                "work_dir": "/tmp/test",
            },
            "agents": [
                {
                    "name": "agent1",
                    "role": "grand_boss",
                    "personality_prompt_path": "test1.txt",
                    "marker": "OK1",
                    "pane_index": 0,
                },
                {
                    "name": "agent2",
                    "role": "middle_manager",
                    "personality_prompt_path": "test2.txt",
                    "marker": "OK2",
                    "pane_index": 1,
                },
            ],
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        manager = CCClusterManager(str(config_file))

        assert len(manager._config.agents) == 2
        assert manager._config.agents[0].name == "agent1"
        assert manager._config.agents[1].name == "agent2"


class TestCCClusterManagerStart:
    """クラスタ起動のテスト"""

    @pytest.mark.asyncio
    async def test_start_creates_session_when_not_exists(self, tmp_path):
        """セッションが存在しない場合に作成される"""
        config_data = {
            "cluster": {
                "name": "test-cluster",
                "session_name": "test-session",
                "work_dir": "/tmp/test",
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
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        manager = CCClusterManager(str(config_file))

        # モックを設定
        manager._tmux.session_exists = Mock(return_value=False)
        manager._tmux.create_session = Mock()
        manager._tmux.create_pane = Mock()

        # エージェントのモック
        with patch("orchestrator.core.cc_cluster_manager.CCProcessLauncher") as MockLauncher:
            mock_launcher = Mock()
            mock_launcher.start = AsyncMock()
            MockLauncher.return_value = mock_launcher

            await manager.start()

            # セッションが作成されたことを確認
            manager._tmux.create_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_skips_session_creation_when_exists(self, tmp_path):
        """セッションが存在する場合に作成をスキップする"""
        config_data = {
            "cluster": {
                "name": "test-cluster",
                "session_name": "test-session",
                "work_dir": "/tmp/test",
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
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        manager = CCClusterManager(str(config_file))

        # モックを設定
        manager._tmux.session_exists = Mock(return_value=True)
        manager._tmux.create_session = Mock()

        # エージェントのモック
        with patch("orchestrator.core.cc_cluster_manager.CCProcessLauncher") as MockLauncher:
            mock_launcher = Mock()
            mock_launcher.start = AsyncMock()
            MockLauncher.return_value = mock_launcher

            await manager.start()

            # セッションが作成されていないことを確認
            manager._tmux.create_session.assert_not_called()

    @pytest.mark.asyncio
    async def test_start_creates_required_panes(self, tmp_path):
        """必要な数のペインが作成される"""
        config_data = {
            "cluster": {
                "name": "test-cluster",
                "session_name": "test-session",
                "work_dir": "/tmp/test",
            },
            "agents": [
                {
                    "name": "agent1",
                    "role": "grand_boss",
                    "personality_prompt_path": "test.txt",
                    "marker": "OK",
                    "pane_index": 0,
                },
                {
                    "name": "agent2",
                    "role": "middle_manager",
                    "personality_prompt_path": "test.txt",
                    "marker": "OK",
                    "pane_index": 1,
                },
                {
                    "name": "agent3",
                    "role": "specialist_coding_writing",
                    "personality_prompt_path": "test.txt",
                    "marker": "OK",
                    "pane_index": 2,
                },
            ],
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        manager = CCClusterManager(str(config_file))

        # モックを設定
        manager._tmux.session_exists = Mock(return_value=False)
        manager._tmux.create_session = Mock()
        manager._tmux.create_pane = Mock()

        # エージェントのモック
        with patch("orchestrator.core.cc_cluster_manager.CCProcessLauncher") as MockLauncher:
            mock_launcher = Mock()
            mock_launcher.start = AsyncMock()
            MockLauncher.return_value = mock_launcher

            await manager.start()

            # 2つの追加ペインが作成される（3エージェント - 1）
            assert manager._tmux.create_pane.call_count == 2

    @pytest.mark.asyncio
    async def test_start_launches_all_agents(self, tmp_path):
        """全エージェントが起動される"""
        config_data = {
            "cluster": {
                "name": "test-cluster",
                "session_name": "test-session",
                "work_dir": "/tmp/test",
            },
            "agents": [
                {
                    "name": "agent1",
                    "role": "grand_boss",
                    "personality_prompt_path": "test.txt",
                    "marker": "OK",
                    "pane_index": 0,
                },
                {
                    "name": "agent2",
                    "role": "middle_manager",
                    "personality_prompt_path": "test.txt",
                    "marker": "OK",
                    "pane_index": 1,
                },
            ],
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        manager = CCClusterManager(str(config_file))

        # モックを設定
        manager._tmux.session_exists = Mock(return_value=True)

        # エージェントのモック
        with patch("orchestrator.core.cc_cluster_manager.CCProcessLauncher") as MockLauncher:
            mock_launcher = Mock()
            mock_launcher.start = AsyncMock()
            MockLauncher.return_value = mock_launcher

            await manager.start()

            # 2つのエージェントが起動されたことを確認
            assert mock_launcher.start.call_count == 2

    @pytest.mark.asyncio
    async def test_start_stores_launchers(self, tmp_path):
        """ランチャーが正しく保存される"""
        config_data = {
            "cluster": {
                "name": "test-cluster",
                "session_name": "test-session",
                "work_dir": "/tmp/test",
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
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        manager = CCClusterManager(str(config_file))

        # モックを設定
        manager._tmux.session_exists = Mock(return_value=True)

        # エージェントのモック
        with patch("orchestrator.core.cc_cluster_manager.CCProcessLauncher") as MockLauncher:
            mock_launcher = Mock()
            mock_launcher.start = AsyncMock()
            MockLauncher.return_value = mock_launcher

            await manager.start()

            # ランチャーが保存されていることを確認
            assert "agent1" in manager._launchers


class TestCCClusterManagerGetAgent:
    """エージェント取得のテスト"""

    def test_get_agent_with_valid_name(self, tmp_path):
        """有効なエージェント名で取得できる"""
        config_data = {
            "cluster": {
                "name": "test-cluster",
                "session_name": "test-session",
                "work_dir": "/tmp/test",
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
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        manager = CCClusterManager(str(config_file))

        # モックランチャーを追加
        mock_launcher = Mock()
        manager._launchers["agent1"] = mock_launcher

        result = manager.get_agent("agent1")

        assert result is mock_launcher

    def test_get_agent_with_invalid_name_raises_error(self, tmp_path):
        """無効なエージェント名でCCClusterAgentNotFoundErrorが送出される"""
        config_data = {
            "cluster": {
                "name": "test-cluster",
                "session_name": "test-session",
                "work_dir": "/tmp/test",
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
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        manager = CCClusterManager(str(config_file))

        with pytest.raises(
            CCClusterAgentNotFoundError, match="エージェント 'invalid' は存在しません"
        ):
            manager.get_agent("invalid")

    def test_get_launcher_returns_same_as_get_agent(self, tmp_path):
        """get_launcher()はget_agent()と同じ結果を返す"""
        config_data = {
            "cluster": {
                "name": "test-cluster",
                "session_name": "test-session",
                "work_dir": "/tmp/test",
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
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        manager = CCClusterManager(str(config_file))

        # モックランチャーを追加
        mock_launcher = Mock()
        manager._launchers["agent1"] = mock_launcher

        # 両方のメソッドで同じ結果が得られることを確認
        result_get_agent = manager.get_agent("agent1")
        result_get_launcher = manager.get_launcher("agent1")

        assert result_get_agent is mock_launcher
        assert result_get_launcher is mock_launcher
        assert result_get_agent is result_get_launcher


class TestCCClusterManagerSendMessage:
    """メッセージ送信のテスト"""

    @pytest.mark.asyncio
    async def test_send_message_calls_agent_send_message(self, tmp_path):
        """エージェントのsend_messageが呼び出される"""
        config_data = {
            "cluster": {
                "name": "test-cluster",
                "session_name": "test-session",
                "work_dir": "/tmp/test",
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
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        manager = CCClusterManager(str(config_file))

        # モックランチャーを設定
        mock_launcher = Mock()
        mock_launcher.send_message = AsyncMock(return_value="response")
        manager._launchers["agent1"] = mock_launcher

        result = await manager.send_message("agent1", "test message")

        assert result == "response"
        mock_launcher.send_message.assert_called_once_with("test message", timeout=30.0)

    @pytest.mark.asyncio
    async def test_send_message_with_custom_timeout(self, tmp_path):
        """カスタムタイムアウトで送信できる"""
        config_data = {
            "cluster": {
                "name": "test-cluster",
                "session_name": "test-session",
                "work_dir": "/tmp/test",
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
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        manager = CCClusterManager(str(config_file))

        # モックランチャーを設定
        mock_launcher = Mock()
        mock_launcher.send_message = AsyncMock(return_value="response")
        manager._launchers["agent1"] = mock_launcher

        await manager.send_message("agent1", "test message", timeout=60.0)

        mock_launcher.send_message.assert_called_once_with("test message", timeout=60.0)


class TestCCClusterManagerStop:
    """クラスタ停止のテスト"""

    @pytest.mark.asyncio
    async def test_stop_stops_all_agents_in_reverse_order(self, tmp_path):
        """エージェントが起動と逆順で停止される"""
        config_data = {
            "cluster": {
                "name": "test-cluster",
                "session_name": "test-session",
                "work_dir": "/tmp/test",
            },
            "agents": [
                {
                    "name": "agent1",
                    "role": "grand_boss",
                    "personality_prompt_path": "test.txt",
                    "marker": "OK",
                    "pane_index": 0,
                },
                {
                    "name": "agent2",
                    "role": "middle_manager",
                    "personality_prompt_path": "test.txt",
                    "marker": "OK",
                    "pane_index": 1,
                },
            ],
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        manager = CCClusterManager(str(config_file))

        # モックランチャーを設定
        mock_launcher1 = Mock()
        mock_launcher1.stop = AsyncMock()
        mock_launcher2 = Mock()
        mock_launcher2.stop = AsyncMock()
        manager._launchers["agent1"] = mock_launcher1
        manager._launchers["agent2"] = mock_launcher2

        await manager.stop()

        # 逆順で停止されたことを確認
        assert mock_launcher2.stop.call_count == 1
        assert mock_launcher1.stop.call_count == 1



class TestCCClusterManagerErrorHandling:
    """エラーハンドリングのテスト"""

    @pytest.mark.asyncio
    async def test_start_propagates_tmux_error(self, tmp_path):
        """tmuxエラーがCCClusterConfigErrorに変換される"""
        config_data = {
            "cluster": {
                "name": "test-cluster",
                "session_name": "test-session",
                "work_dir": "/tmp/test",
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
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        manager = CCClusterManager(str(config_file))

        # モックを設定
        manager._tmux.session_exists = Mock(return_value=False)
        manager._tmux.create_session = Mock(side_effect=TmuxError("tmux error"))

        with pytest.raises(CCClusterConfigError, match="セッションの作成に失敗しました"):
            await manager.start()

    @pytest.mark.asyncio
    async def test_get_agent_propagates_not_found_error(self, tmp_path):
        """エージェントが見つからない場合のエラーメッセージを確認"""
        config_data = {
            "cluster": {
                "name": "test-cluster",
                "session_name": "test-session",
                "work_dir": "/tmp/test",
            },
            "agents": [
                {
                    "name": "agent1",
                    "role": "grand_boss",
                    "personality_prompt_path": "test.txt",
                    "marker": "OK",
                    "pane_index": 0,
                },
                {
                    "name": "agent2",
                    "role": "middle_manager",
                    "personality_prompt_path": "test.txt",
                    "marker": "OK",
                    "pane_index": 1,
                },
            ],
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        manager = CCClusterManager(str(config_file))

        # モックランチャーを追加
        mock_launcher = Mock()
        manager._launchers["agent1"] = mock_launcher
        manager._launchers["agent2"] = mock_launcher

        with pytest.raises(CCClusterAgentNotFoundError) as exc_info:
            manager.get_agent("agent3")

        # エラーメッセージに利用可能なエージェントが含まれていることを確認
        assert "agent1" in str(exc_info.value)
        assert "agent2" in str(exc_info.value)
