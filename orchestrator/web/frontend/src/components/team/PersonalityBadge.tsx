/**
 * PersonalityBadge コンポーネント
 *
 * チームメンバーの性格パラメータを可視化して表示します
 */

import { Smile, Shield, Lightbulb, Users, Heart, type LucideIcon } from "lucide-react";
import type { Personality } from "../../services/types";
import { cn } from "../../lib/utils";

// ============================================================================
// 型定義
// ============================================================================

interface PersonalityBadgeProps {
  personality: Personality;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
}

interface PersonalityBarProps {
  value: number;
  label: string;
  icon: LucideIcon;
  color: string;
  size?: "sm" | "md" | "lg";
}

// ============================================================================
// 定数
// ============================================================================

const PERSONALITY_CONFIG = {
  socialibility: {
    label: "社交性",
    icon: Users,
    color: "bg-blue-500",
    description: "内向的 ←→ 外向的",
  },
  cautiousness: {
    label: "慎重さ",
    icon: Shield,
    color: "bg-yellow-500",
    description: "大胆 ←→ 慎重",
  },
  humor: {
    label: "ユーモア",
    icon: Smile,
    color: "bg-green-500",
    description: "真面目 ←→ ユーモラス",
  },
  curiosity: {
    label: "好奇心",
    icon: Lightbulb,
    color: "bg-purple-500",
    description: "保守的 ←→ 探究的",
  },
  friendliness: {
    label: "親しさやすさ",
    icon: Heart,
    color: "bg-pink-500",
    description: "フォーマル ←→ カジュアル",
  },
} as const;

// ============================================================================
// サブコンポーネント
// ============================================================================

/**
 * 性格パラメータバー
 */
function PersonalityBar({
  value,
  label,
  icon: Icon,
  color,
  size = "md",
}: PersonalityBarProps) {
  const sizeClasses = {
    sm: "h-1.5",
    md: "h-2",
    lg: "h-3",
  };

  const iconSizeClasses = {
    sm: "h-3 w-3",
    md: "h-4 w-4",
    lg: "h-5 w-5",
  };

  return (
    <div className="flex items-center gap-2">
      <Icon className={cn(iconSizeClasses[size], "text-muted-foreground flex-shrink-0")} />
      <div className="flex-1">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-muted-foreground">{label}</span>
          <span className="text-xs text-muted-foreground">{value}</span>
        </div>
        <div className={cn("w-full bg-muted rounded-full overflow-hidden", sizeClasses[size])}>
          <div
            className={cn(color, "h-full transition-all duration-300")}
            style={{ width: `${value}%` }}
          />
        </div>
      </div>
    </div>
  );
}

/**
 * 性格バッジ（コンパクト表示）
 */
function PersonalityBadgeCompact({
  personality,
  size = "sm",
}: PersonalityBadgeProps) {
  // 最も特徴的な性格パラメータを取得
  const getTopTrait = (): { key: string; value: number } => {
    const traits = [
      { key: "socialibility", value: personality.socialibility },
      { key: "cautiousness", value: personality.cautiousness },
      { key: "humor", value: personality.humor },
      { key: "curiosity", value: personality.curiosity },
      { key: "friendliness", value: personality.friendliness },
    ];
    // 最大値を持つ特性を取得
    return traits.reduce((max, trait) =>
      trait.value > max.value ? trait : max
    );
  };

  const topTrait = getTopTrait();
  const config = PERSONALITY_CONFIG[topTrait.key as keyof typeof PERSONALITY_CONFIG];
  const Icon = config.icon;

  const sizeClasses = {
    sm: "h-4 w-4",
    md: "h-5 w-5",
    lg: "h-6 w-6",
  };

  return (
    <div
      className="flex items-center gap-1.5"
      title={`${config.label}: ${config.description} (${topTrait.value}%)`}
    >
      <Icon className={cn(sizeClasses[size], config.color.replace("bg-", "text-"))} />
    </div>
  );
}

/**
 * 性格バッジ（詳細表示）
 */
function PersonalityBadgeDetail({
  personality,
  size = "md",
}: PersonalityBadgeProps) {
  return (
    <div className="space-y-3 p-3 bg-muted/30 rounded-lg">
      <h4 className="text-sm font-medium">性格パラメータ</h4>

      <PersonalityBar
        value={personality.socialibility}
        label="社交性"
        icon={PERSONALITY_CONFIG.socialibility.icon}
        color={PERSONALITY_CONFIG.socialibility.color}
        size={size}
      />

      <PersonalityBar
        value={personality.cautiousness}
        label="慎重さ"
        icon={PERSONALITY_CONFIG.cautiousness.icon}
        color={PERSONALITY_CONFIG.cautiousness.color}
        size={size}
      />

      <PersonalityBar
        value={personality.humor}
        label="ユーモア"
        icon={PERSONALITY_CONFIG.humor.icon}
        color={PERSONALITY_CONFIG.humor.color}
        size={size}
      />

      <PersonalityBar
        value={personality.curiosity}
        label="好奇心"
        icon={PERSONALITY_CONFIG.curiosity.icon}
        color={PERSONALITY_CONFIG.curiosity.color}
        size={size}
      />

      <PersonalityBar
        value={personality.friendliness}
        label="親しさやすさ"
        icon={PERSONALITY_CONFIG.friendliness.icon}
        color={PERSONALITY_CONFIG.friendliness.color}
        size={size}
      />
    </div>
  );
}

// ============================================================================
// メインコンポーネント
// ============================================================================

/**
 * 性格バッジコンポーネント
 *
 * showLabel で表示モードを切り替えます：
 * - true: 詳細表示
 * - false: コンパクト表示
 */
export function PersonalityBadge({
  personality,
  size = "md",
  showLabel = false,
}: PersonalityBadgeProps) {
  if (!personality) {
    return null;
  }

  if (showLabel) {
    return <PersonalityBadgeDetail personality={personality} size={size} />;
  }

  return <PersonalityBadgeCompact personality={personality} size={size} />;
}
