/**
 * ThinkingLogコンポーネント
 *
 * エージェントの思考ログを表示します
 */

import { useEffect, useRef, memo } from "react";
import { Brain, Zap, Heart } from "lucide-react";
import { useTeamStore } from "../../stores/teamStore";
import { useUIStore } from "../../stores/uiStore";
import { formatTime } from "../../lib/utils";
import { cn } from "../../lib/utils";
import { Badge } from "../ui/Badge";
import type { MessageCategory } from "../../services/types";

const categoryConfig: Record<MessageCategory, { icon: React.ComponentType<{ className?: string }>; color: string; bgColor: string; label: string }> = {
  action: { icon: Zap, color: "text-blue-500", bgColor: "bg-blue-500/10", label: "行動" },
  thinking: { icon: Brain, color: "text-yellow-500", bgColor: "bg-yellow-500/10", label: "思考" },
  emotion: { icon: Heart, color: "text-pink-500", bgColor: "bg-pink-500/10", label: "感情" },
};

const emotionEmoji: Record<string, string> = {
  confusion: "😕",
  satisfaction: "😊",
  focus: "🎯",
  concern: "😟",
  neutral: "😐",
};

// 思考ログアイテムコンポーネント（memo化）
const ThinkingLogItem = memo(function ThinkingLogItem({
  log,
  index,
}: {
  log: {
    timestamp: string;
    agentName: string;
    category: MessageCategory;
    emotion?: string;
    content: string;
    taskDetails?: { taskId?: string; status: string };
  };
  index: number;
}) {
  const config = categoryConfig[log.category];
  const Icon = config.icon;
  const emoji = log.emotion ? emotionEmoji[log.emotion] : null;

  return (
    <div
      key={`${log.timestamp}-${index}`}
      className={cn(
        "flex items-start gap-3 p-3 rounded-lg border",
        config.bgColor,
        "hover:bg-accent/50 transition-colors"
      )}
    >
      <div className={cn("mt-0.5", config.color)}>
        <Icon className="h-4 w-4" />
      </div>

      <div className="flex-1 min-w-0 space-y-1">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-medium text-sm">{log.agentName}</span>
          <Badge variant="outline" className="text-xs">
            {config.label}
          </Badge>
          {emoji && (
            <span className="text-lg" title={log.emotion}>
              {emoji}
            </span>
          )}
          {log.timestamp && (
            <span className="text-xs text-muted-foreground">
              {formatTime(log.timestamp)}
            </span>
          )}
        </div>

        <p className="text-sm text-foreground break-words">
          {log.content}
        </p>

        {log.taskDetails && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span>タスク:</span>
            <span className="font-mono">{log.taskDetails.taskId?.slice(0, 8)}</span>
            <Badge variant="secondary">{log.taskDetails.status}</Badge>
          </div>
        )}
      </div>
    </div>
  );
});

export function ThinkingLog() {
  const thinkingLogs = useTeamStore((state) => state.thinkingLogs);
  const isAutoScrollEnabled = useUIStore((state) => state.isAutoScrollEnabled);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isAutoScrollEnabled && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [thinkingLogs, isAutoScrollEnabled]);

  return (
    <div className="h-full flex flex-col">
      <div className="px-6 py-4 border-b border-border">
        <h2 className="font-semibold">思考ログ</h2>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4">
        <div className="space-y-2">
          {thinkingLogs.length === 0 ? (
            <div className="py-12 text-center text-muted-foreground">
              思考ログはまだありません
            </div>
          ) : (
            thinkingLogs.map((log, index) => (
              <ThinkingLogItem key={`${log.timestamp}-${index}`} log={log} index={index} />
            ))
          )}
        </div>
      </div>
    </div>
  );
}
