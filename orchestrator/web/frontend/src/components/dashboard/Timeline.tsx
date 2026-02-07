/**
 * Timelineコンポーネント
 *
 * アクティビティタイムラインを表示します
 */

import { useEffect, useRef, useMemo } from "react";
import { MessageSquare, List, CheckCircle } from "lucide-react";
import { useUIStore } from "../../stores/uiStore";
import { formatTime } from "../../lib/utils";
import { cn } from "../../lib/utils";
import type { TeamMessage, TaskInfo } from "../../services/types";

type TimelineItemType = "message" | "task" | "completed";

interface TimelineItem {
  id: string;
  type: TimelineItemType;
  timestamp: string;
  agent: string;
  content: string;
}

// ストアからタイムラインアイテムを生成
function generateTimelineItems(
  messages: TeamMessage[],
  tasks: TaskInfo[]
): TimelineItem[] {
  const items: TimelineItem[] = [];

  // メッセージを追加
  messages.forEach((msg) => {
    items.push({
      id: `msg-${msg.id}`,
      type: "message",
      timestamp: msg.timestamp,
      agent: msg.sender,
      content: msg.content.slice(0, 100),
    });
  });

  // タスクを追加
  tasks.forEach((task) => {
    if (task.updatedAt) {
      items.push({
        id: `task-${task.taskId}`,
        type: task.status === "completed" ? "completed" : "task",
        timestamp: task.updatedAt,
        agent: task.owner,
        content: task.subject,
      });
    }
  });

  // タイムスタンプでソート
  return items.sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
}

export function Timeline() {
  // TODO: teamStore からの取得を無効化（無限ループ回避のため一時的に空配列）
  const messages: TeamMessage[] = [];
  const tasks: TaskInfo[] = [];
  const isAutoScrollEnabled = useUIStore((state) => state.isAutoScrollEnabled);
  const scrollRef = useRef<HTMLDivElement>(null);

  const timelineItems = useMemo(() => generateTimelineItems(messages, tasks), [messages, tasks]);

  useEffect(() => {
    if (isAutoScrollEnabled && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [timelineItems, isAutoScrollEnabled]);

  const itemConfig = {
    message: { icon: MessageSquare, color: "bg-cyan-500" },
    task: { icon: List, color: "bg-yellow-500" },
    completed: { icon: CheckCircle, color: "bg-green-500" },
  };

  return (
    <div className="h-full flex flex-col">
      <div className="px-6 py-4 border-b border-border">
        <h2 className="font-semibold">アクティビティタイムライン</h2>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-6">
        <div className="relative">
          {/* タイムラインの線 */}
          <div className="absolute left-[7px] top-0 bottom-0 w-[2px] bg-gradient-to-b from-primary via-info to-transparent" />

          <div className="space-y-6">
            {timelineItems.length === 0 ? (
              <div className="pl-8 py-8 text-center text-muted-foreground">
                アクティビティはまだありません
              </div>
            ) : (
              timelineItems.map((item, index) => {
                const config = itemConfig[item.type];
                const Icon = config.icon;

                return (
                  <div key={`${item.id}-${index}`} className="relative pl-8">
                    {/* ドット */}
                    <div className="absolute left-0 top-1.5">
                      <div className={cn("h-4 w-4 rounded-full border-2 border-background", config.color)} />
                    </div>

                    {/* コンテンツ */}
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Icon className="h-3 w-3" />
                        <span>{formatTime(item.timestamp)}</span>
                      </div>
                      <div className="text-sm">
                        <span className="font-medium">{item.agent}</span>
                        <span className="text-muted-foreground mx-1">•</span>
                        <span className="line-clamp-2">{item.content}</span>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
