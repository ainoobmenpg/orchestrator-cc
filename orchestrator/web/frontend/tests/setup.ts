/**
 * Vitestセットアップファイル
 *
 * テスト環境のグローバル設定を行います
 */

import { afterEach, expect } from "vitest";
import { cleanup } from "@testing-library/react";
import * as matchers from "@testing-library/jest-dom/matchers";

// Vitestでjest-domのマッチャーを使用できるようにする
expect.extend(matchers);

// 各テスト後にDOMをクリーンアップ
afterEach(() => {
  cleanup();
});

// IntersectionObserverのモック
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  takeRecords() {
    return [];
  }
  unobserve() {}
} as unknown as IntersectionObserver;

// ResizeObserverのモック
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
} as unknown as ResizeObserver;

// requestAnimationFrameのモック
global.requestAnimationFrame = (callback: FrameRequestCallback) => {
  return setTimeout(callback, 16) as unknown as number;
};

global.cancelAnimationFrame = (id: number) => {
  clearTimeout(id);
};

// MediaRecorderのモック（録音機能などで使用）
global.MediaRecorder = class MediaRecorder {
  constructor() {}
  start() {}
  stop() {}
  static isTypeSupported() {
    return true;
  }
} as unknown as typeof MediaRecorder;
