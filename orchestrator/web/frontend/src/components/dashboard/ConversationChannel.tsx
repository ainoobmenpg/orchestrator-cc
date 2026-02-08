/**
 * ConversationChannelコンポーネント
 *
 * 会話チャンネル用のUIコンポーネント
 * チャンネル選択、メッセージ表示、メッセージ送信機能を提供します
 */

import { useState, useEffect, useRef, useMemo } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Hash, Send, Users, Plus, Trash2, MessageSquare } from "lucide-react";
import { useTeamStore } from "../../stores/teamStore";
import { useUIStore } from "../../stores/uiStore";
import { getWebSocketClient } from "../../services/websocket";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";
import { formatTime, cn } from "../../lib/utils";
import { slideInBottom } from "../../lib/animations";
import ReactMarkdown from "react-markdown";

export function ConversationChannel() {
  const channels = useTeamStore((state) => state.channels);
  const currentChannel = useTeamStore((state) => state.currentChannel);
  const channelMessages = useTeamStore((state) => state.channelMessages);
  const setCurrentChannel = useTeamStore((state) => state.setCurrentChannel);
  const addChannel = useTeamStore((state) => state.addChannel);
  const removeChannel = useTeamStore((state) => state.removeChannel);
  const addSystemLog = useTeamStore((state) => state.addSystemLog);

  const [newChannelName, setNewChannelName] = useState("");
  const [messageInput, setMessageInput] = useState("");
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const isAutoScrollEnabled = useUIStore((state) => state.isAutoScrollEnabled);

  // WebSocketクライアントを取得
  const wsClient = getWebSocketClient();

  // チャンネルメッセージを取得
  const currentMessages = useMemo(() => {
    if (!currentChannel) return [];
    return channelMessages[currentChannel] || [];
  }, [currentChannel, channelMessages]);

  // 現在のチャンネル情報を取得
  const currentChannelInfo = useMemo(() => {
    if (!currentChannel) return null;
    return channels.find((c) => c.name === currentChannel) || null;
  }, [currentChannel, channels]);

  // 自動スクロール
  useEffect(() => {
    if (isAutoScrollEnabled && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [currentMessages, isAutoScrollEnabled]);

  // チャンネル作成
  const handleCreateChannel = () => {
    if (!newChannelName.trim()) return;

    const trimmedName = newChannelName.trim();

    // 既存のチャンネル名をチェック
    if (channels.some((c) => c.name === trimmedName)) {
      addSystemLog({
        timestamp: new Date().toISOString(),
        level: "warning",
        content: `チャンネル ${trimmedName} は既に存在します`,
      });
      return;
    }

    // ストアに追加（参加時にサーバーから通知される）
    addChannel({
      name: trimmedName,
      participants: [],
      messageCount: 0,
    });

    // チャンネルに参加
    wsClient.joinChannel(trimmedName, "user");

    setNewChannelName("");
    setShowCreateDialog(false);

    addSystemLog({
      timestamp: new Date().toISOString(),
      level: "success",
      content: `チャンネル ${trimmedName} を作成しました`,
    });
  };

  // チャンネル削除
  const handleDeleteChannel = (channelName: string) => {
    if (!confirm(`チャンネル ${channelName} を削除しますか？`)) {
      return;
    }

    // チャンネルから退出
    wsClient.leaveChannel(channelName, "user");

    // ストアから削除
    removeChannel(channelName);

    if (currentChannel === channelName) {
      setCurrentChannel(null);
    }

    addSystemLog({
      timestamp: new Date().toISOString(),
      level: "info",
      content: `チャンネル ${channelName} を削除しました`,
    });
  };

  // チャンネル選択
  const handleSelectChannel = (channelName: string) => {
    if (currentChannel === channelName) {
      setCurrentChannel(null);
    } else {
      setCurrentChannel(channelName);
    }
  };

  // メッセージ送信
  const handleSendMessage = () => {
    if (!currentChannel || !messageInput.trim()) return;

    wsClient.sendToChannel(currentChannel, messageInput.trim(), "user");
    setMessageInput("");
  };

  // Enterキーで送信
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <Card className="h-full flex flex-col min-h-0 max-h-[calc(100vh-12rem)]">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
        <div className="flex items-center gap-2">
          <Hash className="h-5 w-5 text-primary" />
          <CardTitle className="text-lg">会話チャンネル</CardTitle>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowCreateDialog(!showCreateDialog)}
            aria-label="チャンネルを作成"
          >
            <Plus className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>

      {/* チャンネル作成ダイアログ */}
      {showCreateDialog && (
        <div className="px-6 pb-4">
          <div className="flex gap-2">
            <input
              type="text"
              value={newChannelName}
              onChange={(e) => setNewChannelName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  handleCreateChannel();
                }
              }}
              placeholder="チャンネル名を入力..."
              className="flex-1 px-3 py-2 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
              aria-label="チャンネル名"
            />
            <Button variant="primary" size="sm" onClick={handleCreateChannel}>
              作成
            </Button>
          </div>
        </div>
      )}

      {/* チャンネルリスト */}
      <div className="px-6 pb-2">
        <div className="flex flex-wrap gap-2">
          {channels.length === 0 ? (
            <div className="text-sm text-muted-foreground py-2">
              チャンネルはまだありません
            </div>
          ) : (
            channels.map((channel) => (
              <motion.button
                key={channel.name}
                onClick={() => handleSelectChannel(channel.name)}
                className={cn(
                  "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
                  "min-h-[36px] min-w-[44px]",
                  "hover:bg-accent",
                  currentChannel === channel.name
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted",
                )}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <Hash className="h-3.5 w-3.5" />
                <span>{channel.name}</span>
                <Badge variant="secondary" className="ml-1 text-xs">
                  {channel.messageCount}
                </Badge>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-5 w-5 p-0 ml-1 hover:bg-destructive hover:text-destructive-foreground"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteChannel(channel.name);
                  }}
                  aria-label={`チャンネル ${channel.name} を削除`}
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              </motion.button>
            ))
          )}
        </div>
      </div>

      {/* チャンネル情報と参加者 */}
      {currentChannelInfo && (
        <div className="px-6 pb-2">
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <div className="flex items-center gap-1">
              <Users className="h-4 w-4" />
              <span>{currentChannelInfo.participants.length}人</span>
            </div>
            {currentChannelInfo.participants.length > 0 && (
              <div className="flex items-center gap-1">
                <span className="text-xs">:</span>
                <span className="text-xs">
                  {currentChannelInfo.participants.join(", ")}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* メッセージエリア */}
      <CardContent className="flex-1 overflow-y-auto p-4 min-h-0">
        <div ref={scrollRef} className="space-y-2">
          {!currentChannel ? (
            <div className="py-12 text-center text-muted-foreground flex flex-col items-center gap-3">
              <MessageSquare className="h-12 w-12 opacity-50" />
              <div>
                <p className="font-medium">チャンネルを選択してください</p>
                <p className="text-sm mt-1">
                  上のチャンネルリストからチャンネルを選択するか、
                  <br />
                  新しいチャンネルを作成してください
                </p>
              </div>
            </div>
          ) : currentMessages.length === 0 ? (
            <div className="py-12 text-center text-muted-foreground flex flex-col items-center gap-3">
              <Hash className="h-12 w-12 opacity-50" />
              <div>
                <p className="font-medium">#{currentChannel}</p>
                <p className="text-sm mt-1">
                  まだメッセージはありません。
                  <br />
                  最初のメッセージを送信してください。
                </p>
              </div>
            </div>
          ) : (
            <AnimatePresence mode="popLayout">
              {currentMessages.map((message, index) => (
                <ChannelMessageItem
                  key={`${message.id}-${index}`}
                  message={message}
                  index={index}
                />
              ))}
            </AnimatePresence>
          )}
        </div>
      </CardContent>

      {/* メッセージ入力エリア */}
      {currentChannel && (
        <div className="p-4 border-t">
          <div className="flex gap-2">
            <textarea
              value={messageInput}
              onChange={(e) => setMessageInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={`#${currentChannel} にメッセージを送信...`}
              className="flex-1 px-3 py-2 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-ring resize-none"
              rows={2}
              aria-label="メッセージ入力"
            />
            <Button
              variant="primary"
              size="md"
              onClick={handleSendMessage}
              disabled={!messageInput.trim()}
              aria-label="メッセージを送信"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </Card>
  );
}

interface ChannelMessageItemProps {
  message: {
    id: string;
    channel: string;
    sender: string;
    content: string;
    timestamp: number;
  };
  index: number;
}

function ChannelMessageItem({ message, index }: ChannelMessageItemProps) {
  const isCurrentUser = message.sender === "user";

  return (
    <motion.div
      variants={slideInBottom}
      initial="initial"
      animate="animate"
      exit={{ opacity: 0, height: 0, marginBottom: 0 }}
      transition={{
        type: "spring",
        stiffness: 400,
        damping: 25,
        delay: Math.min(index * 0.03, 0.3),
      }}
      className={cn(
        "rounded-lg border p-3 transition-colors",
        isCurrentUser
          ? "bg-primary/10 border-primary/30 ml-8"
          : "bg-accent/50 border-border",
      )}
    >
      <div className="flex items-start gap-3">
        <div
          className={cn(
            "h-8 w-8 rounded-full flex items-center justify-center text-sm font-medium flex-shrink-0",
            isCurrentUser
              ? "bg-primary text-primary-foreground"
              : "bg-muted text-muted-foreground",
          )}
        >
          {message.sender.charAt(0).toUpperCase()}
        </div>

        <div className="flex-1 min-w-0 space-y-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-foreground">{message.sender}</span>
            {message.timestamp && (
              <span className="text-xs text-muted-foreground">
                {formatTime(new Date(message.timestamp).toISOString())}
              </span>
            )}
          </div>

          <div className="text-sm text-foreground prose prose-sm dark:prose-invert max-w-none">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
