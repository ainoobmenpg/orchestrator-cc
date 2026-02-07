/**
 * Buttonコンポーネントのテスト
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Button } from "@/components/ui/Button";

describe("Button", () => {
  it("基本のボタンをレンダリングできる", () => {
    render(<Button>クリック</Button>);
    expect(screen.getByRole("button")).toHaveTextContent("クリック");
  });

  it("クリックイベントを発火できる", async () => {
    const handleClick = vi.fn();
    const user = userEvent.setup();

    render(<Button onClick={handleClick}>クリック</Button>);

    await user.click(screen.getByRole("button"));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("disabledのときクリックできない", async () => {
    const handleClick = vi.fn();
    const user = userEvent.setup();

    render(
      <Button onClick={handleClick} disabled>
        クリック
      </Button>
    );

    await user.click(screen.getByRole("button"));
    expect(handleClick).not.toHaveBeenCalled();
  });

  it("variantに応じたクラスが適用される", () => {
    const { rerender } = render(<Button variant="primary">Primary</Button>);
    expect(screen.getByRole("button")).toHaveClass("bg-primary");

    rerender(<Button variant="secondary">Secondary</Button>);
    expect(screen.getByRole("button")).toHaveClass("bg-secondary");

    rerender(<Button variant="danger">Danger</Button>);
    expect(screen.getByRole("button")).toHaveClass("bg-destructive");
  });

  it("sizeに応じたクラスが適用される", () => {
    const { rerender } = render(<Button size="sm">Small</Button>);
    expect(screen.getByRole("button")).toHaveClass("h-8");

    rerender(<Button size="md">Medium</Button>);
    expect(screen.getByRole("button")).toHaveClass("h-9");

    rerender(<Button size="lg">Large</Button>);
    expect(screen.getByRole("button")).toHaveClass("h-10");
  });
});
