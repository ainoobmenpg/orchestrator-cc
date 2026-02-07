/**
 * AgentPanelコンポーネント
 *
 * エージェントの状態を表示するパネルです
 */

import { Bot, ChevronDown, ChevronUp, RefreshCw, RotateCcw, Power } from "lucide-react";
import { useState, useCallback, useMemo } from "react";
import { useTeamStore } from "../../stores/teamStore";
import { useAgentStats } from "../../hooks/useAgents";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { cn } from "../../lib/utils";
import { formatRelativeTime } from "../../lib/utils";
import type { AgentStatus } from "../../services/types";

const statusConfig: Record<AgentStatus, { label: string; variant: "success" | "warning" | "error" | "secondary" }> = {
  running: { label: "実行中", variant: "success" },
  idle: { label: "アイドル", variant: "secondary" },
  stopped: { label: "停止", variant: "error" },
  error: { label: "エラー", variant: "error" },
  unknown: { label: "不明", variant: "secondary" },
};

export function AgentPanel() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const agents = useTeamStore((state) => Array.from(state.agents.values()));
  const stats = useAgentStats();

  const handleRefresh = useCallback(() => {
    // TODO: エージェント情報を再取得
  }, []);

  const toggleCollapse = useCallback(() => {
    setIsCollapsed((prev) => !prev);
  }, []);

  // エージェントリストをステータス別にフィルタリング（キャッシュ用）
  const filteredAgents = useMemo(() => agents, [agents]);

  return (
    <Card className={cn("transition-all duration-300", isCollapsed && "w-16")}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
        {!isCollapsed && (
          <CardTitle className="text-lg">エージェント状態</CardTitle>
        )}
        <div className="flex items-center gap-2">
          <Button
            variant="icon"
            size="sm"
            onClick={handleRefresh}
            title="更新"
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Button
            variant="icon"
            size="sm"
            onClick={toggleCollapse}
            title={isCollapsed ? "展開" : "折りたたみ"}
          >
            {isCollapsed ? (
              <ChevronUp className="h-4 w-4 rotate-180" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>
        </div>
      </CardHeader>

      {!isCollapsed && (
        <CardContent className="space-y-4">
          {/* クラスタ制御ボタン */}
          <div className="flex flex-col gap-2">
            <Button variant="secondary" size="sm">
              <RotateCcw className="h-4 w-4" />
              クラスタ再起動
            </Button>
            <Button variant="danger" size="sm">
              <Power className="h-4 w-4" />
              クラスタ停止
            </Button>
          </div>

          {/* エージェント一覧 */}
          <div className="space-y-2">
            {filteredAgents.length === 0 ? (
              <div className="py-8 text-center text-muted-foreground">
                エージェント情報がありません
              </div>
            ) : (
              filteredAgents.map((agent) => {
                const config = statusConfig[agent.status];
                return (
                  <div
                    key={agent.name}
                    className="flex items-center gap-3 rounded-lg border border-border bg-background p-3 hover:bg-accent/50 transition-colors"
                  >
                    <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                      <Bot className="h-5 w-5 text-primary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium truncate">{agent.name}</span>
                        <Badge variant={config.variant}>{config.label}</Badge>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <span>{agent.role}</span>
                        <span>•</span>
                        <span>{agent.taskCount} タスク</span>
                      </div>
                    </div>
                    {agent.lastActivity && (
                      <span className="text-xs text-muted-foreground">
                        {formatRelativeTime(agent.lastActivity)}
                      </span>
                    )}
                  </div>
                );
              })
            )}
          </div>

          {/* 統計情報 */}
          <div className="flex justify-around pt-4 border-t border-border">
            <div className="text-center">
              <div className="text-2xl font-bold">{stats.total}</div>
              <div className="text-xs text-muted-foreground">総数</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-500">{stats.running}</div>
              <div className="text-xs text-muted-foreground">実行中</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-500">{stats.error}</div>
              <div className="text-xs text-muted-foreground">エラー</div>
            </div>
          </div>
        </CardContent>
      )}
    </Card>
  );
}
