"use client";

import { motion, useReducedMotion } from "motion/react";
import { SiteFooter } from "@/components/marketing/SiteFooter";
import { SiteHeader } from "@/components/marketing/SiteHeader";

const EASE = [0.16, 1, 0.3, 1] as const;

/** Watermelon auth-07 split chrome. No Google, no CDN photo. */
export function AuthShell({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  const reduce = useReducedMotion();
  const hidden = { opacity: 1, y: reduce ? 0 : 16 };
  const visible = { opacity: 1, y: 0 };

  return (
    <div className="flex min-h-[100dvh] flex-col bg-[rgb(var(--sift-bg))]">
      <SiteHeader />
      <main id="main" className="sift-app-main grid flex-1 lg:grid-cols-2">
        <div className="flex flex-1 items-center justify-center p-6 md:p-10">
          <motion.div
            initial="hidden"
            animate="visible"
            variants={{
              hidden: {},
              visible: {
                transition: reduce ? undefined : { staggerChildren: 0.1, delayChildren: 0.08 },
              },
            }}
            className="w-full max-w-[420px]"
          >
            <motion.div
              variants={{ hidden, visible }}
              transition={{ duration: reduce ? 0 : 0.45, ease: EASE }}
              className="mb-6 text-center"
            >
              <h1 className="mb-1 text-3xl font-semibold tracking-tight md:text-4xl">{title}</h1>
              <p className="text-sm text-[rgb(var(--sift-text-muted))]">{description}</p>
            </motion.div>
            <motion.div
              variants={{ hidden, visible }}
              transition={{ duration: reduce ? 0 : 0.45, ease: EASE }}
              className="flex flex-col gap-4"
            >
              {children}
            </motion.div>
          </motion.div>
        </div>
        <div className="hidden p-4 lg:block">
          <aside
            className="relative flex h-full min-h-[32rem] flex-col justify-end overflow-hidden rounded-[2rem] border border-[rgb(var(--sift-border))] bg-cover bg-center p-12"
            style={{ backgroundImage: "url('/noise-gradient.png')" }}
          >
            <p className="relative max-w-md text-3xl font-semibold tracking-tight text-[rgb(var(--sift-text))]">
              Document intelligence you can trust with a sealed contract.
            </p>
            <p className="relative mt-4 max-w-md text-sm text-[rgb(var(--sift-text-muted))]">
              Zitadel for people. API keys for machines. Citations for every answer.
            </p>
          </aside>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
