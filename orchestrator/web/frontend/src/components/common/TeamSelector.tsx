/**
 * TeamSelectorコンポーネント
 *
 * チームを選択するドロップダウンを表示します
 */

import { useCallback, useMemo } from "react";
import { ChevronDown } from "lucide-react";
import type { TeamInfo } from "../../services/types";
import { cn } from "../../lib/utils";

interface TeamSelectorProps {
  teams: TeamInfo[];
  selectedTeamName: string | null;
  onTeamChange: (teamName: string) => void;
  className?: string;
  disabled?: boolean;
}

export function TeamSelector({
  teams,
  selectedTeamName,
  onTeamChange,
  className,
  disabled = false,
}: TeamSelectorProps) {
  const selectedTeam = useMemo(
    () => teams.find((t) => t.name === selectedTeamName),
    [teams, selectedTeamName]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      onTeamChange(e.target.value);
    },
    [onTeamChange]
  );

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <label htmlFor="team-select" className="text-sm text-muted-foreground">
        監視対象:
      </label>
      <div className="relative">
        <select
          id="team-select"
          value={selectedTeamName ?? ""}
          onChange={handleChange}
          disabled={disabled}
          aria-label="チームを選択"
          className={cn(
            "appearance-none rounded-md border border-input bg-background px-3 py-1.5 pr-8 text-sm focus:outline-none focus:ring-2 focus:ring-ring",
            "disabled:cursor-not-allowed disabled:opacity-50",
            disabled && "opacity-50",
          )}
        >
          <option value="">-- チームを選択 --</option>
          {teams.map((team) => (
            <option key={team.name} value={team.name}>
              {team.name}
            </option>
          ))}
        </select>
        <ChevronDown
          className="pointer-events-none absolute right-2 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
          aria-hidden="true"
        />
      </div>

      {selectedTeam && (
        <span className="text-xs text-muted-foreground" aria-live="polite">
          ({selectedTeam.members.length} エージェント)
        </span>
      )}
    </div>
  );
}
