/**
 * useTaskStats フックのテスト
 */

import { describe, it, expect, beforeEach } from "vitest";
import { useTeamStore, useTaskStats } from "@/stores/teamStore";
import type { TaskInfo } from "@/services/types";
import { renderHook, act, waitFor } from "@testing-library/react";

describe("useTaskStats", () => {
  beforeEach(() => {
    useTeamStore.getState().reset();
  });

  it("初期状態のtaskStatsを正しく返す", () => {
    const { result } = renderHook(() => useTaskStats());

    expect(result.current).toEqual({
      pending: 0,
      inProgress: 0,
      completed: 0,
      total: 0,
    });
  });

  it("タスクが追加されるとtaskStatsが更新される", () => {
    const { result } = renderHook(() => useTaskStats());

    // 初期状態
    expect(result.current.total).toBe(0);

    // タスクを追加
    act(() => {
      const tasks: TaskInfo[] = [
        {
          taskId: "task-1",
          subject: "pending task",
          description: "説明",
          status: "pending",
          createdAt: "2024-01-01T00:00:00Z",
        },
        {
          taskId: "task-2",
          subject: "in_progress task",
          description: "説明",
          status: "in_progress",
          createdAt: "2024-01-01T00:00:00Z",
        },
        {
          taskId: "task-3",
          subject: "completed task",
          description: "説明",
          status: "completed",
          createdAt: "2024-01-01T00:00:00Z",
        },
      ];

      useTeamStore.getState().setTasks(tasks);
    });

    // フックの結果が更新されていることを確認
    expect(result.current.pending).toBe(1);
    expect(result.current.inProgress).toBe(1);
    expect(result.current.completed).toBe(1);
    expect(result.current.total).toBe(3);
  });

  it("タスクが更新されるとtaskStatsが再計算される", () => {
    const { result } = renderHook(() => useTaskStats());

    // タスクをセット
    act(() => {
      const tasks: TaskInfo[] = [
        {
          taskId: "task-1",
          subject: "pending task",
          description: "説明",
          status: "pending",
          createdAt: "2024-01-01T00:00:00Z",
        },
        {
          taskId: "task-2",
          subject: "in_progress task",
          description: "説明",
          status: "in_progress",
          createdAt: "2024-01-01T00:00:00Z",
        },
      ];

      useTeamStore.getState().setTasks(tasks);
    });

    expect(result.current.pending).toBe(1);
    expect(result.current.inProgress).toBe(1);
    expect(result.current.completed).toBe(0);

    // タスクをcompletedに更新
    act(() => {
      useTeamStore.getState().updateTask("task-2", { status: "completed" });
    });

    // 統計が更新されていることを確認
    expect(result.current.pending).toBe(1);
    expect(result.current.inProgress).toBe(0);
    expect(result.current.completed).toBe(1);
  });

  it("複数のステータスを持つタスクを正しくカウントする", () => {
    const { result } = renderHook(() => useTaskStats());

    act(() => {
      const tasks: TaskInfo[] = [
        {
          taskId: "task-1",
          subject: "pending 1",
          description: "説明",
          status: "pending",
          createdAt: "2024-01-01T00:00:00Z",
        },
        {
          taskId: "task-2",
          subject: "pending 2",
          description: "説明",
          status: "pending",
          createdAt: "2024-01-01T00:00:00Z",
        },
        {
          taskId: "task-3",
          subject: "pending 3",
          description: "説明",
          status: "pending",
          createdAt: "2024-01-01T00:00:00Z",
        },
        {
          taskId: "task-4",
          subject: "in_progress 1",
          description: "説明",
          status: "in_progress",
          createdAt: "2024-01-01T00:00:00Z",
        },
        {
          taskId: "task-5",
          subject: "in_progress 2",
          description: "説明",
          status: "in_progress",
          createdAt: "2024-01-01T00:00:00Z",
        },
        {
          taskId: "task-6",
          subject: "completed 1",
          description: "説明",
          status: "completed",
          createdAt: "2024-01-01T00:00:00Z",
        },
        {
          taskId: "task-7",
          subject: "completed 2",
          description: "説明",
          status: "completed",
          createdAt: "2024-01-01T00:00:00Z",
        },
      ];

      useTeamStore.getState().setTasks(tasks);
    });

    expect(result.current.pending).toBe(3);
    expect(result.current.inProgress).toBe(2);
    expect(result.current.completed).toBe(2);
    expect(result.current.total).toBe(7);
  });

  it("addTaskでタスクが追加されるとtaskStatsが更新される", () => {
    const { result } = renderHook(() => useTaskStats());

    // 初期タスク
    act(() => {
      const initialTask: TaskInfo = {
        taskId: "task-1",
        subject: "initial task",
        description: "説明",
        status: "completed",
        createdAt: "2024-01-01T00:00:00Z",
      };

      useTeamStore.getState().addTask(initialTask);
    });

    expect(result.current.total).toBe(1);
    expect(result.current.completed).toBe(1);

    // 新しいタスクを追加
    act(() => {
      const newTask: TaskInfo = {
        taskId: "task-2",
        subject: "new task",
        description: "説明",
        status: "pending",
        createdAt: "2024-01-01T00:00:00Z",
      };

      useTeamStore.getState().addTask(newTask);
    });

    expect(result.current.total).toBe(2);
    expect(result.current.pending).toBe(1);
    expect(result.current.completed).toBe(1);
  });

  it("ストアがリセットされるとtaskStatsもリセットされる", () => {
    const { result } = renderHook(() => useTaskStats());

    // タスクを追加
    act(() => {
      const tasks: TaskInfo[] = [
        {
          taskId: "task-1",
          subject: "task",
          description: "説明",
          status: "completed",
          createdAt: "2024-01-01T00:00:00Z",
        },
      ];

      useTeamStore.getState().setTasks(tasks);
    });

    expect(result.current.total).toBe(1);

    // ストアをリセット
    act(() => {
      useTeamStore.getState().reset();
    });

    expect(result.current).toEqual({
      pending: 0,
      inProgress: 0,
      completed: 0,
      total: 0,
    });
  });

  it("空の配列をセットするとすべての統計が0になる", async () => {
    const { result } = renderHook(() => useTaskStats());

    // タスクを追加
    act(() => {
      const tasks: TaskInfo[] = [
        {
          taskId: "task-1",
          subject: "task",
          description: "説明",
          status: "pending",
          createdAt: "2024-01-01T00:00:00Z",
        },
      ];

      useTeamStore.getState().setTasks(tasks);
    });

    // 更新を待機
    await waitFor(() => {
      expect(result.current.total).toBe(1);
    });

    // 空の配列をセット
    act(() => {
      useTeamStore.getState().setTasks([]);
    });

    await waitFor(() => {
      expect(result.current.pending).toBe(0);
      expect(result.current.inProgress).toBe(0);
      expect(result.current.completed).toBe(0);
      expect(result.current.total).toBe(0);
    });
  });
});
