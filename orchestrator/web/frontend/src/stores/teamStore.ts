/**
 * チーム状態管理ストア
 *
 * チーム情報、メンバー、メッセージ、タスク、思考ログの状態を管理します
 *
 * 重要: Mapではなく配列を使用して、persistミドルウェアとの互換性を確保します
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
  // チーム（配列として格納）
  teams: TeamInfo[];
  selectedTeamName: string | null;

  // エージェント（配列として格納）
  agents: AgentInfo[];

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
  taskStats: {
    pending: number;
    inProgress: number;
    completed: number;
    total: number;
  };

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
  teams: [],
  selectedTeamName: null,
  agents: [],
  messages: [],
  messageCount: {
    total: 0,
    thinking: 0,
    task: 0,
    result: 0,
  },
  tasks: [],
  taskStats: {
    pending: 0,
    inProgress: 0,
    completed: 0,
    total: 0,
  },
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
          set({ teams });
        },

        addTeam: (team) => {
          set((state) => {
            // 既存のチームをチェック
            const existingIndex = state.teams.findIndex((t) => t.name === team.name);
            if (existingIndex >= 0) {
              // 既存の場合は更新
              const newTeams = [...state.teams];
              newTeams[existingIndex] = team;
              return { teams: newTeams };
            }
            // 新規の場合は追加
            return { teams: [...state.teams, team] };
          });
        },

        removeTeam: (teamName) => {
          set((state) => ({
            teams: state.teams.filter((t) => t.name !== teamName),
            selectedTeamName:
              state.selectedTeamName === teamName ? null : state.selectedTeamName,
          }));
        },

        updateTeam: (teamName, team) => {
          set((state) => ({
            teams: state.teams.map((t) =>
              t.name === teamName ? team : t,
            ),
          }));
        },

        setSelectedTeam: (teamName) => {
          set({ selectedTeamName: teamName });
        },

        // エージェント操作
        setAgents: (agents) => {
          set({ agents });
        },

        upsertAgent: (agent) => {
          set((state) => {
            const existingIndex = state.agents.findIndex((a) => a.name === agent.name);
            if (existingIndex >= 0) {
              const newAgents = [...state.agents];
              newAgents[existingIndex] = agent;
              return { agents: newAgents };
            }
            return { agents: [...state.agents, agent] };
          });
        },

        removeAgent: (agentName) => {
          set((state) => ({
            agents: state.agents.filter((a) => a.name !== agentName),
          }));
        },

        // メッセージ操作
        addMessage: (message) => {
          set((state) => {
            const newMessages = [...state.messages, message];
            const messageCount = { ...state.messageCount };
            messageCount.total++;

            // メッセージタイプに応じてカウント（messageTypeまたはtypeフィールドをチェック）
            const messageType = message.messageType || message.type;
            if (messageType === "thinking") {
              messageCount.thinking++;
            } else if (messageType === "task") {
              messageCount.task++;
            } else if (messageType === "result") {
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
              const messageType = m.messageType || m.type;
              if (messageType === "thinking") {
                messageCount.thinking++;
              } else if (messageType === "task") {
                messageCount.task++;
              } else if (messageType === "result") {
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
          set({
            tasks,
            taskStats: {
              pending: tasks.filter((t) => t.status === "pending").length,
              inProgress: tasks.filter((t) => t.status === "in_progress").length,
              completed: tasks.filter((t) => t.status === "completed").length,
              total: tasks.length,
            },
          });
        },

        updateTask: (taskId, updates) => {
          set((state) => {
            const newTasks = state.tasks.map((t) =>
              t.taskId === taskId ? { ...t, ...updates } : t,
            );
            return {
              tasks: newTasks,
              taskStats: {
                pending: newTasks.filter((t) => t.status === "pending").length,
                inProgress: newTasks.filter((t) => t.status === "in_progress").length,
                completed: newTasks.filter((t) => t.status === "completed").length,
                total: newTasks.length,
              },
            };
          });
        },

        addTask: (task) => {
          set((state) => {
            const newTasks = [...state.tasks, task];
            return {
              tasks: newTasks,
              taskStats: {
                pending: newTasks.filter((t) => t.status === "pending").length,
                inProgress: newTasks.filter((t) => t.status === "in_progress").length,
                completed: newTasks.filter((t) => t.status === "completed").length,
                total: newTasks.length,
              },
            };
          });
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
        // 選択中のチームとメッセージ・タスクを永続化（最大1000件）
        partialize: (state) => ({
          selectedTeamName: state.selectedTeamName,
          messages: state.messages.slice(-1000), // 最新1000件のみ保存
          tasks: state.tasks,
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

  return selectedTeamName
    ? teams.find((t) => t.name === selectedTeamName) || null
    : null;
};

/**
 * アクティブなエージェントの数を取得する
 */
export const useActiveAgentCount = () => {
  const agents = useTeamStore((state) => state.agents);
  return agents.filter((a) => a.status === "running").length;
};

/**
 * タスクの統計情報を取得する
 *
 * 計算済みの値をストアから取得するため、無限ループが発生しない
 */
export const useTaskStats = () => {
  return useTeamStore((state) => state.taskStats);
};
