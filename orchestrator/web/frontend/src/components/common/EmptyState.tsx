/**
 * EmptyStateコンポーネント
 *
 * データがない場合の空状態を表示します
 * Framer Motionを使用したアニメーションとガイダンス機能を提供します
 */

import type { LucideIcon } from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "../../lib/utils";
import { fadeInFromBottom } from "../../lib/animations";

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
  /** イラストの種類 */
  variant?: "default" | "inbox" | "search" | "error" | "loading";
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
  variant = "default",
}: EmptyStateProps) {
  return (
    <motion.div
      variants={fadeInFromBottom}
      initial="initial"
      animate="animate"
      className={cn(
        "flex flex-col items-center justify-center p-8 text-center",
        className,
      )}
    >
      {Icon && (
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{
            type: "spring",
            stiffness: 200,
            damping: 15,
            delay: 0.1,
          }}
          className={cn(
            "mb-4 flex h-16 w-16 items-center justify-center rounded-full",
            variant === "error"
              ? "bg-red-100 dark:bg-red-900/20"
              : "bg-gray-100 dark:bg-gray-800",
          )}
        >
          <Icon
            className={cn(
              "h-8 w-8",
              variant === "error"
                ? "text-red-600 dark:text-red-400"
                : "text-gray-500 dark:text-gray-400",
              variant === "loading" && "animate-spin",
            )}
          />
        </motion.div>
      )}

      <motion.h3
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="text-lg font-semibold text-gray-900 dark:text-white"
      >
        {title}
      </motion.h3>

      {description && (
        <motion.p
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mt-2 text-sm text-gray-600 dark:text-gray-400 max-w-sm"
        >
          {description}
        </motion.p>
      )}

      {action && (
        <motion.button
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          onClick={action.onClick}
          className="mt-6 rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-blue-700 transition-colors shadow-sm hover:shadow-md"
        >
          {action.label}
        </motion.button>
      )}
    </motion.div>
  );
}
