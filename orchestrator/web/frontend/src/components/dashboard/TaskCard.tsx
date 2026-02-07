/**
 * TaskCardコンポーネント
 *
 * ドラッグ可能なタスクカードです
 * Framer Motionを使用してドラッグ中のスケール効果とドロップ時のスムーズなトランジションを実装しています
 */

import { memo } from "react";
import { motion } from "framer-motion";
import { useSortable } from "@dnd-kit/sortable";
import { GripVertical } from "lucide-react";
import type { TaskInfo } from "../../services/types";
import { cn } from "../../lib/utils";
import { Badge } from "../ui/Badge";
import { formatDateTime } from "../../lib/utils";

interface TaskCardProps {
  task: TaskInfo;
}

export const TaskCard = memo(function TaskCard({ task }: TaskCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    isDragging,
  } = useSortable({ id: task.taskId });

  const motionStyle = transform
    ? {
        x: transform.x,
        y: transform.y,
      }
    : null;

  const statusConfig = {
    pending: { label: "待機中", variant: "secondary" as const },
    in_progress: { label: "進行中", variant: "primary" as const },
    completed: { label: "完了", variant: "success" as const },
  };

  const config = statusConfig[task.status];

  // ARIAラベル用のタスク情報
  const ariaLabel = `タスク: ${task.subject}. ステータス: ${config.label}. ${
    task.owner ? `担当者: ${task.owner}.` : ""
  }${
    task.blockedBy && task.blockedBy.length > 0
      ? ` 依存タスク: ${task.blockedBy.length}件.`
      : ""
  }`;

  return (
    <motion.div
      ref={setNodeRef}
      {...(motionStyle ? { style: motionStyle } : {})}
      role="article"
      tabIndex={0}
      aria-label={ariaLabel}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      whileDrag={{
        scale: 1.05,
        rotate: 2,
        boxShadow: "0 10px 30px rgba(0, 0, 0, 0.2)",
      }}
      transition={{
        type: "spring" as const,
        stiffness: 400,
        damping: 25,
      }}
      className={cn(
        "bg-card border border-border rounded-lg p-3 cursor-pointer hover:border-primary/50 transition-colors",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        isDragging && "opacity-50",
      )}
    >
      <div className="flex items-start gap-3">
        <button
          {...attributes}
          {...listeners}
          aria-label="タスクをドラッグ"
          className="flex-shrink-0 mt-1 text-muted-foreground hover:text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 rounded"
        >
          <GripVertical className="h-4 w-4" />
        </button>

        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-2">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-mono text-muted-foreground">
                {task.taskId.slice(0, 8)}
              </span>
              <Badge variant={config.variant}>{config.label}</Badge>
            </div>
          </div>

          <h4 className="font-medium text-sm mb-1 truncate">
            {task.subject}
          </h4>

          <p className="text-xs text-muted-foreground line-clamp-2 mb-2">
            {task.description}
          </p>

          <div className="flex items-center justify-between text-xs">
            {task.owner && (
              <span className="text-primary font-medium">{task.owner}</span>
            )}
            {task.createdAt && (
              <span className="text-muted-foreground">
                {formatDateTime(task.createdAt)}
              </span>
            )}
          </div>

          {task.blockedBy && task.blockedBy.length > 0 && (
            <div className="mt-2 pt-2 border-t border-border">
              <div className="text-xs text-muted-foreground mb-1">依存タスク:</div>
              <div className="flex flex-wrap gap-1">
                {task.blockedBy.map((depId) => (
                  <span
                    key={depId}
                    className="text-xs px-1.5 py-0.5 rounded bg-warning/20 text-warning-foreground"
                  >
                    {depId.slice(0, 6)}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
});
