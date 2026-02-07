/**
 * SummaryCardsコンポーネントのテスト
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { SummaryCards } from "@/components/dashboard/SummaryCards";

describe("SummaryCards", () => {
  it("各カードの値を正しく表示する", () => {
    render(
      <SummaryCards
        agentCount={5}
        taskCount={10}
        messageCount={20}
        hasErrors={false}
      />
    );

    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();
    expect(screen.getByText("20")).toBeInTheDocument();
    expect(screen.getByText("OK")).toBeInTheDocument();
  });

  it("エラーがあるときに!を表示する", () => {
    render(
      <SummaryCards
        agentCount={0}
        taskCount={0}
        messageCount={0}
        hasErrors={true}
      />
    );

    expect(screen.getByText("!")).toBeInTheDocument();
  });

  it("各カードのタイトルを表示する", () => {
    render(
      <SummaryCards
        agentCount={5}
        taskCount={10}
        messageCount={20}
        hasErrors={false}
      />
    );

    expect(screen.getByText("エージェント")).toBeInTheDocument();
    expect(screen.getByText("タスク")).toBeInTheDocument();
    expect(screen.getByText("メッセージ")).toBeInTheDocument();
    expect(screen.getByText("システム")).toBeInTheDocument();
  });
});
