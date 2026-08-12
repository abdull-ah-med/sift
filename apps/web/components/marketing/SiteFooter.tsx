import Link from "next/link";

/** Marketing footer — minimal link row. */
export function SiteFooter() {
  return (
    <footer className="border-t border-[rgb(var(--sift-border))]">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-6 py-8 text-sm text-[rgb(var(--sift-text-muted))]">
        <span>sift</span>
        <div className="flex gap-4">
          <Link href="/login" className="hover:text-[rgb(var(--sift-text))]">
            Sign in
          </Link>
          <Link href="/collections" className="hover:text-[rgb(var(--sift-text))]">
            App
          </Link>
        </div>
      </div>
    </footer>
  );
}
