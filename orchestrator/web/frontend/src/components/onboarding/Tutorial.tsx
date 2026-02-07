/**
 * チュートリアルモーダルコンポーネント
 *
 * 初回アクセス時に基本機能の説明を表示します
 */

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  ChevronRight,
  ChevronLeft,
  LayoutDashboard,
  MessageSquare,
  CheckCircle2,
  Activity,
} from "lucide-react";
import { cn } from "../../lib/utils";
import {
  getTutorialCompleted,
  markFirstVisit,
  useTutorialState,
} from "../../hooks/useFirstVisit";
import { modalContentScale, modalOverlay } from "../../lib/animations";

/**
 * チュートリアルステップ
 */
interface TutorialStep {
  title: string;
  description: string;
  icon: typeof LayoutDashboard;
}

const tutorialSteps: TutorialStep[] = [
  {
    title: "ダッシュボードへようこそ",
    description:
      "orchestrator-ccは、Claude CodeのAgent Teams機能を使用したマルチエージェント協調システムです。エージェントの状態、タスク、メッセージをリアルタイムで監視できます。",
    icon: LayoutDashboard,
  },
  {
    title: "エージェントパネル",
    description:
      "左側のパネルでは、各エージェントの状態を確認できます。エージェントはタスクに割り当てられたり、メッセージを交換したりします。",
    icon: Activity,
  },
  {
    title: "メッセージ・タイムライン",
    description:
      "エージェント間のメッセージやシステムイベントをリアルタイムで確認できます。思考ログタブでは、エージェントの思考プロセスも追跡できます。",
    icon: MessageSquare,
  },
  {
    title: "タスクボード",
    description:
      "タスクボードでは、現在進行中のタスクをカンバン方式で管理できます。ドラッグ＆ドロップでタスクの状態を確認できます。",
    icon: CheckCircle2,
  },
];

/**
 * チュートリアルモーダルプロパティ
 */
export interface TutorialProps {
  /** 開いているかどうか */
  isOpen?: boolean;
  /** 閉じた時のコールバック */
  onClose?: () => void;
}

export function Tutorial({ onClose }: TutorialProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [dontShowAgain, setDontShowAgain] = useState(false);
  const { markCompleted } = useTutorialState();
  // 初期値を計算関数で設定（useEffect内のsetStateを回避）
  const [shouldShow, setShouldShow] = useState(() => {
    const hasVisited = localStorage.getItem("orchestrator-cc-first-visit");
    const currentIsCompleted = getTutorialCompleted();
    return !hasVisited && !currentIsCompleted;
  });

  // 既に完了している場合は表示しない
  if (!shouldShow) {
    return null;
  }

  const step = tutorialSteps[currentStep]!;
  const IconComponent = step.icon;
  const isLastStep = currentStep === tutorialSteps.length - 1;
  const isFirstStep = currentStep === 0;

  const handleNext = () => {
    if (isLastStep) {
      handleClose();
    } else {
      setCurrentStep((prev) => prev + 1);
    }
  };

  const handlePrevious = () => {
    if (!isFirstStep) {
      setCurrentStep((prev) => prev - 1);
    }
  };

  const handleClose = () => {
    if (dontShowAgain) {
      markCompleted();
    }
    markFirstVisit();
    setShouldShow(false);
    onClose?.();
  };

  return (
    <AnimatePresence>
      {shouldShow && (
        <>
          {/* オーバーレイ */}
          <motion.div
            variants={modalOverlay}
            initial="initial"
            animate="animate"
            exit="exit"
            className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm"
            onClick={handleClose}
          />

          {/* モーダル */}
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <motion.div
              variants={modalContentScale}
              initial="initial"
              animate="animate"
              exit="exit"
              className="relative w-full max-w-lg bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-6 md:p-8"
              onClick={(e) => e.stopPropagation()}
            >
              {/* 閉じるボタン */}
              <button
                onClick={handleClose}
                className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                aria-label="閉じる"
              >
                <X className="h-5 w-5" />
              </button>

              {/* プログレスバー */}
              <div className="mb-6">
                <div className="flex gap-1">
                  {tutorialSteps.map((_, index) => (
                    <div
                      key={index}
                      className={cn(
                        "h-1 flex-1 rounded-full transition-colors duration-300",
                        index <= currentStep
                          ? "bg-blue-500"
                          : "bg-gray-200 dark:bg-gray-700",
                      )}
                    />
                  ))}
                </div>
              </div>

              {/* アイコン */}
              <div className="flex justify-center mb-6">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/30">
                  <IconComponent className="h-8 w-8 text-blue-600 dark:text-blue-400" />
                </div>
              </div>

              {/* タイトルと説明 */}
              <div className="text-center mb-6">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                  {step.title}
                </h2>
                <p className="text-gray-600 dark:text-gray-300">
                  {step.description}
                </p>
              </div>

              {/* ステップインジケーター */}
              <div className="text-center mb-6 text-sm text-gray-500 dark:text-gray-400">
                {currentStep + 1} / {tutorialSteps.length}
              </div>

              {/* 「次回から表示しない」チェックボックス */}
              <div className="flex items-center justify-center mb-6">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={dontShowAgain}
                    onChange={(e) => setDontShowAgain(e.target.checked)}
                    className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-600 dark:text-gray-300">
                    次回から表示しない
                  </span>
                </label>
              </div>

              {/* ナビゲーションボタン */}
              <div className="flex gap-3">
                {!isFirstStep && (
                  <button
                    onClick={handlePrevious}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  >
                    <ChevronLeft className="h-4 w-4" />
                    戻る
                  </button>
                )}
                <button
                  onClick={handleNext}
                  className={cn(
                    "flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors",
                    isFirstStep && "flex-1",
                  )}
                >
                  {isLastStep ? "始める" : "次へ"}
                  {!isLastStep && <ChevronRight className="h-4 w-4" />}
                </button>
              </div>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
}
