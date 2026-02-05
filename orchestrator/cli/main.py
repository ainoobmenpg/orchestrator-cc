"""orchestrator-cc CLI

このモジュールでは、コマンドラインインターフェースを提供します。
"""

import argparse
import asyncio
import json
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
        # 並列起動パラメータを取得
        parallel = not args.sequential
        batch_size = args.batch_size
        await cluster.start(parallel=parallel, batch_size=batch_size)
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


def status_cluster(args: argparse.Namespace) -> None:
    """クラスタの状態を表示します。

    Args:
        args: コマンドライン引数
    """
    from datetime import datetime

    from orchestrator.core.cc_cluster_manager import CCClusterManager

    cluster = CCClusterManager(args.config)
    status = cluster.get_status()

    print(f"\n{'='*50}")
    print(f"クラスタ名: {status['cluster_name']}")
    print(f"tmuxセッション: {status['session_name']}")
    print(f"セッション状態: {'起動中' if status['session_exists'] else '停止中'}")
    print(f"{'='*50}")
    print("\nエージェント状態:")
    print("-" * 50)

    for agent in status["agents"]:
        status_str = "🟢 実行中" if agent["running"] else "🔴 停止"
        last_activity = "N/A"
        if agent["last_activity"] > 0:
            last_activity = datetime.fromtimestamp(agent["last_activity"]).strftime("%Y-%m-%d %H:%M:%S")

        print(f"""
  {agent['name']} ({agent['role']})
    状態: {status_str}
    再起動回数: {agent['restart_count']}
    最終アクティビティ: {last_activity}
""")

    print("-" * 50)


def show_logs(args: argparse.Namespace) -> None:
    """通信ログを表示します。

    Args:
        args: コマンドライン引数
    """
    from datetime import datetime

    from orchestrator.core.cluster_logger import ClusterLogger, LogFilter

    logger = ClusterLogger(log_file=args.log_file)

    # フィルタ条件を作成
    log_filter = LogFilter(
        from_agent=args.from_agent,
        to_agent=args.to_agent,
        msg_type=args.msg_type,
        level=args.level,
        limit=args.limit,
    )

    if args.recent:
        # 最近のログを取得
        entries = logger.get_recent_logs(count=args.limit or 10)
    else:
        # フィルタ適用してログを取得
        entries = logger.read_logs(log_filter)

    if not entries:
        print("ログが見つかりませんでした。")
        return

    # JSON出力モード
    if args.json:
        data = [
            {
                "timestamp": e.timestamp,
                "id": e.id,
                "from_agent": e.from_agent,
                "to_agent": e.to_agent,
                "type": e.type,
                "content": e.content,
                "level": e.level,
            }
            for e in entries
        ]
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    # 表形式出力
    print(f"\n{'='*100}")
    print(f"通信ログ ({len(entries)}件)")
    print(f"{'='*100}\n")

    for entry in entries:
        # タイムスタンプを整形
        try:
            ts = datetime.fromisoformat(entry.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        except:
            ts = entry.timestamp

        # タイプに応じたアイコン
        type_icons = {
            "task": "📋",
            "result": "✅",
            "thought": "💭",
            "error": "❌",
            "info": "ℹ️",
        }
        icon = type_icons.get(entry.type, "📝")

        print(f"{icon} [{ts}] {entry.from_agent} → {entry.to_agent} ({entry.type})")
        print(f"   {entry.content[:100]}{'...' if len(entry.content) > 100 else ''}")
        print()

    print(f"{'='*100}")


def show_tasks(args: argparse.Namespace) -> None:
    """タスク一覧を表示します。

    Args:
        args: コマンドライン引数
    """
    from orchestrator.core.task_tracker import TaskStatus, TaskTracker

    # タスク追跡インスタンスを作成
    tracker = TaskTracker()

    # 全サブタスクを取得
    all_tasks = tracker.get_all_subtasks()

    if not all_tasks:
        print("タスクが見つかりませんでした。")
        return

    # ステータスでフィルタ
    if args.status:
        try:
            filter_status = TaskStatus(args.status)
            all_tasks = [t for t in all_tasks if t.status == filter_status]
        except ValueError:
            print(f"無効なステータス: {args.status}")
            print(f"有効なステータス: {[s.value for s in TaskStatus]}")
            return

    # エージェントでフィルタ
    if args.agent:
        all_tasks = [t for t in all_tasks if t.assigned_to == args.agent]

    if not all_tasks:
        print("条件に一致するタスクが見つかりませんでした。")
        return

    # JSON出力モード
    if args.json:
        data = [
            {
                "id": t.id,
                "description": t.description,
                "assigned_to": t.assigned_to,
                "status": t.status.value,
                "result": t.result,
                "created_at": t.created_at,
                "completed_at": t.completed_at,
            }
            for t in all_tasks
        ]
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    # 表形式出力
    print(f"\n{'='*100}")
    print(f"タスク一覧 ({len(all_tasks)}件)")
    print(f"{'='*100}\n")

    # ステータス別にグループ化
    status_order = [TaskStatus.IN_PROGRESS, TaskStatus.PENDING, TaskStatus.COMPLETED, TaskStatus.FAILED]
    grouped: dict[TaskStatus, list] = {status: [] for status in status_order}

    for task in all_tasks:
        grouped[task.status].append(task)

    for status in status_order:
        tasks = grouped[status]
        if not tasks:
            continue

        # ステータスに応じたアイコン
        status_icons = {
            TaskStatus.PENDING: "⏳",
            TaskStatus.IN_PROGRESS: "🔄",
            TaskStatus.COMPLETED: "✅",
            TaskStatus.FAILED: "❌",
        }
        icon = status_icons[status]

        print(f"{icon} {status.value.upper()} ({len(tasks)}件)")
        print("-" * 100)

        for task in tasks:
            created = task.created_at[:19] if task.created_at else "N/A"
            print(f"  [{task.id}] {task.description}")
            print(f"    担当: {task.assigned_to} | 作成: {created}")
            if task.result:
                result_preview = task.result[:80] + "..." if len(task.result) > 80 else task.result
                print(f"    結果: {result_preview}")
            print()

    print(f"{'='*100}")
    print(f"\nサマリー: {tracker.get_summary()}")


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
    start_parser.add_argument(
        "--sequential",
        action="store_true",
        help="順次起動モード（デフォルト: バッチサイズ3での並列起動）",
    )
    start_parser.add_argument(
        "--batch-size",
        type=int,
        default=3,
        help="並列起動時のバッチサイズ（デフォルト: 3）",
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

    # statusコマンド
    status_parser = subparsers.add_parser("status", help="クラスタの状態を表示")
    status_parser.add_argument(
        "--config",
        default="config/cc-cluster.yaml",
        help="クラスタ設定ファイルのパス（デフォルト: config/cc-cluster.yaml）",
    )

    # logsコマンド
    logs_parser = subparsers.add_parser("logs", help="通信ログを表示")
    logs_parser.add_argument(
        "--log-file",
        default="messages.jsonl",
        help="ログファイルのパス（デフォルト: messages.jsonl）",
    )
    logs_parser.add_argument("--from-agent", help="送信元エージェントでフィルタ")
    logs_parser.add_argument("--to-agent", help="送信先エージェントでフィルタ")
    logs_parser.add_argument("--msg-type", help="メッセージタイプでフィルタ（task/result/thought/error/info）")
    logs_parser.add_argument("--level", help="ログレベルでフィルタ（DEBUG/INFO/WARNING/ERROR）")
    logs_parser.add_argument("--limit", type=int, help="最大表示数")
    logs_parser.add_argument("--recent", action="store_true", help="最近のログを表示")
    logs_parser.add_argument("--json", action="store_true", help="JSON形式で出力")

    # tasksコマンド
    tasks_parser = subparsers.add_parser("tasks", help="タスク一覧を表示")
    tasks_parser.add_argument("--status", help="ステータスでフィルタ（pending/in_progress/completed/failed）")
    tasks_parser.add_argument("--agent", help="担当エージェントでフィルタ")
    tasks_parser.add_argument("--json", action="store_true", help="JSON形式で出力")

    # 引数をパース
    args = parser.parse_args()

    # コマンドを実行
    if args.command == "start":
        start_cluster(args)
    elif args.command == "execute":
        execute_task(args)
    elif args.command == "stop":
        stop_cluster(args)
    elif args.command == "status":
        status_cluster(args)
    elif args.command == "logs":
        show_logs(args)
    elif args.command == "tasks":
        show_tasks(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
