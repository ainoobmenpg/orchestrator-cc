/**
 * 通知フック
 *
 * 通知ストアへの簡易アクセスとヘルパー関数を提供します
 */

import { useUIStore } from "../stores/uiStore";
import type { Notification } from "../stores/uiStore";

/**
 * 通知フック
 *
 * 通知ストアへのアクセスと操作を提供します
 */
export function useNotifications() {
  const notifications = useUIStore((state) => state.notifications);
  const addNotification = useUIStore((state) => state.addNotification);
  const removeNotification = useUIStore((state) => state.removeNotification);
  const clearNotifications = useUIStore((state) => state.clearNotifications);

  /**
   * 成功通知を表示
   */
  const showSuccess = (
    message: string,
    duration?: number,
    action?: Notification["action"],
  ) => {
    addNotification("success", message, duration, action);
  };

  /**
   * エラー通知を表示
   */
  const showError = (
    message: string,
    duration?: number,
    action?: Notification["action"],
  ) => {
    addNotification("error", message, duration, action);
  };

  /**
   * 警告通知を表示
   */
  const showWarning = (
    message: string,
    duration?: number,
    action?: Notification["action"],
  ) => {
    addNotification("warning", message, duration, action);
  };

  /**
   * インフォ通知を表示
   */
  const showInfo = (
    message: string,
    duration?: number,
    action?: Notification["action"],
  ) => {
    addNotification("info", message, duration, action);
  };

  return {
    /** 通知リスト */
    notifications,
    /** 通知を追加 */
    addNotification,
    /** 通知を削除 */
    removeNotification,
    /** 全通知をクリア */
    clearNotifications,
    /** 成功通知を表示 */
    showSuccess,
    /** エラー通知を表示 */
    showError,
    /** 警告通知を表示 */
    showWarning,
    /** インフォ通知を表示 */
    showInfo,
  };
}
