/**
 * チーム状態管理ストア
 *
 * チーム情報、メンバー、メッセージ、タスク、思考ログの状態を管理します
 */

import { create } from "zustand";
import { devtools, persist } from "zustand/middleware";
import type {
  AgentInfo,
  SystemLog,
  TaskInfo,
  TeamInfo,
  TeamMessage,
  ThinkingLog,
} from "../services/types";

// ============================================================================
// ストアの状態型
// ============================================================================

interface TeamState {
  // チーム
  teams: Map<string, TeamInfo>;
  selectedTeamName: string | null;

  // エージェント
  agents: Map<string, AgentInfo>;

  // メッセージ
  messages: TeamMessage[];
  messageCount: {
    total: number;
    thinking: number;
    task: number;
    result: number;
  };

  // タスク
  tasks: TaskInfo[];

  // 思考ログ
  thinkingLogs: ThinkingLog[];

  // システムログ
  systemLogs: SystemLog[];

  // ヘルス状態
  hasErrors: boolean;
}

// ============================================================================
// アクション型
// ============================================================================

interface TeamActions {
  // チーム操作
  setTeams: (teams: TeamInfo[]) => void;
  addTeam: (team: TeamInfo) => void;
  removeTeam: (teamName: string) => void;
  updateTeam: (teamName: string, team: TeamInfo) => void;
  setSelectedTeam: (teamName: string | null) => void;

  // エージェント操作
  setAgents: (agents: AgentInfo[]) => void;
  upsertAgent: (agent: AgentInfo) => void;
  removeAgent: (agentName: string) => void;

  // メッセージ操作
  addMessage: (message: TeamMessage) => void;
  addMessages: (messages: TeamMessage[]) => void;
  clearMessages: () => void;

  // タスク操作
  setTasks: (tasks: TaskInfo[]) => void;
  updateTask: (taskId: string, updates: Partial<TaskInfo>) => void;
  addTask: (task: TaskInfo) => void;

  // 思考ログ操作
  addThinkingLog: (log: ThinkingLog) => void;
  clearThinkingLogs: () => void;

  // システムログ操作
  addSystemLog: (log: SystemLog) => void;
  clearSystemLogs: () => void;

  // ヘルス状態操作
  setHasErrors: (hasErrors: boolean) => void;

  // リセット
  reset: () => void;
}

// ============================================================================
// 初期状態
// ============================================================================

const initialState: TeamState = {
  teams: new Map(),
  selectedTeamName: null,
  agents: new Map(),
  messages: [],
  messageCount: {
    total: 0,
    thinking: 0,
    task: 0,
    result: 0,
  },
  tasks: [],
  thinkingLogs: [],
  systemLogs: [],
  hasErrors: false,
};

// ============================================================================
// ストア作成
// ============================================================================

type TeamStore = TeamState & TeamActions;

export const useTeamStore = create<TeamStore>()(
  devtools(
    persist(
      (set) => ({
        ...initialState,

        // チーム操作
        setTeams: (teams) => {
          const teamsMap = new Map(teams.map((t) => [t.name, t]));
          set({ teams: teamsMap });
        },

        addTeam: (team) => {
          set((state) => {
            const newTeams = new Map(state.teams);
            newTeams.set(team.name, team);
            return { teams: newTeams };
          });
        },

        removeTeam: (teamName) => {
          set((state) => {
            const newTeams = new Map(state.teams);
            newTeams.delete(teamName);
            return {
              teams: newTeams,
              selectedTeamName:
                state.selectedTeamName === teamName ? null : state.selectedTeamName,
            };
          });
        },

        updateTeam: (teamName, team) => {
          set((state) => {
            const newTeams = new Map(state.teams);
            newTeams.set(teamName, team);
            return { teams: newTeams };
          });
        },

        setSelectedTeam: (teamName) => {
          set({ selectedTeamName: teamName });
        },

        // エージェント操作
        setAgents: (agents) => {
          const agentsMap = new Map(agents.map((a) => [a.name, a]));
          set({ agents: agentsMap });
        },

        upsertAgent: (agent) => {
          set((state) => {
            const newAgents = new Map(state.agents);
            newAgents.set(agent.name, agent);
            return { agents: newAgents };
          });
        },

        removeAgent: (agentName) => {
          set((state) => {
            const newAgents = new Map(state.agents);
            newAgents.delete(agentName);
            return { agents: newAgents };
          });
        },

        // メッセージ操作
        addMessage: (message) => {
          set((state) => {
            const newMessages = [...state.messages, message];
            const messageCount = { ...state.messageCount };
            messageCount.total++;

            // メッセージタイプに応じてカウント
            if (message.messageType === "thinking") {
              messageCount.thinking++;
            } else if (message.messageType === "task") {
              messageCount.task++;
            } else if (message.messageType === "result") {
              messageCount.result++;
            }

            return { messages: newMessages, messageCount };
          });
        },

        addMessages: (messages) => {
          set((state) => {
            const newMessages = [...state.messages, ...messages];
            const messageCount = { ...state.messageCount };
            messageCount.total += messages.length;

            messages.forEach((m) => {
              if (m.messageType === "thinking") {
                messageCount.thinking++;
              } else if (m.messageType === "task") {
                messageCount.task++;
              } else if (m.messageType === "result") {
                messageCount.result++;
              }
            });

            return { messages: newMessages, messageCount };
          });
        },

        clearMessages: () => {
          set({
            messages: [],
            messageCount: {
              total: 0,
              thinking: 0,
              task: 0,
              result: 0,
            },
          });
        },

        // タスク操作
        setTasks: (tasks) => {
          set({ tasks });
        },

        updateTask: (taskId, updates) => {
          set((state) => ({
            tasks: state.tasks.map((t) =>
              t.taskId === taskId ? { ...t, ...updates } : t,
            ),
          }));
        },

        addTask: (task) => {
          set((state) => ({
            tasks: [...state.tasks, task],
          }));
        },

        // 思考ログ操作
        addThinkingLog: (log) => {
          set((state) => ({
            thinkingLogs: [...state.thinkingLogs, log],
          }));
        },

        clearThinkingLogs: () => {
          set({ thinkingLogs: [] });
        },

        // システムログ操作
        addSystemLog: (log) => {
          set((state) => {
            const newLogs = [...state.systemLogs, log];
            const hasErrors = newLogs.some((l) => l.level === "error");
            return { systemLogs: newLogs, hasErrors };
          });
        },

        clearSystemLogs: () => {
          set({ systemLogs: [], hasErrors: false });
        },

        // ヘルス状態操作
        setHasErrors: (hasErrors) => {
          set({ hasErrors });
        },

        // リセット
        reset: () => {
          set(initialState);
        },
      }),
      {
        name: "team-store",
        // MapオブジェクトはJSONでシリアライズできないため、特別な処理が必要
        partialize: (state) => ({
          selectedTeamName: state.selectedTeamName,
          // その他の状態は永続化しない（リアルタイムデータのため）
        }),
      },
    ),
    { name: "TeamStore" },
  ),
);

// ============================================================================
// セレクター（カスタムフック用）
// ============================================================================

/**
 * 選択中のチーム情報を取得する
 */
export const useSelectedTeam = () => {
  const selectedTeamName = useTeamStore((state) => state.selectedTeamName);
  const teams = useTeamStore((state) => state.teams);

  return selectedTeamName ? teams.get(selectedTeamName) : null;
};

/**
 * アクティブなエージェントの数を取得する
 */
export const useActiveAgentCount = () => {
  const agents = useTeamStore((state) => state.agents);
  return Array.from(agents.values()).filter(
    (a) => a.status === "running",
  ).length;
};

/**
 * タスクの統計情報を取得する
 */
export const useTaskStats = () => {
  const tasks = useTeamStore((state) => state.tasks);

  return {
    pending: tasks.filter((t) => t.status === "pending").length,
    inProgress: tasks.filter((t) => t.status === "in_progress").length,
    completed: tasks.filter((t) => t.status === "completed").length,
    total: tasks.length,
  };
};
