/**
 * APIクライアント
 *
 * orchestrator-ccバックエンドとのHTTP通信を担当します
 */

import type {
  ApiErrorResponse,
  GetHealthStatusResponse,
  GetTeamMessagesResponse,
  GetTeamStatusResponse,
  GetTeamTasksResponse,
  GetTeamThinkingResponse,
  GetTeamsResponse,
  TeamInfo,
} from "./types";

// ============================================================================
// 設定
// ============================================================================

const API_BASE_URL = "/api";

// ============================================================================
// ユーティリティ関数
// ============================================================================

/**
 * APIリクエストを実行する
 */
async function fetchApi<T>(
  endpoint: string,
  options?: RequestInit,
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    let errorMessage = `APIエラー: ${response.status} ${response.statusText}`;
    try {
      const errorData = (await response.json()) as ApiErrorResponse;
      if (errorData.error) {
        errorMessage = errorData.error;
      }
    } catch {
      // JSONパースエラーは無視
    }
    throw new Error(errorMessage);
  }

  return response.json() as Promise<T>;
}

// ============================================================================
// チームAPI
// ============================================================================

/**
 * チーム一覧を取得する
 */
export async function getTeams(): Promise<TeamInfo[]> {
  const response = await fetchApi<GetTeamsResponse>("/teams");
  return response.teams;
}

/**
 * チームのメッセージ一覧を取得する
 */
export async function getTeamMessages(
  teamName: string,
): Promise<import("./types").TeamMessage[]> {
  const response = await fetchApi<GetTeamMessagesResponse>(
    `/teams/${encodeURIComponent(teamName)}/messages`,
  );
  return response.messages;
}

/**
 * チームのタスクリストを取得する
 */
export async function getTeamTasks(
  teamName: string,
): Promise<import("./types").TaskInfo[]> {
  const response = await fetchApi<GetTeamTasksResponse>(
    `/teams/${encodeURIComponent(teamName)}/tasks`,
  );
  return response.tasks;
}

/**
 * チームの思考ログを取得する
 */
export async function getTeamThinking(
  teamName: string,
  agent?: string,
): Promise<import("./types").ThinkingLog[]> {
  const params = new URLSearchParams();
  if (agent) {
    params.set("agent", agent);
  }

  const queryString = params.toString();
  const endpoint = `/teams/${encodeURIComponent(teamName)}/thinking${queryString ? `?${queryString}` : ""}`;

  const response = await fetchApi<GetTeamThinkingResponse>(endpoint);
  return response.thinking;
}

/**
 * チームのステータスを取得する
 */
export async function getTeamStatus(teamName: string): Promise<GetTeamStatusResponse> {
  return fetchApi<GetTeamStatusResponse>(
    `/teams/${encodeURIComponent(teamName)}/status`,
  );
}

/**
 * エージェントのアクティビティを更新する
 */
export async function updateAgentActivity(
  teamName: string,
  agentName: string,
): Promise<{ message: string }> {
  return fetchApi<{ message: string }>(
    `/teams/${encodeURIComponent(teamName)}/activity`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ agent_name: agentName }),
    },
  );
}

// ============================================================================
// ヘルスモニターAPI
// ============================================================================

/**
 * ヘルスステータスを取得する
 */
export async function getHealthStatus(): Promise<GetHealthStatusResponse> {
  return fetchApi<GetHealthStatusResponse>("/health");
}

/**
 * ヘルスモニタリングを開始する
 */
export async function startHealthMonitoring(): Promise<{ message: string }> {
  return fetchApi<{ message: string }>("/health/start", {
    method: "POST",
  });
}

/**
 * ヘルスモニタリングを停止する
 */
export async function stopHealthMonitoring(): Promise<{ message: string }> {
  return fetchApi<{ message: string }>("/health/stop", {
    method: "POST",
  });
}

// ============================================================================
// チーム監視API
// ============================================================================

/**
 * チーム監視を開始する
 */
export async function startTeamsMonitoring(): Promise<{ message: string }> {
  return fetchApi<{ message: string }>("/teams/monitoring/start", {
    method: "POST",
  });
}

/**
 * チーム監視を停止する
 */
export async function stopTeamsMonitoring(): Promise<{ message: string }> {
  return fetchApi<{ message: string }>("/teams/monitoring/stop", {
    method: "POST",
  });
}
