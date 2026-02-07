/**
 * SkipLinkコンポーネント
 *
 * キーボードユーザーがメインコンテンツへスキップするためのリンクを提供します
 * スクリーンリーダーを使用するユーザーにとって重要なアクセシビリティ機能です
 */

import { cn } from "../../lib/utils";

interface SkipLinkProps {
  /** スキップ先の要素ID */
  targetId?: string;
  /** クラス名 */
  className?: string;
}

export function SkipLink({ targetId = "main-content", className }: SkipLinkProps) {
  return (
    <a
      href={`#${targetId}`}
      className={cn(
        // デフォルトでは視覚的に隠す（キーボードフォーカス時に表示）
        "sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4",
        "focus:z-50 focus:rounded-md focus:bg-primary focus:px-4 focus:py-2",
        "focus:text-primary-foreground focus:shadow-lg",
        "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
        className,
      )}
    >
      コンテンツへスキップ
    </a>
  );
}

/**
 * サブスキップリンクコンポーネント
 *
 * メインコンテンツ内でセクション間をスキップするためのリンクを提供します
 */
interface SubSkipLinkProps {
  /** リンクテキスト */
  label: string;
  /** スキップ先の要素ID */
  targetId: string;
  /** クラス名 */
  className?: string;
}

export function SubSkipLink({ label, targetId, className }: SubSkipLinkProps) {
  return (
    <a
      href={`#${targetId}`}
      className={cn(
        "sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-12",
        "focus:z-50 focus:rounded-md focus:bg-primary focus:px-4 focus:py-2",
        "focus:text-primary-foreground focus:shadow-lg",
        "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
        className,
      )}
    >
      {label}
    </a>
  );
}
