/**
 * WebSocketクライアント
 *
 * orchestrator-ccバックエンドとのWebSocket通信を担当します
 */

import type { WebSocketMessage } from "./types";

// ============================================================================
// 設定
// ============================================================================

const WS_URL = () => {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = import.meta.env.DEV ? "127.0.0.1:8000" : window.location.host;
  return `${protocol}//${host}/ws`;
};

const RECONNECT_DELAY = 3000;
const MAX_RECONNECT_ATTEMPTS = 10;
const HEARTBEAT_INTERVAL = 15000;
const HEARTBEAT_TIMEOUT = 30000;

// ============================================================================
// 型定義
// ============================================================================

/** WebSocket接続状態 */
export type ConnectionState =
  | "disconnected"
  | "connecting"
  | "connected"
  | "error";

/** メッセージハンドラー型 */
type MessageHandler = (message: WebSocketMessage) => void;

/** イベントハンドラー型 */
type EventHandler = () => void;

// ============================================================================
// WebSocketClientクラス
// ============================================================================

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private lastPongTime = 0;
  private messageHandlers = new Map<string, Set<MessageHandler>>();
  private connectionStateHandlers = new Set<EventHandler>();
  private currentState: ConnectionState = "disconnected";

  constructor() {
    // ウィンドウフォーカス時に接続状態をチェック
    window.addEventListener("focus", () => {
      if (this.currentState === "disconnected") {
        this.connect();
      }
    });
  }

  // ========================================================================
  // 接続管理
  // ========================================================================

  /**
   * WebSocket接続を確立する
   */
  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    this.setState("connecting");

    try {
      this.ws = new WebSocket(WS_URL());
      this.setupEventListeners();
    } catch (error) {
      console.error("WebSocket接続エラー:", error);
      this.setState("error");
      this.scheduleReconnect();
    }
  }

  /**
   * WebSocket接続を切断する
   */
  disconnect(): void {
    this.stopHeartbeat();
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.onclose = null;
      this.ws.onerror = null;
      this.ws.onopen = null;
      this.ws.onmessage = null;
      this.ws.close();
      this.ws = null;
    }
    this.setState("disconnected");
  }

  /**
   * WebSocketイベントリスナーを設定する
   */
  private setupEventListeners(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      console.log("WebSocket接続完了");
      this.reconnectAttempts = 0;
      this.setState("connected");
      this.startHeartbeat();

      // 初期データをリクエスト
      this.send({
        type: "subscribe",
        channels: ["messages", "thinking", "status"],
      } as WebSocketMessage);
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WebSocketMessage;
        this.handleMessage(message);
      } catch (error) {
        console.error("メッセージ解析エラー:", error, event.data);
      }
    };

    this.ws.onerror = (error) => {
      console.error("WebSocketエラー:", error);
    };

    this.ws.onclose = () => {
      console.log("WebSocket切断");
      this.stopHeartbeat();
      this.setState("disconnected");
      this.scheduleReconnect();
    };
  }

  /**
   * 再接続をスケジュールする
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      console.error("再接続を諦めました");
      this.setState("error");
      return;
    }

    this.reconnectAttempts++;
    console.log(
      `再接続試行 ${this.reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS}`,
    );

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, RECONNECT_DELAY);
  }

  // ========================================================================
  // メッセージ送信
  // ========================================================================

  /**
   * メッセージを送信する
   */
  send(data: Record<string, unknown> | WebSocketMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn("WebSocket未接続: メッセージ送信スキップ", data);
    }
  }

  // ========================================================================
  // メッセージハンドリング
  // ========================================================================

  /**
   * 受信メッセージを処理する
   */
  private handleMessage(message: WebSocketMessage): void {
    const handlers = this.messageHandlers.get(message.type);
    if (handlers) {
      handlers.forEach((handler) => {
        try {
          handler(message);
        } catch (error) {
          console.error(`メッセージハンドラーエラー (${message.type}):`, error);
        }
      });
    }

    // Pongメッセージの特殊処理
    if (message.type === "pong") {
      this.lastPongTime = Date.now();
    }
  }

  /**
   * メッセージハンドラーを登録する
   */
  on(type: string, handler: MessageHandler): () => void {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, new Set());
    }
    this.messageHandlers.get(type)!.add(handler);

    // クリーンアップ関数を返す
    return () => {
      this.off(type, handler);
    };
  }

  /**
   * メッセージハンドラーを解除する
   */
  off(type: string, handler: MessageHandler): void {
    const handlers = this.messageHandlers.get(type);
    if (handlers) {
      handlers.delete(handler);
      if (handlers.size === 0) {
        this.messageHandlers.delete(type);
      }
    }
  }

  /**
   * 全てのメッセージハンドラーを解除する
   */
  removeAllListeners(type?: string): void {
    if (type) {
      this.messageHandlers.delete(type);
    } else {
      this.messageHandlers.clear();
    }
  }

  // ========================================================================
  // 接続状態管理
  // ========================================================================

  /**
   * 接続状態を変更する
   */
  private setState(state: ConnectionState): void {
    if (this.currentState !== state) {
      this.currentState = state;
      this.connectionStateHandlers.forEach((handler) => {
        try {
          handler();
        } catch (error) {
          console.error("接続状態ハンドラーエラー:", error);
        }
      });
    }
  }

  /**
   * 現在の接続状態を取得する
   */
  getState(): ConnectionState {
    return this.currentState;
  }

  /**
   * 接続状態ハンドラーを登録する
   */
  onStateChange(handler: EventHandler): () => void {
    this.connectionStateHandlers.add(handler);

    // クリーンアップ関数を返す
    return () => {
      this.connectionStateHandlers.delete(handler);
    };
  }

  // ========================================================================
  // ハートビート
  // ========================================================================

  /**
   * ハートビートを開始する
   */
  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.lastPongTime = Date.now();

    this.heartbeatTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        // Ping送信
        this.send({
          type: "ping",
          timestamp: Date.now(),
        } as WebSocketMessage);

        // タイムアウトチェック
        const timeSinceLastPong = Date.now() - this.lastPongTime;
        if (timeSinceLastPong > HEARTBEAT_TIMEOUT) {
          console.warn("heartbeat timeout - 接続が切れた可能性があります");
          this.ws.close();
        }
      }
    }, HEARTBEAT_INTERVAL);

    console.log(`heartbeat開始 (${HEARTBEAT_INTERVAL}ms間隔)`);
  }

  /**
   * ハートビートを停止する
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
      console.log("heartbeat停止");
    }
  }
}

// ============================================================================
// シングルトンインスタンス
// ============================================================================

let wsClient: WebSocketClient | null = null;

/**
 * WebSocketクライアントのシングルトンインスタンスを取得する
 */
export function getWebSocketClient(): WebSocketClient {
  if (!wsClient) {
    wsClient = new WebSocketClient();
  }
  return wsClient;
}
