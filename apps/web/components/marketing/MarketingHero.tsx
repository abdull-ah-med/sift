"use client";

import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { HashLink } from "@/components/marketing/HashLink";
import { useReducedMotion } from "motion/react";
import ColorBends from "@/components/marketing/ColorBends";
import FadeContent from "@/components/bits/FadeContent";
import SplitText from "@/components/bits/SplitText";

/** Full-viewport hero with React Bits ColorBends and load reveals. */
export function MarketingHero() {
  const reduce = useReducedMotion();

  return (
    <section className="relative flex min-h-[100dvh] flex-col justify-between overflow-hidden">
      <div className="absolute inset-0" aria-hidden>
        <ColorBends
          className="pointer-events-none"
          rotation={140}
          speed={reduce ? 0.06 : 0.15}
          colors={["#1b6986"]}
          transparent
          autoRotate={0}
          scale={1}
          frequency={1}
          warpStrength={reduce ? 0.35 : 1}
          mouseInfluence={reduce ? 0 : 0.1}
          parallax={0}
          noise={0}
          iterations={1}
          intensity={reduce ? 1.2 : 2}
          bandWidth={3}
        />
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-[rgb(var(--sift-bg))]" />
      </div>
      <div className="relative z-10 mx-auto flex w-full max-w-7xl flex-1 flex-col justify-between px-6 py-28 md:px-12 md:py-32">
        <div className="flex max-w-[850px] flex-col gap-8 md:gap-10">
          <FadeContent delay={0} duration={0.4} threshold={0}>
            <p className="text-sm font-medium text-[rgb(var(--sift-text-muted))]">
              Privacy-first document intelligence
            </p>
          </FadeContent>
          <SplitText
            tag="h1"
            text="Document intelligence you can trust with a sealed contract."
            className="text-4xl font-medium leading-[1.08] tracking-tight text-[rgb(var(--sift-text))] md:text-5xl"
            textAlign="left"
            splitType="words"
            delay={40}
            duration={0.45}
            ease="power2.out"
            from={{ opacity: 0, y: 12 }}
            to={{ opacity: 1, y: 0 }}
            threshold={0}
          />
          <FadeContent delay={0.2} duration={0.4} threshold={0}>
            <Link
              href="/signup"
              className="group inline-flex w-fit items-center gap-4 rounded-full bg-[rgb(var(--sift-accent))] p-1 pl-5 text-sm font-medium text-[rgb(var(--sift-text))]"
            >
              <span>Get started</span>
              <span className="relative flex size-8 shrink-0 items-center justify-center overflow-hidden rounded-full bg-[rgb(34_40_49)]">
                <ArrowUpRight
                  className="size-4 text-[rgb(var(--sift-text))] transition-transform duration-150 ease-[var(--ease-out)] motion-safe:group-hover:translate-x-0.5 motion-safe:group-hover:-translate-y-0.5"
                  strokeWidth={1.5}
                />
              </span>
            </Link>
          </FadeContent>
        </div>

        <FadeContent delay={0.28} duration={0.4} threshold={0}>
          <div className="mt-16 flex flex-col justify-between gap-10 pt-8 lg:flex-row lg:items-end">
            <p className="max-w-xl text-base leading-relaxed text-[rgb(var(--sift-text-muted))] md:text-lg">
              Upload sensitive PDFs, review extractions, search with hybrid retrieval, and chat with
              answers that cite the chunks they came from.
            </p>
            <div className="flex flex-wrap items-center gap-8">
              <HashLink href="/#product">Product</HashLink>
              <HashLink href="/#how-it-works">How it works</HashLink>
              <HashLink href="/login">Sign in</HashLink>
              <HashLink href="/#product" className="hidden md:inline">
                Scroll to Discover
              </HashLink>
            </div>
          </div>
        </FadeContent>
      </div>
    </section>
  );
}
