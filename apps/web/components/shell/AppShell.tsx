"use client";

import { useState } from "react";
import { AppSidebar } from "./AppSidebar";
import { AppTopbar } from "./AppTopbar";
import { CommandPalette } from "./CommandPalette";

/** Authenticated product chrome — sidebar + topbar + ⌘K. */
export function AppShell({ children }: { children: React.ReactNode }) {
  const [cmdOpen, setCmdOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-[rgb(var(--sift-bg))] text-[rgb(var(--sift-text))]">
      <AppSidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <AppTopbar onOpenCommand={() => setCmdOpen(true)} />
        <main className="sift-app-main flex-1 overflow-auto px-6 py-6">{children}</main>
      </div>
      <CommandPalette open={cmdOpen} onOpenChange={setCmdOpen} />
    </div>
  );
}
