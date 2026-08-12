import Link from "next/link";

const LINKS = [
  { href: "/login", label: "Sign in" },
  { href: "/collections", label: "App" },
  { href: "/privacy", label: "Privacy" },
  { href: "/terms", label: "Terms" },
] as const;

/** Marketing footer — watermelon footer-1 link row, no newsletter form. */
export function SiteFooter() {
  return (
    <footer className="border-t border-[rgb(var(--sift-border))]">
      <div className="mx-auto flex max-w-6xl flex-col gap-6 px-6 py-10 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-semibold tracking-tight text-[rgb(var(--sift-text))]">sift</p>
          <p className="mt-1 text-sm text-[rgb(var(--sift-text-muted))]">
            Privacy-first document intelligence
          </p>
        </div>
        <nav className="flex flex-wrap gap-4 text-sm text-[rgb(var(--sift-text-muted))]">
          {LINKS.map((link) => (
            <Link key={link.href} href={link.href} className="hover:text-[rgb(var(--sift-text))]">
              {link.label}
            </Link>
          ))}
        </nav>
      </div>
    </footer>
  );
}
