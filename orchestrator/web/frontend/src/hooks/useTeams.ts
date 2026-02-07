/**
 * チームフック
 *
 * チーム情報の取得と管理を提供します
 */

import { useQuery, useMutation } from "@tanstack/react-query";
import { getTeams, getTeamStatus, updateAgentActivity } from "../services/api";
import { useTeamStore } from "../stores/teamStore";
import { useWebSocket } from "./useWebSocket";

/**
 * チーム一覧を取得するフック
 */
export function useTeams() {
  const setTeams = useTeamStore((state) => state.setTeams);
  const { isConnected } = useWebSocket();

  return useQuery({
    queryKey: ["teams"],
    queryFn: async () => {
      const teams = await getTeams();
      setTeams(teams);
      return teams;
    },
    staleTime: 1000 * 60, // 1分間キャッシュ
    refetchInterval: isConnected ? false : 5000, // 接続中は自動更新しない、未接続時は5秒ごと
  });
}

/**
 * 特定のチーム情報を取得するフック
 */
export function useTeam(teamName: string | null) {
  return useQuery({
    queryKey: ["team", teamName],
    queryFn: async () => {
      if (!teamName) return null;
      return getTeamStatus(teamName);
    },
    enabled: !!teamName,
    staleTime: 1000 * 30, // 30秒間キャッシュ
  });
}

/**
 * エージェントアクティビティ更新ミューテーション
 */
export function useUpdateAgentActivity() {
  return useMutation({
    mutationFn: async ({ teamName, agentName }: { teamName: string; agentName: string }) => {
      return updateAgentActivity(teamName, agentName);
    },
  });
}
