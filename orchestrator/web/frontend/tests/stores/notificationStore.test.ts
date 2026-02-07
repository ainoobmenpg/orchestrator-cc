/**
 * uiStore（通知機能）のテスト
 */

import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import { useUIStore } from "@/stores/uiStore";

describe("uiStore - 通知機能", () => {
  beforeEach(() => {
    useUIStore.getState().reset();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("初期状態が正しい", () => {
    const state = useUIStore.getState();
    expect(state.notifications).toEqual([]);
  });

  it("通知を追加できる", () => {
    useUIStore.getState().addNotification("info", "テスト通知");
    const state = useUIStore.getState();

    expect(state.notifications).toHaveLength(1);
    expect(state.notifications[0].message).toBe("テスト通知");
    expect(state.notifications[0].type).toBe("info");
  });

  it("通知を削除できる", () => {
    useUIStore.getState().addNotification("info", "テスト通知");
    const state = useUIStore.getState();
    const id = state.notifications[0].id;

    useUIStore.getState().removeNotification(id);

    expect(useUIStore.getState().notifications).toHaveLength(0);
  });

  it("全通知をクリアできる", () => {
    useUIStore.getState().addNotification("info", "通知1");
    useUIStore.getState().addNotification("success", "通知2");

    useUIStore.getState().clearNotifications();

    expect(useUIStore.getState().notifications).toHaveLength(0);
  });

  it("通知の自動消去が機能する", () => {
    useUIStore.getState().addNotification("info", "自動消去テスト", 1000);

    expect(useUIStore.getState().notifications).toHaveLength(1);

    vi.advanceTimersByTime(1000);

    expect(useUIStore.getState().notifications).toHaveLength(0);
  });

  it("各種タイプの通知を追加できる", () => {
    useUIStore.getState().addNotification("info", "情報通知");
    useUIStore.getState().addNotification("success", "成功通知");
    useUIStore.getState().addNotification("warning", "警告通知");
    useUIStore.getState().addNotification("error", "エラー通知");

    const state = useUIStore.getState();
    expect(state.notifications).toHaveLength(4);
  });
});
