/**
 * MessageListコンポーネント
 *
 * メッセージログを表示します
 * Framer Motionを使用してメッセージ追加時のスライドインアニメーションを実装しています
 */

import { useEffect, useRef } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Bot, AlertCircle, CheckCircle, Clock } from "lucide-react";
import { useTeamStore } from "../../stores/teamStore";
import { useUIStore } from "../../stores/uiStore";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { formatTime, cn } from "../../lib/utils";
import { slideInBottom } from "../../lib/animations";

export function MessageList() {
  const messages = useTeamStore((state) => state.messages);
  const isAutoScrollEnabled = useUIStore((state) => state.isAutoScrollEnabled);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isAutoScrollEnabled && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isAutoScrollEnabled]);

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
        <CardTitle className="text-lg">メッセージログ</CardTitle>
        <Badge variant="secondary">{messages.length}件</Badge>
      </CardHeader>

      <CardContent className="flex-1 overflow-y-auto">
        <div ref={scrollRef} className="space-y-2">
          {messages.length === 0 ? (
            <div className="py-12 text-center text-muted-foreground">
              メッセージはまだありません
            </div>
          ) : (
            <AnimatePresence mode="popLayout">
              {messages.map((message, index) => (
                <MessageItem
                  key={`${message.id}-${index}`}
                  message={message}
                  index={index}
                />
              ))}
            </AnimatePresence>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

interface MessageItemProps {
  message: {
    id: string;
    sender: string;
    recipient: string;
    content: string;
    timestamp: string;
    messageType: string;
  };
  index: number;
}

function MessageItem({ message, index }: MessageItemProps) {
  const isThinking = message.messageType === "thinking";
  const isTask = message.messageType === "task";
  const isResult = message.messageType === "result";

  const typeConfig = {
    thinking: {
      icon: AlertCircle,
      color: "text-yellow-500",
      bgColor: "bg-yellow-500/10",
      borderColor: "border-yellow-500/30",
      label: "思考",
    },
    task: {
      icon: Clock,
      color: "text-blue-500",
      bgColor: "bg-blue-500/10",
      borderColor: "border-blue-500/30",
      label: "タスク",
    },
    result: {
      icon: CheckCircle,
      color: "text-green-500",
      bgColor: "bg-green-500/10",
      borderColor: "border-green-500/30",
      label: "結果",
    },
    default: {
      icon: Bot,
      color: "text-cyan-500",
      bgColor: "bg-cyan-500/10",
      borderColor: "border-cyan-500/30",
      label: "メッセージ",
    },
  };

  const config = isThinking
    ? typeConfig.thinking
    : isTask
      ? typeConfig.task
      : isResult
        ? typeConfig.result
        : typeConfig.default;

  const Icon = config.icon;

  return (
    <motion.div
      variants={slideInBottom}
      initial="initial"
      animate="animate"
      exit={{ opacity: 0, height: 0, marginBottom: 0 }}
      transition={{
        type: "spring",
        stiffness: 400,
        damping: 25,
        delay: Math.min(index * 0.03, 0.3),
      }}
      className={cn(
        "rounded-lg border p-3 transition-colors hover:bg-accent/50",
        config.bgColor,
        config.borderColor,
      )}
    >
      <div className="flex items-start gap-3">
        <Icon className={cn("h-5 w-5 mt-0.5 flex-shrink-0", config.color)} />

        <div className="flex-1 min-w-0 space-y-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-foreground">{message.sender}</span>
            {message.recipient && (
              <>
                <span className="text-muted-foreground">→</span>
                <span className="font-medium text-foreground">{message.recipient}</span>
              </>
            )}
            <Badge variant="outline" className="text-xs">
              {config.label}
            </Badge>
            {message.timestamp && (
              <span className="text-xs text-muted-foreground">
                {formatTime(message.timestamp)}
              </span>
            )}
          </div>

          <div className="text-sm text-foreground whitespace-pre-wrap break-words font-mono bg-background/50 rounded p-2">
            {message.content}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
