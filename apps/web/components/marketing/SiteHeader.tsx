import Link from "next/link";
import { Button } from "@sift/ui";

/** Marketing navbar — shadcn navbar-01 structure, sift tokens. */
export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-[rgb(var(--sift-border))] bg-[rgb(var(--sift-bg))]/90 backdrop-blur-sm">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between gap-4 px-6">
        <Link
          href="/"
          className="text-sm font-semibold tracking-tight text-[rgb(var(--sift-text))]"
        >
          sift
        </Link>
        <nav className="hidden items-center gap-6 text-sm text-[rgb(var(--sift-text-muted))] md:flex">
          <a href="#product" className="hover:text-[rgb(var(--sift-text))]">
            Product
          </a>
          <a href="#how-it-works" className="hover:text-[rgb(var(--sift-text))]">
            How it works
          </a>
        </nav>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" asChild>
            <Link href="/login">Sign in</Link>
          </Button>
          <Button size="sm" asChild>
            <Link href="/signup">Get started</Link>
          </Button>
        </div>
      </div>
    </header>
  );
}
