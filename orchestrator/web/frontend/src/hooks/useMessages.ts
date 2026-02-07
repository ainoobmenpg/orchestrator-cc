/**
 * メッセージフック
 *
 * チームメッセージの取得と管理を提供します
 */

import { useQuery } from "@tanstack/react-query";
import { getTeamMessages } from "../services/api";

/**
 * チームメッセージ一覧を取得するフック
 */
export function useMessages(teamName: string | null) {
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
    clearMessages: () => {},  // TODO: 無限ループ回避のため空関数
  };
}

/**
 * メッセージ統計を取得するフック
 * TODO: teamStore からの取得を無効化（無限ループ回避のため一時的に固定値）
 */
export function useMessageStats() {
  // TODO: teamStore を使わずに、選択されたチームのメッセージから計算する
  return {
    total: 0,
    thinking: 0,
    task: 0,
    result: 0,
  };
}
