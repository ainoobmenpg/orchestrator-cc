/**
 * アニメーションバリアント共通定義
 *
 * Framer Motionで使用するアニメーションバリアントを定義しています
 */

import type { Transition, Variants } from "framer-motion";

// ============================================================================
// 共通トランジション
// ============================================================================

/** デフォルトのスプリングトランジション */
export const springTransition: Transition = {
  type: "spring",
  stiffness: 300,
  damping: 30,
};

/** 緩やかなトランジション */
export const gentleTransition: Transition = {
  type: "spring",
  stiffness: 200,
  damping: 25,
};

/** 高速トランジション */
export const fastTransition: Transition = {
  duration: 0.2,
};

/** 標準トランジション */
export const defaultTransition: Transition = {
  duration: 0.3,
};

// ============================================================================
// フェードインアニメーション
// ============================================================================

/** フェードインバリアント */
export const fadeIn: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
};

/** フェードイン（上から） */
export const fadeInFromTop: Variants = {
  initial: { opacity: 0, y: -20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 },
};

/** フェードイン（下から） */
export const fadeInFromBottom: Variants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: 20 },
};

// ============================================================================
// スライドインアニメーション
// ============================================================================

/** スライドイン（左から） */
export const slideInLeft: Variants = {
  initial: { opacity: 0, x: -50 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: -50 },
};

/** スライドイン（右から） */
export const slideInRight: Variants = {
  initial: { opacity: 0, x: 50 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: 50 },
};

/** スライドイン（上から） */
export const slideInTop: Variants = {
  initial: { opacity: 0, y: -50 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -50 },
};

/** スライドイン（下から） */
export const slideInBottom: Variants = {
  initial: { opacity: 0, y: 50 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: 50 },
};

// ============================================================================
// スケールアニメーション
// ============================================================================

/** スケールイン */
export const scaleIn: Variants = {
  initial: { opacity: 0, scale: 0.9 },
  animate: { opacity: 1, scale: 1 },
  exit: { opacity: 0, scale: 0.9 },
};

/** スケールイン（バウンス付き） */
export const scaleInBounce: Variants = {
  initial: { opacity: 0, scale: 0.5 },
  animate: {
    opacity: 1,
    scale: 1,
    transition: {
      type: "spring",
      stiffness: 400,
      damping: 15,
    },
  },
  exit: { opacity: 0, scale: 0.5 },
};

// ============================================================================
// コンテナアニメーション（子要素の順次アニメーション）
// ============================================================================

/** スタガーコンテナ（フェードイン） */
export const staggerContainer: Variants = {
  initial: { opacity: 0 },
  animate: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.1,
    },
  },
  exit: {
    opacity: 0,
    transition: {
      staggerChildren: 0.05,
      staggerDirection: -1,
    },
  },
};

/** スタガーアイテム（フェードイン） */
export const staggerItem: Variants = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: 20 },
};

/** スタガーコンテナ（スライドイン） */
export const staggerSlideContainer: Variants = {
  initial: { opacity: 0 },
  animate: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
      delayChildren: 0.05,
    },
  },
  exit: {
    opacity: 0,
    transition: {
      staggerChildren: 0.05,
      staggerDirection: -1,
    },
  },
};

/** スタガーアイテム（スライドイン） */
export const staggerSlideItem: Variants = {
  initial: { opacity: 0, x: -20 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: -20 },
};

// ============================================================================
// ページ遷移アニメーション
// ============================================================================

/** ページスライドイン（右から） */
export const pageSlideIn: Variants = {
  initial: { opacity: 0, x: 20 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: -20 },
};

/** ページフェードイン */
export const pageFadeIn: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
};

/** ページスケールイン */
export const pageScaleIn: Variants = {
  initial: { opacity: 0, scale: 0.95 },
  animate: { opacity: 1, scale: 1 },
  exit: { opacity: 0, scale: 0.95 },
};

// ============================================================================
// リストアイテムアニメーション
// ============================================================================

/** リストアイテム追加 */
export const listItemAdd: Variants = {
  initial: { opacity: 0, height: 0, marginBottom: 0 },
  animate: {
    opacity: 1,
    height: "auto",
    marginBottom: "0.5rem",
    transition: {
      height: {
        type: "spring",
        stiffness: 300,
        damping: 30,
      },
      opacity: { duration: 0.2 },
    },
  },
  exit: {
    opacity: 0,
    height: 0,
    marginBottom: 0,
    transition: {
      height: { duration: 0.2 },
      opacity: { duration: 0.1 },
    },
  },
};

// ============================================================================
// ドラッグ＆ドロップアニメーション
// ============================================================================

/** ドラッグ中のスタイル */
export const dragStyles = {
  drag: {
    scale: 1.05,
    boxShadow: "0 10px 30px rgba(0, 0, 0, 0.2)",
    transition: {
      type: "spring",
      stiffness: 400,
      damping: 25,
    },
  },
};

/** ドロップ時のアニメーション */
export const dropAnimation = {
  scale: 1,
  boxShadow: "0 4px 12px rgba(0, 0, 0, 0.1)",
  transition: {
    type: "spring",
    stiffness: 400,
    damping: 25,
  },
};

// ============================================================================
// パルスアニメーション
// ============================================================================

/** パルスアニメーション（接続状態などに使用） */
export const pulseAnimation = {
  scale: [1, 1.1, 1],
  opacity: [1, 0.8, 1],
  transition: {
    duration: 1.5,
    repeat: Infinity,
    ease: "easeInOut",
  },
};

/** 呼吸アニメーション（より緩やかなパルス） */
export const breatheAnimation = {
  scale: [1, 1.05, 1],
  transition: {
    duration: 2,
    repeat: Infinity,
    ease: "easeInOut",
  },
};

// ============================================================================
// 回転アニメーション
// ============================================================================

/** 回転アニメーション（ローディングなど） */
export const spinAnimation = {
  rotate: 360,
  transition: {
    duration: 1,
    repeat: Infinity,
    ease: "linear",
  },
};

// ============================================================================
// シェイクアニメーション（エラー時など）
// ============================================================================

/** シェイクアニメーション */
export const shakeAnimation = {
  x: [0, -10, 10, -10, 10, 0],
  transition: {
    duration: 0.4,
  },
};

// ============================================================================
// モーダルアニメーション
// ============================================================================

/** モーダルオーバーレイ */
export const modalOverlay: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  exit: { opacity: 0 },
};

/** モーダルコンテンツ（スケール） */
export const modalContentScale: Variants = {
  initial: { opacity: 0, scale: 0.9 },
  animate: {
    opacity: 1,
    scale: 1,
    transition: {
      type: "spring",
      stiffness: 300,
      damping: 30,
    },
  },
  exit: {
    opacity: 0,
    scale: 0.9,
    transition: { duration: 0.2 },
  },
};

/** モーダルコンテンツ（スライド） */
export const modalContentSlide: Variants = {
  initial: { opacity: 0, y: 50 },
  animate: {
    opacity: 1,
    y: 0,
    transition: {
      type: "spring",
      stiffness: 300,
      damping: 30,
    },
  },
  exit: {
    opacity: 0,
    y: 50,
    transition: { duration: 0.2 },
  },
};
