"""orchestrator-cc CLI

このモジュールでは、コマンドラインインターフェースを提供します。
"""

import argparse
import asyncio
import sys


def start_cluster(args: argparse.Namespace) -> None:
    """クラスタを起動します。

    Args:
        args: コマンドライン引数
    """
    from orchestrator.core.cc_cluster_manager import CCClusterManager

    async def _start() -> None:
        cluster = CCClusterManager(args.config)
        await cluster.start()
        print(f"クラスタ '{cluster._config.name}' を起動しました")
        print(f"tmuxセッション: {cluster._config.session_name}")
        print(f"tmux attach -t {cluster._config.session_name} で確認できます")

    asyncio.run(_start())


def stop_cluster(args: argparse.Namespace) -> None:
    """クラスタを停止します。

    Args:
        args: コマンドライン引数
    """
    from orchestrator.core.cc_cluster_manager import CCClusterManager

    async def _stop() -> None:
        cluster = CCClusterManager(args.config)
        await cluster.stop()
        print("クラスタを停止しました")

    asyncio.run(_stop())


def main() -> None:
    """メインエントリーポイント"""
    parser = argparse.ArgumentParser(description="orchestrator-cc CLI")
    subparsers = parser.add_subparsers(dest="command", help="サブコマンド")

    # startコマンド
    start_parser = subparsers.add_parser("start", help="クラスタを起動")
    start_parser.add_argument(
        "--config",
        default="config/cc-cluster.yaml",
        help="クラスタ設定ファイルのパス（デフォルト: config/cc-cluster.yaml）",
    )

    # stopコマンド
    stop_parser = subparsers.add_parser("stop", help="クラスタを停止")
    stop_parser.add_argument(
        "--config",
        default="config/cc-cluster.yaml",
        help="クラスタ設定ファイルのパス（デフォルト: config/cc-cluster.yaml）",
    )

    # 引数をパース
    args = parser.parse_args()

    # コマンドを実行
    if args.command == "start":
        start_cluster(args)
    elif args.command == "stop":
        stop_cluster(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
