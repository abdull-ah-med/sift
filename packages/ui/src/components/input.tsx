import * as React from "react";

import { cn } from "../lib/utils";

/** Watermelon `input`, sift tokens, 4px radius (ADR 0001). */
export const Input = React.forwardRef<HTMLInputElement, React.ComponentProps<"input">>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        data-slot="input"
        className={cn(
          "h-10 w-full min-w-0 rounded-md border border-[rgb(var(--sift-border-strong))] bg-[rgb(var(--sift-surface))] px-3 py-2 text-sm text-[rgb(var(--sift-text))] shadow-none transition-[color,box-shadow] outline-none",
          "placeholder:text-[rgb(var(--sift-text-muted))] file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-[rgb(var(--sift-text))]",
          "focus-visible:ring-2 focus-visible:ring-[rgb(var(--sift-accent))]",
          "aria-invalid:border-[rgb(var(--sift-danger))] aria-invalid:ring-[rgb(var(--sift-danger))]/30",
          "disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50",
          className,
        )}
        ref={ref}
        {...props}
      />
    );
  },
);
Input.displayName = "Input";
