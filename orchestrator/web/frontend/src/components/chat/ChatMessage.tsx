/**
 * ChatMessageコンポーネント
 *
 * Slack風のチャットメッセージを表示します
 * エージェントごとのアイコン、色分け、タイムスタンプを表示します
 */

import { memo } from "react";
import { cn } from "../../lib/utils";
import { formatTime } from "../../lib/utils";

// ============================================================================
// 型定義
// ============================================================================

export interface ChatMessageProps {
  id: string;
  agentName: string;
  content: string;
  timestamp: string;
  avatarUrl?: string;
  isOwn?: boolean;
  showAvatar?: boolean;
  reactions?: Reaction[];
  onReactionAdd?: (emoji: string) => void;
}

export interface Reaction {
  emoji: string;
  count: number;
  users: string[];
}

// ============================================================================
// エージェントごとの色設定
// ============================================================================

const AGENT_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  default: { bg: "bg-gray-100", border: "border-gray-200", text: "text-gray-700" },
  "team-lead": { bg: "bg-blue-50", border: "border-blue-200", text: "text-blue-700" },
  researcher: { bg: "bg-purple-50", border: "border-purple-200", text: "text-purple-700" },
  "coding-specialist": { bg: "bg-green-50", border: "border-green-200", text: "text-green-700" },
  "testing-specialist": { bg: "bg-orange-50", border: "border-orange-200", text: "text-orange-700" },
  "review-specialist": { bg: "bg-pink-50", border: "border-pink-200", text: "text-pink-700" },
};

// エージェント名から色設定を取得
function getAgentColor(agentName: string): { bg: string; border: string; text: string } {
  // エージェント名からロールを推測
  const lowerName = agentName.toLowerCase();

  const defaultColor = AGENT_COLORS.default;
  const teamLeadColor = AGENT_COLORS["team-lead"];
  const researcherColor = AGENT_COLORS.researcher;
  const codingSpecialistColor = AGENT_COLORS["coding-specialist"];
  const testingSpecialistColor = AGENT_COLORS["testing-specialist"];
  const reviewSpecialistColor = AGENT_COLORS["review-specialist"];

  if (lowerName.includes("lead") || lowerName.includes("leader")) {
    return (teamLeadColor as { bg: string; border: string; text: string }) ?? defaultColor;
  }
  if (lowerName.includes("research") || lowerName.includes("researcher")) {
    return (researcherColor as { bg: string; border: string; text: string }) ?? defaultColor;
  }
  if (lowerName.includes("coding") || lowerName.includes("coder") || lowerName.includes("developer")) {
    return (codingSpecialistColor as { bg: string; border: string; text: string }) ?? defaultColor;
  }
  if (lowerName.includes("testing") || lowerName.includes("tester") || lowerName.includes("test")) {
    return (testingSpecialistColor as { bg: string; border: string; text: string }) ?? defaultColor;
  }
  if (lowerName.includes("review") || lowerName.includes("reviewer")) {
    return (reviewSpecialistColor as { bg: string; border: string; text: string }) ?? defaultColor;
  }

  // デフォルト色（エージェント名のハッシュから決定）
  const hash = agentName.split("").reduce((acc, char) => acc + char.charCodeAt(0), 0);
  const allColors = Object.values(AGENT_COLORS);
  const colors = allColors.filter((c): c is { bg: string; border: string; text: string } => c !== AGENT_COLORS.default);
  return (colors[hash % colors.length] as { bg: string; border: string; text: string }) ?? defaultColor;
}

// エージェント名からイニシャルを取得
function getInitials(agentName: string): string {
  const parts = agentName.split(/[\s-]+/);
  if (parts.length >= 2 && parts[0] && parts[1]) {
    const firstChar = parts[0][0] ?? "";
    const secondChar = parts[1][0] ?? "";
    return (firstChar + secondChar).toUpperCase();
  }
  const firstTwo = agentName.slice(0, 2);
  return firstTwo.length === 2 ? firstTwo.toUpperCase() : agentName.slice(0, 1).toUpperCase();
}

// ============================================================================
// コンポーネント
// ============================================================================

const ReactionBadge = memo(function ReactionBadge({
  reaction,
  onAdd,
}: {
  reaction: Reaction;
  onAdd?: () => void;
}) {
  return (
    <button
      onClick={onAdd}
      className={cn(
        "flex items-center gap-1 px-2 py-0.5 rounded-full text-xs",
        "bg-accent hover:bg-accent/80 transition-colors",
        "border border-border"
      )}
    >
      <span>{reaction.emoji}</span>
      <span className="text-muted-foreground">{reaction.count}</span>
    </button>
  );
});

export const ChatMessage = memo(function ChatMessage({
  id,
  agentName,
  content,
  timestamp,
  avatarUrl,
  isOwn = false,
  showAvatar = true,
  reactions = [],
  onReactionAdd,
}: ChatMessageProps) {
  const agentColor = getAgentColor(agentName);
  const initials = getInitials(agentName);

  const formattedTime = formatTime(timestamp);

  return (
    <div
      className={cn(
        "flex gap-3 p-3 rounded-lg hover:bg-accent/30 transition-colors",
        isOwn && "flex-row-reverse"
      )}
    >
      {/* アバター */}
      {showAvatar && (
        <div
          className={cn(
            "flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center",
            "border-2",
            agentColor.border,
            agentColor.bg,
            agentColor.text,
            "font-semibold text-sm"
          )}
        >
          {avatarUrl ? (
            <img
              src={avatarUrl}
              alt={agentName}
              className="w-full h-full rounded-full object-cover"
            />
          ) : (
            <span>{initials}</span>
          )}
        </div>
      )}

      {/* メッセージコンテンツ */}
      <div className={cn("flex-1 min-w-0", isOwn && "flex flex-col items-end")}>
        {/* ヘッダー */}
        <div className={cn("flex items-baseline gap-2 mb-1", isOwn && "flex-row-reverse")}>
          <span className={cn("font-medium text-sm", agentColor.text)}>
            {agentName}
          </span>
          <span className="text-xs text-muted-foreground">{formattedTime}</span>
        </div>

        {/* 本文 */}
        <div
          className={cn(
            "text-sm leading-relaxed break-words",
            "bg-background border border-border rounded-lg px-3 py-2",
            "shadow-sm"
          )}
        >
          {content}
        </div>

        {/* リアクション */}
        {reactions.length > 0 && (
          <div className={cn("flex gap-1 mt-2", isOwn && "justify-end")}>
            {reactions.map((reaction, idx) => (
              <ReactionBadge
                key={`${id}-reaction-${idx}`}
                reaction={reaction}
                {...(onReactionAdd !== undefined && {
                  onAdd: () => onReactionAdd(reaction.emoji)
                })}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
});
