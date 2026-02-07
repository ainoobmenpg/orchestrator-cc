/**
 * タスクフック
 *
 * タスク情報の取得と管理を提供します
 *
 * 注意: このフックは非推奨です。直接 useTeamStore を使用してください。
 * これはReact Queryの依存を削除するためにリファクタリングされました。
 */

import { useMemo } from "react";
import { useTeamStore } from "../stores/teamStore";

/**
 * チームタスクリストを取得するフック（非推奨）
 *
 * 代わりに useTeamStore を直接使用してください:
 * const tasks = useTeamStore((state) => state.tasks);
 *
 * @deprecated ストアを直接使用してください
 */
export function useTasks(_teamName: string | null) {
  const tasks = useTeamStore((state) => state.tasks);

  return useMemo(
    () => ({
      data: tasks,
      isLoading: false,
      isError: false,
      isSuccess: true,
      tasks: tasks,
      refetch: () => {}, // WebSocket経由で自動更新されるため不要
    }),
    [tasks]
  );
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
