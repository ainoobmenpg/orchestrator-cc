/**
 * メッセージフック
 *
 * チームメッセージの取得と管理を提供します
 */

import { useQuery } from "@tanstack/react-query";
import { getTeamMessages } from "../services/api";
import { useTeamStore } from "../stores/teamStore";

/**
 * チームメッセージ一覧を取得するフック
 */
export function useMessages(teamName: string | null) {
  const clearMessages = useTeamStore((state) => state.clearMessages);

  const query = useQuery({
    queryKey: ["messages", teamName],
    queryFn: async () => {
      if (!teamName) return [];
      const messages = await getTeamMessages(teamName);
      // アイドル通知をフィルタリング
      const filtered = messages.filter(
        (m) =>
          m.messageType !== "idle_notification",
      );
      return filtered;
    },
    enabled: !!teamName,
    staleTime: 1000 * 30, // 30秒間キャッシュ
  });

  return {
    ...query,
    messages: query.data ?? [],  // クエリデータを直接返す
    clearMessages,
  };
}

/**
 * メッセージ統計を取得するフック
 */
export function useMessageStats() {
  const messageCount = useTeamStore((state) => state.messageCount);

  return {
    total: messageCount.total,
    thinking: messageCount.thinking,
    task: messageCount.task,
    result: messageCount.result,
  };
}
