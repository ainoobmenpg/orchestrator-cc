/**
 * タスクフック
 *
 * タスク情報の取得と管理を提供します
 */

import { useQuery } from "@tanstack/react-query";
import { getTeamTasks } from "../services/api";

/**
 * チームタスクリストを取得するフック
 */
export function useTasks(teamName: string | null) {
  const query = useQuery({
    queryKey: ["tasks", teamName],
    queryFn: async () => {
      if (!teamName) return [];
      return getTeamTasks(teamName);
    },
    enabled: !!teamName,
    staleTime: 1000 * 30, // 30秒間キャッシュ
  });

  return {
    ...query,
    tasks: query.data ?? [],  // クエリデータを直接返す
  };
}

/**
 * 特定のタスクを取得するフック
 * TODO: teamStore からの取得を無効化（無限ループ回避のため一時的にnullを返す）
 */
export function useTask(_taskId: string | null) {
  // TODO: teamStore を使わずに、選択されたチームのタスクから取得する
  return null;
}

/**
 * タスク統計を取得するフック
 * TODO: teamStore からの取得を無効化（無限ループ回避のため一時的に固定値）
 */
export function useTasksStats() {
  // TODO: teamStore を使わずに、選択されたチームのタスクから計算する
  return {
    pending: 0,
    inProgress: 0,
    completed: 0,
    total: 0,
  };
}

/**
 * ステータス別のタスクリストを取得するフック
 * TODO: teamStore からの取得を無効化（無限ループ回避のため一時的に空配列を返す）
 */
export function useTasksByStatus(_status: import("../services/types").TaskStatus) {
  // TODO: teamStore を使わずに、選択されたチームのタスクからフィルタリングする
  return [];
}
