import Link from "next/link";
import { Button } from "@sift/ui";

/** Brand-first marketing hero (design-philosophy §11). */
export function MarketingHero() {
  return (
    <section className="relative overflow-hidden">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgb(var(--sift-surface))_0%,rgb(var(--sift-bg))_55%)]"
      />
      <div className="relative mx-auto flex max-w-6xl flex-col gap-8 px-6 pb-24 pt-20 md:pt-28">
        <p className="text-sm font-medium tracking-wide text-[rgb(var(--sift-accent))]">sift</p>
        <h1 className="max-w-3xl text-4xl font-semibold tracking-tight text-[rgb(var(--sift-text))] md:text-5xl md:leading-[1.05]">
          Document intelligence you can trust with a sealed contract.
        </h1>
        <p className="max-w-xl text-lg text-[rgb(var(--sift-text-muted))]">
          Collection-scoped RAG with citations, review, and audit — modern minimal dark, built for
          serious corpora.
        </p>
        <div className="flex flex-wrap gap-3">
          <Button size="lg" asChild>
            <Link href="/signup">Get started</Link>
          </Button>
          <Button size="lg" variant="secondary" asChild>
            <Link href="/login">Sign in</Link>
          </Button>
        </div>
      </div>
    </section>
  );
}
