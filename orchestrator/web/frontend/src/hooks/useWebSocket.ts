/**
 * WebSocketフック
 *
 * WebSocket接続の管理とメッセージハンドリングを提供します
 *
 * 重要: このフックは複数のコンポーネントから呼び出されても、
 * イベントハンドラーの登録は1回のみ行われます。
 * 接続状態はグローバル変数として管理し、再レンダリングを回避します。
 */

import { useEffect, useCallback } from "react";
import { getWebSocketClient } from "../services/websocket";
import { getTeamMessages, getTeamTasks } from "../services/api";
import { useTeamStore } from "../stores/teamStore";
import { notify } from "../stores/uiStore";
import { errorHandler } from "../services/errorHandler";

// ============================================================================
// モジュールレベルの変数（シングルトン）
// ============================================================================

/** WebSocket接続状態 */
export type ConnectionState =
  | "connected"
  | "connecting"
  | "disconnected"
  | "error";

/**
 * モジュールレベルの接続状態（グローバル変数として管理）
 * これにより、再レンダリングを引き起こさずに状態を共有できます
 */
let wsConnectionState: ConnectionState = "disconnected";

let wsClient: ReturnType<typeof getWebSocketClient> | null = null;
let isInitialized = false;
let unsubscribers: (() => void)[] = [];

// ============================================================================
// 内部関数
// ============================================================================

/**
 * 接続状態を変更する
 */
function setConnectionState(state: ConnectionState): void {
  wsConnectionState = state;
  // グローバル変数にも設定（Header コンポーネントから監視するため）
  if (typeof window !== "undefined") {
    window.__wsConnectionState = state;
  }
}

/**
 * WebSocketクライアントを初期化し、イベントハンドラーを登録します
 * この関数は1回のみ実行されます
 */
function initializeWebSocket() {
  if (isInitialized) {
    return;
  }

  wsClient = getWebSocketClient();

  // ストアのアクションを取得
  const addTeam = useTeamStore.getState().addTeam;
  const removeTeam = useTeamStore.getState().removeTeam;
  const updateTeam = useTeamStore.getState().updateTeam;
  const upsertAgent = useTeamStore.getState().upsertAgent;
  const addMessage = useTeamStore.getState().addMessage;
  const addThinkingLog = useTeamStore.getState().addThinkingLog;
  const addSystemLog = useTeamStore.getState().addSystemLog;
  const setTasks = useTeamStore.getState().setTasks;
  const setHasErrors = useTeamStore.getState().setHasErrors;
  const addChannel = useTeamStore.getState().addChannel;
  const addChannelMessage = useTeamStore.getState().addChannelMessage;

  // メッセージハンドラーを登録
  const unsubscribeConnected = wsClient.on("connected", async () => {
    setConnectionState("connected");

    // 再接続時に選択中のチームデータを再取得（Issue #45対応）
    const selectedTeamName = useTeamStore.getState().selectedTeamName;
    if (selectedTeamName) {
      try {
        // メッセージとタスクを再取得して上書き
        const [messages, tasks] = await Promise.all([
          getTeamMessages(selectedTeamName),
          getTeamTasks(selectedTeamName),
        ]);

        // setStateで直接上書き（重複チェック済みのため）
        useTeamStore.setState({
          messages,
          messageCount: {
            total: messages.length,
            thinking: messages.filter((m) => m.messageType === "thinking").length,
            task: messages.filter((m) => m.messageType === "task").length,
            result: messages.filter((m) => m.messageType === "result").length,
          },
          tasks,
        });
      } catch (error) {
        console.error(`再接続時のデータ取得エラー (${selectedTeamName}):`, error);
      }
    }

    notify.success("ダッシュボードに接続しました");
  });

  const unsubscribeTeamCreated = wsClient.on("team_created", (msg) => {
    if (msg.type === "team_created") {
      addTeam(msg.team);
      addSystemLog({
        timestamp: new Date().toISOString(),
        level: "success",
        content: `チームが作成されました: ${msg.teamName}`,
      });
    }
  });

  const unsubscribeTeamDeleted = wsClient.on("team_deleted", (msg) => {
    if (msg.type === "team_deleted") {
      removeTeam(msg.teamName);
      addSystemLog({
        timestamp: new Date().toISOString(),
        level: "warning",
        content: `チームが削除されました: ${msg.teamName}`,
      });
    }
  });

  const unsubscribeTeamUpdated = wsClient.on("team_updated", (msg) => {
    if (msg.type === "team_updated") {
      updateTeam(msg.teamName, msg.team);
    }
  });

  const unsubscribeTeamMessage = wsClient.on("team_message", (msg) => {
    if (msg.type === "team_message") {
      // アイドル通知はフィルタリング
      if (msg.message.messageType !== "idle_notification") {
        addMessage(msg.message);
      }
    }
  });

  const unsubscribeThinkingLog = wsClient.on("thinking_log", (msg) => {
    if (msg.type === "thinking_log") {
      addThinkingLog(msg.log);
    }
  });

  const unsubscribeTasksUpdated = wsClient.on("tasks_updated", (msg) => {
    if (msg.type === "tasks_updated") {
      setTasks(msg.tasks);
    }
  });

  const unsubscribeSystemLog = wsClient.on("system_log", (msg) => {
    if (msg.type === "system_log") {
      addSystemLog({
        timestamp: msg.timestamp,
        level: msg.level,
        content: msg.content,
      });
    }
  });

  const unsubscribeHealthEvent = wsClient.on("health_event", (msg) => {
    if (msg.type === "health_event") {
      const hasError = msg.event.status === "error";
      setHasErrors(hasError);
    }
  });

  const unsubscribeAgents = wsClient.on("agents", (msg) => {
    if (msg.type === "agents") {
      msg.agents.forEach((agent) => {
        upsertAgent(agent);
      });
    }
  });

  // 会話チャンネル関連のハンドラー
  const unsubscribeChannelMessage = wsClient.on("channel_message", (msg) => {
    if (msg.type === "channel_message") {
      addChannelMessage({
        id: `${msg.channel}-${msg.timestamp}-${msg.sender}`,
        channel: msg.channel,
        sender: msg.sender,
        content: msg.content,
        timestamp: msg.timestamp,
      });
    }
  });

  const unsubscribeChannelJoined = wsClient.on("channel_joined", (msg) => {
    if (msg.type === "channel_joined") {
      addChannel({
        name: msg.channel,
        participants: msg.participants,
        messageCount: 0,
      });
      addSystemLog({
        timestamp: new Date().toISOString(),
        level: "success",
        content: `チャンネル ${msg.channel} に参加しました`,
      });
    }
  });

  const unsubscribeChannelLeft = wsClient.on("channel_left", (msg) => {
    if (msg.type === "channel_left") {
      addSystemLog({
        timestamp: new Date().toISOString(),
        level: "info",
        content: `チャンネル ${msg.channel} から退出しました`,
      });
    }
  });

  const unsubscribeChannelsList = wsClient.on("channels_list", (msg) => {
    if (msg.type === "channels_list") {
      const setChannels = useTeamStore.getState().setChannels;
      setChannels(msg.channels);
    }
  });

  const unsubscribeParticipantJoined = wsClient.on("participant_joined", (msg) => {
    if (msg.type === "participant_joined") {
      addSystemLog({
        timestamp: new Date().toISOString(),
        level: "info",
        content: `${msg.agent_id} がチャンネル ${msg.channel} に参加しました`,
      });
    }
  });

  const unsubscribeParticipantLeft = wsClient.on("participant_left", (msg) => {
    if (msg.type === "participant_left") {
      addSystemLog({
        timestamp: new Date().toISOString(),
        level: "info",
        content: `${msg.agent_id} がチャンネル ${msg.channel} から退出しました`,
      });
    }
  });

  // クリーンアップ関数を保存
  unsubscribers = [
    unsubscribeConnected,
    unsubscribeTeamCreated,
    unsubscribeTeamDeleted,
    unsubscribeTeamUpdated,
    unsubscribeTeamMessage,
    unsubscribeThinkingLog,
    unsubscribeTasksUpdated,
    unsubscribeSystemLog,
    unsubscribeHealthEvent,
    unsubscribeAgents,
    unsubscribeChannelMessage,
    unsubscribeChannelJoined,
    unsubscribeChannelLeft,
    unsubscribeParticipantJoined,
    unsubscribeParticipantLeft,
    unsubscribeChannelsList,
  ];

  // 接続状態変化のハンドラー
  const unsubscribeStateChange = wsClient.onStateChange(() => {
    const state = wsClient?.getState();

    if (state === "connected") {
      setConnectionState("connected");
    } else if (state === "connecting") {
      setConnectionState("connecting");
    } else if (state === "error") {
      setConnectionState("error");
      errorHandler.handleWebSocketError(
        "WebSocket接続でエラーが発生しました。再接続を試みています...",
        undefined,
        { state },
      );
    } else if (state === "disconnected") {
      setConnectionState("disconnected");
      errorHandler.handleWebSocketError(
        "サーバーとの接続が切断されました",
        undefined,
        { state },
      );
    }
  });

  unsubscribers.push(unsubscribeStateChange);

  // 接続を開始
  wsClient.connect();

  isInitialized = true;
}

/**
 * WebSocket接続をクリーンアップします
 */
function cleanupWebSocket(): void {
  if (!isInitialized) {
    return;
  }

  // 全てのイベントハンドラーを解除
  unsubscribers.forEach((unsub) => {
    try {
      unsub();
    } catch {
      // エラーを無視
    }
  });

  unsubscribers = [];
  isInitialized = false;
}

// ============================================================================
// カスタムフック
// ============================================================================

/**
 * WebSocket接続を管理するフック
 *
 * 複数のコンポーネントから呼び出されても、初期化は1回のみ行われます。
 * 接続状態はレンダリングに依存しないため、無限レンダリングを防ぎます。
 */
export function useWebSocket() {
  // 初期化（最初の呼び出し時のみ）
  useEffect(() => {
    // グローバル変数を初期化
    if (typeof window !== "undefined") {
      window.__wsConnectionState = wsConnectionState;
    }

    if (!isInitialized) {
      initializeWebSocket();
    }

    // クリーンアップは行わず、接続は維持する
    return () => {
      // クリーンアップなし（接続を維持）
    };
  }, []);

  // 接続状態を取得（グローバル変数から直接取得）
  // キャッシュされた関数として返すことで、毎回同じ参照を返す
  const getConnectionState = useCallback(
    () => wsConnectionState,
    [],
  );

  // 手動で再接続
  const reconnect = useCallback(() => {
    if (wsClient) {
      wsClient.disconnect();
      wsClient.connect();
    }
  }, []);

  // 接続状態を動的に取得する関数を返す
  // これにより、必要なときに最新の状態を取得できる
  return {
    getConnectionState,
    reconnect,
    // ヘルパー関数
    isConnected: () => getConnectionState() === "connected",
    connectionState: getConnectionState,
  };
}

/**
 * WebSocket接続を強制的にクリーンアップします
 * （テストや開発用）
 */
export function cleanupWebSocketForTesting(): void {
  cleanupWebSocket();
  wsClient = null;
  wsConnectionState = "disconnected";
}

/**
 * WebSocket接続状態を取得する（フック外から使用する場合）
 */
export function getWebSocketConnectionState(): ConnectionState {
  return wsConnectionState;
}
