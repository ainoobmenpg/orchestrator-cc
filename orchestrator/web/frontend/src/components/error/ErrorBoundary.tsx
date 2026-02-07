/**
 * ErrorBoundaryコンポーネント
 *
 * Reactコンポーネントツリー内で発生したJavaScriptエラーをキャッチし、
 * フォールバックUIを表示します
 *
 * 参考: https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary
 */

import { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";
import { Button } from "../ui/Button";
import { useUIStore } from "../../stores/uiStore";

interface ErrorBoundaryProps {
  /** 子コンポーネント */
  children: ReactNode;
  /** エラー時に表示するフォールバックUI */
  fallback?: ReactNode;
  /** エラー発生時のコールバック */
  onError: ((error: Error, errorInfo: ErrorInfo) => void) | undefined;
  /** クラス名 */
  className?: string;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * デフォルトのエラー表示コンポーネント
 */
interface DefaultErrorFallbackProps {
  error: Error | null;
  resetError: () => void;
}

function DefaultErrorFallback({ error, resetError }: DefaultErrorFallbackProps) {
  return (
    <div className="flex min-h-[400px] items-center justify-center p-4">
      <div className="flex max-w-md flex-col items-center text-center">
        {/* エラーアイコン */}
        <div className="mb-6 rounded-full bg-destructive/10 p-6">
          <AlertTriangle className="h-16 w-16 text-destructive" />
        </div>

        {/* エラーメッセージ */}
        <h1 className="mb-2 text-2xl font-bold text-foreground">
          予期しないエラーが発生しました
        </h1>
        <p className="mb-6 text-muted-foreground">
          申し訳ありません。アプリケーションでエラーが発生しました。
          {error?.message && (
            <span className="mt-2 block text-sm">
              エラー詳細: {error.message}
            </span>
          )}
        </p>

        {/* アクションボタン */}
        <div className="flex flex-col gap-3 sm:flex-row">
          <Button
            onClick={resetError}
            variant="default"
            className="flex items-center gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            リロード
          </Button>
          <Button
            onClick={() => (window.location.href = "/")}
            variant="ghost"
            className="flex items-center gap-2"
          >
            <Home className="h-4 w-4" />
            ホームに戻る
          </Button>
        </div>

        {/* 開発者向け情報（開発環境のみ） */}
        {import.meta.env.DEV && error?.stack && (
          <details className="mt-6 w-full text-left">
            <summary className="cursor-pointer text-sm font-medium text-muted-foreground hover:text-foreground">
              スタックトレース（開発モード）
            </summary>
            <pre className="mt-2 overflow-auto rounded-md bg-muted p-4 text-xs">
              {error.stack}
            </pre>
          </details>
        )}
      </div>
    </div>
  );
}

/**
 * ErrorBoundaryクラスコンポーネント
 */
export class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
    this.handleReset = this.handleReset.bind(this);
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
    };
  }

  override componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // エラー情報を状態に保存
    this.setState({
      error,
      errorInfo,
    });

    // コンソールに出力
    console.error("ErrorBoundary caught an error:", error, errorInfo);

    // エラーハンドラーを呼び出し
    this.props.onError?.(error, errorInfo);

    // 通知システムにエラーを送信（uiStoreが利用可能な場合）
    try {
      useUIStore?.getState().addNotification(
        "error",
        `エラーが発生しました: ${error.message}`,
        5000,
      );
    } catch {
      // uiStoreが利用できない場合は無視
    }
  }

  handleReset(): void {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
    // ページをリロード
    window.location.reload();
  }

  override render(): ReactNode {
    if (this.state.hasError) {
      // カスタムフォールバックが提供されている場合は使用
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // デフォルトのエラー表示
      return <DefaultErrorFallback error={this.state.error} resetError={this.handleReset} />;
    }

    return this.props.children;
  }
}

/**
 * 関数コンポーネント用のErrorBoundaryラッパー
 *
 * 使用例:
 * ```tsx
 * <WithErrorBoundary>
 *   <YourComponent />
 * </WithErrorBoundary>
 * ```
 */
interface WithErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

export function WithErrorBoundary({
  children,
  fallback,
  onError,
}: WithErrorBoundaryProps) {
  return (
    <ErrorBoundary fallback={fallback} onError={onError}>
      {children}
    </ErrorBoundary>
  );
}
