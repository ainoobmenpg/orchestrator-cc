/**
 * MainLayoutコンポーネント
 *
 * ダッシュボードのメインレイアウトを提供します
 */

import type { ReactNode } from "react";
import { Header } from "./Header";
import { Footer } from "./Footer";
import { TabNav } from "../dashboard/TabNav";
import { NotificationContainer } from "../common/NotificationContainer";

interface MainLayoutProps {
  children: ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
  return (
    <div className="flex h-screen flex-col bg-background text-foreground">
      <Header />
      <TabNav />
      <main className="flex-1 overflow-hidden">
        {children}
      </main>
      <Footer />
      <NotificationContainer />
    </div>
  );
}
