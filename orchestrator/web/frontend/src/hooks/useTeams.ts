/**
 * チームフック
 *
 * チーム情報の取得と管理を提供します
 */

import { useMemo } from "react";
import { useTeamStore } from "../stores/teamStore";

/**
 * チーム一覧を取得するフック
 */
export function useTeams() {
  const teams = useTeamStore((state) => state.teams);

  return useMemo(
    () => ({
      data: teams,
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
 */
export function useTeam(teamName: string | null) {
  const teams = useTeamStore((state) => state.teams);

  return teamName ? teams.find((t) => t.name === teamName) || null : null;
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
