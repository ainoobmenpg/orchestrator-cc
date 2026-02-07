/**
 * LiveRegionコンポーネント
 *
 * スクリーンリーダーを使用するユーザーに動的な変更を通知するための
 * ライブリージョン（ARIA Live Region）を提供します
 *
 * 参考: https://www.w3.org/WAI/ARIA/apg/example-index/live-region-live
 */

import { useEffect, useRef } from "react";
import { cn } from "../../lib/utils";

interface LiveRegionProps {
  /** 通知するメッセージ */
  message: string;
  /** 重要度のレベル */
  politeness?: "polite" | "assertive" | "off";
  /** クラス名 */
  className?: string;
}

/**
 * ライブリージョンコンポーネント
 *
 * 動的なコンテンツの変更をスクリーンリーダーに通知します
 */
export function LiveRegion({
  message,
  politeness = "polite",
  className,
}: LiveRegionProps) {
  const announcementRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (announcementRef.current && message) {
      // メッセージが変更されたら通知
      announcementRef.current.textContent = message;
    }
  }, [message]);

  return (
    <div
      ref={announcementRef}
      role="status"
      aria-live={politeness}
      aria-atomic="true"
      className={cn("sr-only", className)}
    >
      {/* メッセージはuseEffectで設定されます */}
    </div>
  );
}

/**
 * 複数のライブリージョンを管理するコンテナコンポーネント
 *
 * アプリケーション全体で1つのインスタンスを使用します
 */
interface LiveRegionContainerProps {
  /** 一般的な通知 */
  politeMessage?: string;
  /** 重要な通知 */
  assertiveMessage?: string;
  /** クラス名 */
  className?: string;
}

export function LiveRegionContainer({
  politeMessage,
  assertiveMessage,
  className,
}: LiveRegionContainerProps) {
  return (
    <div className={className}>
      {politeMessage && (
        <div
          role="status"
          aria-live="polite"
          aria-atomic="true"
          className="sr-only"
        >
          {politeMessage}
        </div>
      )}
      {assertiveMessage && (
        <div
          role="alert"
          aria-live="assertive"
          aria-atomic="true"
          className="sr-only"
        >
          {assertiveMessage}
        </div>
      )}
    </div>
  );
}
