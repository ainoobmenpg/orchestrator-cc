/**
 * グローバル型定義
 */

import type { ConnectionState } from "./hooks/useWebSocket";

declare global {
  interface Window {
    /** WebSocket接続状態（グローバル変数） */
    __wsConnectionState?: ConnectionState;
  }
}

export {};
