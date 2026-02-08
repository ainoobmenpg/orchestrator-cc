/**
 * ChatMessageListコンポーネント
 *
 * チャットメッセージ一覧を表示します
 * 思考ログ、チームメッセージを統合して表示します
 */

import { useEffect, useRef, useMemo } from "react";
import { ChatMessage } from "./ChatMessage";
import { ThinkingMessage } from "./ThinkingMessage";
import { TypingIndicator } from "./TypingIndicator";
import { cn } from "../../lib/utils";
import type { ThinkingLog } from "../../services/types";
import type { TeamMessage } from "../../services/types";

export interface ChatMessageListProps {
  /** 思考ログ */
  thinkingLogs?: ThinkingLog[];
  /** チームメッセージ */
  teamMessages?: TeamMessage[];
  /** 入力中のエージェント名 */
  typingAgents?: string[];
  /** 自動スクロール有効フラグ */
  autoScroll?: boolean;
  /** カスタムクラス名 */
  className?: string;
  /** リアクション追加ハンドラー */
  onReactionAdd?: (messageId: string, emoji: string) => void;
}

/** 統合メッセージ型 */
interface UnifiedMessage {
  id: string;
  type: "thinking" | "team";
  timestamp: string;
}

export function ChatMessageList({
  thinkingLogs = [],
  teamMessages = [],
  typingAgents = [],
  autoScroll = true,
  className,
  onReactionAdd,
}: ChatMessageListProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const endRef = useRef<HTMLDivElement>(null);

  // メッセージを統合してタイムスタンプ順にソート
  const messages = useMemo(() => {
    const unified: (UnifiedMessage & {
      log?: ThinkingLog;
      message?: TeamMessage;
    })[] = [
      ...thinkingLogs.map((log) => ({
        id: `thinking-${log.timestamp}-${log.agentName}`,
        type: "thinking" as const,
        timestamp: log.timestamp,
        log,
      })),
      ...teamMessages.map((msg) => ({
        id: `team-${msg.id}`,
        type: "team" as const,
        timestamp: msg.timestamp,
        message: msg,
      })),
    ];

    return unified.sort(
      (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );
  }, [thinkingLogs, teamMessages]);

  // 自動スクロール
  useEffect(() => {
    if (autoScroll && endRef.current) {
      endRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, autoScroll]);

  // メッセージをグループ化（同じエージェントの連続メッセージをまとめる）
  const groupedMessages = useMemo(() => {
    const groups: typeof messages = [];
    let currentAgent: string | null = null;
    let lastTime = 0;
    const GROUPING_THRESHOLD = 5 * 60 * 1000; // 5分

    messages.forEach((msg) => {
      const agentName = msg.type === "thinking" ? msg.log!.agentName : msg.message!.sender;
      const msgTime = new Date(msg.timestamp).getTime();

      if (
        currentAgent === agentName &&
        msgTime - lastTime < GROUPING_THRESHOLD
      ) {
        // 同じグループに追加
        groups.push(msg);
      } else {
        // 新しいグループ
        currentAgent = agentName;
        groups.push(msg);
      }

      lastTime = msgTime;
    });

    return groups;
  }, [messages]);

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* メッセージリスト */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-2">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            <p>メッセージはまだありません</p>
          </div>
        ) : (
          <div className="space-y-1">
            {messages.map((msg, index) => {
              const prevMsg = messages[index - 1];
              const showAvatar =
                !prevMsg ||
                prevMsg.type !== msg.type ||
                (msg.type === "thinking"
                  ? prevMsg.log!.agentName !== msg.log!.agentName
                  : prevMsg.message!.sender !== msg.message!.sender);

              if (msg.type === "thinking") {
                return (
                  <ThinkingMessage
                    key={msg.id}
                    log={msg.log!}
                  />
                );
              } else {
                const teamMsg = msg.message!;
                return (
                  <ChatMessage
                    key={msg.id}
                    id={msg.id}
                    agentName={teamMsg.sender}
                    content={teamMsg.content}
                    timestamp={teamMsg.timestamp}
                    showAvatar={showAvatar}
                    onReactionAdd={
                      onReactionAdd
                        ? (emoji) => onReactionAdd(msg.id, emoji)
                        : undefined
                    }
                  />
                );
              }
            })}
            <div ref={endRef} />
          </div>
        )}
      </div>

      {/* 入力中インジケーター */}
      {typingAgents.length > 0 && (
        <div className="px-4 py-2">
          <TypingIndicator agentNames={typingAgents} />
        </div>
      )}
    </div>
  );
}
