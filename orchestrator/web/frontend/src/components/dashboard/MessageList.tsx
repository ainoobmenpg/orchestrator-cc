/**
 * MessageListコンポーネント
 *
 * メッセージログを表示します
 * Framer Motionを使用してメッセージ追加時のスライドインアニメーションを実装しています
 *
 * 会話チャンネルモードと通常メッセージモードの切り替え機能を提供します
 */

import { useEffect, useRef, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Bot, AlertCircle, CheckCircle, Clock, Hash } from "lucide-react";
import { useTeamStore } from "../../stores/teamStore";
import { useUIStore } from "../../stores/uiStore";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { formatTime, cn } from "../../lib/utils";
import { slideInBottom } from "../../lib/animations";
import ReactMarkdown from "react-markdown";

/** 表示モード */
type ViewMode = "messages" | "channel";

export function MessageList() {
  const messages = useTeamStore((state) => state.messages);
  const currentChannel = useTeamStore((state) => state.currentChannel);
  const channelMessages = useTeamStore((state) => state.channelMessages);
  const isAutoScrollEnabled = useUIStore((state) => state.isAutoScrollEnabled);
  const scrollRef = useRef<HTMLDivElement>(null);

  // 表示モード
  const [viewMode, setViewMode] = useState<ViewMode>("messages");

  // アイドル通知やタスク割り当てなどのシステムメッセージをフィルタリング
  const filteredMessages = useMemo(() => {
    return messages.filter((message) => {
      const content = message.content;
      // idle_notification を含むJSONメッセージを除外
      if (content.includes('"type":"idle_notification"')) {
        return false;
      }
      // task_assignment を含むJSONメッセージを除外
      if (content.includes('"type":"task_assignment"')) {
        return false;
      }
      return true;
    });
  }, [messages]);

  // チャンネルメッセージを取得
  const currentChannelMessages = useMemo(() => {
    if (!currentChannel) return [];
    return channelMessages[currentChannel] || [];
  }, [currentChannel, channelMessages]);

  // 表示するメッセージ（モードによって切り替え）
  const displayMessages = viewMode === "channel" ? currentChannelMessages : filteredMessages;
  const displayCount = displayMessages.length;
  const displayTitle = viewMode === "channel" && currentChannel ? `#${currentChannel}` : "メッセージログ";

  useEffect(() => {
    if (isAutoScrollEnabled && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [displayMessages, isAutoScrollEnabled]);

  // モード切り替え時のチャンネルチェック
  const handleModeChange = (mode: ViewMode) => {
    if (mode === "channel" && !currentChannel) {
      // チャンネルが選択されていない場合はモードを変更しない
      return;
    }
    setViewMode(mode);
  };

  return (
    <Card className="h-full flex flex-col min-h-0 max-h-[calc(100vh-12rem)]">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
        <div className="flex items-center gap-2">
          <CardTitle className="text-lg">{displayTitle}</CardTitle>
          {/* モード切り替えボタン */}
          {currentChannel && (
            <div className="flex gap-1">
              <Button
                variant={viewMode === "messages" ? "primary" : "ghost"}
                size="sm"
                onClick={() => handleModeChange("messages")}
                aria-label="通常メッセージモード"
              >
                <Bot className="h-4 w-4" />
              </Button>
              <Button
                variant={viewMode === "channel" ? "primary" : "ghost"}
                size="sm"
                onClick={() => handleModeChange("channel")}
                aria-label="チャンネルモード"
              >
                <Hash className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
        <Badge variant="secondary">{displayCount}件</Badge>
      </CardHeader>

      <CardContent className="flex-1 overflow-y-auto p-4 min-h-0">
        <div ref={scrollRef} className="space-y-2">
          {displayMessages.length === 0 ? (
            <div className="py-12 text-center text-muted-foreground">
              {viewMode === "channel" ? (
                <>
                  <p>チャンネル {currentChannel} にメッセージはまだありません</p>
                </>
              ) : (
                <>メッセージはまだありません</>
              )}
            </div>
          ) : (
            <AnimatePresence mode="popLayout">
              {displayMessages.map((message, index) => (
                <MessageItem
                  key={`${message.id}-${index}`}
                  message={message}
                  index={index}
                  isChannelMode={viewMode === "channel"}
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
    recipient?: string;
    content: string;
    timestamp: string | number;
    messageType?: string;
    channel?: string;
  };
  index: number;
  isChannelMode?: boolean;
}

function MessageItem({ message, index, isChannelMode }: MessageItemProps) {
  // チャンネルモードの場合
  if (isChannelMode) {
    const isCurrentUser = message.sender === "user";
    const timestamp = typeof message.timestamp === "number"
      ? new Date(message.timestamp).toISOString()
      : message.timestamp;

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
          "rounded-lg border p-3 transition-colors",
          isCurrentUser
            ? "bg-primary/10 border-primary/30 ml-8"
            : "bg-accent/50 border-border",
        )}
      >
        <div className="flex items-start gap-3">
          <div
            className={cn(
              "h-8 w-8 rounded-full flex items-center justify-center text-sm font-medium flex-shrink-0",
              isCurrentUser
                ? "bg-primary text-primary-foreground"
                : "bg-muted text-muted-foreground",
            )}
          >
            {message.sender.charAt(0).toUpperCase()}
          </div>

          <div className="flex-1 min-w-0 space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-medium text-foreground">{message.sender}</span>
              {timestamp && (
                <span className="text-xs text-muted-foreground">
                  {formatTime(timestamp)}
                </span>
              )}
            </div>

            <div className="text-sm text-foreground prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          </div>
        </div>
      </motion.div>
    );
  }

  // 通常メッセージモードの場合
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
                {formatTime(typeof message.timestamp === 'string' ? message.timestamp : String(message.timestamp))}
              </span>
            )}
          </div>

          <div className="text-sm text-foreground prose prose-sm dark:prose-invert max-w-none">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
