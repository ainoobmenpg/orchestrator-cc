import { useState, useEffect, useMemo, useCallback } from "react";
import { RefreshCw, MessageSquare } from "lucide-react";
import { useWebSocket } from "../../hooks/useWebSocket";
import { useTeamStore } from "../../stores/teamStore";
import { useUIStore } from "../../stores/uiStore";
import { notify } from "../../stores/uiStore";
import { cn } from "../../lib/utils";
import type { ConnectionState } from "../../hooks/useWebSocket";
import type { TeamInfo } from "../../services/types";

export function Header() {
  const { reconnect } = useWebSocket();
  const activeTab = useUIStore((state) => state.activeTab);
  const setActiveTab = useUIStore((state) => state.setActiveTab);

  // ストアから直接取得（セレクターを使用して最小限の再レンダリング）
  const teams = useTeamStore((state) => state.teams);
  const selectedTeamName = useTeamStore((state) => state.selectedTeamName);
  const setSelectedTeam = useTeamStore((state) => state.setSelectedTeam);

  const [isReconnecting, setIsReconnecting] = useState(false);
  const [connectionState, setConnectionState] = useState<ConnectionState>("disconnected");

  // 選択中のチームを取得
  const selectedTeam = useMemo(
    () => teams.find((t: TeamInfo) => t.name === selectedTeamName) || null,
    [teams, selectedTeamName]
  );

  const handleTeamChange = useCallback((teamName: string) => {
    setSelectedTeam(teamName || null);
  }, [setSelectedTeam]);

  const handleReconnect = async () => {
    setIsReconnecting(true);
    try {
      reconnect();
      notify.info("再接続を試みています...");
    } finally {
      setTimeout(() => setIsReconnecting(false), 1000);
    }
  };

  // 接続状態を監視してローカルステートを更新
  useEffect(() => {
    const updateConnectionState = () => {
      // グローバル変数から直接接続状態を取得
      const state = window.__wsConnectionState ?? "disconnected";

      // 状態が実際に変更された場合のみ更新
      setConnectionState((prevState) => {
        if (prevState !== state) {
          return state;
        }
        return prevState;
      });
    };

    // 初期値を設定
    updateConnectionState();

    // ポーリングで接続状態を監視（再レンダリングを引き起こさない）
    const interval = setInterval(updateConnectionState, 500);

    return () => clearInterval(interval);
  }, []);

  const connectionStatusClass = {
    connected: "bg-green-500",
    connecting: "bg-yellow-500",
    disconnected: "bg-red-500",
    error: "bg-red-500",
  }[connectionState];

  const connectionStatusText = {
    connected: "接続中",
    connecting: "接続中...",
    disconnected: "切断中",
    error: "エラー",
  }[connectionState];

  return (
    <header className="flex h-14 items-center justify-between border-b border-border bg-background px-4">
      {/* 左側: タイトルとクラスタ名 */}
      <div className="flex items-center gap-4">
        <h1 className="text-lg font-semibold">orchestrator-cc Dashboard</h1>
        <span className="text-sm text-muted-foreground">
          クラスタ: {selectedTeam?.name || "未選択"}
        </span>
      </div>

      {/* 中央: タブ・チーム選択 */}
      <div className="flex items-center gap-4">
        {/* タブ切り替え */}
        <div className="flex items-center bg-muted rounded-lg p-1">
          <button
            onClick={() => setActiveTab("dashboard")}
            className={cn(
              "px-3 py-1.5 text-sm font-medium rounded-md transition-colors",
              activeTab === "dashboard"
                ? "bg-background text-foreground"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            ダッシュボード
          </button>
          <button
            onClick={() => setActiveTab("conference")}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-md transition-colors",
              activeTab === "conference"
                ? "bg-background text-foreground"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            <MessageSquare className="h-4 w-4" />
            会議室
          </button>
        </div>

        {/* チーム選択 */}
        <div className="flex items-center gap-2">
          <label htmlFor="team-select" className="text-sm text-muted-foreground">
            監視対象:
          </label>
          <select
            id="team-select"
            value={selectedTeamName ?? ""}
            onChange={(e) => handleTeamChange(e.target.value)}
            className="rounded-md border border-input bg-background px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="">-- チームを選択 --</option>
            {teams.map((team: TeamInfo) => (
              <option key={team.name} value={team.name}>
                {team.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* 右側: 接続状態 */}
      <div className="flex items-center gap-4">
        {/* 接続ステータス */}
        <div className="flex items-center gap-2">
          <div className={`h-2 w-2 rounded-full ${connectionStatusClass}`} />
          <span className="text-sm text-muted-foreground">
            {connectionStatusText}
          </span>
        </div>

        {/* 再接続ボタン */}
        <button
          onClick={handleReconnect}
          disabled={isReconnecting || connectionState === "connected"}
          className="rounded-md p-2 text-muted-foreground hover:bg-accent hover:text-accent-foreground disabled:opacity-50"
          title="再接続"
        >
          <RefreshCw className={`h-4 w-4 ${isReconnecting ? "animate-spin" : ""}`} />
        </button>
      </div>
    </header>
  );
}
