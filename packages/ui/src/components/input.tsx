import * as React from "react";

import { cn } from "../lib/utils";

export const Input = React.forwardRef<HTMLInputElement, React.ComponentProps<"input">>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-10 w-full rounded-md border border-[rgb(var(--sift-border-strong))] bg-[rgb(var(--sift-surface))] px-3 py-2 text-sm text-[rgb(var(--sift-text))] placeholder:text-[rgb(var(--sift-text-muted))] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[rgb(var(--sift-accent))] disabled:cursor-not-allowed disabled:opacity-50",
          className,
        )}
        ref={ref}
        {...props}
      />
    );
  },
);
Input.displayName = "Input";
