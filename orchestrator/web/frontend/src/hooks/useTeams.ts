/**
 * チームフック
 *
 * チーム情報の取得と管理を提供します
 */

import { useQuery, useMutation } from "@tanstack/react-query";
import { getTeams, getTeamStatus, updateAgentActivity } from "../services/api";

/**
 * チーム一覧を取得するフック
 */
export function useTeams() {
  const query = useQuery({
    queryKey: ["teams"],
    queryFn: async () => {
      const teams = await getTeams();
      return teams;
    },
    staleTime: 1000 * 60, // 1分間キャッシュ
    refetchInterval: false,
  });

  return {
    data: query.data ?? [],  // クエリデータを直接返す
    isLoading: query.isLoading,
    isError: query.isError,
    isSuccess: query.isSuccess,
    refetch: query.refetch,
  };
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
