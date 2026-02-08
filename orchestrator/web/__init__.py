"""Webモジュール

このパッケージでは、FastAPIベースのダッシュボードバックエンドを提供します。

サブモジュール:
- channel_client: エージェント向けチャンネル操作クライアント
- message_handler: WebSocket接続管理とチャンネル管理
- team_models: Agent Teamsデータモデル
- teams_monitor: Teams監視モジュール
"""

from orchestrator.web.channel_client import (
    ChannelClient,
    get_channel_client,
    init_channel_client,
    reset_channel_client,
)

__all__ = [
    "ChannelClient",
    "get_channel_client",
    "init_channel_client",
    "reset_channel_client",
]
