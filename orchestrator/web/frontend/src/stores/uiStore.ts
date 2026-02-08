/**
 * UI状態管理ストア
 *
 * タブ、パネル、モーダル、通知などのUI状態を管理します
 */

import { create } from "zustand";
import { devtools, persist } from "zustand/middleware";

// ============================================================================
// 型定義
// ============================================================================

/** タブ名 */
export type TabName = "dashboard" | "tasks" | "conference";

/** 通知タイプ */
export type NotificationType = "info" | "success" | "warning" | "error";

/** 通知 */
export interface Notification {
  id: string;
  type: NotificationType;
  message: string;
  duration?: number;
  action: {
    label: string;
    onClick: () => void;
  } | undefined;
}

/** モーダル型 */
export type ModalType =
  | "reconnect"
  | "confirm"
  | "cluster-restart"
  | "cluster-shutdown"
  | null;

// ============================================================================
// ストアの状態型
// ============================================================================

interface UIState {
  // タブ
  activeTab: TabName;

  // パネル
  isAgentPanelCollapsed: boolean;
  isThinkingLogVisible: boolean;
  isTimestampVisible: boolean;

  // スクロール
  isAutoScrollEnabled: boolean;

  // モーダル
  activeModal: ModalType;
  modalData: Record<string, unknown>;

  // 通知
  notifications: Notification[];

  // ローディング
  isLoading: boolean;
  loadingMessage: string | null;

  // フィルター
  thinkingAgentFilter: string | null;
}

// ============================================================================
// アクション型
// ============================================================================

interface UIActions {
  // タブ操作
  setActiveTab: (tab: TabName) => void;

  // パネル操作
  toggleAgentPanel: () => void;
  setAgentPanelCollapsed: (collapsed: boolean) => void;
  toggleThinkingLogVisibility: () => void;
  toggleTimestampVisibility: () => void;

  // スクロール操作
  toggleAutoScroll: () => void;
  setAutoScrollEnabled: (enabled: boolean) => void;

  // モーダル操作
  openModal: (modal: ModalType, data?: Record<string, unknown>) => void;
  closeModal: () => void;

  // 通知操作
  addNotification: (
    type: NotificationType,
    message: string,
    duration?: number,
    action?: Notification["action"],
  ) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;

  // ローディング操作
  setLoading: (loading: boolean, message?: string) => void;

  // フィルター操作
  setThinkingAgentFilter: (agentName: string | null) => void;

  // リセット
  reset: () => void;
}

// ============================================================================
// 初期状態
// ============================================================================

const initialState: UIState = {
  activeTab: "dashboard",
  isAgentPanelCollapsed: false,
  isThinkingLogVisible: true,
  isTimestampVisible: false,
  isAutoScrollEnabled: true,
  activeModal: null,
  modalData: {},
  notifications: [],
  isLoading: false,
  loadingMessage: null,
  thinkingAgentFilter: null,
};

// ============================================================================
// ストア作成
// ============================================================================

type UIStore = UIState & UIActions;

export const useUIStore = create<UIStore>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,

        // タブ操作
        setActiveTab: (tab) => {
          set({ activeTab: tab });
        },

        // パネル操作
        toggleAgentPanel: () => {
          set((state) => ({
            isAgentPanelCollapsed: !state.isAgentPanelCollapsed,
          }));
        },

        setAgentPanelCollapsed: (collapsed) => {
          set({ isAgentPanelCollapsed: collapsed });
        },

        toggleThinkingLogVisibility: () => {
          set((state) => ({
            isThinkingLogVisible: !state.isThinkingLogVisible,
          }));
        },

        toggleTimestampVisibility: () => {
          set((state) => ({
            isTimestampVisible: !state.isTimestampVisible,
          }));
        },

        // スクロール操作
        toggleAutoScroll: () => {
          set((state) => ({
            isAutoScrollEnabled: !state.isAutoScrollEnabled,
          }));
        },

        setAutoScrollEnabled: (enabled) => {
          set({ isAutoScrollEnabled: enabled });
        },

        // モーダル操作
        openModal: (modal, data = {}) => {
          set({ activeModal: modal, modalData: data });
        },

        closeModal: () => {
          set({ activeModal: null, modalData: {} });
        },

        // 通知操作
        addNotification: (type, message, duration, action) => {
          const id = `notification-${Date.now()}-${Math.random()}`;
          const notification: Notification = {
            id,
            type,
            message,
            duration: duration ?? 3000,
            action: action ?? undefined,
          };

          set((state) => ({
            notifications: [...state.notifications, notification],
          }));

          // 自動消去
          if (notification.duration && notification.duration > 0) {
            setTimeout(() => {
              get().removeNotification(id);
            }, notification.duration);
          }
        },

        removeNotification: (id) => {
          set((state) => ({
            notifications: state.notifications.filter((n) => n.id !== id),
          }));
        },

        clearNotifications: () => {
          set({ notifications: [] });
        },

        // ローディング操作
        setLoading: (loading, message) => {
          set({ isLoading: loading, loadingMessage: message ?? null });
        },

        // フィルター操作
        setThinkingAgentFilter: (agentName) => {
          set({ thinkingAgentFilter: agentName });
        },

        // リセット
        reset: () => {
          set(initialState);
        },
      }),
      {
        name: "ui-store",
        // 通知やローディング状態は永続化しない
        partialize: (state) => ({
          activeTab: state.activeTab,
          isAgentPanelCollapsed: state.isAgentPanelCollapsed,
          isThinkingLogVisible: state.isThinkingLogVisible,
          isTimestampVisible: state.isTimestampVisible,
          isAutoScrollEnabled: state.isAutoScrollEnabled,
        }),
      },
    ),
    { name: "UIStore" },
  ),
);

// ============================================================================
// ユーティリティ関数
// ============================================================================

/**
 * 通知を表示するヘルパー関数
 */
export const notify = {
  info: (message: string, duration?: number) => {
    useUIStore.getState().addNotification("info", message, duration);
  },
  success: (message: string, duration?: number) => {
    useUIStore.getState().addNotification("success", message, duration);
  },
  warning: (message: string, duration?: number) => {
    useUIStore.getState().addNotification("warning", message, duration);
  },
  error: (message: string, duration?: number) => {
    useUIStore.getState().addNotification("error", message, duration);
  },
};
