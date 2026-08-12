"use client";

import * as React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { X } from "lucide-react";

import { cn } from "../lib/utils";

export function Sheet(props: React.ComponentProps<typeof DialogPrimitive.Root>) {
  return <DialogPrimitive.Root {...props} />;
}

export function SheetTrigger(props: React.ComponentProps<typeof DialogPrimitive.Trigger>) {
  return <DialogPrimitive.Trigger {...props} />;
}

export function SheetClose(props: React.ComponentProps<typeof DialogPrimitive.Close>) {
  return <DialogPrimitive.Close {...props} />;
}

export function SheetPortal(props: React.ComponentProps<typeof DialogPrimitive.Portal>) {
  return <DialogPrimitive.Portal {...props} />;
}

export function SheetOverlay({
  className,
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Overlay>) {
  return (
    <DialogPrimitive.Overlay
      className={cn(
        "fixed inset-0 z-50 bg-[rgb(var(--sift-overlay))] backdrop-blur-sm",
        className,
      )}
      {...props}
    />
  );
}

export function SheetContent({
  className,
  children,
  side = "right",
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Content> & {
  side?: "top" | "right" | "bottom" | "left";
}) {
  return (
    <SheetPortal>
      <SheetOverlay />
      <DialogPrimitive.Content
        className={cn(
          "fixed z-50 flex flex-col gap-4 bg-[rgb(var(--sift-surface))] text-[rgb(var(--sift-text))] shadow-[0_8px_24px_rgb(0_0_0_/_0.45)] transition-transform duration-200 ease-[cubic-bezier(0.2,0.8,0.2,1)]",
          side === "right" && "inset-y-0 right-0 h-full w-3/4 border-l border-[rgb(var(--sift-border))] sm:max-w-sm",
          side === "left" && "inset-y-0 left-0 h-full w-3/4 border-r border-[rgb(var(--sift-border))] sm:max-w-sm",
          side === "top" && "inset-x-0 top-0 border-b border-[rgb(var(--sift-border))]",
          side === "bottom" && "inset-x-0 bottom-0 border-t border-[rgb(var(--sift-border))]",
          className,
        )}
        {...props}
      >
        {children}
        <DialogPrimitive.Close className="absolute top-3 right-3 flex size-10 items-center justify-center rounded-md text-[rgb(var(--sift-text-muted))] hover:text-[rgb(var(--sift-text))] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[rgb(var(--sift-accent))]">
          <X className="size-5" strokeWidth={1.5} />
          <span className="sr-only">Close</span>
        </DialogPrimitive.Close>
      </DialogPrimitive.Content>
    </SheetPortal>
  );
}

export function SheetHeader({ className, ...props }: React.ComponentProps<"div">) {
  return <div className={cn("flex flex-col gap-1.5 p-4", className)} {...props} />;
}

export function SheetFooter({ className, ...props }: React.ComponentProps<"div">) {
  return <div className={cn("mt-auto flex flex-col gap-2 p-4", className)} {...props} />;
}

export function SheetTitle({
  className,
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Title>) {
  return (
    <DialogPrimitive.Title className={cn("font-semibold", className)} {...props} />
  );
}

export function SheetDescription({
  className,
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Description>) {
  return (
    <DialogPrimitive.Description
      className={cn("text-sm text-[rgb(var(--sift-text-muted))]", className)}
      {...props}
    />
  );
}
