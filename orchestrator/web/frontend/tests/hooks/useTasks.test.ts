/**
 * useTasksフックのテスト
 *
 * 注意: useTasksStatsは非推奨のため、代わりにuseTaskStatsをteamStoreから使用してください
 */

import { describe, it, expect, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useTasks, useTasksByStatus } from "@/hooks/useTasks";
import { useTeamStore, useTaskStats } from "@/stores/teamStore";

describe("useTasks", () => {
  beforeEach(() => {
    useTeamStore.getState().reset();
  });

  it("タスクリストを取得できる", () => {
    const { result } = renderHook(() => useTasks());

    expect(result.current.data).toEqual([]);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isError).toBe(false);
    expect(result.current.isSuccess).toBe(true);
  });

  it("ステータス別のタスクを取得できる", () => {
    const { result } = renderHook(() => useTasksByStatus("pending"));

    expect(result.current).toEqual([]);
  });

  it("ステータス別のタスクが正しくフィルタリングされる", () => {
    // タスクを追加
    act(() => {
      useTeamStore.getState().setTasks([
        {
          taskId: "test-1",
          subject: "pending task",
          description: "説明",
          status: "pending",
          createdAt: "2024-01-01T00:00:00Z",
        },
        {
          taskId: "test-2",
          subject: "in_progress task",
          description: "説明",
          status: "in_progress",
          createdAt: "2024-01-01T00:00:00Z",
        },
        {
          taskId: "test-3",
          subject: "another pending task",
          description: "説明",
          status: "pending",
          createdAt: "2024-01-01T00:00:00Z",
        },
      ]);
    });

    const { result } = renderHook(() => useTasksByStatus("pending"));

    expect(result.current).toHaveLength(2);
    expect(result.current[0].taskId).toBe("test-1");
    expect(result.current[1].taskId).toBe("test-3");
  });
});

describe("useTaskStats (teamStore)", () => {
  beforeEach(() => {
    useTeamStore.getState().reset();
  });

  it("タスク統計を取得できる", () => {
    const { result } = renderHook(() => useTaskStats());

    expect(result.current.pending).toBe(0);
    expect(result.current.inProgress).toBe(0);
    expect(result.current.completed).toBe(0);
    expect(result.current.total).toBe(0);
  });

  it("タスクが追加されたとき統計が更新される", () => {
    const { result } = renderHook(() => useTaskStats());

    // タスクを追加
    act(() => {
      useTeamStore.getState().setTasks([
        {
          taskId: "test-1",
          subject: "テストタスク",
          description: "説明",
          status: "pending",
          createdAt: "2024-01-01T00:00:00Z",
        },
      ]);
    });

    expect(result.current.total).toBe(1);
    expect(result.current.pending).toBe(1);
  });
});
