"""会話チャンネル機能のテスト

ConversationChannel, ChannelManager クラスのテスト
"""

import pytest

from orchestrator.web.message_handler import (
    ConversationChannel,
    ChannelManager,
    validate_channel_name,
)


class TestValidateChannelName:
    """チャンネル名検証のテスト"""

    def test_valid_channel_names(self):
        """有効なチャンネル名のテスト"""
        valid_names = [
            "general",
            "test-channel",
            "test_channel",
            "Channel123",
            "a",
            "A" * 50,  # 最大長
        ]
        for name in valid_names:
            assert validate_channel_name(name), f"'{name}' should be valid"

    def test_invalid_channel_names(self):
        """無効なチャンネル名のテスト"""
        invalid_names = [
            "",  # 空文字列
            " " * 5,  # スペースのみ
            "test channel",  # スペースを含む
            "test.channel",  # ピリオドを含む
            "test/channel",  # スラッシュを含む
            "test@channel",  # 記号を含む
            "日本語",  # 日本語
            "Test!Channel",  # 感嘆符を含む
            "A" * 51,  # 最大長超過
            None,  # None
            123,  # 数値
        ]
        for name in invalid_names:
            assert not validate_channel_name(name), f"'{name}' should be invalid"


class TestConversationChannel:
    """ConversationChannel クラスのテスト"""

    def test_initialization(self):
        """初期化のテスト"""
        channel = ConversationChannel("test-channel")
        assert channel.channel_name == "test-channel"
        assert len(channel.participants) == 0
        assert len(channel.messages) == 0

    def test_join(self):
        """参加のテスト"""
        channel = ConversationChannel("test-channel")
        channel.join("agent-1")
        channel.join("agent-2")

        assert "agent-1" in channel.participants
        assert "agent-2" in channel.participants
        assert len(channel.participants) == 2

    def test_leave(self):
        """退出のテスト"""
        channel = ConversationChannel("test-channel")
        channel.join("agent-1")
        channel.join("agent-2")
        channel.leave("agent-1")

        assert "agent-1" not in channel.participants
        assert "agent-2" in channel.participants
        assert len(channel.participants) == 1

    def test_leave_nonexistent_agent(self):
        """存在しないエージェントの退出はエラーにならない"""
        channel = ConversationChannel("test-channel")
        channel.leave("nonexistent")  # エラーにならないはず
        assert len(channel.participants) == 0

    def test_add_message(self):
        """メッセージ追加のテスト"""
        channel = ConversationChannel("test-channel")
        message = {"sender": "agent-1", "content": "Hello", "timestamp": 1234567890}

        channel.add_message(message)

        assert len(channel.messages) == 1
        assert channel.messages[0] == message

    def test_add_message_limit(self):
        """メッセージ履歴の制限（最大100件）"""
        channel = ConversationChannel("test-channel")

        # 101件のメッセージを追加
        for i in range(101):
            channel.add_message({"sender": "agent-1", "content": f"Message {i}", "timestamp": i})

        # 最大100件に制限されている
        assert len(channel.messages) == 100
        # 最古のメッセージが削除されている
        assert channel.messages[0]["content"] == "Message 1"
        assert channel.messages[-1]["content"] == "Message 100"

    def test_get_messages_default_limit(self):
        """メッセージ取得のデフォルト制限（50件）"""
        channel = ConversationChannel("test-channel")

        for i in range(100):
            channel.add_message({"sender": "agent-1", "content": f"Message {i}", "timestamp": i})

        messages = channel.get_messages()
        assert len(messages) == 50  # デフォルトで50件
        assert messages[0]["content"] == "Message 50"
        assert messages[-1]["content"] == "Message 99"

    def test_get_messages_custom_limit(self):
        """カスタム制限でのメッセージ取得"""
        channel = ConversationChannel("test-channel")

        for i in range(100):
            channel.add_message({"sender": "agent-1", "content": f"Message {i}", "timestamp": i})

        messages = channel.get_messages(limit=10)
        assert len(messages) == 10

    def test_get_participants_returns_copy(self):
        """参加者リストのコピーが返される"""
        channel = ConversationChannel("test-channel")
        channel.join("agent-1")

        participants = channel.get_participants()
        participants.add("agent-2")  # コピーに追加

        # オリジナルは変更されていない
        assert "agent-2" not in channel.participants


class TestChannelManager:
    """ChannelManager クラスのテスト"""

    def test_initialization(self):
        """初期化のテスト"""
        manager = ChannelManager()
        assert len(manager.channels) == 0

    def test_create_channel(self):
        """チャンネル作成のテスト"""
        manager = ChannelManager()
        channel = manager.create_channel("test-channel")

        assert isinstance(channel, ConversationChannel)
        assert channel.channel_name == "test-channel"
        assert "test-channel" in manager.channels

    def test_create_channel_invalid_name(self):
        """無効なチャンネル名で ValueError が送出される"""
        manager = ChannelManager()

        with pytest.raises(ValueError, match="Invalid channel name"):
            manager.create_channel("")  # 空文字列

        with pytest.raises(ValueError, match="Invalid channel name"):
            manager.create_channel("invalid name!")  # スペースと記号

        with pytest.raises(ValueError, match="Invalid channel name"):
            manager.create_channel("a" * 51)  # 長すぎる

    def test_create_channel_returns_existing(self):
        """既存のチャンネル名の場合、既存のチャンネルが返される"""
        manager = ChannelManager()
        channel1 = manager.create_channel("test-channel")
        channel2 = manager.create_channel("test-channel")

        assert channel1 is channel2  # 同一インスタンス
        assert len(manager.channels) == 1

    def test_get_channel(self):
        """チャンネル取得のテスト"""
        manager = ChannelManager()
        manager.create_channel("test-channel")

        channel = manager.get_channel("test-channel")
        assert isinstance(channel, ConversationChannel)

    def test_get_channel_nonexistent(self):
        """存在しないチャンネルで None が返される"""
        manager = ChannelManager()
        assert manager.get_channel("nonexistent") is None

    def test_delete_channel(self):
        """チャンネル削除のテスト"""
        manager = ChannelManager()
        manager.create_channel("test-channel")

        result = manager.delete_channel("test-channel")

        assert result is True
        assert "test-channel" not in manager.channels

    def test_delete_channel_nonexistent(self):
        """存在しないチャンネルの削除で False が返される"""
        manager = ChannelManager()
        assert manager.delete_channel("nonexistent") is False

    def test_list_channels(self):
        """チャンネル一覧のテスト"""
        manager = ChannelManager()
        manager.create_channel("channel-1")
        manager.create_channel("channel-2")
        manager.create_channel("channel-3")

        channels = manager.list_channels()
        assert set(channels) == {"channel-1", "channel-2", "channel-3"}

    def test_list_channels_empty(self):
        """空のチャンネル一覧"""
        manager = ChannelManager()
        assert manager.list_channels() == []
