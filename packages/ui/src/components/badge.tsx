import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "../lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium",
  {
    variants: {
      variant: {
        default:
          "border-[rgb(var(--sift-border))] bg-[rgb(var(--sift-surface))] text-[rgb(var(--sift-text))]",
        accent:
          "border-transparent bg-[rgb(var(--sift-accent))] text-[rgb(var(--sift-text))]",
        outline: "border-[rgb(var(--sift-border-strong))] text-[rgb(var(--sift-text))]",
        danger:
          "border-[rgb(var(--sift-danger))]/40 bg-[rgb(var(--sift-danger))]/10 text-[rgb(var(--sift-danger))]",
        warning:
          "border-[rgb(var(--sift-warning))]/40 bg-[rgb(var(--sift-warning))]/10 text-[rgb(var(--sift-warning))]",
        success:
          "border-[rgb(var(--sift-success))]/40 bg-[rgb(var(--sift-success))]/10 text-[rgb(var(--sift-success))]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  },
);

export type BadgeProps = React.ComponentProps<"span"> & VariantProps<typeof badgeVariants>;

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}
