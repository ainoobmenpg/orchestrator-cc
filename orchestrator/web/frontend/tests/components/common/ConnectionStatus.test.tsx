/**
 * ConnectionStatusコンポーネントのテスト
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ConnectionStatus } from "@/components/common/ConnectionStatus";

describe("ConnectionStatus", () => {
  it("接続中のステータスを表示する", () => {
    render(<ConnectionStatus state="connecting" />);
    expect(screen.getByText("接続中...")).toBeInTheDocument();
  });

  it("接続済みのステータスを表示する", () => {
    render(<ConnectionStatus state="connected" />);
    expect(screen.getByText("接続中")).toBeInTheDocument();
  });

  it("切断のステータスを表示する", () => {
    render(<ConnectionStatus state="disconnected" />);
    expect(screen.getByText("切断中")).toBeInTheDocument();
  });

  it("エラーのステータスを表示する", () => {
    render(<ConnectionStatus state="error" />);
    expect(screen.getByText("エラー")).toBeInTheDocument();
  });

  it("aria-live属性を持つ", () => {
    const { container } = render(<ConnectionStatus state="connected" />);
    const statusElement = container.querySelector('[aria-live="polite"]');
    expect(statusElement).toBeInTheDocument();
  });
});
