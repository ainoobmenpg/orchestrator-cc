/**
 * Appコンポーネント
 *
 * アプリケーションのルートコンポーネントです
 */

import { useEffect } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { ErrorBoundary } from "./components/error/ErrorBoundary";
import { SkipLink } from "./components/common/SkipLink";
import { LiveRegionContainer } from "./components/common/LiveRegion";
import { MainLayout } from "./components/layout/MainLayout";
import { DashboardPage } from "./pages/DashboardPage";
import { setupGlobalErrorHandlers } from "./services/errorHandler";

// グローバルエラーハンドラーをセットアップ
setupGlobalErrorHandlers();

// React Queryクライアントの作成
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      gcTime: 1000 * 60 * 5, // 5分間キャッシュ
    },
  },
});

function App() {
  // マウント時にWebSocketクライアントを初期化
  useEffect(() => {
    // WebSocket接続の初期化はuseWebSocketフックで行われます
    // ここではグローバルエラーハンドラーのセットアップのみ行います
  }, []);

  return (
    <ErrorBoundary onError={undefined}>
      {/* スキップリンク - キーボードユーザー向け */}
      <SkipLink targetId="main-content" />

      {/* Live Region - スクリーンリーダー用通知エリア */}
      <LiveRegionContainer />

      <QueryClientProvider client={queryClient}>
        <MainLayout>
          <main id="main-content" tabIndex={-1}>
            <DashboardPage />
            {/* タブによる切り替えは UIStore で管理 */}
            {/* 実際のページ表示は DashboardPage 内で制御 */}
          </main>
        </MainLayout>
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
