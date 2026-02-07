/**
 * 初回アクセス検出フック
 *
 * localStorageを使用して初回アクセスを管理します
 */

import { useEffect, useState } from "react";

const FIRST_VISIT_KEY = "orchestrator-cc-first-visit";
const TUTORIAL_COMPLETED_KEY = "orchestrator-cc-tutorial-completed";

// カスタムイベント名
const FIRST_VISIT_EVENT = "orchestrator-cc-first-visit-changed";

/**
 * 初回アクセス検出フック
 *
 * @returns 初回アクセスかどうか
 */
export function useFirstVisit(): boolean {
  const [isFirstVisit, setIsFirstVisit] = useState(false);

  useEffect(() => {
    // 初期値を設定
    const hasVisited = localStorage.getItem(FIRST_VISIT_KEY);
    setIsFirstVisit(!hasVisited);

    // storageイベントで他タブからの変更を検出
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === FIRST_VISIT_KEY) {
        setIsFirstVisit(!e.newValue);
      }
    };

    // カスタムイベントで同タブ内からの変更を検出
    const handleFirstVisitChange = () => {
      const hasVisited = localStorage.getItem(FIRST_VISIT_KEY);
      setIsFirstVisit(!hasVisited);
    };

    window.addEventListener("storage", handleStorageChange);
    window.addEventListener(FIRST_VISIT_EVENT, handleFirstVisitChange);
    return () => {
      window.removeEventListener("storage", handleStorageChange);
      window.removeEventListener(FIRST_VISIT_EVENT, handleFirstVisitChange);
    };
  }, []);

  return isFirstVisit;
}

/**
 * 初回アクセスをマークする
 */
export function markFirstVisit(): void {
  localStorage.setItem(FIRST_VISIT_KEY, "true");
  // カスタムイベントを発火して同タブ内のコンポーネントに通知
  window.dispatchEvent(new Event(FIRST_VISIT_EVENT));
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
