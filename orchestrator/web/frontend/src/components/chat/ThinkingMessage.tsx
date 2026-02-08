/**
 * ThinkingMessageコンポーネント
 *
 * エージェントの思考ログをSlack風のメッセージとして表示します
 * 感情表現、カテゴリー分類を活用して「人間臭さ」を表現します
 */

import { memo } from "react";
import { cn } from "../../lib/utils";
import { formatTime } from "../../lib/utils";
import { CATEGORY_CONFIG, EMOTION_CONFIG, inferCategory, inferEmotion } from "../../hooks/useThinkingLog";
import type { ThinkingLog } from "../../services/types";

export interface ThinkingMessageProps {
  log: ThinkingLog;
  showCategory?: boolean;
  showEmotion?: boolean;
}

/**
 * 思考ログをSlack風のメッセージとして表示するコンポーネント
 */
export const ThinkingMessage = memo(function ThinkingMessage({
  log,
  showCategory = true,
  showEmotion = true,
}: ThinkingMessageProps) {
  const category = inferCategory(log);
  const emotion = inferEmotion(log);
  const categoryConfig = CATEGORY_CONFIG[category];
  const emotionConfig = EMOTION_CONFIG[emotion];

  const formattedTime = formatTime(log.timestamp);

  return (
    <div
      className={cn(
        "flex gap-3 p-3 rounded-lg hover:bg-accent/30 transition-colors",
        categoryConfig.color === "blue" && "bg-blue-50/30",
        categoryConfig.color === "yellow" && "bg-yellow-50/30",
        categoryConfig.color === "pink" && "bg-pink-50/30",
        categoryConfig.color === "orange" && "bg-orange-50/30",
        categoryConfig.color === "purple" && "bg-purple-50/30",
        categoryConfig.color === "cyan" && "bg-cyan-50/30"
      )}
    >
      {/* 感情アイコン（アバター代わり） */}
      <div className="flex-shrink-0">
        <div
          className={cn(
            "w-10 h-10 rounded-full flex items-center justify-center text-2xl",
            "bg-background border-2 border-border shadow-sm"
          )}
          title={`${emotionConfig.label}: ${categoryConfig.label}`}
        >
          {emotionConfig.emoji}
        </div>
      </div>

      {/* メッセージコンテンツ */}
      <div className="flex-1 min-w-0">
        {/* ヘッダー */}
        <div className="flex items-baseline gap-2 mb-1 flex-wrap">
          <span className="font-medium text-sm">{log.agentName}</span>
          <span className="text-xs text-muted-foreground">{formattedTime}</span>

          {/* カテゴリーバッジ */}
          {showCategory && (
            <span
              className={cn(
                "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs",
                "bg-background border border-border"
              )}
            >
              <span>{categoryConfig.icon}</span>
              <span className="text-muted-foreground">{categoryConfig.label}</span>
            </span>
          )}

          {/* 感情バッジ */}
          {showEmotion && emotion !== "neutral" && (
            <span
              className={cn(
                "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs",
                "bg-muted"
              )}
            >
              <span>{emotionConfig.emoji}</span>
              <span>{emotionConfig.label}</span>
            </span>
          )}
        </div>

        {/* 本文 */}
        <div className="text-sm leading-relaxed break-words">
          {log.content}
        </div>

        {/* タスク詳細（あれば） */}
        {log.taskDetails && (
          <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
            <span className="font-mono bg-background px-2 py-1 rounded">
              {log.taskDetails.taskId?.slice(0, 8) ?? "N/A"}
            </span>
            <span className="px-2 py-1 rounded bg-background border border-border">
              {log.taskDetails.status}
            </span>
          </div>
        )}
      </div>
    </div>
  );
});
