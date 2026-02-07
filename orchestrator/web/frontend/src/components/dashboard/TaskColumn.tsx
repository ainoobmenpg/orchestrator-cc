/**
 * TaskColumnコンポーネント
 *
 * タスボードのカラムを表示します
 */

import { useDroppable } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { Badge } from "../ui/Badge";
import { TaskCard } from "./TaskCard";
import type { TaskInfo } from "../../services/types";

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

  // TODO: teamStore からの取得を無効化（無限ループ回避のため一時的に空配列）
  const tasks: TaskInfo[] = [];

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
          items={tasks.map((t) => t.taskId)}
          strategy={verticalListSortingStrategy}
        >
          {tasks.length === 0 ? (
            <div className="py-8 text-center text-muted-foreground text-sm">
              タスクなし
            </div>
          ) : (
            tasks.map((task) => <TaskCard key={task.taskId} task={task} />)
          )}
        </SortableContext>
      </div>
    </div>
  );
}
