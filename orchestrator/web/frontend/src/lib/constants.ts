/**
 * アプリケーション定数
 */

// ============================================================================
// アプリケーション情報
// ============================================================================

export const APP_NAME = "orchestrator-cc Dashboard";
export const APP_VERSION = "2.0.0";

// ============================================================================
// WebSocket設定
// ============================================================================

export const WS_RECONNECT_DELAY = 3000;
export const WS_MAX_RECONNECT_ATTEMPTS = 10;
export const WS_HEARTBEAT_INTERVAL = 15000;
export const WS_HEARTBEAT_TIMEOUT = 30000;

// ============================================================================
// データ制限
// ============================================================================

export const DEFAULT_MESSAGE_BUFFER_SIZE = 1000;
export const DEFAULT_MAX_THINKING_LOGS = 500;
export const DEFAULT_MAX_SYSTEM_LOGS = 500;

// ============================================================================
// アニメーション設定
// ============================================================================

export const ANIMATION_DURATION = {
  fast: 150,
  normal: 250,
  slow: 350,
} as const;

export const ANIMATION_EASING = {
  default: "cubic-bezier(0.4, 0, 0.2, 1)",
  in: "cubic-bezier(0.4, 0, 1, 1)",
  out: "cubic-bezier(0, 0, 0.2, 1)",
  bounce: "cubic-bezier(0.68, -0.55, 0.265, 1.55)",
} as const;

// ============================================================================
// 通知設定
// ============================================================================

export const NOTIFICATION_DURATION = {
  short: 2000,
  default: 3000,
  long: 5000,
} as const;

// ============================================================================
// レスポンシブブレークポイント（Tailwind CSSと一致）
// ============================================================================

export const BREAKPOINTS = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  "2xl": 1536,
} as const;

// ============================================================================
// ローカルストレージキー
// ============================================================================

export const STORAGE_KEYS = {
  theme: "orchestrator-cc-theme",
  fontSize: "orchestrator-cc-font-size",
  density: "orchestrator-cc-density",
  activeTab: "orchestrator-cc-active-tab",
  selectedTeam: "orchestrator-cc-selected-team",
} as const;

// ============================================================================
// APIエンドポイント
// ============================================================================

export const API_ENDPOINTS = {
  teams: "/api/teams",
  teamMessages: (teamName: string) => `/api/teams/${encodeURIComponent(teamName)}/messages`,
  teamTasks: (teamName: string) => `/api/teams/${encodeURIComponent(teamName)}/tasks`,
  teamThinking: (teamName: string) => `/api/teams/${encodeURIComponent(teamName)}/thinking`,
  teamStatus: (teamName: string) => `/api/teams/${encodeURIComponent(teamName)}/status`,
  health: "/api/health",
  healthStart: "/api/health/start",
  healthStop: "/api/health/stop",
  teamsMonitoringStart: "/api/teams/monitoring/start",
  teamsMonitoringStop: "/api/teams/monitoring/stop",
} as const;

// ============================================================================
// アイコン（lucide-react）
// ============================================================================

export const ICONS = {
  // 接続状態
  wifi: "Wifi",
  wifiOff: "WifiOff",

  // ステータス
  checkCircle: "CheckCircle2",
  xCircle: "XCircle",
  alertCircle: "AlertCircle",
  info: "Info",

  // ナビゲーション
  home: "Home",
  list: "List",
  messageSquare: "MessageSquare",
  timeline: "Timeline",
  settings: "Settings",

  // アクション
  refreshCw: "RefreshCw",
  play: "Play",
  pause: "Pause",
  stop: "Stop",
  trash: "Trash",
  download: "Download",

  // エージェント
  bot: "Bot",
  cpu: "Cpu",
  activity: "Activity",

  // タスク
  checkSquare: "CheckSquare",
  clock: "Clock",
  circle: "Circle",

  // UI
  chevronDown: "ChevronDown",
  chevronUp: "ChevronUp",
  chevronLeft: "ChevronLeft",
  chevronRight: "ChevronRight",
  x: "X",
  menu: "Menu",
  moreVertical: "MoreVertical",
  filter: "Filter",
  search: "Search",

  // ファイル
  file: "File",
  fileText: "FileText",
  folder: "Folder",

  // その他
  zap: "Zap",
  globe: "Globe",
  shield: "Shield",
  lock: "Lock",
} as const;

// ============================================================================
// 色定義（Tailwind CSSの色と一致）
// ============================================================================

export const COLORS = {
  primary: {
    DEFAULT: "hsl(var(--primary))",
    foreground: "hsl(var(--primary-foreground))",
  },
  secondary: {
    DEFAULT: "hsl(var(--secondary))",
    foreground: "hsl(var(--secondary-foreground))",
  },
  destructive: {
    DEFAULT: "hsl(var(--destructive))",
    foreground: "hsl(var(--destructive-foreground))",
  },
  muted: {
    DEFAULT: "hsl(var(--muted))",
    foreground: "hsl(var(--muted-foreground))",
  },
  accent: {
    DEFAULT: "hsl(var(--accent))",
    foreground: "hsl(var(--accent-foreground))",
  },
  success: "hsl(142 76% 36%)",
  warning: "hsl(43 96% 56%)",
  error: "hsl(0 84% 60%)",
  info: "hsl(199 89% 48%)",
} as const;

// ============================================================================
// 正規表現パターン
// ============================================================================

export const PATTERNS = {
  // JSON形式のコンテンツを検出
  jsonContent: /^\s*{/,
  // タスク割り当てメッセージ
  taskAssignment: /"type":\s*"task_assignment"/,
  // アイドル通知
  idleNotification: /"type":\s*"idle_notification"/,
} as const;

// ============================================================================
// キーボードショートカット
// ============================================================================

export const KEYBOARD_SHORTCUTS = {
  // タブ切り替え
  tabDashboard: "1",
  tabTasks: "2",
  tabMessages: "3",
  tabTimeline: "4",
  tabSystem: "5",

  // その他
  clearLogs: "Ctrl+K",
  exportLogs: "Ctrl+E",
  toggleSidebar: "Ctrl+B",
  focusSearch: "Ctrl+F",
} as const;
