import Link from "next/link";
import { Button } from "@sift/ui";

/** Closing CTA band — shadcn cta-01, sift tokens. */
export function CtaBand() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-24">
      <div className="rounded-lg border border-[rgb(var(--sift-border))] bg-[rgb(var(--sift-surface))] px-8 py-12 md:px-12">
        <h2 className="max-w-xl text-2xl font-semibold tracking-tight md:text-3xl">
          Open a collection. Put the contracts in. Keep the citations.
        </h2>
        <p className="mt-3 max-w-lg text-sm text-[rgb(var(--sift-text-muted))]">
          Start with a workspace, or sign in if you already have one.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Button asChild>
            <Link href="/signup">Get started</Link>
          </Button>
          <Button variant="secondary" asChild>
            <Link href="/login">Sign in</Link>
          </Button>
        </div>
      </div>
    </section>
  );
}
