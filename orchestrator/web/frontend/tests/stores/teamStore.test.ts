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
    expect(state.teams).toEqual([]);
    expect(state.agents).toEqual([]);
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

    expect(state.teams[0]).toEqual(teams[0]);
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

    expect(state.agents[0]).toEqual(agents[0]);
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

    expect(state.agents[0]).toEqual(agent);
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

    expect(state.teams).toEqual([]);
  });

  // taskStats関連のテスト
  describe("taskStats", () => {
    it("初期状態のtaskStatsはすべて0", () => {
      const state = useTeamStore.getState();
      expect(state.taskStats.pending).toBe(0);
      expect(state.taskStats.inProgress).toBe(0);
      expect(state.taskStats.completed).toBe(0);
      expect(state.taskStats.total).toBe(0);
    });

    it("setTasksでtaskStatsが正しく計算される", () => {
      const tasks: TaskInfo[] = [
        {
          taskId: "task-1",
          subject: "pending task",
          description: "説明",
          status: "pending",
          createdAt: "2024-01-01T00:00:00Z",
        },
        {
          taskId: "task-2",
          subject: "in_progress task",
          description: "説明",
          status: "in_progress",
          createdAt: "2024-01-01T00:00:00Z",
        },
        {
          taskId: "task-3",
          subject: "completed task",
          description: "説明",
          status: "completed",
          createdAt: "2024-01-01T00:00:00Z",
        },
        {
          taskId: "task-4",
          subject: "another pending task",
          description: "説明",
          status: "pending",
          createdAt: "2024-01-01T00:00:00Z",
        },
      ];

      useTeamStore.getState().setTasks(tasks);
      const state = useTeamStore.getState();

      expect(state.taskStats.pending).toBe(2);
      expect(state.taskStats.inProgress).toBe(1);
      expect(state.taskStats.completed).toBe(1);
      expect(state.taskStats.total).toBe(4);
    });

    it("updateTaskでtaskStatsが正しく更新される", () => {
      // まずタスクをセット
      const tasks: TaskInfo[] = [
        {
          taskId: "task-1",
          subject: "pending task",
          description: "説明",
          status: "pending",
          createdAt: "2024-01-01T00:00:00Z",
        },
        {
          taskId: "task-2",
          subject: "in_progress task",
          description: "説明",
          status: "in_progress",
          createdAt: "2024-01-01T00:00:00Z",
        },
      ];

      useTeamStore.getState().setTasks(tasks);
      let state = useTeamStore.getState();
      expect(state.taskStats.pending).toBe(1);
      expect(state.taskStats.inProgress).toBe(1);
      expect(state.taskStats.completed).toBe(0);

      // タスクをcompletedに更新
      useTeamStore.getState().updateTask("task-2", { status: "completed" });
      state = useTeamStore.getState();
      expect(state.taskStats.pending).toBe(1);
      expect(state.taskStats.inProgress).toBe(0);
      expect(state.taskStats.completed).toBe(1);
      expect(state.taskStats.total).toBe(2);
    });

    it("addTaskでtaskStatsが正しく更新される", () => {
      // 初期状態
      const tasks: TaskInfo[] = [
        {
          taskId: "task-1",
          subject: "existing task",
          description: "説明",
          status: "completed",
          createdAt: "2024-01-01T00:00:00Z",
        },
      ];

      useTeamStore.getState().setTasks(tasks);
      let state = useTeamStore.getState();
      expect(state.taskStats.total).toBe(1);
      expect(state.taskStats.completed).toBe(1);

      // 新しいタスクを追加
      const newTask: TaskInfo = {
        taskId: "task-2",
        subject: "new task",
        description: "説明",
        status: "pending",
        createdAt: "2024-01-01T00:00:00Z",
      };

      useTeamStore.getState().addTask(newTask);
      state = useTeamStore.getState();
      expect(state.taskStats.total).toBe(2);
      expect(state.taskStats.pending).toBe(1);
      expect(state.taskStats.completed).toBe(1);
    });

    it("空のタスク配列をセットするとtaskStatsはすべて0になる", () => {
      useTeamStore.getState().setTasks([]);
      const state = useTeamStore.getState();

      expect(state.taskStats.pending).toBe(0);
      expect(state.taskStats.inProgress).toBe(0);
      expect(state.taskStats.completed).toBe(0);
      expect(state.taskStats.total).toBe(0);
    });
  });
});
