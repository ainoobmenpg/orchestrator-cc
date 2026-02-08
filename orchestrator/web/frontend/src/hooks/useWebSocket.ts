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
import { useTeamStore } from "../stores/teamStore";
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

  // メッセージハンドラーを登録
  const unsubscribeConnected = wsClient.on("connected", () => {
    setConnectionState("connected");
    // 通知を削除（無限レンダリング対策）
    // notify.success("ダッシュボードに接続しました");
  });

  // 初期チームデータを受信
  const unsubscribeTeams = wsClient.on("teams", (msg) => {
    if (msg.type === "teams" && msg.teams) {
      // 現在のストアのチームと比較して、変更がある場合のみ更新
      const currentTeams = useTeamStore.getState().teams;
      const currentNames = new Set(currentTeams.map((t) => t.name));
      const newNames = new Set(msg.teams.map((t) => t.name));

      // チーム数または名前が異なる場合のみ更新
      if (
        msg.teams.length !== currentTeams.length ||
        ![...newNames].every((name) => currentNames.has(name))
      ) {
        // setTeamsを使用して一括更新
        useTeamStore.getState().setTeams(msg.teams);

        // 自動選択ロジック: 選択中のチームがない場合、最初のチームを自動選択
        const currentSelection = useTeamStore.getState().selectedTeamName;
        if (!currentSelection && msg.teams.length > 0) {
          useTeamStore.getState().setSelectedTeam(msg.teams[0].name);
        }
      }
    }
  });

  const unsubscribeTeamCreated = wsClient.on("team_created", (msg) => {
    if (msg.type === "team_created") {
      addTeam(msg.team);

      // 自動選択ロジック: 選択中のチームがない場合、新規作成されたチームを自動選択
      const currentSelection = useTeamStore.getState().selectedTeamName;
      if (!currentSelection) {
        useTeamStore.getState().setSelectedTeam(msg.teamName);
      }

      addSystemLog({
        timestamp: new Date().toISOString(),
        level: "success",
        content: `チームが作成されました: ${msg.teamName}`,
      });
    }
  });

  const unsubscribeTeamDeleted = wsClient.on("team_deleted", (msg) => {
    if (msg.type === "team_deleted") {
      const currentSelection = useTeamStore.getState().selectedTeamName;

      removeTeam(msg.teamName);

      // 削除されたチームが選択されていた場合、別のチームを自動選択
      if (currentSelection === msg.teamName) {
        const remainingTeams = useTeamStore.getState().teams;
        if (remainingTeams.length > 0) {
          useTeamStore.getState().setSelectedTeam(remainingTeams[0].name);
        } else {
          useTeamStore.getState().setSelectedTeam(null);
        }
      }

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
      // アイドル通知はフィルタリング（messageTypeまたはtypeフィールドをチェック）
      const messageType = msg.message.messageType || msg.message.type;
      if (messageType !== "idle_notification") {
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

  // クリーンアップ関数を保存
  unsubscribers = [
    unsubscribeConnected,
    unsubscribeTeams,
    unsubscribeTeamCreated,
    unsubscribeTeamDeleted,
    unsubscribeTeamUpdated,
    unsubscribeTeamMessage,
    unsubscribeThinkingLog,
    unsubscribeTasksUpdated,
    unsubscribeSystemLog,
    unsubscribeHealthEvent,
    unsubscribeAgents,
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

  // 接続は useWebSocket フックから遅延して開始する
  // これにより、ハンドラーが確実に登録されてから接続が確立される

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

      // ハンドラーが登録されてから接続を開始するために遅延させる
      setTimeout(() => {
        if (wsClient && wsClient.getState() === "disconnected") {
          wsClient.connect();
        }
      }, 100);
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
