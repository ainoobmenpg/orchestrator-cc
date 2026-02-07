/**
 * ツールチップコンポーネント
 *
 * マウスホバー時に追加情報を表示するコンポーネントです
 */

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";

/**
 * ツールチップの位置
 */
export type TooltipPosition =
  | "top"
  | "bottom"
  | "left"
  | "right"
  | "top-left"
  | "top-right"
  | "bottom-left"
  | "bottom-right";

/**
 * ツールチッププロパティ
 */
export interface TooltipProps {
  /** ツールチップの内容 */
  content: string;
  /** 子要素 */
  children: React.ReactNode;
  /** 位置 */
  position?: TooltipPosition;
  /** 遅延時間（ミリ秒） */
  delay?: number;
  /** カスタムクラス名 */
  className?: string;
  /** ツールチップのカスタムクラス名 */
  tooltipClassName?: string;
  /** 矢印を表示するかどうか */
  showArrow?: boolean;
}

/**
 * 位置ごとのスタイルクラス
 */
const positionStyles: Record<TooltipPosition, string> = {
  top: "bottom-full left-1/2 -translate-x-1/2 mb-2",
  bottom: "top-full left-1/2 -translate-x-1/2 mt-2",
  left: "right-full top-1/2 -translate-y-1/2 mr-2",
  right: "left-full top-1/2 -translate-y-1/2 ml-2",
  "top-left": "bottom-full right-0 mb-2",
  "top-right": "bottom-full left-0 mb-2",
  "bottom-left": "top-full right-0 mt-2",
  "bottom-right": "top-full left-0 mt-2",
};

/**
 * 矢印の位置スタイル
 */
const arrowPositionStyles: Record<
  TooltipPosition,
  { borderStyle: string; rotateClass: string }
> = {
  top: {
    borderStyle: "border-l-transparent border-r-transparent border-b-transparent",
    rotateClass: "",
  },
  bottom: {
    borderStyle: "border-l-transparent border-r-transparent border-t-transparent",
    rotateClass: "rotate-180",
  },
  left: {
    borderStyle: "border-t-transparent border-b-transparent border-r-transparent",
    rotateClass: "-rotate-90",
  },
  right: {
    borderStyle: "border-t-transparent border-b-transparent border-l-transparent",
    rotateClass: "rotate-90",
  },
  "top-left": {
    borderStyle: "border-l-transparent border-r-transparent border-b-transparent",
    rotateClass: "",
  },
  "top-right": {
    borderStyle: "border-l-transparent border-r-transparent border-b-transparent",
    rotateClass: "",
  },
  "bottom-left": {
    borderStyle: "border-l-transparent border-r-transparent border-t-transparent",
    rotateClass: "rotate-180",
  },
  "bottom-right": {
    borderStyle: "border-l-transparent border-r-transparent border-t-transparent",
    rotateClass: "rotate-180",
  },
};

export function Tooltip({
  content,
  children,
  position = "top",
  delay = 200,
  className,
  tooltipClassName,
  showArrow = true,
}: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [timeoutId, setTimeoutId] = useState<ReturnType<typeof setTimeout> | null>(null);

  const handleMouseEnter = () => {
    const id = setTimeout(() => {
      setIsVisible(true);
    }, delay);
    setTimeoutId(id);
  };

  const handleMouseLeave = () => {
    if (timeoutId) {
      clearTimeout(timeoutId);
      setTimeoutId(null);
    }
    setIsVisible(false);
  };

  const arrowStyles = arrowPositionStyles[position];

  return (
    <div
      className={cn("relative inline-block", className)}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {children}

      <AnimatePresence>
        {isVisible && (
          <motion.div
            variants={fadeIn}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ duration: 0.15 }}
            className={cn(
              "absolute z-50 px-3 py-1.5 text-sm text-white bg-gray-900 dark:bg-gray-700 rounded-lg shadow-lg whitespace-nowrap pointer-events-none",
              positionStyles[position],
              tooltipClassName,
            )}
          >
            {content}
            {showArrow && (
              <div
                className={cn(
                  "absolute w-2 h-2 bg-gray-900 dark:bg-gray-700 border-4",
                  arrowStyles.borderStyle,
                  arrowStyles.rotateClass,
                  position === "top" || position === "top-left" || position === "top-right"
                    ? "bottom-[-8px] left-1/2 -translate-x-1/2"
                    : position === "bottom" || position === "bottom-left" || position === "bottom-right"
                    ? "top-[-8px] left-1/2 -translate-x-1/2"
                    : position === "left"
                    ? "right-[-8px] top-1/2 -translate-y-1/2"
                    : "left-[-8px] top-1/2 -translate-y-1/2",
                )}
              />
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
