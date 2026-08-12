"use client";

import * as React from "react";
import * as SwitchPrimitive from "@radix-ui/react-switch";

import { cn } from "../lib/utils";

export function Switch({
  className,
  ...props
}: React.ComponentProps<typeof SwitchPrimitive.Root>) {
  return (
    <SwitchPrimitive.Root
      className={cn(
        "peer inline-flex h-6 w-10 shrink-0 cursor-pointer items-center rounded-full border border-[rgb(var(--sift-border-strong))] bg-[rgb(var(--sift-bg))] transition-colors duration-200 ease-[cubic-bezier(0.2,0.8,0.2,1)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[rgb(var(--sift-accent))] disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-[rgb(var(--sift-accent))]",
        className,
      )}
      {...props}
    >
      <SwitchPrimitive.Thumb
        className={cn(
          "pointer-events-none block size-5 rounded-full bg-[rgb(var(--sift-text))] transition-transform duration-200 ease-[cubic-bezier(0.2,0.8,0.2,1)] data-[state=checked]:translate-x-4 data-[state=unchecked]:translate-x-0.5",
        )}
      />
    </SwitchPrimitive.Root>
  );
}
