import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "../lib/utils";

/** Watermelon `button` variants, sift tokens, pill radius (ADR 0001). */
const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-full text-sm font-medium transition-all disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 [&_svg]:shrink-0 outline-none focus-visible:ring-2 focus-visible:ring-[rgb(var(--sift-accent))]",
  {
    variants: {
      variant: {
        default: "bg-[rgb(var(--sift-accent))] text-[rgb(34_40_49)] hover:opacity-90",
        secondary:
          "bg-[rgb(var(--sift-surface))] text-[rgb(var(--sift-text))] border border-[rgb(var(--sift-border-strong))] hover:border-[rgb(var(--sift-text))]/25",
        outline:
          "border border-[rgb(var(--sift-border-strong))] bg-transparent text-[rgb(var(--sift-text))] hover:bg-[rgb(var(--sift-surface))]",
        ghost: "hover:bg-[rgb(var(--sift-surface))] text-[rgb(var(--sift-text))]",
        link: "text-[rgb(var(--sift-accent))] underline-offset-4 hover:underline",
        destructive:
          "border border-[rgb(var(--sift-danger))] bg-transparent text-[rgb(var(--sift-danger))] hover:bg-[rgb(var(--sift-danger))]/10",
      },
      size: {
        default: "h-10 px-4 py-2 has-[>svg]:px-3",
        sm: "h-9 px-3 has-[>svg]:px-2.5",
        lg: "h-11 px-8 has-[>svg]:px-6",
        icon: "size-10",
        "icon-sm": "size-8",
        "icon-lg": "size-11",
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
  ({ className, variant = "default", size = "default", asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        data-slot="button"
        data-variant={variant}
        data-size={size}
        className={cn(buttonVariants({ variant, size }), className)}
        ref={ref}
        {...props}
      />
    );
  },
);
Button.displayName = "Button";

export { buttonVariants };
