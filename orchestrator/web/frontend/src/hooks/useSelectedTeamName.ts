/**
 * 選択中のチーム名を管理するカスタムフック
 * シンプルな localStorage 管理のみ
 */

import { useState, useCallback } from "react";

const STORAGE_KEY = "selectedTeamName";

/**
 * 選択中のチーム名を管理するフック
 */
export function useSelectedTeamName() {
  const [selectedTeamName, setSelectedTeamNameState] = useState<string | null>(() => {
    try {
      return localStorage.getItem(STORAGE_KEY) || null;
    } catch {
      return null;
    }
  });

  const setSelectedTeamName = useCallback((teamName: string | null) => {
    setSelectedTeamNameState(teamName);
    try {
      if (teamName) {
        localStorage.setItem(STORAGE_KEY, teamName);
      } else {
        localStorage.removeItem(STORAGE_KEY);
      }
    } catch (e) {
      console.error("Failed to save selectedTeamName to localStorage:", e);
    }
  }, []);

  return { selectedTeamName, setSelectedTeamName };
}
