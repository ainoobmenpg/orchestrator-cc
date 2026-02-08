/**
 * DashboardPageコンポーネント
 *
 * ダッシュボードの各ページを表示します
 * AnimatePresenceを使用したタブ切り替えアニメーションを実装しています
 */

import { AnimatePresence } from "framer-motion";
import { useUIStore } from "../stores/uiStore";
import { useTeamStore } from "../stores/teamStore";
import { EmptyState } from "../components/common/EmptyState";
import { Users } from "lucide-react";
import { PageTransition } from "../components/ui/PageTransition";
import { MessageList } from "../components/dashboard/MessageList";
import { TaskBoard } from "../components/dashboard/TaskBoard";

export function DashboardPage() {
  const activeTab = useUIStore((state) => state.activeTab);
  const selectedTeamName = useTeamStore((state) => state.selectedTeamName);

  if (!selectedTeamName) {
    return (
      <div className="flex h-full items-center justify-center">
        <EmptyState
          icon={Users}
          title="チームを選択してください"
          description="監視するチームを選択すると、ここにダッシュボードが表示されます"
        />
      </div>
    );
  }

  // タブに応じたページを表示
  return (
    <AnimatePresence mode="wait">
      {activeTab === "dashboard" && (
        <PageTransition key="dashboard">
          <ConferenceRoomView />
        </PageTransition>
      )}
      {activeTab === "tasks" && (
        <PageTransition key="tasks">
          <TasksView />
        </PageTransition>
      )}
    </AnimatePresence>
  );
}

// 会議ルームビュー
function ConferenceRoomView() {
  return (
    <div className="h-full p-4">
      <MessageList />
    </div>
  );
}

// タスクボードビュー
function TasksView() {
  return (
    <div className="h-full">
      <TaskBoard />
    </div>
  );
}

// 各ページコンポーネントのエクスポート
export function TasksPage() {
  return <TasksView />;
}
