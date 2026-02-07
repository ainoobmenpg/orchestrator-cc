/**
 * チームフック
 *
 * チーム情報の取得と管理を提供します
 *
 * 注意: このフックは非推奨です。直接 useTeamStore を使用してください。
 * これはReact Queryの依存を削除するためにリファクタリングされました。
 */

import { useMemo } from "react";
import { useTeamStore } from "../stores/teamStore";

/**
 * チーム一覧を取得するフック（非推奨）
 *
 * 代わりに useTeamStore を直接使用してください:
 * const teams = useTeamStore((state) => state.teams);
 * const teamsList = useMemo(() => Array.from(teams.values()), [teams]);
 *
 * @deprecated ストアを直接使用してください
 */
export function useTeams() {
  const teams = useTeamStore((state) => state.teams);

  return useMemo(
    () => ({
      data: Array.from(teams.values()),
      isLoading: false,
      isError: false,
      isSuccess: true,
      refetch: () => {}, // WebSocket経由で自動更新されるため不要
    }),
    [teams]
  );
}

/**
 * 特定のチーム情報を取得するフック
 *
 * @deprecated ストアを直接使用してください
 */
export function useTeam(teamName: string | null) {
  const teams = useTeamStore((state) => state.teams);

  return teamName ? teams.get(teamName) || null : null;
}

/**
 * エージェントアクティビティ更新
 *
 * @deprecated WebSocket経由で自動更新されるため不要
 */
export function useUpdateAgentActivity() {
  // WebSocket経由で自動更新されるため、この関数は何もしない
  return {
    mutate: async () => {
      // 何もしない - データはWebSocket経由で更新される
    },
    mutateAsync: async () => {
      // 何もしない
    },
  };
}
