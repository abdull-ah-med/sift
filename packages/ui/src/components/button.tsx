import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "../lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[rgb(var(--sift-accent))] disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default:
          "bg-[rgb(var(--sift-accent))] text-[rgb(34_40_49)] hover:opacity-90",
        secondary:
          "bg-[rgb(var(--sift-surface))] text-[rgb(var(--sift-text))] border border-[rgb(var(--sift-border-strong))]",
        ghost: "hover:bg-[rgb(var(--sift-surface))] text-[rgb(var(--sift-text))]",
        link: "text-[rgb(var(--sift-accent))] underline-offset-4 hover:underline",
        destructive:
          "border border-[rgb(var(--sift-danger))] bg-transparent text-[rgb(var(--sift-danger))] hover:bg-[rgb(var(--sift-danger))]/10",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp className={cn(buttonVariants({ variant, size }), className)} ref={ref} {...props} />
    );
  },
);
Button.displayName = "Button";
