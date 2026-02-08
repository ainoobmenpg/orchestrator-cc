/**
 * TeamMemberList コンポーネント
 *
 * チームメンバーのリストを表示し、性格パラメータを確認できます
 */

import { useState } from "react";
import { ChevronDown, ChevronRight, User } from "lucide-react";
import type { TeamMember } from "../../services/types";
import { PersonalityBadge } from "./PersonalityBadge";
import { cn } from "../../lib/utils";

// ============================================================================
// 型定義
// ============================================================================

interface TeamMemberListProps {
  members: TeamMember[];
  className?: string;
}

interface TeamMemberItemProps {
  member: TeamMember;
  isExpanded: boolean;
  onToggle: () => void;
}

// ============================================================================
// サブコンポーネント
// ============================================================================

/**
 * チームメンバー項目
 */
function TeamMemberItem({ member, isExpanded, onToggle }: TeamMemberItemProps) {
  return (
    <div className="border border-border rounded-lg overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-3 p-3 hover:bg-muted/50 transition-colors"
        aria-expanded={isExpanded}
        aria-label={`${member.name}の詳細を${isExpanded ? "折りたたむ" : "展開"}`}
      >
        <User className="h-4 w-4 text-muted-foreground flex-shrink-0" />
        <span className="font-medium">{member.name}</span>
        <span className="text-xs text-muted-foreground">({member.agentType})</span>
        {member.personality && (
          <PersonalityBadge personality={member.personality} size="sm" />
        )}
        <div className="ml-auto">
          {isExpanded ? (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronRight className="h-4 w-4 text-muted-foreground" />
          )}
        </div>
      </button>

      {isExpanded && (
        <div className="p-3 pt-0 border-t border-border bg-muted/30 space-y-3">
          {/* 基本情報 */}
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">エージェントID:</span>
              <span className="font-mono text-xs">{member.agentId}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">モデル:</span>
              <span className="font-mono text-xs">{member.model}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">参加日時:</span>
              <span className="text-xs">
                {new Date(member.joinedAt).toLocaleString("ja-JP")}
              </span>
            </div>
            {member.cwd && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">作業ディレクトリ:</span>
                <span className="font-mono text-xs truncate max-w-[200px]">
                  {member.cwd}
                </span>
              </div>
            )}
          </div>

          {/* 性格パラメータ */}
          {member.personality && (
            <PersonalityBadge
              personality={member.personality}
              size="sm"
              showLabel={true}
            />
          )}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// メインコンポーネント
// ============================================================================

/**
 * チームメンバーリストコンポーネント
 */
export function TeamMemberList({ members, className }: TeamMemberListProps) {
  const [expandedMembers, setExpandedMembers] = useState<Set<string>>(new Set());

  const toggleMember = (memberId: string) => {
    setExpandedMembers((prev) => {
      const next = new Set(prev);
      if (next.has(memberId)) {
        next.delete(memberId);
      } else {
        next.add(memberId);
      }
      return next;
    });
  };

  if (members.length === 0) {
    return (
      <div className={cn("text-center py-8 text-muted-foreground", className)}>
        <User className="h-12 w-12 mx-auto mb-3 opacity-50" />
        <p>メンバーがいません</p>
      </div>
    );
  }

  return (
    <div className={cn("space-y-2", className)}>
      {members.map((member) => (
        <TeamMemberItem
          key={member.agentId}
          member={member}
          isExpanded={expandedMembers.has(member.agentId)}
          onToggle={() => toggleMember(member.agentId)}
        />
      ))}
    </div>
  );
}
