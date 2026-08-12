import * as React from "react";

import { cn } from "../lib/utils";

export const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.ComponentProps<"textarea">
>(({ className, ...props }, ref) => {
  return (
    <textarea
      ref={ref}
      className={cn(
        "flex min-h-20 w-full rounded-md border border-[rgb(var(--sift-border-strong))] bg-[rgb(var(--sift-surface))] px-3 py-2 text-sm text-[rgb(var(--sift-text))] placeholder:text-[rgb(var(--sift-text-muted))] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[rgb(var(--sift-accent))] disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    />
  );
});
Textarea.displayName = "Textarea";
