/**
 * Footerコンポーネント
 *
 * ダッシュボードのフッターを表示します
 */

import { Trash2, Download } from "lucide-react";
import { useUIStore } from "../../stores/uiStore";
import { notify } from "../../stores/uiStore";
import type { TeamMessage } from "../../services/types";

export function Footer() {
  const {
    isThinkingLogVisible,
    isAutoScrollEnabled,
    isTimestampVisible,
    toggleThinkingLogVisibility,
    toggleAutoScroll,
    toggleTimestampVisibility,
  } = useUIStore();

  // TODO: teamStore からの取得を無効化（無限ループ回避のため一時的に空配列・空関数）
  const clearMessages = () => {};
  const clearSystemLogs = () => {};
  const messages: TeamMessage[] = [];

  const handleClearLogs = () => {
    clearMessages();
    clearSystemLogs();
    notify.success("ログをクリアしました");
  };

  const handleExportLogs = () => {
    const data = messages
      .map((m) => {
        const timestamp = m.timestamp ? new Date(m.timestamp).toLocaleString("ja-JP") : "";
        return `[${timestamp}] ${m.sender} -> ${m.recipient}: ${m.content}`;
      })
      .join("\n");

    const blob = new Blob([data], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `messages-${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);

    notify.success("ログをエクスポートしました");
  };

  return (
    <footer className="flex h-12 items-center justify-between border-t border-border bg-background px-4">
      {/* 左側: 設定チェックボックス */}
      <div className="flex items-center gap-4">
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={isThinkingLogVisible}
            onChange={toggleThinkingLogVisibility}
            className="h-4 w-4 rounded border-input"
          />
          <span>思考ログを表示</span>
        </label>

        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={isAutoScrollEnabled}
            onChange={toggleAutoScroll}
            className="h-4 w-4 rounded border-input"
          />
          <span>自動スクロール</span>
        </label>

        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={isTimestampVisible}
            onChange={toggleTimestampVisibility}
            className="h-4 w-4 rounded border-input"
          />
          <span>タイムスタンプ表示</span>
        </label>
      </div>

      {/* 右側: アクションボタン */}
      <div className="flex items-center gap-2">
        <button
          onClick={handleClearLogs}
          className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground"
        >
          <Trash2 className="h-4 w-4" />
          <span>ログをクリア</span>
        </button>

        <button
          onClick={handleExportLogs}
          className="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground"
        >
          <Download className="h-4 w-4" />
          <span>エクスポート</span>
        </button>
      </div>
    </footer>
  );
}
