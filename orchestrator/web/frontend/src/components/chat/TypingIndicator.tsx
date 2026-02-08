/**
 * TypingIndicatorコンポーネント
 *
 * エージェントが入力中であることを示すインジケーターを表示します
 */

import { memo } from "react";
import { cn } from "../../lib/utils";

export interface TypingIndicatorProps {
  /** 入力中のエージェント名 */
  agentNames: string[];
  /** カスタムクラス名 */
  className?: string;
}

const DOTS = [0, 1, 2];

export const TypingIndicator = memo(function TypingIndicator({
  agentNames,
  className,
}: TypingIndicatorProps) {
  if (agentNames.length === 0) {
    return null;
  }

  const getText = () => {
    if (agentNames.length === 1) {
      return `${agentNames[0]}が入力中...`;
    }
    if (agentNames.length === 2) {
      return `${agentNames[0]}と${agentNames[1]}が入力中...`;
    }
    return `${agentNames.length}人が入力中...`;
  };

  return (
    <div className={cn("flex items-center gap-2 px-3 py-2", className)}>
      <div className="flex gap-1">
        {DOTS.map((i) => (
          <span
            key={i}
            className={cn(
              "w-2 h-2 rounded-full bg-muted-foreground/50",
              "animate-bounce"
            )}
            style={{
              animationDelay: `${i * 150}ms`,
              animationDuration: "1s",
            }}
          />
        ))}
      </div>
      <span className="text-xs text-muted-foreground">{getText()}</span>
    </div>
  );
});
