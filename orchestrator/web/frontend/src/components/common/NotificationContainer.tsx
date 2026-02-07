/**
 * NotificationContainerコンポーネント
 *
 * 通知を表示するコンテナコンポーネントです
 * Framer Motionを使用してスライドイン/アウトアニメーションを実装しています
 */

import { AnimatePresence, motion } from "framer-motion";
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  Info,
  X,
} from "lucide-react";
import { useUIStore } from "../../stores/uiStore";
import type { NotificationType } from "../../stores/uiStore";
import { cn } from "../../lib/utils";

/**
 * 通知タイプごとのスタイル定義
 */
const NOTIFICATION_STYLES: Record<
  NotificationType,
  { bg: string; border: string; icon: typeof CheckCircle }
> = {
  info: {
    bg: "bg-blue-500/90",
    border: "border-blue-600",
    icon: Info,
  },
  success: {
    bg: "bg-green-500/90",
    border: "border-green-600",
    icon: CheckCircle,
  },
  warning: {
    bg: "bg-yellow-500/90",
    border: "border-yellow-600",
    icon: AlertTriangle,
  },
  error: {
    bg: "bg-red-500/90",
    border: "border-red-600",
    icon: XCircle,
  },
};

export function NotificationContainer() {
  const notifications = useUIStore((state) => state.notifications);
  const removeNotification = useUIStore((state) => state.removeNotification);

  return (
    <div className="pointer-events-none fixed top-4 right-4 z-50 flex flex-col gap-2">
      <AnimatePresence mode="popLayout">
        {notifications.map((notification) => {
          const styles = NOTIFICATION_STYLES[notification.type];
          const IconComponent = styles.icon;

          return (
            <motion.div
              key={notification.id}
              initial={{ opacity: 0, x: 100, scale: 0.9 }}
              animate={{
                opacity: 1,
                x: 0,
                scale: 1,
                transition: {
                  type: "spring" as const,
                  stiffness: 400,
                  damping: 25,
                },
              }}
              exit={{
                opacity: 0,
                x: 100,
                scale: 0.9,
                transition: { duration: 0.2 },
              }}
              layout
              className={cn(
                "pointer-events-auto flex w-full max-w-md items-start gap-3 rounded-lg border p-4 text-white shadow-lg backdrop-blur-sm",
                styles.bg,
                styles.border,
              )}
            >
              {/* アイコン */}
              <IconComponent className="h-5 w-5 flex-shrink-0 mt-0.5" />

              {/* メッセージ */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium break-words">
                  {notification.message}
                </p>
                {notification.action && (
                  <button
                    onClick={notification.action.onClick}
                    className="mt-2 text-sm underline opacity-90 hover:opacity-100 transition-opacity"
                  >
                    {notification.action.label}
                  </button>
                )}
              </div>

              {/* 閉じるボタン */}
              <button
                onClick={() => removeNotification(notification.id)}
                className="text-white/70 hover:text-white transition-colors flex-shrink-0"
                aria-label="通知を閉じる"
              >
                <X className="h-4 w-4" />
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
