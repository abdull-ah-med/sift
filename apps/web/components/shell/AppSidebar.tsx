"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@sift/ui";

const NAV = [
  { href: "/collections", label: "Collections" },
  { href: "/tenants", label: "Tenants" },
  { href: "/settings/api-keys", label: "API keys" },
  { href: "/settings/audit", label: "Audit" },
] as const;

/** Dense product sidebar — Linear/Vercel calibration. */
export function AppSidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex w-52 shrink-0 flex-col border-r border-[rgb(var(--sift-border))] bg-[rgb(var(--sift-surface))]">
      <div className="border-b border-[rgb(var(--sift-border))] px-4 py-3">
        <Link href="/collections" className="text-sm font-semibold tracking-tight text-[rgb(var(--sift-text))]">
          sift
        </Link>
      </div>
      <nav className="flex flex-col gap-0.5 p-2">
        {NAV.map((item) => {
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "rounded-md px-3 py-2 text-sm text-[rgb(var(--sift-text-muted))] hover:bg-[rgb(var(--sift-bg))] hover:text-[rgb(var(--sift-text))]",
                active && "bg-[rgb(var(--sift-bg))] font-medium text-[rgb(var(--sift-text))]",
              )}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
