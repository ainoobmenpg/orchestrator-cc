/**
 * メッセージフック
 *
 * チームメッセージの取得と管理を提供します
 */

import { useQuery } from "@tanstack/react-query";
import { getTeamMessages } from "../services/api";
import { useTeamStore } from "../stores/teamStore";
import { useWebSocket } from "./useWebSocket";

/**
 * チームメッセージ一覧を取得するフック
 */
export function useMessages(teamName: string | null) {
  const { isConnected } = useWebSocket();
  const addMessages = useTeamStore((state) => state.addMessages);
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
    staleTime: isConnected ? Infinity : 1000 * 30, // 接続中は更新しない
  });

  // クエリ結果が返ってきたらストアに追加
  if (query.data && teamName) {
    addMessages(query.data);
  }

  return {
    ...query,
    messages: useTeamStore((state) => state.messages),
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
