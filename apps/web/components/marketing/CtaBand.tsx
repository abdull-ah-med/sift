import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { Button } from "@sift/ui";

/** Watermelon cta-1 layout without blur orbs or gradients. */
export function CtaBand() {
  return (
    <section className="mx-auto w-full max-w-5xl px-6 py-16">
      <div className="flex flex-col items-center justify-between gap-8 rounded-xl border border-[rgb(var(--sift-border))] bg-[rgb(var(--sift-surface))] p-8 md:flex-row md:gap-12 md:px-10 md:py-16">
        <div className="flex max-w-xl flex-col gap-2 text-center md:text-left">
          <h2 className="text-2xl font-semibold tracking-tight md:text-3xl">
            Open a collection. Put the contracts in. Keep the citations.
          </h2>
          <p className="text-sm text-[rgb(var(--sift-text-muted))] md:text-base">
            Start with a workspace, or sign in if you already have one.
          </p>
        </div>
        <div className="flex w-full shrink-0 justify-center md:w-auto">
          <Button size="lg" asChild className="h-12 w-full px-8 md:w-auto">
            <Link href="/signup">
              Get started
              <ArrowUpRight size={16} strokeWidth={1.5} />
            </Link>
          </Button>
        </div>
      </div>
    </section>
  );
}
