/**
 * WebSocketフック
 *
 * WebSocket接続の管理とメッセージハンドリングを提供します
 */

import { useEffect, useCallback, useRef } from "react";
import { getWebSocketClient, type ConnectionState } from "../services/websocket";
import { useTeamStore } from "../stores/teamStore";
import { notify } from "../stores/uiStore";
import { errorHandler } from "../services/errorHandler";

// ============================================================================
// カスタムフック
// ============================================================================

/**
 * WebSocket接続を管理するフック
 */
export function useWebSocket() {
  const clientRef = useRef<ReturnType<typeof getWebSocketClient> | null>(null);

  // ストアのアクションを参照
  const addTeam = useTeamStore((state) => state.addTeam);
  const removeTeam = useTeamStore((state) => state.removeTeam);
  const updateTeam = useTeamStore((state) => state.updateTeam);
  const upsertAgent = useTeamStore((state) => state.upsertAgent);
  const addMessage = useTeamStore((state) => state.addMessage);
  const addThinkingLog = useTeamStore((state) => state.addThinkingLog);
  const addSystemLog = useTeamStore((state) => state.addSystemLog);
  const setTasks = useTeamStore((state) => state.setTasks);
  const setHasErrors = useTeamStore((state) => state.setHasErrors);

  // 初期化
  useEffect(() => {
    if (!clientRef.current) {
      clientRef.current = getWebSocketClient();
    }

    const client = clientRef.current;

    // メッセージハンドラーを登録
    const unsubscribeConnected = client.on("connected", () => {
      notify.success("ダッシュボードに接続しました");
    });

    const unsubscribeTeamCreated = client.on("team_created", (msg) => {
      if (msg.type === "team_created") {
        addTeam(msg.team);
        addSystemLog({
          timestamp: new Date().toISOString(),
          level: "success",
          content: `チームが作成されました: ${msg.teamName}`,
        });
      }
    });

    const unsubscribeTeamDeleted = client.on("team_deleted", (msg) => {
      if (msg.type === "team_deleted") {
        removeTeam(msg.teamName);
        addSystemLog({
          timestamp: new Date().toISOString(),
          level: "warning",
          content: `チームが削除されました: ${msg.teamName}`,
        });
      }
    });

    const unsubscribeTeamUpdated = client.on("team_updated", (msg) => {
      if (msg.type === "team_updated") {
        updateTeam(msg.teamName, msg.team);
      }
    });

    const unsubscribeTeamMessage = client.on("team_message", (msg) => {
      if (msg.type === "team_message") {
        // アイドル通知はフィルタリング
        if (msg.message.messageType !== "idle_notification") {
          addMessage(msg.message);
        }
      }
    });

    const unsubscribeThinkingLog = client.on("thinking_log", (msg) => {
      if (msg.type === "thinking_log") {
        addThinkingLog(msg.log);
      }
    });

    const unsubscribeTasksUpdated = client.on("tasks_updated", (msg) => {
      if (msg.type === "tasks_updated") {
        setTasks(msg.tasks);
      }
    });

    const unsubscribeSystemLog = client.on("system_log", (msg) => {
      if (msg.type === "system_log") {
        addSystemLog({
          timestamp: msg.timestamp,
          level: msg.level,
          content: msg.content,
        });
      }
    });

    const unsubscribeHealthEvent = client.on("health_event", (msg) => {
      if (msg.type === "health_event") {
        const hasError = msg.event.status === "error";
        setHasErrors(hasError);
      }
    });

    const unsubscribeAgents = client.on("agents", (msg) => {
      if (msg.type === "agents") {
        msg.agents.forEach((agent) => {
          upsertAgent(agent);
        });
      }
    });

    // クリーンアップ
    return () => {
      unsubscribeConnected();
      unsubscribeTeamCreated();
      unsubscribeTeamDeleted();
      unsubscribeTeamUpdated();
      unsubscribeTeamMessage();
      unsubscribeThinkingLog();
      unsubscribeTasksUpdated();
      unsubscribeSystemLog();
      unsubscribeHealthEvent();
      unsubscribeAgents();
    };
  }, [addTeam, removeTeam, updateTeam, upsertAgent, addMessage, addThinkingLog, addSystemLog, setTasks, setHasErrors]);

  // 接続状態の監視とエラーハンドリング
  useEffect(() => {
    const client = clientRef.current;
    if (!client) return;

    // 接続状態変化のハンドラー
    const unsubscribeStateChange = client.onStateChange(() => {
      const state = client.getState();

      // エラー状態の場合に通知
      if (state === "error") {
        errorHandler.handleWebSocketError(
          "WebSocket接続でエラーが発生しました。再接続を試みています...",
          undefined,
          { state },
        );
      }
      // 接続が切れた場合に通知
      else if (state === "disconnected") {
        errorHandler.handleWebSocketError(
          "サーバーとの接続が切断されました",
          undefined,
          { state },
        );
      }
    });

    return () => {
      unsubscribeStateChange();
    };
  }, []);

  // 接続
  useEffect(() => {
    const client = clientRef.current;
    if (client) {
      client.connect();
    }

    return () => {
      // アンマウント時には切断しない（他のコンポーネントで使用される可能性があるため）
    };
  }, []);

  // 接続状態を取得
  const getConnectionState = useCallback((): ConnectionState => {
    return clientRef.current?.getState() ?? "disconnected";
  }, []);

  // 手動で再接続
  const reconnect = useCallback(() => {
    const client = clientRef.current;
    if (client) {
      client.disconnect();
      client.connect();
    }
  }, []);

  return {
    isConnected: getConnectionState() === "connected",
    connectionState: getConnectionState(),
    reconnect,
  };
}
