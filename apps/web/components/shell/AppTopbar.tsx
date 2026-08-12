"use client";

import Link from "next/link";
import { Button } from "@sift/ui";

type AppTopbarProps = {
  onOpenCommand: () => void;
};

/** App topbar with breadcrumbs slot + ⌘K affordance. */
export function AppTopbar({ onOpenCommand }: AppTopbarProps) {
  return (
    <header className="flex h-12 shrink-0 items-center justify-between gap-4 border-b border-[rgb(var(--sift-border))] bg-[rgb(var(--sift-bg))] px-4">
      <p className="text-xs text-[rgb(var(--sift-text-muted))]">Workspace</p>
      <div className="flex items-center gap-2">
        <Button type="button" variant="secondary" size="sm" onClick={onOpenCommand}>
          Search… <kbd className="ml-2 text-[10px] opacity-70">⌘K</kbd>
        </Button>
        <Button variant="ghost" size="sm" asChild>
          <Link href="/login">Account</Link>
        </Button>
      </div>
    </header>
  );
}
