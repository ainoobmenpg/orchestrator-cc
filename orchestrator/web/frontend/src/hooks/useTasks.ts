/**
 * タスクフック
 *
 * タスク情報の取得と管理を提供します
 */

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { getTeamTasks } from "../services/api";
import { useTeamStore } from "../stores/teamStore";
import { useWebSocket } from "./useWebSocket";

/**
 * チームタスクリストを取得するフック
 */
export function useTasks(teamName: string | null) {
  const { isConnected } = useWebSocket();
  const setTasks = useTeamStore((state) => state.setTasks);

  const query = useQuery({
    queryKey: ["tasks", teamName],
    queryFn: async () => {
      if (!teamName) return [];
      return getTeamTasks(teamName);
    },
    enabled: !!teamName,
    staleTime: isConnected ? Infinity : 1000 * 30, // 接続中は更新しない
  });

  // クエリ結果が返ってきたらストアに設定
  if (query.data && teamName) {
    setTasks(query.data);
  }

  return {
    ...query,
    tasks: useTeamStore((state) => state.tasks),
  };
}

/**
 * 特定のタスクを取得するフック
 */
export function useTask(taskId: string | null) {
  const tasks = useTeamStore((state) => state.tasks);

  return taskId ? tasks.find((t) => t.taskId === taskId) : null;
}

/**
 * タスク統計を取得するフック
 */
export function useTasksStats() {
  const tasks = useTeamStore((state) => state.tasks);

  return useMemo(() => ({
    pending: tasks.filter((t) => t.status === "pending").length,
    inProgress: tasks.filter((t) => t.status === "in_progress").length,
    completed: tasks.filter((t) => t.status === "completed").length,
    total: tasks.length,
  }), [tasks]);
}

/**
 * ステータス別のタスクリストを取得するフック
 */
export function useTasksByStatus(status: import("../services/types").TaskStatus) {
  const tasks = useTeamStore((state) => state.tasks);

  return useMemo(() => tasks.filter((t) => t.status === status), [tasks, status]);
}
