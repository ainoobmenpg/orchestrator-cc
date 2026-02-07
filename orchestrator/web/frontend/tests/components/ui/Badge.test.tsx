/**
 * Badgeコンポーネントのテスト
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Badge } from "@/components/ui/Badge";

describe("Badge", () => {
  it("基本のバッジをレンダリングできる", () => {
    render(<Badge>テスト</Badge>);
    expect(screen.getByText("テスト")).toBeInTheDocument();
  });

  it("variantに応じたスタイルが適用される", () => {
    const { rerender } = render(<Badge variant="primary">Primary</Badge>);
    expect(screen.getByText("Primary")).toHaveClass("bg-primary");

    rerender(<Badge variant="secondary">Secondary</Badge>);
    expect(screen.getByText("Secondary")).toHaveClass("bg-secondary");

    rerender(<Badge variant="success">Success</Badge>);
    expect(screen.getByText("Success")).toHaveClass("bg-green-500");

    rerender(<Badge variant="warning">Warning</Badge>);
    expect(screen.getByText("Warning")).toHaveClass("bg-yellow-500");

    rerender(<Badge variant="error">Error</Badge>);
    expect(screen.getByText("Error")).toHaveClass("bg-red-500");
  });

  it("outline variantで正しく表示される", () => {
    render(<Badge variant="outline">Outline</Badge>);
    expect(screen.getByText("Outline")).toHaveClass("border");
  });
});
