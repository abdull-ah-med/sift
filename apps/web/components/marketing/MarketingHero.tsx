"use client";

import Link from "next/link";
import { ArrowDown, ArrowUpRight } from "lucide-react";
import { motion, useReducedMotion } from "motion/react";

const EASE = [0.16, 1, 0.3, 1] as const;

/** Watermelon hero-1 content (no CDN photo). Pill nav lives in SiteHeader. */
export function MarketingHero() {
  const reduce = useReducedMotion();
  const hidden = { opacity: 1, y: reduce ? 0 : 24 };
  const visible = { opacity: 1, y: 0 };

  return (
    <section className="relative flex min-h-[calc(100dvh-4.5rem)] flex-col justify-between overflow-hidden">
      <motion.div
        initial="hidden"
        animate="visible"
        variants={{
          hidden: {},
          visible: {
            transition: reduce ? undefined : { staggerChildren: 0.12, delayChildren: 0.08 },
          },
        }}
        className="relative z-10 mx-auto flex w-full max-w-6xl flex-1 flex-col justify-between px-6 py-16 md:px-12 md:py-20"
      >
        <div className="flex max-w-[850px] flex-col gap-8 md:gap-10">
          <motion.p
            variants={{ hidden, visible }}
            transition={{ duration: reduce ? 0 : 0.5, ease: EASE }}
            className="text-sm font-medium text-[rgb(var(--sift-text-muted))]"
          >
            Privacy-first document intelligence
          </motion.p>
          <motion.h1
            variants={{ hidden, visible }}
            transition={{ duration: reduce ? 0 : 0.6, ease: EASE }}
            className="text-4xl font-medium leading-[1.08] tracking-tight text-[rgb(var(--sift-text))] md:text-5xl"
          >
            Document intelligence you can trust with a sealed contract.
          </motion.h1>
          <motion.div variants={{ hidden, visible }} transition={{ duration: reduce ? 0 : 0.5, ease: EASE }}>
            <Link
              href="/signup"
              className="group inline-flex w-fit items-center gap-4 rounded-full bg-[rgb(var(--sift-accent))] p-1 pl-5 text-sm font-medium text-[rgb(34_40_49)]"
            >
              <span>Get started</span>
              <span className="relative flex size-8 shrink-0 items-center justify-center overflow-hidden rounded-full bg-[rgb(34_40_49)]">
                <ArrowUpRight
                  className="size-4 text-[rgb(var(--sift-text))] transition-transform duration-300 group-hover:translate-x-0.5 group-hover:-translate-y-0.5"
                  strokeWidth={1.5}
                />
              </span>
            </Link>
          </motion.div>
        </div>

        <motion.div
          variants={{ hidden, visible }}
          transition={{ duration: reduce ? 0 : 0.5, ease: EASE }}
          className="mt-16 flex flex-col justify-between gap-10 pt-8 lg:flex-row lg:items-end"
        >
          <p className="max-w-xl text-base leading-relaxed text-[rgb(var(--sift-text-muted))] md:text-lg">
            Upload sensitive PDFs, review extractions, search with hybrid retrieval, and chat with
            answers that cite the chunks they came from.
          </p>
          <div className="flex flex-wrap items-center gap-8">
            <Link href="/#product" className="text-sm text-[rgb(var(--sift-text))] hover:opacity-80">
              Product
            </Link>
            <Link href="/#how-it-works" className="text-sm text-[rgb(var(--sift-text))] hover:opacity-80">
              How it works
            </Link>
            <Link href="/login" className="text-sm text-[rgb(var(--sift-text))] hover:opacity-80">
              Sign in
            </Link>
            <a
              href="#product"
              className="hidden items-center gap-2 text-sm text-[rgb(var(--sift-text-muted))] md:inline-flex"
            >
              Scroll to Discover
              {reduce ? (
                <ArrowDown size={16} strokeWidth={1.5} />
              ) : (
                <motion.span
                  animate={{ y: [0, 4, 0] }}
                  transition={{ repeat: Infinity, duration: 1.8, ease: "easeInOut" }}
                  className="inline-flex"
                >
                  <ArrowDown size={16} strokeWidth={1.5} />
                </motion.span>
              )}
            </a>
          </div>
        </motion.div>
      </motion.div>
    </section>
  );
}
