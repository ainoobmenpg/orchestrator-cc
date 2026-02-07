/**
 * SummaryCardsコンポーネント
 *
 * ダッシュボードの要約カードを表示します
 */

import { memo } from "react";
import { Bot, List, MessageSquare, Activity } from "lucide-react";
import { Card, CardContent } from "../ui/Card";
import { cn } from "../../lib/utils";

interface SummaryCardProps {
  title: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  variant: "agents" | "tasks" | "messages" | "system";
  onClick?: () => void;
}

const SummaryCard = memo(function SummaryCard({ title, value, icon: Icon, variant, onClick }: SummaryCardProps) {
  const variants = {
    agents: "from-blue-500/10 to-blue-600/5 border-blue-500/20 hover:border-blue-500/40",
    tasks: "from-yellow-500/10 to-yellow-600/5 border-yellow-500/20 hover:border-yellow-500/40",
    messages: "from-cyan-500/10 to-cyan-600/5 border-cyan-500/20 hover:border-cyan-500/40",
    system: "from-purple-500/10 to-purple-600/5 border-purple-500/20 hover:border-purple-500/40",
  };

  return (
    <Card
      onClick={onClick}
      className={cn(
        "cursor-pointer bg-gradient-to-br transition-all hover:scale-[1.02]",
        variants[variant],
      )}
    >
      <CardContent className="flex flex-col items-center p-6">
        <Icon className="h-8 w-8 text-muted-foreground mb-2" />
        <div className="text-3xl font-bold">{value}</div>
        <div className="text-sm text-muted-foreground mt-1">{title}</div>
      </CardContent>
    </Card>
  );
});

interface SummaryCardsProps {
  agentCount: number;
  taskCount: number;
  messageCount: number;
  hasErrors: boolean;
}

export const SummaryCards = memo(function SummaryCards({
  agentCount,
  taskCount,
  messageCount,
  hasErrors,
}: SummaryCardsProps) {
  return (
    <div className="grid grid-cols-2 gap-4 p-4 md:grid-cols-4 lg:gap-6">
      <SummaryCard
        title="エージェント"
        value={agentCount}
        icon={Bot}
        variant="agents"
      />
      <SummaryCard
        title="タスク"
        value={taskCount}
        icon={List}
        variant="tasks"
      />
      <SummaryCard
        title="メッセージ"
        value={messageCount}
        icon={MessageSquare}
        variant="messages"
      />
      <SummaryCard
        title="システム"
        value={hasErrors ? "!" : "OK"}
        icon={Activity}
        variant="system"
      />
    </div>
  );
});
