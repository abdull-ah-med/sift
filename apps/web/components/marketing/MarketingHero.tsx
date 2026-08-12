"use client";

import Link from "next/link";
import { ArrowDown, ArrowUpRight } from "lucide-react";
import { motion, useReducedMotion } from "motion/react";
import { Button } from "@sift/ui";

const EASE = [0.16, 1, 0.3, 1] as const;

/** Full-viewport hero — watermelon hero-1 structure, sift copy, no remote image. */
export function MarketingHero() {
  const reduce = useReducedMotion();
  const hidden = reduce ? { opacity: 1, y: 0 } : { opacity: 0, y: 24 };
  const visible = { opacity: 1, y: 0 };

  return (
    <section className="relative flex min-h-[calc(100dvh-4.5rem)] flex-col justify-between overflow-hidden px-6 pb-10 pt-16 md:px-12 md:pb-12 md:pt-24">
      <motion.div
        initial="hidden"
        animate="visible"
        variants={{
          hidden: {},
          visible: {
            transition: reduce ? undefined : { staggerChildren: 0.12, delayChildren: 0.08 },
          },
        }}
        className="mx-auto flex w-full max-w-6xl flex-1 flex-col justify-between"
      >
        <div className="flex flex-col gap-8">
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
            className="max-w-3xl text-4xl font-semibold tracking-tight text-[rgb(var(--sift-text))] md:text-5xl md:leading-[1.05]"
          >
            Document intelligence you can trust with a sealed contract.
          </motion.h1>
          <motion.div
            variants={{ hidden, visible }}
            transition={{ duration: reduce ? 0 : 0.5, ease: EASE }}
            className="flex flex-wrap gap-3"
          >
            <Button size="lg" asChild>
              <Link href="/signup">
                Get started
                <ArrowUpRight size={16} strokeWidth={1.5} />
              </Link>
            </Button>
            <Button size="lg" variant="secondary" asChild>
              <Link href="/login">Sign in</Link>
            </Button>
          </motion.div>
        </div>

        <motion.div
          variants={{ hidden, visible }}
          transition={{ duration: reduce ? 0 : 0.5, ease: EASE }}
          className="mt-16 flex flex-col justify-between gap-8 md:flex-row md:items-end"
        >
          <p className="max-w-xl text-lg text-[rgb(var(--sift-text-muted))]">
            Upload sensitive PDFs, review extractions, search with hybrid retrieval, and chat with
            answers that cite the chunks they came from.
          </p>
          <a
            href="#product"
            className="inline-flex items-center gap-2 text-sm text-[rgb(var(--sift-text-muted))] hover:text-[rgb(var(--sift-text))]"
          >
            Scroll to product
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
        </motion.div>
      </motion.div>
    </section>
  );
}
