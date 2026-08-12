import Link from "next/link";
import { Button } from "@sift/ui";

/** Marketing navbar — shadcn Button primitives, sift tokens. */
export function SiteHeader() {
  return (
    <header className="border-b border-[rgb(var(--sift-border))] bg-[rgb(var(--sift-bg))]/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-4">
        <Link href="/" className="text-lg font-semibold tracking-tight text-[rgb(var(--sift-text))]">
          sift
        </Link>
        <nav className="flex items-center gap-2">
          <Button variant="ghost" asChild>
            <Link href="/login">Sign in</Link>
          </Button>
          <Button asChild>
            <Link href="/signup">Get started</Link>
          </Button>
        </nav>
      </div>
    </header>
  );
}
