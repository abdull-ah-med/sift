"use client";

import { useState } from "react";
import Link from "next/link";
import { Menu, X } from "lucide-react";
import { Button } from "@sift/ui";

const NAV = [
  { label: "Product", href: "/#product" },
  { label: "How it works", href: "/#how-it-works" },
] as const;

/** Pill marketing navbar — watermelon hero-1 chrome, rounded-full bar. */
export function SiteHeader() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 px-4 pt-4">
      <div className="mx-auto flex h-12 max-w-5xl items-center justify-between gap-3 rounded-full border border-[rgb(var(--sift-border-strong))] bg-[rgb(var(--sift-bg))]/80 px-2 pl-5 backdrop-blur-sm">
        <Link
          href="/"
          className="text-sm font-semibold tracking-tight text-[rgb(var(--sift-text))]"
        >
          sift
        </Link>
        <nav className="hidden items-center gap-6 text-sm text-[rgb(var(--sift-text-muted))] md:flex">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="hover:text-[rgb(var(--sift-text))]"
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="sm" asChild className="hidden sm:inline-flex">
            <Link href="/login">Sign in</Link>
          </Button>
          <Button size="sm" asChild>
            <Link href="/signup">Get started</Link>
          </Button>
          <button
            type="button"
            className="inline-flex h-9 w-9 items-center justify-center rounded-full text-[rgb(var(--sift-text))] md:hidden"
            aria-expanded={open}
            aria-controls="marketing-nav"
            aria-label={open ? "Close menu" : "Open menu"}
            onClick={() => setOpen((value) => !value)}
          >
            {open ? <X size={16} strokeWidth={1.5} /> : <Menu size={16} strokeWidth={1.5} />}
          </button>
        </div>
      </div>
      {open ? (
        <div
          id="marketing-nav"
          className="mx-auto mt-2 flex max-w-5xl flex-col gap-1 rounded-lg border border-[rgb(var(--sift-border))] bg-[rgb(var(--sift-surface))] p-3 md:hidden"
        >
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-md px-3 py-2 text-sm text-[rgb(var(--sift-text))]"
              onClick={() => setOpen(false)}
            >
              {item.label}
            </Link>
          ))}
          <Link
            href="/login"
            className="rounded-md px-3 py-2 text-sm text-[rgb(var(--sift-text-muted))] sm:hidden"
            onClick={() => setOpen(false)}
          >
            Sign in
          </Link>
        </div>
      ) : null}
    </header>
  );
}
