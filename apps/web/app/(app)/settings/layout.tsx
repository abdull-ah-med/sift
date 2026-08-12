import Link from "next/link";

const ITEMS = [
  { href: "/settings/api-keys", label: "API keys" },
  { href: "/settings/audit", label: "Audit" },
] as const;

/** Settings subnav — shadcn settings sidebar pattern. */
export default function SettingsLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-8 md:flex-row">
      <nav className="flex gap-2 md:w-44 md:flex-col">
        {ITEMS.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="rounded-md px-3 py-2 text-sm text-[rgb(var(--sift-text-muted))] hover:bg-[rgb(var(--sift-surface))] hover:text-[rgb(var(--sift-text))]"
          >
            {item.label}
          </Link>
        ))}
      </nav>
      <div className="min-w-0 flex-1">{children}</div>
    </div>
  );
}
