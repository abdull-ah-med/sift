"use client";

import { Toaster as Sonner, type ToasterProps } from "sonner";

/** Single app toaster — mount once in the root layout. */
export function Toaster({ theme = "dark", position = "bottom-right", ...props }: ToasterProps) {
  return (
    <Sonner
      theme={theme}
      position={position}
      visibleToasts={3}
      duration={4000}
      toastOptions={{
        classNames: {
          toast:
            "!bg-[rgb(var(--sift-surface))] !text-[rgb(var(--sift-text))] !border !border-[rgb(var(--sift-border-strong))] !rounded-lg",
          title: "!text-[rgb(var(--sift-text))]",
          description: "!text-[rgb(var(--sift-text-muted))]",
          actionButton:
            "!bg-[rgb(var(--sift-accent))] !text-[rgb(var(--sift-bg))]",
          cancelButton:
            "!bg-[rgb(var(--sift-bg))] !text-[rgb(var(--sift-text))]",
        },
      }}
      {...props}
    />
  );
}
