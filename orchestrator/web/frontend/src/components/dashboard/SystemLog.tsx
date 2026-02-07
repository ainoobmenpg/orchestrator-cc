/**
 * SystemLogコンポーネント
 *
 * システムログを表示します
 */

import { useEffect, useRef, memo } from "react";
import { Info, CheckCircle, AlertTriangle, AlertCircle, X } from "lucide-react";
import { useUIStore } from "../../stores/uiStore";
import { Button } from "../ui/Button";
import { formatTime } from "../../lib/utils";
import { cn } from "../../lib/utils";
import type { SystemLog } from "../../services/types";

const logLevelConfig = {
  info: { icon: Info, color: "text-blue-500", bgColor: "bg-blue-500/10" },
  success: { icon: CheckCircle, color: "text-green-500", bgColor: "bg-green-500/10" },
  warning: { icon: AlertTriangle, color: "text-yellow-500", bgColor: "bg-yellow-500/10" },
  error: { icon: AlertCircle, color: "text-red-500", bgColor: "bg-red-500/10" },
};

// ログアイテムコンポーネント（memo化）
const LogItem = memo(function LogItem({
  log,
  index,
}: {
  log: SystemLog;
  index: number;
}) {
  const config = logLevelConfig[log.level];
  const Icon = config.icon;

  return (
    <div
      key={`${log.timestamp ?? "no-timestamp"}-${index}`}
      className={cn(
        "flex items-start gap-3 px-3 py-2 rounded hover:bg-accent/50 transition-colors",
        config.bgColor
      )}
    >
      <Icon className={cn("h-4 w-4 mt-0.5 flex-shrink-0", config.color)} />

      {log.timestamp && (
        <span className="text-xs text-muted-foreground flex-shrink-0">
          {formatTime(log.timestamp)}
        </span>
      )}

      <span className="font-medium uppercase flex-shrink-0 w-16">
        {log.level}
      </span>

      <span className="flex-1 break-words">{log.content}</span>
    </div>
  );
});

export function SystemLog() {
  // TODO: teamStore からの取得を無効化（無限ループ回避のため一時的に空配列・空関数）
  const systemLogs: SystemLog[] = [];
  const clearSystemLogs = () => {};
  const isAutoScrollEnabled = useUIStore((state) => state.isSystemLogAutoScrollEnabled);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isAutoScrollEnabled && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [systemLogs, isAutoScrollEnabled]);

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between px-6 py-4 border-b border-border">
        <h2 className="font-semibold">システムログ</h2>
        <Button
          variant="icon"
          size="sm"
          onClick={clearSystemLogs}
          title="クリア"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4">
        <div className="space-y-1 font-mono text-sm">
          {systemLogs.length === 0 ? (
            <div className="py-12 text-center text-muted-foreground">
              システムログはまだありません
            </div>
          ) : (
            systemLogs.map((log, index) => <LogItem key={`${log.timestamp}-${index}`} log={log} index={index} />)
          )}
        </div>
      </div>
    </div>
  );
}
