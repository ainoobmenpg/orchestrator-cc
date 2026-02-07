/**
 * useTasksフックのテスト
 */

import { describe, it, expect, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useTasksStats, useTasksByStatus } from "@/hooks/useTasks";
import { useTeamStore } from "@/stores/teamStore";

describe("useTasks", () => {
  beforeEach(() => {
    useTeamStore.getState().reset();
  });

  it("タスク統計を取得できる", () => {
    const { result } = renderHook(() => useTasksStats());

    expect(result.current.pending).toBe(0);
    expect(result.current.inProgress).toBe(0);
    expect(result.current.completed).toBe(0);
    expect(result.current.total).toBe(0);
  });

  it("ステータス別のタスクを取得できる", () => {
    const { result } = renderHook(() => useTasksByStatus("pending"));

    expect(result.current).toEqual([]);
  });

  it("タスクが追加されたとき統計が更新される", () => {
    const { result } = renderHook(() => useTasksStats());

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
