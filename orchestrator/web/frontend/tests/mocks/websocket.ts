/**
 * WebSocketモック
 *
 * WebSocket APIのモック実装を提供します
 */

import { vi } from "vitest";

export class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  url: string;
  readyState: number = MockWebSocket.CONNECTING;
  onopen: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;

  private sendCallback = vi.fn();
  private closeCallback = vi.fn();
  private eventListeners: Map<string, Set<EventListener>> = new Map();

  constructor(url: string) {
    this.url = url;
    // 接続をシミュレート
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      this.onopen?.(new Event("open"));
    }, 0);
  }

  send(data: string | ArrayBufferLike | Blob | ArrayBufferView) {
    this.sendCallback(data);
  }

  close(code?: number, reason?: string) {
    this.readyState = MockWebSocket.CLOSING;
    setTimeout(() => {
      this.readyState = MockWebSocket.CLOSED;
      this.closeCallback(code, reason);
      this.onclose?.(new CloseEvent("close", { code, reason }));
    }, 0);
  }

  addEventListener(
    type: string,
    callback: EventListener | null,
    options?: AddEventListenerOptions | boolean
  ) {
    if (!callback) return;
    if (!this.eventListeners.has(type)) {
      this.eventListeners.set(type, new Set());
    }
    this.eventListeners.get(type)!.add(callback);
  }

  removeEventListener(
    type: string,
    callback: EventListener | null,
    options?: EventListenerOptions | boolean
  ) {
    if (!callback) return;
    this.eventListeners.get(type)?.delete(callback);
  }

  // テスト用ヘルパーメソッド
  mockMessage(data: unknown) {
    const event = new MessageEvent("message", { data });
    this.onmessage?.(event);
    this.eventListeners.get("message")?.forEach((callback) =>
      callback(event)
    );
  }

  mockError() {
    const event = new Event("error");
    this.onerror?.(event);
    this.eventListeners.get("error")?.forEach((callback) => callback(event));
  }
}

// グローバルWebSocketをモックに置き換え
global.WebSocket = MockWebSocket as any;
