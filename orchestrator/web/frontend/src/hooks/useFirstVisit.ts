/**
 * 初回アクセス検出フック
 *
 * localStorageを使用して初回アクセスを管理します
 */

import { useEffect, useState } from "react";

const FIRST_VISIT_KEY = "orchestrator-cc-first-visit";
const TUTORIAL_COMPLETED_KEY = "orchestrator-cc-tutorial-completed";

/**
 * 初回アクセス検出フック
 *
 * @returns 初回アクセスかどうか
 */
export function useFirstVisit(): boolean {
  const [isFirstVisit, setIsFirstVisit] = useState(false);

  useEffect(() => {
    const hasVisited = localStorage.getItem(FIRST_VISIT_KEY);
    if (!hasVisited) {
      setIsFirstVisit(true);
    }
  }, []);

  return isFirstVisit;
}

/**
 * 初回アクセスをマークする
 */
export function markFirstVisit(): void {
  localStorage.setItem(FIRST_VISIT_KEY, "true");
}

/**
 * チュートリアル完了状態を取得
 */
export function getTutorialCompleted(): boolean {
  return localStorage.getItem(TUTORIAL_COMPLETED_KEY) === "true";
}

/**
 * チュートリアル完了をマークする
 */
export function markTutorialCompleted(): void {
  localStorage.setItem(TUTORIAL_COMPLETED_KEY, "true");
}

/**
 * チュートリアル完了状態をリセットする（開発用）
 */
export function resetTutorialCompleted(): void {
  localStorage.removeItem(TUTORIAL_COMPLETED_KEY);
  localStorage.removeItem(FIRST_VISIT_KEY);
}

/**
 * チュートリアル完了フック
 *
 * @returns チュートリアル完了状態と操作関数
 */
export function useTutorialState() {
  const [isCompleted, setIsCompleted] = useState(false);

  useEffect(() => {
    setIsCompleted(getTutorialCompleted());
  }, []);

  const markCompleted = () => {
    markTutorialCompleted();
    setIsCompleted(true);
  };

  const reset = () => {
    resetTutorialCompleted();
    setIsCompleted(false);
  };

  return {
    isCompleted,
    markCompleted,
    reset,
  };
}
