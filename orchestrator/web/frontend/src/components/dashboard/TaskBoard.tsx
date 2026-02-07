/**
 * TaskBoardコンポーネント
 *
 * タスクボードを表示します（ドラッグ&ドロップ対応）
 */

import { DndContext, PointerSensor, useSensor, useSensors, type DragEndEvent } from "@dnd-kit/core";
import { useTeamStore } from "../../stores/teamStore";
import { useTasksStats } from "../../hooks/useTasks";
import { TaskColumn } from "./TaskColumn";

export function TaskBoard() {
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    })
  );

  const updateTask = useTeamStore((state) => state.updateTask);

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      const taskId = active.id as string;
      const newStatus = over.id as "pending" | "in_progress" | "completed";

      updateTask(taskId, { status: newStatus as import("../../services/types").TaskStatus });
    }
  };

  const stats = useTasksStats();

  return (
    <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
      <div className="flex-1 flex gap-4 p-4 overflow-x-auto">
        <TaskColumn
          title="待機中"
          status="pending"
          icon="⏳"
          count={stats.pending}
        />
        <TaskColumn
          title="進行中"
          status="in_progress"
          icon="🔄"
          count={stats.inProgress}
        />
        <TaskColumn
          title="完了"
          status="completed"
          icon="✅"
          count={stats.completed}
        />
      </div>
    </DndContext>
  );
}
