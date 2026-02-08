/**
 * teamStoreのテスト
 */

import { describe, it, expect, beforeEach } from "vitest";
import { useTeamStore } from "@/stores/teamStore";
import type { AgentInfo, TaskInfo, TeamInfo } from "@/services/types";

describe("teamStore", () => {
  beforeEach(() => {
    useTeamStore.getState().reset();
  });

  it("初期状態が正しい", () => {
    const state = useTeamStore.getState();
    expect(state.teams).toBeInstanceOf(Map);
    expect(state.agents).toBeInstanceOf(Map);
    expect(state.messages).toEqual([]);
    expect(state.tasks).toEqual([]);
  });

  it("チームを設定できる", () => {
    const teams: TeamInfo[] = [
      {
        name: "test-team",
        createdAt: "2024-01-01T00:00:00Z",
        members: [],
      },
    ];

    useTeamStore.getState().setTeams(teams);
    const state = useTeamStore.getState();

    expect(state.teams.get("test-team")).toEqual(teams[0]);
  });

  it("エージェントを設定できる", () => {
    const agents: AgentInfo[] = [
      {
        name: "test-agent",
        role: "specialist",
        status: "running",
        taskCount: 0,
      },
    ];

    useTeamStore.getState().setAgents(agents);
    const state = useTeamStore.getState();

    expect(state.agents.get("test-agent")).toEqual(agents[0]);
  });

  it("エージェントを追加・更新できる", () => {
    const agent: AgentInfo = {
      name: "test-agent",
      role: "specialist",
      status: "running",
      taskCount: 0,
    };

    useTeamStore.getState().upsertAgent(agent);
    const state = useTeamStore.getState();

    expect(state.agents.get("test-agent")).toEqual(agent);
  });

  it("メッセージを追加できる", () => {
    const message = {
      id: "msg-1",
      sender: "test-agent",
      content: "テストメッセージ",
      timestamp: "2024-01-01T00:00:00Z",
      messageType: "thinking" as const,
    };

    useTeamStore.getState().addMessage(message);
    const state = useTeamStore.getState();

    expect(state.messages).toHaveLength(1);
    expect(state.messages[0]).toEqual(message);
    expect(state.messageCount.total).toBe(1);
    expect(state.messageCount.thinking).toBe(1);
  });

  it("タスクを設定できる", () => {
    const tasks: TaskInfo[] = [
      {
        taskId: "task-1",
        subject: "テストタスク",
        description: "説明",
        status: "pending",
        createdAt: "2024-01-01T00:00:00Z",
      },
    ];

    useTeamStore.getState().setTasks(tasks);
    const state = useTeamStore.getState();

    expect(state.tasks).toEqual(tasks);
  });

  it("システムログを追加できる", () => {
    const log = {
      timestamp: "2024-01-01T00:00:00Z",
      level: "info" as const,
      content: "テストログ",
    };

    useTeamStore.getState().addSystemLog(log);
    const state = useTeamStore.getState();

    expect(state.systemLogs).toHaveLength(1);
    expect(state.systemLogs[0]).toEqual(log);
    expect(state.hasErrors).toBe(false);
  });

  it("エラーログ追加時にhasErrorsがtrueになる", () => {
    const log = {
      timestamp: "2024-01-01T00:00:00Z",
      level: "error" as const,
      content: "エラーログ",
    };

    useTeamStore.getState().addSystemLog(log);
    const state = useTeamStore.getState();

    expect(state.hasErrors).toBe(true);
  });

  it("リセットできる", () => {
    useTeamStore.getState().setTeams([
      {
        name: "test-team",
        createdAt: "2024-01-01T00:00:00Z",
        members: [],
      },
    ]);

    useTeamStore.getState().reset();
    const state = useTeamStore.getState();

    expect(state.teams.size).toBe(0);
  });
});
