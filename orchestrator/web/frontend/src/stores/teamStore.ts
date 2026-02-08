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
  ChannelInfo,
  ChannelMessage,
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

  // 会話チャンネル
  channels: ChannelInfo[];
  currentChannel: string | null;
  channelMessages: Record<string, ChannelMessage[]>;
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

  // 会話チャンネル操作
  setChannels: (channels: ChannelInfo[]) => void;
  setCurrentChannel: (channelName: string | null) => void;
  addChannel: (channel: ChannelInfo) => void;
  removeChannel: (channelName: string) => void;
  addChannelMessage: (message: ChannelMessage) => void;
  getChannelMessages: (channelName: string) => ChannelMessage[];

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
  channels: [],
  currentChannel: null,
  channelMessages: {},
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
          set((state) => {
            // チームが切り替わった場合
            if (state.selectedTeamName !== teamName) {
              // APIから既存メッセージを取得（非同期）
              if (teamName) {
                fetch(`/api/teams/${encodeURIComponent(teamName)}/messages`)
                  .then((response) => response.json())
                  .then((data) => {
                    if (data.messages) {
                      // 取得したメッセージで上書き（追加ではなく）
                      // APIレスポンスが返ってくる前にWebSocket経由でメッセージが届いても、
                      // ここで上書きされることで正しい順序を保証する
                      useTeamStore.setState({
                        messages: data.messages,
                        messageCount: {
                          total: data.messages.length,
                          thinking: data.messages.filter((m: TeamMessage) => m.messageType === "thinking").length,
                          task: data.messages.filter((m: TeamMessage) => m.messageType === "task").length,
                          result: data.messages.filter((m: TeamMessage) => m.messageType === "result").length,
                        },
                      });
                    }
                  })
                  .catch((error) => {
                    console.error(`Failed to fetch messages for team ${teamName}:`, error);
                    useTeamStore.getState().addSystemLog({
                      timestamp: new Date().toISOString(),
                      level: "error",
                      content: `メッセージの取得に失敗しました: ${teamName}`,
                    });
                  });
              }

              return {
                selectedTeamName: teamName,
                messages: [],
                messageCount: {
                  total: 0,
                  thinking: 0,
                  task: 0,
                  result: 0,
                },
                thinkingLogs: [],
              };
            }
            return { selectedTeamName: teamName };
          });
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
            // 重複チェック - 既存のメッセージと同じIDの場合は何もしない
            const existingMessage = state.messages.find(
              (msg) => msg.id === message.id,
            );
            if (existingMessage) {
              return state;
            }

            const newMessages = [...state.messages, message];
            const messageCount = { ...state.messageCount };
            messageCount.total++;

            // メッセージタイプに応じてカウント
            const messageType = message.messageType;
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
            // 重複チェック - 既存のメッセージIDを除外して追加
            const existingIds = new Set(state.messages.map((msg) => msg.id));
            const newMessagesOnly = messages.filter((msg) => !existingIds.has(msg.id));

            // 新しいメッセージがない場合は何もしない
            if (newMessagesOnly.length === 0) {
              return state;
            }

            const newMessages = [...state.messages, ...newMessagesOnly];
            const messageCount = { ...state.messageCount };
            messageCount.total += newMessagesOnly.length;

            newMessagesOnly.forEach((m) => {
              const messageType = m.messageType;
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

        // 会話チャンネル操作
        setChannels: (channels) => {
          set({ channels });
        },

        setCurrentChannel: (channelName) => {
          set((state) => {
            // チームが切り替わった場合と同様に処理
            if (state.currentChannel !== channelName) {
              return {
                currentChannel: channelName,
              };
            }
            return { currentChannel: channelName };
          });
        },

        addChannel: (channel) => {
          set((state) => {
            const existingIndex = state.channels.findIndex((c) => c.name === channel.name);
            if (existingIndex >= 0) {
              const newChannels = [...state.channels];
              newChannels[existingIndex] = channel;
              return { channels: newChannels };
            }
            return { channels: [...state.channels, channel] };
          });
        },

        removeChannel: (channelName) => {
          set((state) => {
            const newChannelMessages = { ...state.channelMessages };
            delete newChannelMessages[channelName];
            return {
              channels: state.channels.filter((c) => c.name !== channelName),
              channelMessages: newChannelMessages,
              currentChannel:
                state.currentChannel === channelName ? null : state.currentChannel,
            };
          });
        },

        addChannelMessage: (message) => {
          set((state) => {
            const channelName = message.channel;
            const channelMessages = { ...state.channelMessages };

            if (!channelMessages[channelName]) {
              channelMessages[channelName] = [];
            }

            // 重複チェック
            const existingMessage = channelMessages[channelName].find(
              (msg) => msg.id === message.id,
            );
            if (existingMessage) {
              return state;
            }

            channelMessages[channelName] = [...channelMessages[channelName], message];

            // チャンネルのメッセージカウントを更新
            const channels = state.channels.map((ch) =>
              ch.name === channelName
                ? { ...ch, messageCount: channelMessages[channelName].length }
                : ch,
            );

            return {
              channelMessages,
              channels,
            };
          });
        },

        getChannelMessages: (channelName) => {
          return useTeamStore.getState().channelMessages[channelName] || [];
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
