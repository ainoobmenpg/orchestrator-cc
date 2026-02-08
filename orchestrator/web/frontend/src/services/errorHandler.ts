/**
 * グローバルエラーハンドラー
 *
 * WebSocketエラー、APIエラー、予期しないエラーを一元的に管理し、
 * 通知システムを通じてユーザーに通知します
 */

import { useUIStore } from "../stores/uiStore";
import type { NotificationType } from "../stores/uiStore";

// ============================================================================
// 型定義
// ============================================================================

/** エラーの種類 */
export type ErrorCategory =
  | "websocket"
  | "api"
  | "network"
  | "validation"
  | "authentication"
  | "unknown";

/** エラーコンテキスト */
export interface ErrorContext {
  /** エラーの種類 */
  category: ErrorCategory;
  /** エラーメッセージ */
  message: string;
  /** 元のエラーオブジェクト */
  error?: Error | unknown;
  /** 追加情報 */
  metadata?: Record<string, unknown>;
  /** 通知タイプ（省略時は自動判定） */
  notificationType?: NotificationType;
  /** 通知の持続時間（ミリ秒） */
  duration?: number;
}

/** エラーハンドラーの設定 */
interface ErrorHandlerConfig {
  /** エラーをコンソールに出力するか */
  logToConsole: boolean;
  /** 通知を表示するか */
  showNotification: boolean;
  /** エラーを詳細に記録するか（開発モード） */
  verboseLogging: boolean;
}

// ============================================================================
// デフォルト設定
// ============================================================================

const DEFAULT_CONFIG: ErrorHandlerConfig = {
  logToConsole: true,
  showNotification: true,
  verboseLogging: import.meta.env.DEV,
};

// ============================================================================
// ErrorHandlerクラス
// ============================================================================

class ErrorHandler {
  private config: ErrorHandlerConfig;
  private errorCounts = new Map<string, number>();

  constructor(config: ErrorHandlerConfig = DEFAULT_CONFIG) {
    this.config = config;
  }

  /**
   * エラーを処理する
   */
  handle(context: ErrorContext): void {
    const { category, message, error, metadata, notificationType, duration } = context;

    // エラーカウントの更新（重複通知の抑制）
    const errorKey = `${category}:${message}`;
    const count = (this.errorCounts.get(errorKey) || 0) + 1;
    this.errorCounts.set(errorKey, count);

    // 5回以上同じエラーが発生した場合は通知を抑制
    if (count > 5 && count % 10 !== 0) {
      return;
    }

    // コンソールに出力
    if (this.config.logToConsole) {
      this.logToConsole(category, message, error, metadata);
    }

    // 通知を表示
    if (this.config.showNotification) {
      this.showNotification(
        notificationType || this.inferNotificationType(category),
        this.formatMessage(message, category, count),
        duration,
      );
    }
  }

  /**
   * WebSocketエラーを処理する
   */
  handleWebSocketError(
    message: string,
    error?: Error | unknown,
    metadata?: Record<string, unknown>,
  ): void {
    const context: ErrorContext = {
      category: "websocket",
      message,
      notificationType: "warning",
      duration: 5000,
    };
    if (error !== undefined) context.error = error;
    if (metadata !== undefined) context.metadata = metadata;

    this.handle(context);
  }

  /**
   * APIエラーを処理する
   */
  handleApiError(
    message: string,
    error?: Error | unknown,
    metadata?: Record<string, unknown>,
  ): void {
    const context: ErrorContext = {
      category: "api",
      message,
      notificationType: "error",
      duration: 5000,
    };
    if (error !== undefined) context.error = error;
    if (metadata !== undefined) context.metadata = metadata;

    this.handle(context);
  }

  /**
   * ネットワークエラーを処理する
   */
  handleNetworkError(
    message: string,
    error?: Error | unknown,
    metadata?: Record<string, unknown>,
  ): void {
    const context: ErrorContext = {
      category: "network",
      message,
      notificationType: "warning",
      duration: 7000,
    };
    if (error !== undefined) context.error = error;
    if (metadata !== undefined) context.metadata = metadata;

    this.handle(context);
  }

  /**
   * 検証エラーを処理する
   */
  handleValidationError(
    message: string,
    metadata?: Record<string, unknown>,
  ): void {
    const context: ErrorContext = {
      category: "validation",
      message,
      notificationType: "info",
      duration: 3000,
    };
    if (metadata !== undefined) context.metadata = metadata;

    this.handle(context);
  }

  /**
   * 認証エラーを処理する
   */
  handleAuthenticationError(
    message: string,
    error?: Error | unknown,
    metadata?: Record<string, unknown>,
  ): void {
    const context: ErrorContext = {
      category: "authentication",
      message,
      notificationType: "error",
      duration: 10000,
    };
    if (error !== undefined) context.error = error;
    if (metadata !== undefined) context.metadata = metadata;

    this.handle(context);
  }

  /**
   * 通知を表示する
   */
  private showNotification(
    type: NotificationType,
    message: string,
    duration?: number,
  ): void {
    try {
      useUIStore.getState().addNotification(type, message, duration);
    } catch (err) {
      // uiStoreが利用できない場合はフォールバック
      console.error("通知の表示に失敗しました:", err);
      // フォールバックとしてalert（開発モードのみ）
      if (import.meta.env.DEV) {
         
        alert(`[${type}] ${message}`);
      }
    }
  }

  /**
   * コンソールに出力する
   */
  private logToConsole(
    category: ErrorCategory,
    message: string,
    error?: Error | unknown,
    metadata?: Record<string, unknown>,
  ): void {
    const prefix = `[${category.toUpperCase()}]`;

    if (metadata && this.config.verboseLogging) {
      const metadataStr = JSON.stringify(metadata, null, 2);
      switch (category) {
        case "websocket":
        case "network":
          console.warn(prefix, message, error, `\nMetadata: ${metadataStr}`);
          break;
        case "api":
        case "authentication":
          console.error(prefix, message, error, `\nMetadata: ${metadataStr}`);
          break;
        default:
          console.log(prefix, message, error, `\nMetadata: ${metadataStr}`);
      }
    } else {
      switch (category) {
        case "websocket":
        case "network":
          console.warn(prefix, message, error);
          break;
        case "api":
        case "authentication":
          console.error(prefix, message, error);
          break;
        default:
          console.log(prefix, message, error);
      }
    }
  }

  /**
   * エラーカテゴリから通知タイプを推測する
   */
  private inferNotificationType(category: ErrorCategory): NotificationType {
    switch (category) {
      case "websocket":
        return "warning";
      case "api":
        return "error";
      case "network":
        return "warning";
      case "validation":
        return "info";
      case "authentication":
        return "error";
      default:
        return "error";
    }
  }

  /**
   * メッセージをフォーマットする
   */
  private formatMessage(
    message: string,
    _category: ErrorCategory,
    count: number,
  ): string {
    if (count > 1) {
      return `${message} (${count}回発生)`;
    }
    return message;
  }

  /**
   * エラーカウントをリセットする
   */
  resetErrorCounts(): void {
    this.errorCounts.clear();
  }

  /**
   * 設定を更新する
   */
  updateConfig(config: Partial<ErrorHandlerConfig>): void {
    this.config = { ...this.config, ...config };
  }
}

// ============================================================================
// シングルトンインスタンス
// ============================================================================

const globalErrorHandler = new ErrorHandler();

export { globalErrorHandler as errorHandler };

// ============================================================================
// ユーティリティ関数
// ============================================================================

/**
 * 非同期関数のエラーをハンドリングするヘルパー
 */
export async function withErrorHandling<T>(
  fn: () => Promise<T>,
  context: Partial<ErrorContext>,
): Promise<T | null> {
  try {
    return await fn();
  } catch (error) {
    const errorContext: ErrorContext = {
      category: context.category ?? "unknown",
      message: context.message ?? "処理中にエラーが発生しました",
      error,
    };
    if (context.metadata !== undefined) errorContext.metadata = context.metadata;
    if (context.notificationType !== undefined) errorContext.notificationType = context.notificationType;
    if (context.duration !== undefined) errorContext.duration = context.duration;

    globalErrorHandler.handle(errorContext);
    return null;
  }
}

/**
 * 同期関数のエラーをハンドリングするヘルパー
 */
export function withSyncErrorHandling<T>(
  fn: () => T,
  context: Partial<ErrorContext>,
): T | null {
  try {
    return fn();
  } catch (error) {
    const errorContext: ErrorContext = {
      category: context.category ?? "unknown",
      message: context.message ?? "処理中にエラーが発生しました",
      error,
    };
    if (context.metadata !== undefined) errorContext.metadata = context.metadata;
    if (context.notificationType !== undefined) errorContext.notificationType = context.notificationType;
    if (context.duration !== undefined) errorContext.duration = context.duration;

    globalErrorHandler.handle(errorContext);
    return null;
  }
}

// ============================================================================
// グローバルエラーハンドラーの設定
// ============================================================================

/**
 * グローバルな未キャッチエラーを処理する
 */
export function setupGlobalErrorHandlers(): void {
  // 未処理のPromise rejectionをキャッチ
  window.addEventListener("unhandledrejection", (event) => {
    console.error("未処理のPromise rejection:", event.reason);
    globalErrorHandler.handle({
      category: "unknown",
      message: "予期しないエラーが発生しました",
      error: event.reason,
    });
  });

  // 未処理のエラーをキャッチ
  window.addEventListener("error", (event) => {
    console.error("未処理のエラー:", event.error);
    globalErrorHandler.handle({
      category: "unknown",
      message: "予期しないエラーが発生しました",
      error: event.error,
    });
  });
}
