"""orchestrator-cc CLI

このモジュールでは、コマンドラインインターフェースを提供します。
"""

import argparse
import asyncio
import sys
from pathlib import Path


def start_cluster(args: argparse.Namespace) -> None:
    """クラスタを起動します。

    Args:
        args: コマンドライン引数
    """
    from orchestrator.core.cc_cluster_manager import CCClusterManager
    from orchestrator.core.yaml_monitor import YAMLMonitor

    async def _start() -> None:
        cluster = CCClusterManager(args.config)
        await cluster.start()
        print(f"クラスタ '{cluster._config.name}' を起動しました")
        print(f"tmuxセッション: {cluster._config.session_name}")
        print(f"tmux attach -t {cluster._config.session_name} で確認できます")

        # YAML監視を開始
        queue_dir = Path(cluster._config.work_dir) / "queue"
        queue_dir.mkdir(parents=True, exist_ok=True)

        def yaml_callback(file_path: str) -> None:
            """YAMLファイル変更時のコールバック"""
            print(f"[YAML Monitor] 変更検知: {file_path}")
            # 実際のエージェント通知はNotificationServiceで行う

        monitor = YAMLMonitor(str(queue_dir), yaml_callback)
        monitor.start()
        print(f"[YAML Monitor] {queue_dir} の監視を開始しました")

        # 監視を続ける（無限ループ）
        try:
            while monitor.is_running():
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nクラスタを停止します...")
            monitor.stop()
            await cluster.stop()

    asyncio.run(_start())


def execute_task(args: argparse.Namespace) -> None:
    """タスクを実行します。

    Args:
        args: コマンドライン引数
    """
    from orchestrator.core.cc_cluster_manager import CCClusterManager

    async def _execute() -> None:
        cluster = CCClusterManager(args.config)
        # 既存のクラスタに接続
        cluster.connect()
        # Grand Bossにタスクを送信
        result = await cluster.send_message("grand_boss", args.task)
        print(result)

    asyncio.run(_execute())


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

    # executeコマンド
    execute_parser = subparsers.add_parser("execute", help="タスクを実行")
    execute_parser.add_argument("task", help="実行するタスク")
    execute_parser.add_argument(
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
    elif args.command == "execute":
        execute_task(args)
    elif args.command == "stop":
        stop_cluster(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
