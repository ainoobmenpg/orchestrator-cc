/**
 * ErrorStateコンポーネント
 *
 * 汎用的なエラー状態を表示するコンポーネントです
 * 404、500、WebSocket接続エラーなどの様々なエラー状態に対応します
 */

import { AlertTriangle, WifiOff, ServerCrash, FileQuestion } from "lucide-react";
import { Button } from "../ui/Button";
import { cn } from "../../lib/utils";

/** エラーの種類 */
export type ErrorType =
  | "network"
  | "server"
  | "not-found"
  | "websocket"
  | "unauthorized"
  | "generic";

interface ErrorStateProps {
  /** エラーの種類 */
  type: ErrorType;
  /** エラーメッセージ */
  message?: string;
  /** 詳細な説明 */
  description?: string;
  /** リカバリーアクション */
  actions?: Array<{
    label: string;
    onClick: () => void;
    variant?: "default" | "primary" | "secondary" | "danger" | "ghost" | "icon";
  }>;
  /** クラス名 */
  className?: string | undefined;
}

/** エラータイプごとの設定 */
const ERROR_CONFIGS: Record<
  ErrorType,
  {
    icon: React.ComponentType<{ className?: string }>;
    defaultTitle: string;
    defaultDescription: string;
    bgColor: string;
    iconColor: string;
  }
> = {
  network: {
    icon: WifiOff,
    defaultTitle: "ネットワークエラー",
    defaultDescription: "ネットワーク接続を確認してください",
    bgColor: "bg-orange-500/10",
    iconColor: "text-orange-500",
  },
  server: {
    icon: ServerCrash,
    defaultTitle: "サーバーエラー",
    defaultDescription: "サーバーで問題が発生しています。しばらく待ってから再試行してください",
    bgColor: "bg-red-500/10",
    iconColor: "text-red-500",
  },
  "not-found": {
    icon: FileQuestion,
    defaultTitle: "ページが見つかりません",
    defaultDescription: "お探しのページは存在しないか、移動しました",
    bgColor: "bg-blue-500/10",
    iconColor: "text-blue-500",
  },
  websocket: {
    icon: WifiOff,
    defaultTitle: "接続が切断されました",
    defaultDescription: "リアルタイム更新のためにサーバーに再接続してください",
    bgColor: "bg-yellow-500/10",
    iconColor: "text-yellow-500",
  },
  unauthorized: {
    icon: AlertTriangle,
    defaultTitle: "アクセス権限がありません",
    defaultDescription: "このページにアクセスする権限がありません",
    bgColor: "bg-purple-500/10",
    iconColor: "text-purple-500",
  },
  generic: {
    icon: AlertTriangle,
    defaultTitle: "エラーが発生しました",
    defaultDescription: "予期しないエラーが発生しました",
    bgColor: "bg-gray-500/10",
    iconColor: "text-gray-500",
  },
};

/**
 * ErrorStateコンポーネント
 */
export function ErrorState({
  type,
  message,
  description,
  actions,
  className,
}: ErrorStateProps) {
  const config = ERROR_CONFIGS[type];
  const Icon = config.icon;

  return (
    <div
      className={cn(
        "flex min-h-[300px] items-center justify-center p-6",
        className,
      )}
    >
      <div className="flex max-w-md flex-col items-center text-center">
        {/* アイコン */}
        <div className={cn("mb-6 rounded-full p-6", config.bgColor)}>
          <Icon className={cn("h-12 w-12", config.iconColor)} />
        </div>

        {/* タイトル */}
        <h2 className="mb-2 text-xl font-bold text-foreground">
          {message || config.defaultTitle}
        </h2>

        {/* 説明 */}
        <p className="mb-6 text-sm text-muted-foreground">
          {description || config.defaultDescription}
        </p>

        {/* アクションボタン */}
        {actions && actions.length > 0 && (
          <div className="flex flex-col gap-3 sm:flex-row">
            {actions.map((action, index) => (
              <Button
                key={index}
                onClick={action.onClick}
                variant={action.variant || "default"}
              >
                {action.label}
              </Button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * プリセットのエラー状態コンポーネント
 */

/** WebSocket接続エラー */
export function WebSocketError({
  onReconnect,
  className,
}: {
  onReconnect?: () => void;
  className?: string | undefined;
}) {
  return (
    <ErrorState
      type="websocket"
      description="リアルタイム更新のためにサーバーに再接続してください"
      actions={[
        {
          label: "再接続",
          onClick: onReconnect || (() => window.location.reload()),
          variant: "default",
        },
      ]}
      className={className}
    />
  );
}

/** 404 Not Found */
export function NotFoundError({
  onGoHome,
  className,
}: {
  onGoHome?: () => void;
  className?: string | undefined;
}) {
  return (
    <ErrorState
      type="not-found"
      actions={[
        {
          label: "ホームに戻る",
          onClick: onGoHome || (() => (window.location.href = "/")),
          variant: "ghost",
        },
      ]}
      className={className}
    />
  );
}

/** サーエーエラー */
export function ServerError({
  onRetry,
  className,
}: {
  onRetry?: () => void;
  className?: string | undefined;
}) {
  return (
    <ErrorState
      type="server"
      actions={[
        {
          label: "再試行",
          onClick: onRetry || (() => window.location.reload()),
          variant: "default",
        },
      ]}
      className={className}
    />
  );
}

/** ネットワークエラー */
export function NetworkError({
  onRetry,
  className,
}: {
  onRetry?: () => void;
  className?: string | undefined;
}) {
  return (
    <ErrorState
      type="network"
      actions={[
        {
          label: "再試行",
          onClick: onRetry || (() => window.location.reload()),
          variant: "default",
        },
      ]}
      className={className}
    />
  );
}
