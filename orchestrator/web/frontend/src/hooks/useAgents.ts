/**
 * エージェントフック
 *
 * エージェント情報の取得と管理を提供します
 */

import { useMemo } from "react";
import { useTeamStore } from "../stores/teamStore";
import type { AgentStatus } from "../services/types";

/**
 * 全エージェント一覧を取得するフック
 */
export function useAgents() {
  const agents = useTeamStore((state) => state.agents);

  return {
    agents,
  };
}

/**
 * 特定のエージェントを取得するフック
 */
export function useAgent(agentName: string | null) {
  const agents = useTeamStore((state) => state.agents);

  return agentName ? agents.find((a) => a.name === agentName) : null;
}

/**
 * アクティブなエージェントの統計を取得するフック
 */
export function useAgentStats() {
  const agents = useTeamStore((state) => state.agents);

  return useMemo(() => {
    const total = agents.length;
    const running = agents.filter((a) => a.status === "running").length;
    const idle = agents.filter((a) => a.status === "idle").length;
    const stopped = agents.filter((a) => a.status === "stopped").length;
    const error = agents.filter((a) => a.status === "error").length;

    return { total, running, idle, stopped, error };
  }, [agents]);
}

/**
 * ステータス別のエージェント一覧を取得するフック
 */
export function useAgentsByStatus(status: AgentStatus) {
  const { agents } = useAgents();

  return useMemo(() => {
    return agents.filter((a) => a.status === status);
  }, [agents, status]);
}
