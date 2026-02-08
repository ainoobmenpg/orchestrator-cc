/**
 * ChatInputコンポーネント
 *
 * チャットメッセージ入力フォームを提供します
 * ユーザーからのメッセージ送信、リアクション送信をサポートします
 */

import { useState, useCallback, KeyboardEvent, FormEvent } from "react";
import { Send, Smile } from "lucide-react";
import { cn } from "../../lib/utils";

export interface ChatInputProps {
  /** 送信ハンドラー */
  onSend: (content: string) => void;
  /** プレースホルダー */
  placeholder?: string;
  /** 無効状態 */
  disabled?: boolean;
  /** カスタムクラス名 */
  className?: string;
}

// よく使う絵文字リスト
const COMMON_EMOJIS = [
  "👍", "👎", "❤️", "😂", "😮", "😢", "😡", "🎉", "🙏", "🔥",
  "❓", "❗", "✅", "❌", "💡", "🤔", "😕", "😊", "🎯", "⚡",
];

/**
 * チャット入力コンポーネント
 */
export function ChatInput({
  onSend,
  placeholder = "メッセージを入力...",
  disabled = false,
  className,
}: ChatInputProps) {
  const [content, setContent] = useState("");
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);

  const handleSubmit = useCallback(
    (e: FormEvent) => {
      e.preventDefault();
      const trimmed = content.trim();
      if (trimmed && !disabled) {
        onSend(trimmed);
        setContent("");
      }
    },
    [content, disabled, onSend]
  );

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      // Enterで送信（Shift+Enterは改行）
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        const trimmed = content.trim();
        if (trimmed && !disabled) {
          onSend(trimmed);
          setContent("");
        }
      }
    },
    [content, disabled, onSend]
  );

  const handleEmojiSelect = useCallback((emoji: string) => {
    setContent((prev) => prev + emoji);
    setShowEmojiPicker(false);
  }, []);

  return (
    <div className={cn("relative", className)}>
      <form onSubmit={handleSubmit} className="flex items-end gap-2">
        {/* 絵文字ボタン */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowEmojiPicker((prev) => !prev)}
            disabled={disabled}
            className={cn(
              "p-2 rounded-lg text-muted-foreground hover:bg-accent",
              "disabled:opacity-50 disabled:cursor-not-allowed"
            )}
            title="絵文字を挿入"
          >
            <Smile className="h-5 w-5" />
          </button>

          {/* 絵文字ピッカー */}
          {showEmojiPicker && (
            <div className="absolute bottom-full left-0 mb-2 p-2 bg-background border border-border rounded-lg shadow-lg">
              <div className="grid grid-cols-5 gap-1">
                {COMMON_EMOJIS.map((emoji) => (
                  <button
                    key={emoji}
                    type="button"
                    onClick={() => handleEmojiSelect(emoji)}
                    className="p-2 text-xl hover:bg-accent rounded transition-colors"
                  >
                    {emoji}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* メンションボタン（将来の拡張用） */}
        {/* TODO: メンション機能の実装
        <button
          type="button"
          disabled={disabled}
          className={cn(
            "p-2 rounded-lg text-muted-foreground hover:bg-accent",
            "disabled:opacity-50 disabled:cursor-not-allowed"
          )}
          title="メンションを挿入"
        >
          <AtSign className="h-5 w-5" />
        </button>
        */}

        {/* テキスト入力 */}
        <div className="flex-1 relative">
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            rows={1}
            className={cn(
              "w-full px-4 py-2 pr-12 rounded-lg",
              "bg-background border border-border",
              "focus:outline-none focus:ring-2 focus:ring-ring",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              "resize-none overflow-hidden",
              "min-h-[40px] max-h-[200px]"
            )}
            style={{
              height: "auto",
            }}
          />
        </div>

        {/* 送信ボタン */}
        <button
          type="submit"
          disabled={disabled || !content.trim()}
          className={cn(
            "p-2 rounded-lg",
            "bg-primary text-primary-foreground",
            "hover:bg-primary/90",
            "disabled:opacity-50 disabled:cursor-not-allowed"
          )}
          title="送信（Enter）"
        >
          <Send className="h-5 w-5" />
        </button>
      </form>
    </div>
  );
}
