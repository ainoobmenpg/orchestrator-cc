"""ChannelClientモジュールのテスト

エージェント向けチャンネル操作クライアントのテスト
"""

import pytest

from orchestrator.web.channel_client import (
    ChannelClient,
    get_channel_client,
    init_channel_client,
    reset_channel_client,
)
from orchestrator.web.message_handler import ChannelManager


class TestChannelClient:
    """ChannelClient クラスのテスト"""

    def setup_method(self):
        """各テストメソッドの前に実行"""
        # グローバル状態をリセット
        reset_channel_client()
        # ChannelManagerとChannelClientを作成
        self.manager = ChannelManager()
        self.client = ChannelClient(self.manager)

    def test_initialization(self):
        """初期化のテスト"""
        assert self.client._manager is self.manager

    def test_join_channel(self):
        """チャンネル参加のテスト"""
        result = self.client.join_channel("test-channel", "agent-1", "TestAgent")

        assert result["success"] is True
        assert result["channel"] == "test-channel"
        assert result["agent_id"] == "agent-1"
        assert result["agent_name"] == "TestAgent"
        assert "agent-1" in result["participants"]

        # チャンネルが作成されている
        channel = self.manager.get_channel("test-channel")
        assert channel is not None
        assert "agent-1" in channel.get_participants()

    def test_join_channel_invalid_name(self):
        """無効なチャンネル名での参加テスト"""
        result = self.client.join_channel("", "agent-1", "TestAgent")

        assert result["success"] is False
        assert "error" in result

    def test_join_multiple_agents(self):
        """複数のエージェントが参加するテスト"""
        self.client.join_channel("test-channel", "agent-1", "AgentOne")
        self.client.join_channel("test-channel", "agent-2", "AgentTwo")

        result = self.client.join_channel("test-channel", "agent-3", "AgentThree")

        assert result["success"] is True
        assert len(result["participants"]) == 3
        assert "agent-1" in result["participants"]
        assert "agent-2" in result["participants"]
        assert "agent-3" in result["participants"]

    def test_leave_channel(self):
        """チャンネル退出のテスト"""
        # まず参加
        self.client.join_channel("test-channel", "agent-1", "TestAgent")

        # 退出
        result = self.client.leave_channel("test-channel", "agent-1")

        assert result["success"] is True
        assert result["channel"] == "test-channel"
        assert result["agent_id"] == "agent-1"

        # 参加者から削除されている
        channel = self.manager.get_channel("test-channel")
        # 参加者がいなくなったのでチャンネルが削除されている
        assert channel is None

    def test_leave_channel_nonexistent(self):
        """存在しないチャンネルからの退出テスト"""
        result = self.client.leave_channel("nonexistent", "agent-1")

        assert result["success"] is False
        assert "error" in result

    def test_leave_channel_with_remaining_participants(self):
        """他の参加者がいる場合の退出テスト"""
        self.client.join_channel("test-channel", "agent-1", "AgentOne")
        self.client.join_channel("test-channel", "agent-2", "AgentTwo")

        # agent-1が退出
        result = self.client.leave_channel("test-channel", "agent-1")

        assert result["success"] is True

        # チャンネルは残っている（agent-2がまだいる）
        channel = self.manager.get_channel("test-channel")
        assert channel is not None
        assert "agent-2" in channel.get_participants()
        assert "agent-1" not in channel.get_participants()

    def test_send_message(self):
        """メッセージ送信のテスト"""
        # まず参加
        self.client.join_channel("test-channel", "agent-1", "TestAgent")

        # メッセージ送信
        result = self.client.send_message("test-channel", "Hello, world!", "agent-1", "TestAgent")

        assert result["success"] is True
        assert result["channel"] == "test-channel"
        assert "message_id" in result
        assert "timestamp" in result

        # チャンネルにメッセージが保存されている
        channel = self.manager.get_channel("test-channel")
        messages = channel.get_messages()
        assert len(messages) == 1
        assert messages[0]["content"] == "Hello, world!"
        assert messages[0]["sender"] == "TestAgent"

    def test_send_message_nonexistent_channel(self):
        """存在しないチャンネルへのメッセージ送信テスト"""
        result = self.client.send_message("nonexistent", "Hello", "agent-1", "TestAgent")

        assert result["success"] is False
        assert "error" in result

    def test_send_multiple_messages(self):
        """複数のメッセージ送信テスト"""
        self.client.join_channel("test-channel", "agent-1", "TestAgent")

        for i in range(5):
            self.client.send_message("test-channel", f"Message {i}", "agent-1", "TestAgent")

        channel = self.manager.get_channel("test-channel")
        messages = channel.get_messages()
        assert len(messages) == 5

    def test_list_channels(self):
        """チャンネル一覧取得のテスト"""
        # チャンネルを作成
        self.client.join_channel("channel-1", "agent-1", "AgentOne")
        self.client.join_channel("channel-2", "agent-2", "AgentTwo")
        self.client.join_channel("channel-3", "agent-3", "AgentThree")

        # 一覧取得
        channels = self.client.list_channels()

        assert len(channels) == 3

        channel_names = {ch["name"] for ch in channels}
        assert "channel-1" in channel_names
        assert "channel-2" in channel_names
        assert "channel-3" in channel_names

        # チャンネル情報を確認
        for ch in channels:
            assert "name" in ch
            assert "participants" in ch
            assert "message_count" in ch

    def test_list_channels_empty(self):
        """空のチャンネル一覧テスト"""
        channels = self.client.list_channels()
        assert channels == []

    def test_get_channel_info(self):
        """チャンネル情報取得のテスト"""
        self.client.join_channel("test-channel", "agent-1", "TestAgent")
        self.client.send_message("test-channel", "Hello!", "agent-1", "TestAgent")

        info = self.client.get_channel_info("test-channel")

        assert info is not None
        assert info["name"] == "test-channel"
        assert "agent-1" in info["participants"]
        assert info["message_count"] == 1
        assert len(info["messages"]) == 1

    def test_get_channel_info_nonexistent(self):
        """存在しないチャンネルの情報取得テスト"""
        info = self.client.get_channel_info("nonexistent")
        assert info is None

    def test_get_channel_messages(self):
        """チャンネルメッセージ履歴取得のテスト"""
        self.client.join_channel("test-channel", "agent-1", "TestAgent")

        for i in range(10):
            self.client.send_message("test-channel", f"Message {i}", "agent-1", "TestAgent")

        messages = self.client.get_channel_messages("test-channel")

        assert len(messages) == 10
        assert messages[0]["content"] == "Message 0"
        assert messages[-1]["content"] == "Message 9"

    def test_get_channel_messages_with_limit(self):
        """取得件数制限付きのメッセージ取得テスト"""
        self.client.join_channel("test-channel", "agent-1", "TestAgent")

        for i in range(50):
            self.client.send_message("test-channel", f"Message {i}", "agent-1", "TestAgent")

        messages = self.client.get_channel_messages("test-channel", limit=10)

        assert len(messages) == 10

    def test_get_channel_messages_nonexistent(self):
        """存在しないチャンネルのメッセージ取得テスト"""
        messages = self.client.get_channel_messages("nonexistent")
        assert messages == []

    def test_is_participant(self):
        """参加者確認のテスト"""
        self.client.join_channel("test-channel", "agent-1", "TestAgent")

        assert self.client.is_participant("test-channel", "agent-1") is True
        assert self.client.is_participant("test-channel", "agent-2") is False

    def test_is_participant_nonexistent_channel(self):
        """存在しないチャンネルでの参加者確認テスト"""
        assert self.client.is_participant("nonexistent", "agent-1") is False


class TestGlobalChannelClient:
    """グローバルChannelClientインスタンスのテスト"""

    def setup_method(self):
        """各テストメソッドの前に実行"""
        reset_channel_client()

    def test_init_channel_client(self):
        """ChannelClient初期化のテスト"""
        manager = ChannelManager()
        client = init_channel_client(manager)

        assert isinstance(client, ChannelClient)
        assert client._manager is manager

    def test_get_channel_client(self):
        """ChannelClient取得のテスト"""
        manager = ChannelManager()
        init_channel_client(manager)

        client = get_channel_client()

        assert isinstance(client, ChannelClient)

    def test_get_channel_client_before_init(self):
        """初期化前のChannelClient取得テスト"""
        client = get_channel_client()
        assert client is None

    def test_reset_channel_client(self):
        """ChannelClientリセットのテスト"""
        manager = ChannelManager()
        init_channel_client(manager)

        # リセット前に取得できる
        assert get_channel_client() is not None

        reset_channel_client()

        # リセット後に取得できない
        assert get_channel_client() is None

    def test_init_multiple_times(self):
        """複数回の初期化テスト（最後のものが有効）"""
        manager1 = ChannelManager()
        manager2 = ChannelManager()

        client1 = init_channel_client(manager1)
        client2 = init_channel_client(manager2)

        # 同じインスタンスが返されるわけではないが、
        # get_channel_client() は最新のものを返すはず
        current = get_channel_client()
        assert current is not None
        assert current._manager is manager2
