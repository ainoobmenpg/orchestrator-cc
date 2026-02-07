/**
 * DashboardPageコンポーネント
 *
 * ダッシュボードの各ページを表示します
 * AnimatePresenceを使用したタブ切り替えアニメーションを実装しています
 */

import { AnimatePresence } from "framer-motion";
import { useUIStore } from "../stores/uiStore";
import { useTeamStore } from "../stores/teamStore";
import { useAgentStats } from "../hooks/useAgents";
import { useTaskStats } from "../stores/teamStore";
import { useMessageStats } from "../hooks/useMessages";
import { useSelectedTeam } from "../stores/teamStore";
import { SummaryCards } from "../components/dashboard/SummaryCards";
import { AgentPanel } from "../components/dashboard/AgentPanel";
import { Timeline } from "../components/dashboard/Timeline";
import { TaskBoard } from "../components/dashboard/TaskBoard";
import { MessageList } from "../components/dashboard/MessageList";
import { SystemLog } from "../components/dashboard/SystemLog";
import { EmptyState } from "../components/common/EmptyState";
import { Bot } from "lucide-react";
import { PageTransition } from "../components/ui/PageTransition";

export function DashboardPage() {
  const activeTab = useUIStore((state) => state.activeTab);
  const selectedTeam = useSelectedTeam();

  if (!selectedTeam) {
    return (
      <div className="flex h-full items-center justify-center">
        <EmptyState
          icon={Bot}
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
          <DashboardView />
        </PageTransition>
      )}
      {activeTab === "tasks" && (
        <PageTransition key="tasks">
          <TasksView />
        </PageTransition>
      )}
      {activeTab === "messages" && (
        <PageTransition key="messages">
          <MessagesView />
        </PageTransition>
      )}
      {activeTab === "timeline" && (
        <PageTransition key="timeline">
          <TimelineView />
        </PageTransition>
      )}
      {activeTab === "system" && (
        <PageTransition key="system">
          <SystemView />
        </PageTransition>
      )}
    </AnimatePresence>
  );
}

// 各タブのビューコンポーネント
function DashboardView() {
  const stats = useAgentStats();
  const taskStats = useTaskStats();
  const messageStats = useMessageStats();
  const hasErrors = useTeamStore((state) => state.hasErrors);

  return (
    <div className="flex h-full gap-4 p-4">
      <AgentPanel />
      <div className="flex-1 flex flex-col gap-4">
        <SummaryCards
          agentCount={stats.total}
          taskCount={taskStats.total}
          messageCount={messageStats.total}
          hasErrors={hasErrors}
        />
        <div className="flex-1 min-h-0">
          <Timeline />
        </div>
      </div>
    </div>
  );
}

function TasksView() {
  return (
    <div className="h-full">
      <TaskBoard />
    </div>
  );
}

function MessagesView() {
  return (
    <div className="h-full p-4">
      <MessageList />
    </div>
  );
}

function TimelineView() {
  return (
    <div className="h-full">
      <Timeline />
    </div>
  );
}

function SystemView() {
  return (
    <div className="h-full">
      <SystemLog />
    </div>
  );
}

// 各ページコンポーネントのエクスポート
export function TasksPage() {
  return <TasksView />;
}

export function MessagesPage() {
  return <MessagesView />;
}

export function TimelinePage() {
  return <TimelineView />;
}

export function SystemPage() {
  return <SystemView />;
}
