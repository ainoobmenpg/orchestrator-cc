/**
 * TaskColumnコンポーネント
 *
 * タスボードのカラムを表示します
 */

import { useMemo } from "react";
import { useDroppable } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { useTeamStore } from "../../stores/teamStore";
import { Badge } from "../ui/Badge";
import { TaskCard } from "./TaskCard";

interface TaskColumnProps {
  title: string;
  status: "pending" | "in_progress" | "completed";
  icon: string;
  count: number;
}

export function TaskColumn({ title, status, icon, count }: TaskColumnProps) {
  const { setNodeRef } = useDroppable({
    id: status,
  });

  const tasks = useTeamStore((state) => state.tasks);

  // useMemoでキャッシュして無限ループを防止
  const filteredTasks = useMemo(
    () => tasks.filter((t) => t.status === status),
    [tasks, status]
  );

  return (
    <div className="flex flex-col min-w-[280px] flex-1">
      <div className="flex items-center justify-between px-4 py-3 bg-muted/50 rounded-t-lg border border-border">
        <div className="flex items-center gap-2">
          <span className="text-lg">{icon}</span>
          <span className="font-medium">{title}</span>
        </div>
        <Badge variant="secondary">{count}</Badge>
      </div>

      <div
        ref={setNodeRef}
        className="flex-1 bg-background rounded-b-lg border border-t-0 border-border p-3 space-y-2 overflow-y-auto min-h-[200px]"
      >
        <SortableContext
          items={filteredTasks.map((t) => t.taskId)}
          strategy={verticalListSortingStrategy}
        >
          {filteredTasks.length === 0 ? (
            <div className="py-8 text-center text-muted-foreground text-sm">
              タスクなし
            </div>
          ) : (
            filteredTasks.map((task) => <TaskCard key={task.taskId} task={task} />)
          )}
        </SortableContext>
      </div>
    </div>
  );
}
