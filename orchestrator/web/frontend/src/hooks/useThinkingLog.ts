/**
 * 思考ログフック
 *
 * エージェントの思考ログを管理・表示するためのフックです
 * カテゴリー分類、感情表現、フィルタリング機能を提供します
 */

import { useMemo } from "react";
import { useTeamStore } from "../stores/teamStore";
import type { MessageCategory, EmotionType, ThinkingLog } from "../services/types";

// ============================================================================
// 型定義
// ============================================================================

/** 思考ログのカテゴリー拡張 */
export type ThinkingLogCategory = MessageCategory | "complaint" | "mutter" | "question";

/** 感情タイプ拡張 */
export type ThinkingEmotion = EmotionType | "excited" | "frustrated" | "curious" | "relieved";

/** フィルターオプション */
export interface ThinkingLogFilter {
  category?: ThinkingLogCategory[];
  emotion?: ThinkingEmotion[];
  agentName?: string[];
  searchQuery?: string;
}

/** 思考ログ統計 */
export interface ThinkingLogStats {
  total: number;
  byCategory: Record<ThinkingLogCategory, number>;
  byEmotion: Record<ThinkingEmotion, number>;
  byAgent: Record<string, number>;
}

// ============================================================================
// 定数
// ============================================================================

/** カテゴリー設定 */
export const CATEGORY_CONFIG: Record<
  ThinkingLogCategory,
  { label: string; icon: string; color: string; description: string }
> = {
  action: {
    label: "行動",
    icon: "⚡",
    color: "blue",
    description: "エージェントが実行したアクション",
  },
  thinking: {
    label: "思考",
    icon: "🧠",
    color: "yellow",
    description: "エージェントの思考プロセス",
  },
  emotion: {
    label: "感情",
    icon: "❤️",
    color: "pink",
    description: "エージェントの感情的な反応",
  },
  complaint: {
    label: "愚痴",
    icon: "😤",
    color: "orange",
    description: "エージェントの不満や愚痴",
  },
  mutter: {
    label: "独り言",
    icon: "💭",
    color: "purple",
    description: "エージェントの独り言",
  },
  question: {
    label: "質問",
    icon: "❓",
    color: "cyan",
    description: "エージェントからの質問",
  },
};

/** 感情設定 */
export const EMOTION_CONFIG: Record<
  ThinkingEmotion,
  { label: string; emoji: string; color: string }
> = {
  confusion: { label: "混乱", emoji: "😕", color: "yellow" },
  satisfaction: { label: "満足", emoji: "😊", color: "green" },
  focus: { label: "集中", emoji: "🎯", color: "blue" },
  concern: { label: "懸念", emoji: "😟", color: "orange" },
  neutral: { label: "中立", emoji: "😐", color: "gray" },
  excited: { label: "興奮", emoji: "🤩", color: "purple" },
  frustrated: { label: "挫折", emoji: "😫", color: "red" },
  curious: { label: "好奇", emoji: "🤔", color: "cyan" },
  relieved: { label: "安堵", emoji: "😌", color: "green" },
};

// ============================================================================
// ヘルパー関数
// ============================================================================

/**
 * 思考ログからカテゴリーを推測する
 */
export function inferCategory(log: ThinkingLog): ThinkingLogCategory {
  const content = log.content.toLowerCase();

  // 既にカテゴリーが設定されている場合はそれを使用
  if (log.category && Object.keys(CATEGORY_CONFIG).includes(log.category)) {
    return log.category as ThinkingLogCategory;
  }

  // 愚痴のキーワード
  const complaintKeywords = [
    "むずかしい",
    "むり",
    "できない",
    "わからない",
    "つらい",
    "めんどくさい",
    "面倒",
    "難しい",
    "無理",
    "出来ない",
    "分からない",
    "辛い",
    "挫折",
    "失敗",
  ];

  // 独り言のキーワード
  const mutterKeywords = [
    "ふむ",
    "なるほど",
    "そうか",
    "えーっと",
    "えっと",
    "うーん",
    "うん",
    "まあ",
    "やっぱり",
    "やっぱ",
    "たぶん",
    "おそらく",
    "恐らく",
  ];

  // 質問のキーワード
  const questionKeywords = [
    "?",
    "？",
    "どうしよう",
    "どうすれば",
    "どうやる",
    "教えて",
    "知ってる",
    "わかる",
    "分かる",
    "わからない",
    "分からない",
  ];

  if (complaintKeywords.some((kw) => content.includes(kw))) {
    return "complaint";
  }

  if (questionKeywords.some((kw) => content.includes(kw))) {
    return "question";
  }

  if (mutterKeywords.some((kw) => content.includes(kw))) {
    return "mutter";
  }

  return log.category as ThinkingLogCategory || "thinking";
}

/**
 * 思考ログから感情を推測する
 */
export function inferEmotion(log: ThinkingLog): ThinkingEmotion {
  const content = log.content.toLowerCase();
  const category = inferCategory(log);

  // 既に感情が設定されている場合はそれを使用
  if (log.emotion && Object.keys(EMOTION_CONFIG).includes(log.emotion)) {
    return log.emotion as ThinkingEmotion;
  }

  // カテゴリーから感情を推測
  if (category === "complaint") {
    return "frustrated";
  }

  if (category === "question") {
    return "curious";
  }

  // 感情のキーワード
  const emotionKeywords: Record<ThinkingEmotion, string[]> = {
    confusion: ["混乱", "わからない", "不明", "謎"],
    satisfaction: ["満足", "成功", "完了", "できた", "うまく"],
    focus: ["集中", "作業", "実行", "開始"],
    concern: ["懸念", "心配", "注意", "危険"],
    neutral: [],
    excited: ["わーい", "やったー", "すごい", "最高", "興奮"],
    frustrated: ["むかつく", "最悪", "失敗", "ダメ"],
    curious: ["気になる", "知りたい", "面白い", "興味深い"],
    relieved: ["助かった", "よかった", "安堵", "安心"],
  };

  for (const [emotion, keywords] of Object.entries(emotionKeywords)) {
    if (keywords.some((kw) => content.includes(kw))) {
      return emotion as ThinkingEmotion;
    }
  }

  return log.emotion as ThinkingEmotion || "neutral";
}

// ============================================================================
// カスタムフック
// ============================================================================

/**
 * 思考ログフック
 *
 * エージェントの思考ログを管理・表示するためのフックです
 */
export function useThinkingLog(filter?: ThinkingLogFilter) {
  const thinkingLogs = useTeamStore((state) => state.thinkingLogs);

  // フィルタリング適用後のログ
  const filteredLogs = useMemo(() => {
    let logs = [...thinkingLogs];

    // カテゴリーフィルター
    if (filter?.category && filter.category.length > 0) {
      logs = logs.filter((log) => {
        const category = inferCategory(log);
        return filter.category!.includes(category);
      });
    }

    // 感情フィルター
    if (filter?.emotion && filter.emotion.length > 0) {
      logs = logs.filter((log) => {
        const emotion = inferEmotion(log);
        return filter.emotion!.includes(emotion);
      });
    }

    // エージェントフィルター
    if (filter?.agentName && filter.agentName.length > 0) {
      logs = logs.filter((log) => filter.agentName!.includes(log.agentName));
    }

    // 検索クエリ
    if (filter?.searchQuery && filter.searchQuery.trim() !== "") {
      const query = filter.searchQuery.toLowerCase();
      logs = logs.filter((log) =>
        log.content.toLowerCase().includes(query) ||
        log.agentName.toLowerCase().includes(query)
      );
    }

    return logs;
  }, [thinkingLogs, filter]);

  // 統計情報
  const stats = useMemo<ThinkingLogStats>(() => {
    const stats: ThinkingLogStats = {
      total: thinkingLogs.length,
      byCategory: {} as Record<ThinkingLogCategory, number>,
      byEmotion: {} as Record<ThinkingEmotion, number>,
      byAgent: {},
    };

    // 初期化
    Object.keys(CATEGORY_CONFIG).forEach((key) => {
      stats.byCategory[key as ThinkingLogCategory] = 0;
    });
    Object.keys(EMOTION_CONFIG).forEach((key) => {
      stats.byEmotion[key as ThinkingEmotion] = 0;
    });

    // 集計
    thinkingLogs.forEach((log) => {
      const category = inferCategory(log);
      const emotion = inferEmotion(log);

      stats.byCategory[category] = (stats.byCategory[category] || 0) + 1;
      stats.byEmotion[emotion] = (stats.byEmotion[emotion] || 0) + 1;
      stats.byAgent[log.agentName] = (stats.byAgent[log.agentName] || 0) + 1;
    });

    return stats;
  }, [thinkingLogs]);

  // エージェント一覧
  const agents = useMemo(() => {
    const agentSet = new Set(thinkingLogs.map((log) => log.agentName));
    return Array.from(agentSet).sort();
  }, [thinkingLogs]);

  // 最新のログ
  const latestLog = useMemo(() => {
    return thinkingLogs.length > 0
      ? thinkingLogs[thinkingLogs.length - 1]
      : null;
  }, [thinkingLogs]);

  return {
    logs: thinkingLogs,
    filteredLogs,
    stats,
    agents,
    latestLog,
    // ヘルパー関数
    inferCategory,
    inferEmotion,
    getCategoryConfig: (category: ThinkingLogCategory) => CATEGORY_CONFIG[category],
    getEmotionConfig: (emotion: ThinkingEmotion) => EMOTION_CONFIG[emotion],
  };
}

/**
 * 特定エージェントの思考ログフック
 */
export function useAgentThinkingLog(agentName: string) {
  const { logs, stats, latestLog, ...rest } = useThinkingLog({
    agentName: [agentName],
  });

  const agentLogs = useMemo(() => {
    return logs.filter((log) => log.agentName === agentName);
  }, [logs, agentName]);

  return {
    ...rest,
    logs: agentLogs,
    filteredLogs: agentLogs,
    agentName,
  };
}
