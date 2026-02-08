/**
 * TaskBoardコンポーネントのテスト
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { TaskBoard } from "@/components/dashboard/TaskBoard";
import { useTeamStore } from "@/stores/teamStore";
import type { TaskInfo } from "@/services/types";

// @dnd-kitのモック
vi.mock("@dnd-kit/core", async () => {
  const actual = await vi.importActual("@dnd-kit/core");
  return {
    ...actual,
    DndContext: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
    PointerSensor: class PointerSensor {},
    useSensor: () => ({}),
    useSensors: () => ({}),
  };
});

vi.mock("@dnd-kit/sortable", () => ({
  SortableContext: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  verticalListSortingStrategy: {},
  useSortable: () => ({
    attributes: {},
    listeners: {},
    setNodeRef: () => {},
    transform: null,
    isDragging: false,
  }),
}));

describe("TaskBoard", () => {
  beforeEach(() => {
    useTeamStore.getState().reset();
  });

  it("各カラムを正しくレンダリングする", () => {
    render(<TaskBoard />);

    expect(screen.getByText("待機中")).toBeInTheDocument();
    expect(screen.getByText("進行中")).toBeInTheDocument();
    expect(screen.getByText("完了")).toBeInTheDocument();
  });

  it("各カラムのアイコンを表示する", () => {
    render(<TaskBoard />);

    expect(screen.getByText("⏳")).toBeInTheDocument();
    expect(screen.getByText("🔄")).toBeInTheDocument();
    expect(screen.getByText("✅")).toBeInTheDocument();
  });

  it("タスク統計が正しく表示される", () => {
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
    render(<TaskBoard />);

    // 各カラムのバッジ数を確認
    const badges = screen.getAllByText("1");
    expect(badges).toHaveLength(3);
  });

  it("タスクがない場合はすべて0を表示する", () => {
    useTeamStore.getState().setTasks([]);
    render(<TaskBoard />);

    const badges = screen.getAllByText("0");
    expect(badges).toHaveLength(3);
  });

  it("複数タスクがある場合、統計が正しく集計される", () => {
    const tasks: TaskInfo[] = [
      {
        taskId: "task-1",
        subject: "pending task 1",
        description: "説明",
        status: "pending",
        createdAt: "2024-01-01T00:00:00Z",
      },
      {
        taskId: "task-2",
        subject: "pending task 2",
        description: "説明",
        status: "pending",
        createdAt: "2024-01-01T00:00:00Z",
      },
      {
        taskId: "task-3",
        subject: "in_progress task",
        description: "説明",
        status: "in_progress",
        createdAt: "2024-01-01T00:00:00Z",
      },
      {
        taskId: "task-4",
        subject: "completed task 1",
        description: "説明",
        status: "completed",
        createdAt: "2024-01-01T00:00:00Z",
      },
      {
        taskId: "task-5",
        subject: "completed task 2",
        description: "説明",
        status: "completed",
        createdAt: "2024-01-01T00:00:00Z",
      },
    ];

    useTeamStore.getState().setTasks(tasks);
    render(<TaskBoard />);

    // pending: 2, in_progress: 1, completed: 2
    const allBadges = screen.getAllByText(/\d+/);
    const badgeValues = allBadges.map((badge) => parseInt(badge.textContent || "0"));

    expect(badgeValues).toContain(2);
    expect(badgeValues).toContain(1);
  });
});
