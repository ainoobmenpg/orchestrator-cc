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
    agents: Array.from(agents.values()),
    agentsMap: agents,
  };
}

/**
 * 特定のエージェントを取得するフック
 */
export function useAgent(agentName: string | null) {
  const agents = useTeamStore((state) => state.agents);

  return agentName ? agents.get(agentName) : null;
}

/**
 * アクティブなエージェントの統計を取得するフック
 */
export function useAgentStats() {
  const agents = useTeamStore((state) => state.agents);

  return useMemo(() => {
    const agentList = Array.from(agents.values());

    return {
      total: agentList.length,
      running: agentList.filter((a) => a.status === "running").length,
      idle: agentList.filter((a) => a.status === "idle").length,
      stopped: agentList.filter((a) => a.status === "stopped").length,
      error: agentList.filter((a) => a.status === "error").length,
    };
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
