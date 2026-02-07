/**
 * Badgeコンポーネント
 *
 * バッジコンポーネントです
 */

import { forwardRef, type HTMLAttributes } from "react";
import { cn } from "../../lib/utils";

export interface BadgeProps extends HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "primary" | "secondary" | "success" | "warning" | "error" | "outline";
}

export const Badge = forwardRef<HTMLDivElement, BadgeProps>(
  ({ className, variant = "default", ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors",
          "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
          {
            "bg-primary text-primary-foreground": variant === "primary",
            "bg-secondary text-secondary-foreground": variant === "secondary",
            "bg-green-500 text-white": variant === "success",
            "bg-yellow-500 text-white": variant === "warning",
            "bg-red-500 text-white": variant === "error",
            "border border-border bg-background": variant === "outline",
            "bg-muted text-foreground": variant === "default",
          },
          className,
        )}
        {...props}
      />
    );
  },
);

Badge.displayName = "Badge";
