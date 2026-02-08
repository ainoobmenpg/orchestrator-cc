/**
 * useAgentsフックのテスト
 */

import { describe, it, expect, beforeEach } from "vitest";
import { renderHook } from "@testing-library/react";
import { useAgents, useAgentStats, useAgentsByStatus } from "@/hooks/useAgents";
import { useTeamStore } from "@/stores/teamStore";

describe("useAgents", () => {
  beforeEach(() => {
    // テスト前にストアをリセット
    useTeamStore.getState().reset();
  });

  it("エージェント一覧を取得できる", () => {
    const { result } = renderHook(() => useAgents());

    expect(result.current.agents).toEqual([]);
  });

  it("エージェント統計を取得できる", () => {
    const { result } = renderHook(() => useAgentStats());

    expect(result.current.total).toBe(0);
    expect(result.current.running).toBe(0);
    expect(result.current.idle).toBe(0);
    expect(result.current.stopped).toBe(0);
    expect(result.current.error).toBe(0);
  });

  it("ステータス別のエージェントを取得できる", () => {
    const { result } = renderHook(() => useAgentsByStatus("running"));

    expect(result.current).toEqual([]);
  });
});
