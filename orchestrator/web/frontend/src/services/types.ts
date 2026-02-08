/**
 * 型定義
 *
 * orchestrator-ccバックエンドとの通信で使用する型定義
 */

// ============================================================================
// エニュメレーション
// ============================================================================

/** メッセージのカテゴリ */
export const enum MessageCategory {
  ACTION = "action",
  THINKING = "thinking",
  EMOTION = "emotion",
}

/** 感情タイプ */
export const enum EmotionType {
  CONFUSION = "confusion",
  SATISFACTION = "satisfaction",
  FOCUS = "focus",
  CONCERN = "concern",
  NEUTRAL = "neutral",
}

/** タスクステータス */
export const enum TaskStatus {
  PENDING = "pending",
  IN_PROGRESS = "in_progress",
  COMPLETED = "completed",
}

/** エージェントステータス */
export const enum AgentStatus {
  RUNNING = "running",
  IDLE = "idle",
  STOPPED = "stopped",
  ERROR = "error",
  UNKNOWN = "unknown",
}

// ============================================================================
// データモデル
// ============================================================================

/** 性格パラメータ */
export interface Personality {
  socialibility: number;  // 社交性（0-100）
  cautiousness: number;   // 慎重さ（0-100）
  humor: number;         // ユーモア（0-100）
  curiosity: number;     // 好奇心（0-100）
  friendliness: number;   // 親しさやすさ（0-100）
}

/** チームメンバー情報 */
export interface TeamMember {
  agentId: string;
  name: string;
  agentType: string;
  model: string;
  joinedAt: number;
  cwd: string;
  personality?: Personality;
}

/** チーム情報 */
export interface TeamInfo {
  name: string;
  description: string;
  createdAt: number;
  leadAgentId: string;
  leadSessionId: string;
  members: TeamMember[];
}

/** チームメッセージ */
export interface TeamMessage {
  id: string;
  sender: string;
  recipient: string;
  content: string;
  timestamp: string;
  messageType: string;
}

/** 思考ログ */
export interface ThinkingLog {
  agentName: string;
  content: string;
  timestamp: string;
  category: MessageCategory;
  emotion: EmotionType;
  taskDetails?: {
    status: string;
    taskId?: string;
  };
}

/** タスク情報 */
export interface TaskInfo {
  taskId: string;
  subject: string;
  description: string;
  status: TaskStatus;
  owner: string;
  blockedBy?: string[];
  blocks?: string[];
  createdAt?: string;
  updatedAt?: string;
}

/** エージェント情報 */
export interface AgentInfo {
  name: string;
  role: string;
  status: AgentStatus;
  lastActivity: string | null;
  taskCount: number;
}

/** システムログ */
export interface SystemLog {
  timestamp: string | null;
  level: "info" | "success" | "warning" | "error";
  content: string;
}

/** ヘルスイベント */
export interface HealthEvent {
  agentName: string;
  teamName: string;
  status: string;
  timestamp: string;
  details?: Record<string, unknown>;
}

// ============================================================================
// WebSocketメッセージ型
// ============================================================================

/** WebSocketメッセージのベース型 */
export interface BaseWebSocketMessage {
  type: string;
}

/** 接続確立メッセージ */
export interface ConnectedMessage extends BaseWebSocketMessage {
  type: "connected";
  message: string;
}

/** 購読確定メッセージ */
export interface SubscribedMessage extends BaseWebSocketMessage {
  type: "subscribed";
  channels: string[];
}

/** Pongメッセージ */
export interface PongMessage extends BaseWebSocketMessage {
  type: "pong";
  timestamp?: number;
}

/** Pingメッセージ */
export interface PingMessage extends BaseWebSocketMessage {
  type: "ping";
  timestamp: number;
}

/** Subscribeメッセージ */
export interface SubscribeMessage extends BaseWebSocketMessage {
  type: "subscribe";
  channels: string[];
}

/** ステータスメッセージ */
export interface StatusMessage extends BaseWebSocketMessage {
  type: "status";
  agent: string;
  status: string;
}

/** エージェントメッセージ */
export interface AgentMessage extends BaseWebSocketMessage {
  type: "message" | "task" | "result" | "idle_notification";
  timestamp: string;
  fromAgent?: string;
  toAgent?: string;
  content: string;
}

/** 思考メッセージ */
export interface ThinkingMessage extends BaseWebSocketMessage {
  type: "thinking";
  timestamp: string;
  agent: string;
  content: string;
}

/** エージェント一覧メッセージ */
export interface AgentsMessage extends BaseWebSocketMessage {
  type: "agents";
  agents: AgentInfo[];
  clusterName?: string;
}

/** エラーメッセージ */
export interface ErrorMessage extends BaseWebSocketMessage {
  type: "error";
  message: string;
}

/** システムログメッセージ */
export interface SystemLogMessage extends BaseWebSocketMessage {
  type: "system_log";
  timestamp: string | null;
  level: "info" | "success" | "warning" | "error";
  content: string;
}

/** クラスタイベントメッセージ */
export interface ClusterEventMessage extends BaseWebSocketMessage {
  type: "cluster_event";
  event: string;
  data?: Record<string, unknown>;
}

/** チーム作成メッセージ */
export interface TeamCreatedMessage extends BaseWebSocketMessage {
  type: "team_created";
  teamName: string;
  team: TeamInfo;
}

/** チーム削除メッセージ */
export interface TeamDeletedMessage extends BaseWebSocketMessage {
  type: "team_deleted";
  teamName: string;
}

/** チーム更新メッセージ */
export interface TeamUpdatedMessage extends BaseWebSocketMessage {
  type: "team_updated";
  teamName: string;
  team: TeamInfo;
}

/** チームメッセージ */
export interface TeamMessageMessage extends BaseWebSocketMessage {
  type: "team_message";
  teamName: string;
  message: TeamMessage;
}

/** 思考ログメッセージ */
export interface ThinkingLogMessage extends BaseWebSocketMessage {
  type: "thinking_log";
  teamName: string;
  log: ThinkingLog;
}

/** タスク更新メッセージ */
export interface TasksUpdatedMessage extends BaseWebSocketMessage {
  type: "tasks_updated";
  teamName: string;
  tasks: TaskInfo[];
}

/** ヘルスイベントメッセージ */
export interface HealthEventMessage extends BaseWebSocketMessage {
  type: "health_event";
  event: HealthEvent;
}

/** WebSocketメッセージの共用体型 */
export type WebSocketMessage =
  | ConnectedMessage
  | SubscribedMessage
  | SubscribeMessage
  | PongMessage
  | PingMessage
  | StatusMessage
  | AgentMessage
  | ThinkingMessage
  | AgentsMessage
  | ErrorMessage
  | SystemLogMessage
  | ClusterEventMessage
  | TeamCreatedMessage
  | TeamDeletedMessage
  | TeamUpdatedMessage
  | TeamMessageMessage
  | ThinkingLogMessage
  | TasksUpdatedMessage
  | HealthEventMessage;

// ============================================================================
// APIリクエスト/レスポンス型
// ============================================================================

/** チーム一覧APIレスポンス */
export interface GetTeamsResponse {
  teams: TeamInfo[];
}

/** チームメッセージAPIレスポンス */
export interface GetTeamMessagesResponse {
  teamName: string;
  messages: TeamMessage[];
}

/** チームタスクAPIレスポンス */
export interface GetTeamTasksResponse {
  teamName: string;
  tasks: TaskInfo[];
}

/** チーム思考ログAPIレスポンス */
export interface GetTeamThinkingResponse {
  teamName: string;
  agent?: string;
  thinking: ThinkingLog[];
}

/** チームステータスAPIレスポンス */
export interface GetTeamStatusResponse {
  name: string;
  status: string;
  members: TeamMember[];
}

/** ヘルスステータスAPIレスポンス */
export interface GetHealthStatusResponse {
  isRunning: boolean;
  events: HealthEvent[];
}

/** APIエラーレスポンス */
export interface ApiErrorResponse {
  error: string;
}
