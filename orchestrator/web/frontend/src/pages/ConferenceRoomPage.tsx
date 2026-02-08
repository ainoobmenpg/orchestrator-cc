/**
 * ConferenceRoomPageコンポーネント
 *
 * Slack風のチャットUIを提供する「会議室」ページです
 * エージェントの思考ログ、チームメッセージをリアルタイムで表示します
 */

import { useState, useCallback, useEffect } from "react";
import { Users, MessageSquare, Brain, Settings, X, Bell, BellOff } from "lucide-react";
import { ChatMessageList } from "../components/chat/ChatMessageList";
import { ChatInput } from "../components/chat/ChatInput";
import { useTeamStore } from "../stores/teamStore";
import { useThinkingLog } from "../hooks/useThinkingLog";
import { getWebSocketClient } from "../services/websocket";
import { cn } from "../lib/utils";

// ============================================================================
// 型定義
// ============================================================================

type ViewMode = "all" | "thinking" | "messages";

interface FilterOptions {
  category?: string[];
  emotion?: string[];
  agent?: string[];
}

// ============================================================================
// 定数
// ============================================================================

const VIEW_MODE_CONFIG = {
  all: { label: "すべて", icon: MessageSquare },
  thinking: { label: "思考ログ", icon: Brain },
  messages: { label: "メッセージ", icon: Users },
};

// ============================================================================
// コンポーネント
// ============================================================================

export function ConferenceRoomPage() {
  const { logs: thinkingLogs, agents } = useThinkingLog();
  const messages = useTeamStore((state) => state.messages);
  const selectedTeam = useTeamStore((state) =>
    state.teams.find((t) => t.name === state.selectedTeamName)
  );

  // UI状態
  const [viewMode, setViewMode] = useState<ViewMode>("all");
  const [showFilters, setShowFilters] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [typingAgents, setTypingAgents] = useState<string[]>([]);

  // フィルター状態
  const [filterOptions, setFilterOptions] = useState<FilterOptions>({});

  // WebSocketクライアントを取得
  const wsClient = getWebSocketClient();

  // メッセージ送信ハンドラー
  const handleSendMessage = useCallback((content: string) => {
    if (wsClient) {
      wsClient.send({
        type: "message",
        content,
        timestamp: new Date().toISOString(),
      });
    }
  }, [wsClient]);

  // リアクション追加ハンドラー
  const handleReactionAdd = useCallback((messageId: string, emoji: string) => {
    // 将来の実装: WebSocketでリアクションを送信
    console.log(`Reaction ${emoji} added to message ${messageId}`);
  }, []);

  // 表示メッセージをフィルタリング
  const displayThinkingLogs = thinkingLogs;
  const displayMessages = messages;

  // 通知設定切り替え
  const handleToggleMute = useCallback(() => {
    setIsMuted((prev) => !prev);
  }, []);

  // フィルターダイアログを開閉
  const handleToggleFilters = useCallback(() => {
    setShowFilters((prev) => !prev);
  }, []);

  return (
    <div className="flex flex-col h-full bg-background">
      {/* ヘッダー */}
      <header className="flex items-center justify-between px-4 py-3 border-b border-border bg-background">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-semibold">会議室</h1>
          {selectedTeam && (
            <span className="text-sm text-muted-foreground">
              {selectedTeam.name}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* ビューモード切り替え */}
          <div className="flex items-center bg-muted rounded-lg p-1">
            {(Object.keys(VIEW_MODE_CONFIG) as ViewMode[]).map((mode) => {
              const config = VIEW_MODE_CONFIG[mode];
              const Icon = config.icon;
              return (
                <button
                  key={mode}
                  onClick={() => setViewMode(mode)}
                  className={cn(
                    "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
                    viewMode === mode
                      ? "bg-background text-foreground shadow-sm"
                      : "text-muted-foreground hover:text-foreground"
                  )}
                  title={config.label}
                >
                  <Icon className="h-4 w-4" />
                  <span className="hidden sm:inline">{config.label}</span>
                </button>
              );
            })}
          </div>

          {/* ミュート切り替え */}
          <button
            onClick={handleToggleMute}
            className={cn(
              "p-2 rounded-lg text-muted-foreground hover:bg-accent",
              "transition-colors"
            )}
            title={isMuted ? "通知オン" : "通知オフ"}
          >
            {isMuted ? (
              <BellOff className="h-5 w-5" />
            ) : (
              <Bell className="h-5 w-5" />
            )}
          </button>

          {/* フィルター */}
          <button
            onClick={handleToggleFilters}
            className={cn(
              "p-2 rounded-lg text-muted-foreground hover:bg-accent",
              "transition-colors"
            )}
            title="フィルター"
          >
            <Settings className="h-5 w-5" />
          </button>
        </div>
      </header>

      {/* フィルターパネル */}
      {showFilters && (
        <div className="px-4 py-3 border-b border-border bg-muted/30">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium">フィルター</h3>
            <button
              onClick={handleToggleFilters}
              className="p-1 rounded hover:bg-accent"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="space-y-3">
            {/* エージェントフィルター */}
            <div>
              <label className="text-xs text-muted-foreground mb-1 block">
                エージェント
              </label>
              <div className="flex flex-wrap gap-1">
                {agents.map((agent) => (
                  <button
                    key={agent}
                    onClick={() => {
                      setFilterOptions((prev) => ({
                        ...prev,
                        agent: prev.agent?.includes(agent)
                          ? prev.agent.filter((a) => a !== agent)
                          : [...(prev.agent || []), agent],
                      }));
                    }}
                    className={cn(
                      "px-2 py-1 text-xs rounded-full transition-colors",
                      filterOptions.agent?.includes(agent)
                        ? "bg-primary text-primary-foreground"
                        : "bg-background border border-border hover:bg-accent"
                    )}
                  >
                    {agent}
                  </button>
                ))}
              </div>
            </div>

            {/* クリアボタン */}
            <button
              onClick={() => setFilterOptions({})}
              className="text-xs text-muted-foreground hover:text-foreground"
            >
              フィルターをクリア
            </button>
          </div>
        </div>
      )}

      {/* メッセージリスト */}
      <div className="flex-1 overflow-hidden">
        <ChatMessageList
          thinkingLogs={displayThinkingLogs}
          teamMessages={displayMessages}
          typingAgents={typingAgents}
          autoScroll={true}
          onReactionAdd={handleReactionAdd}
        />
      </div>

      {/* 入力エリア */}
      <div className="border-t border-border bg-background p-4">
        <ChatInput
          onSend={handleSendMessage}
          placeholder="メッセージを入力... (Enterで送信、Shift+Enterで改行)"
        />
      </div>
    </div>
  );
}
