/**
 * TaskColumnコンポーネントのテスト
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, act } from "@testing-library/react";
import { TaskColumn } from "@/components/dashboard/TaskColumn";
import { useTeamStore } from "@/stores/teamStore";
import type { TaskInfo } from "@/services/types";

// @dnd-kitのモック
vi.mock("@dnd-kit/core", () => ({
  useDroppable: () => ({
    setNodeRef: vi.fn(),
    isOver: false,
  }),
}));

vi.mock("@dnd-kit/sortable", () => ({
  SortableContext: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  verticalListSortingStrategy: {},
}));

// TaskCardのモック
vi.mock("@/components/dashboard/TaskCard", () => ({
  TaskCard: ({ task }: { task: TaskInfo }) => (
    <div data-testid={`task-${task.taskId}`}>{task.subject}</div>
  ),
}));

describe("TaskColumn", () => {
  beforeEach(() => {
    useTeamStore.getState().reset();
  });

  it("カラムのタイトルとアイコンを表示する", () => {
    render(<TaskColumn title="待機中" status="pending" icon="⏳" count={0} />);

    expect(screen.getByText("待機中")).toBeInTheDocument();
    expect(screen.getByText("⏳")).toBeInTheDocument();
  });

  it("タスク数を正しく表示する", () => {
    render(<TaskColumn title="進行中" status="in_progress" icon="🔄" count={5} />);

    expect(screen.getByText("5")).toBeInTheDocument();
  });

  it("タスクがない場合、「タスクなし」を表示する", () => {
    render(<TaskColumn title="完了" status="completed" icon="✅" count={0} />);

    expect(screen.getByText("タスクなし")).toBeInTheDocument();
  });

  it("ステータスに応じたタスクをフィルタリングして表示する", () => {
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
    ];

    useTeamStore.getState().setTasks(tasks);
    render(<TaskColumn title="待機中" status="pending" icon="⏳" count={2} />);

    // pendingタスクのみが表示される
    expect(screen.getByTestId("task-task-1")).toBeInTheDocument();
    expect(screen.getByTestId("task-task-2")).toBeInTheDocument();
    expect(screen.queryByTestId("task-task-3")).not.toBeInTheDocument();
  });

  it("in_progressステータスのタスクを正しくフィルタリングする", () => {
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
    render(<TaskColumn title="進行中" status="in_progress" icon="🔄" count={1} />);

    expect(screen.queryByTestId("task-task-1")).not.toBeInTheDocument();
    expect(screen.getByTestId("task-task-2")).toBeInTheDocument();
    expect(screen.queryByTestId("task-task-3")).not.toBeInTheDocument();
  });

  it("completedステータスのタスクを正しくフィルタリングする", () => {
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
        subject: "completed task 1",
        description: "説明",
        status: "completed",
        createdAt: "2024-01-01T00:00:00Z",
      },
      {
        taskId: "task-3",
        subject: "completed task 2",
        description: "説明",
        status: "completed",
        createdAt: "2024-01-01T00:00:00Z",
      },
    ];

    useTeamStore.getState().setTasks(tasks);
    render(<TaskColumn title="完了" status="completed" icon="✅" count={2} />);

    expect(screen.queryByTestId("task-task-1")).not.toBeInTheDocument();
    expect(screen.getByTestId("task-task-2")).toBeInTheDocument();
    expect(screen.getByTestId("task-task-3")).toBeInTheDocument();
  });

  it("タスクが追加されたときに再レンダリングする", () => {
    const initialTasks: TaskInfo[] = [
      {
        taskId: "task-1",
        subject: "existing task",
        description: "説明",
        status: "pending",
        createdAt: "2024-01-01T00:00:00Z",
      },
    ];

    useTeamStore.getState().setTasks(initialTasks);

    const { rerender } = render(
      <TaskColumn title="待機中" status="pending" icon="⏳" count={1} />
    );

    expect(screen.getByTestId("task-task-1")).toBeInTheDocument();

    // 新しいタスクを追加（actでラップ）
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

    rerender(<TaskColumn title="待機中" status="pending" icon="⏳" count={2} />);

    expect(screen.getByTestId("task-task-1")).toBeInTheDocument();
    expect(screen.getByTestId("task-task-2")).toBeInTheDocument();
  });
});
