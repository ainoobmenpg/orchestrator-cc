/**
 * useMessagesフックのテスト
 */

import { describe, it, expect, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useMessageStats } from "@/hooks/useMessages";
import { useTeamStore } from "@/stores/teamStore";

describe("useMessages", () => {
  beforeEach(() => {
    useTeamStore.getState().reset();
  });

  it("メッセージ統計を取得できる", () => {
    const { result } = renderHook(() => useMessageStats());

    expect(result.current.total).toBe(0);
    expect(result.current.thinking).toBe(0);
    expect(result.current.task).toBe(0);
    expect(result.current.result).toBe(0);
  });

  it("メッセージが追加されたとき統計が更新される", () => {
    const { result } = renderHook(() => useMessageStats());

    // メッセージを追加
    act(() => {
      useTeamStore.getState().addMessages([
        {
          id: "msg-1",
          sender: "test-agent",
          content: "テストメッセージ",
          timestamp: "2024-01-01T00:00:00Z",
          messageType: "thinking",
        },
      ]);
    });

    expect(result.current.total).toBe(1);
    expect(result.current.thinking).toBe(1);
  });
});
