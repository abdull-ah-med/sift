"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Command } from "cmdk";

const JUMPS = [
  { value: "home", label: "Home", href: "/home" },
  { value: "collections", label: "Collections", href: "/collections" },
  { value: "tenants", label: "Tenants", href: "/tenants" },
  { value: "api-keys", label: "API keys", href: "/settings/api-keys" },
  { value: "audit", label: "Audit log", href: "/settings/audit" },
] as const;

type CommandPaletteProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

/** ⌘K command palette via cmdk — no open/close animation. */
export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        onOpenChange(!open);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onOpenChange]);

  useEffect(() => {
    if (!open) setQuery("");
  }, [open]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-[rgb(var(--sift-overlay))] pt-[20vh]">
      <button
        type="button"
        aria-label="Close command palette"
        className="absolute inset-0 cursor-default"
        onClick={() => onOpenChange(false)}
      />
      <Command
        className="relative z-10 w-full max-w-lg overflow-hidden rounded-lg border border-[rgb(var(--sift-border-strong))] bg-[rgb(var(--sift-surface))]"
        label="Command menu"
      >
        <Command.Input
          value={query}
          onValueChange={setQuery}
          placeholder="Jump to…"
          className="w-full border-b border-[rgb(var(--sift-border))] bg-transparent px-4 py-3 text-sm text-[rgb(var(--sift-text))] outline-none placeholder:text-[rgb(var(--sift-text-muted))]"
        />
        <Command.List className="max-h-72 overflow-auto p-2">
          <Command.Empty className="px-3 py-6 text-center text-sm text-[rgb(var(--sift-text-muted))]">
            No matches. Try Home, Collections, or Settings.
          </Command.Empty>
          <Command.Group
            heading="Navigate"
            className="px-1 text-xs text-[rgb(var(--sift-text-muted))]"
          >
            {JUMPS.map((item) => (
              <Command.Item
                key={item.value}
                value={item.value}
                onSelect={() => {
                  onOpenChange(false);
                  router.push(item.href);
                }}
                className="cursor-pointer rounded-md px-3 py-2 text-sm text-[rgb(var(--sift-text))] aria-selected:bg-[rgb(var(--sift-bg))]"
              >
                {item.label}
              </Command.Item>
            ))}
          </Command.Group>
        </Command.List>
      </Command>
    </div>
  );
}
