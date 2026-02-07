/**
 * Buttonコンポーネント
 *
 * 基本的なボタンコンポーネントです
 */

import { forwardRef, type ButtonHTMLAttributes } from "react";
import { cn } from "../../lib/utils";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "primary" | "secondary" | "danger" | "ghost" | "icon";
  size?: "sm" | "md" | "lg";
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "md", ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center gap-1.5 rounded-md font-medium transition-colors",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
          "disabled:pointer-events-none disabled:opacity-50",
          // モバイル対応: 最小タッチサイズ（44x44px）とタップ時のフィードバック
          "min-h-[44px] min-w-[44px] active:scale-95",
          // スムーズなトランジション
          "transition-transform duration-100 ease-in-out",
          {
            "bg-background border border-border hover:bg-accent": variant === "default",
            "bg-primary text-primary-foreground hover:bg-primary/90": variant === "primary",
            "bg-secondary text-secondary-foreground hover:bg-secondary/80": variant === "secondary",
            "bg-destructive text-destructive-foreground hover:bg-destructive/90": variant === "danger",
            "hover:bg-accent": variant === "ghost",
          },
          {
            "h-8 px-2.5 text-xs": size === "sm",
            "h-9 px-4 text-sm": size === "md",
            "h-10 px-6 text-base": size === "lg",
          },
          variant === "icon" && "h-9 w-9 p-0 min-h-[36px] min-w-[36px]",
          className,
        )}
        {...props}
      />
    );
  },
);

Button.displayName = "Button";
