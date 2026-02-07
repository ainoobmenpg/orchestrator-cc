/**
 * PageTransitionコンポーネント
 *
 * ページ遷移時のアニメーションを提供するラッパーコンポーネントです
 */

import { motion } from "framer-motion";
import type { Variants } from "framer-motion";

/**
 * ページ遷移アニメーションの種類
 */
export type PageTransitionType = "fade" | "slide" | "scale";

/**
 * PageTransitionプロパティ
 */
export interface PageTransitionProps {
  /** 子要素 */
  children: React.ReactNode;
  /** アニメーションの種類 */
  type?: PageTransitionType;
  /** カスタムクラス名 */
  className?: string;
}

/**
 * アニメーションタイプごとのバリアント
 */
const transitionVariants: Record<PageTransitionType, Variants> = {
  fade: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
  },
  slide: {
    initial: { opacity: 0, x: 20 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: -20 },
  },
  scale: {
    initial: { opacity: 0, scale: 0.95 },
    animate: { opacity: 1, scale: 1 },
    exit: { opacity: 0, scale: 0.95 },
  },
};

export function PageTransition({
  children,
  type = "fade",
  className = "",
}: PageTransitionProps) {
  const variants = transitionVariants[type];

  return (
    <motion.div
      variants={variants}
      initial="initial"
      animate="animate"
      exit="exit"
      className={className}
    >
      {children}
    </motion.div>
  );
}
