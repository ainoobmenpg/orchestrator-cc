/**
 * メッセージフック
 *
 * チームメッセージの取得と管理を提供します
 *
 * 注意: このフックは非推奨です。直接 useTeamStore を使用してください。
 * これはReact Queryの依存を削除するためにリファクタリングされました。
 */

import { useMemo } from "react";
import { useTeamStore } from "../stores/teamStore";

/**
 * チームメッセージ一覧を取得するフック（非推奨）
 *
 * 代わりに useTeamStore を直接使用してください:
 * const messages = useTeamStore((state) => state.messages);
 * const clearMessages = useTeamStore((state) => state.clearMessages);
 *
 * @deprecated ストアを直接使用してください
 */
export function useMessages(_teamName: string | null) {
  const messages = useTeamStore((state) => state.messages);
  const clearMessages = useTeamStore((state) => state.clearMessages);

  return useMemo(
    () => ({
      data: messages,
      isLoading: false,
      isError: false,
      isSuccess: true,
      messages: messages,
      clearMessages,
      refetch: () => {}, // WebSocket経由で自動更新されるため不要
    }),
    [messages, clearMessages]
  );
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
