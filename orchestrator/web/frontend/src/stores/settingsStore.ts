/**
 * 設定ストア
 *
 * テーマ、フォントサイズ、表示設定などのユーザー設定を管理します
 */

import { create } from "zustand";
import { devtools, persist } from "zustand/middleware";

// ============================================================================
// 型定義
// ============================================================================

/** テーマ */
export type Theme = "dark" | "light" | "system";

/** フォントサイズ */
export type FontSize = "small" | "medium" | "large";

/** 密度 */
export type Density = "comfortable" | "compact" | "spacious";

// ============================================================================
// ストアの状態型
// ============================================================================

interface SettingsState {
  // 外観
  theme: Theme;
  fontSize: FontSize;
  density: Density;

  // 表示設定
  showAgentAvatars: boolean;
  showThinkingEmotions: boolean;
  animateMessages: boolean;
  soundEnabled: boolean;

  // データ設定
  messageBufferSize: number;
  maxThinkingLogs: number;
  maxSystemLogs: number;

  // WebSocket設定
  wsReconnectDelay: number;
  wsMaxReconnectAttempts: number;
}

// ============================================================================
// アクション型
// ============================================================================

interface SettingsActions {
  // 外観設定
  setTheme: (theme: Theme) => void;
  setFontSize: (size: FontSize) => void;
  setDensity: (density: Density) => void;

  // 表示設定
  toggleAgentAvatars: () => void;
  toggleThinkingEmotions: () => void;
  toggleAnimateMessages: () => void;
  toggleSoundEnabled: () => void;

  // データ設定
  setMessageBufferSize: (size: number) => void;
  setMaxThinkingLogs: (max: number) => void;
  setMaxSystemLogs: (max: number) => void;

  // WebSocket設定
  setWsReconnectDelay: (delay: number) => void;
  setWsMaxReconnectAttempts: (max: number) => void;

  // リセット
  reset: () => void;
}

// ============================================================================
// 初期状態
// ============================================================================

const initialState: SettingsState = {
  theme: "dark",
  fontSize: "medium",
  density: "comfortable",
  showAgentAvatars: true,
  showThinkingEmotions: true,
  animateMessages: true,
  soundEnabled: false,
  messageBufferSize: 1000,
  maxThinkingLogs: 500,
  maxSystemLogs: 500,
  wsReconnectDelay: 3000,
  wsMaxReconnectAttempts: 10,
};

// ============================================================================
// ストア作成
// ============================================================================

type SettingsStore = SettingsState & SettingsActions;

export const useSettingsStore = create<SettingsStore>()(
  devtools(
    persist(
      (set) => ({
        ...initialState,

        // 外観設定
        setTheme: (theme) => {
          set({ theme });
          // HTML要素のdata-theme属性を更新
          if (typeof document !== "undefined") {
            const root = document.documentElement;
            if (theme === "system") {
              const systemTheme = window.matchMedia("(prefers-color-scheme: dark)")
                .matches
                ? "dark"
                : "light";
              root.setAttribute("data-theme", systemTheme);
            } else {
              root.setAttribute("data-theme", theme);
            }
          }
        },

        setFontSize: (fontSize) => {
          set({ fontSize });
          // HTML要素のfont-sizeを更新
          if (typeof document !== "undefined") {
            const root = document.documentElement;
            const sizes = {
              small: "14px",
              medium: "16px",
              large: "18px",
            };
            root.style.fontSize = sizes[fontSize];
          }
        },

        setDensity: (density) => {
          set({ density });
          // HTML要素のdata-density属性を更新
          if (typeof document !== "undefined") {
            const root = document.documentElement;
            root.setAttribute("data-density", density);
          }
        },

        // 表示設定
        toggleAgentAvatars: () => {
          set((state) => ({ showAgentAvatars: !state.showAgentAvatars }));
        },

        toggleThinkingEmotions: () => {
          set((state) => ({ showThinkingEmotions: !state.showThinkingEmotions }));
        },

        toggleAnimateMessages: () => {
          set((state) => ({ animateMessages: !state.animateMessages }));
        },

        toggleSoundEnabled: () => {
          set((state) => ({ soundEnabled: !state.soundEnabled }));
        },

        // データ設定
        setMessageBufferSize: (size) => {
          set({ messageBufferSize: Math.max(100, Math.min(5000, size)) });
        },

        setMaxThinkingLogs: (max) => {
          set({ maxThinkingLogs: Math.max(100, Math.min(2000, max)) });
        },

        setMaxSystemLogs: (max) => {
          set({ maxSystemLogs: Math.max(100, Math.min(2000, max)) });
        },

        // WebSocket設定
        setWsReconnectDelay: (delay) => {
          set({ wsReconnectDelay: Math.max(1000, Math.min(30000, delay)) });
        },

        setWsMaxReconnectAttempts: (max) => {
          set({ wsMaxReconnectAttempts: Math.max(1, Math.min(100, max)) });
        },

        // リセット
        reset: () => {
          set(initialState);
        },
      }),
      {
        name: "settings-store",
      },
    ),
    { name: "SettingsStore" },
  ),
);

// ============================================================================
// 初期化処理
// ============================================================================

/**
 * テーマを適用する
 */
export function applyTheme(theme: Theme): void {
  if (typeof document === "undefined") return;

  const root = document.documentElement;
  let resolvedTheme: "dark" | "light" = "dark";

  if (theme === "system") {
    resolvedTheme = window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  } else {
    resolvedTheme = theme;
  }

  root.setAttribute("data-theme", resolvedTheme);
}

/**
 * フォントサイズを適用する
 */
export function applyFontSize(fontSize: FontSize): void {
  if (typeof document === "undefined") return;

  const root = document.documentElement;
  const sizes: Record<FontSize, string> = {
    small: "14px",
    medium: "16px",
    large: "18px",
  };
  root.style.fontSize = sizes[fontSize];
}

/**
 * 密度を適用する
 */
export function applyDensity(density: Density): void {
  if (typeof document === "undefined") return;

  const root = document.documentElement;
  root.setAttribute("data-density", density);
}

/**
 * システムテーマ変更を監視する
 */
export function watchSystemTheme(callback: (theme: "dark" | "light") => void): () => void {
  if (typeof window === "undefined") return () => {};

  const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
  const handler = (e: MediaQueryListEvent) => {
    callback(e.matches ? "dark" : "light");
  };

  mediaQuery.addEventListener("change", handler);

  return () => {
    mediaQuery.removeEventListener("change", handler);
  };
}

// アプリケーション起動時に設定を適用
if (typeof window !== "undefined") {
  const settings = useSettingsStore.getState();
  applyTheme(settings.theme);
  applyFontSize(settings.fontSize);
  applyDensity(settings.density);

  // システムテーマ変更を監視
  watchSystemTheme(() => {
    if (useSettingsStore.getState().theme === "system") {
      applyTheme("system");
    }
  });
}
