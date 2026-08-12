import Link from "next/link";

const GROUPS = [
  {
    title: "Product",
    links: [
      { href: "/#product", label: "Product" },
      { href: "/#how-it-works", label: "How it works" },
      { href: "/collections", label: "App" },
    ],
  },
  {
    title: "Account",
    links: [
      { href: "/login", label: "Sign in" },
      { href: "/signup", label: "Get started" },
      { href: "/invite", label: "Invite" },
    ],
  },
  {
    title: "Legal",
    links: [
      { href: "/privacy", label: "Privacy" },
      { href: "/terms", label: "Terms" },
    ],
  },
] as const;

/** Watermelon footer-1 columns. No newsletter form. */
export function SiteFooter() {
  return (
    <footer className="w-full px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl border border-[rgb(var(--sift-border))] bg-[rgb(var(--sift-bg))] p-8 sm:p-12">
        <div className="flex flex-col justify-between gap-12 xl:flex-row">
          <div className="shrink-0 xl:w-[320px]">
            <p className="text-xl font-semibold tracking-tight">sift</p>
            <p className="mt-3 max-w-sm text-sm text-[rgb(var(--sift-text-muted))]">
              Privacy-first document intelligence
            </p>
          </div>
          <div className="grid flex-1 grid-cols-2 gap-8 sm:grid-cols-3">
            {GROUPS.map((group) => (
              <div key={group.title} className="space-y-5">
                <h2 className="text-sm font-medium">{group.title}</h2>
                <ul className="space-y-4">
                  {group.links.map((link) => (
                    <li key={link.href}>
                      <Link
                        href={link.href}
                        className="text-sm text-[rgb(var(--sift-text-muted))] hover:text-[rgb(var(--sift-text))]"
                      >
                        {link.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
        <div className="mt-16 flex items-center justify-center border-t border-[rgb(var(--sift-border))] pt-8">
          <p className="text-center text-xs text-[rgb(var(--sift-text-muted))]">sift</p>
        </div>
      </div>
    </footer>
  );
}
