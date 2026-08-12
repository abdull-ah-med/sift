"use client";

import { motion, useReducedMotion } from "motion/react";
import { SiteFooter } from "@/components/marketing/SiteFooter";
import { SiteHeader } from "@/components/marketing/SiteHeader";

const EASE = [0.16, 1, 0.3, 1] as const;

/** Split auth chrome — watermelon auth-07 layout, no CDN photo, no Google. */
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
  const hidden = reduce ? { opacity: 1, y: 0 } : { opacity: 1, y: 16 };
  const visible = { opacity: 1, y: 0 };

  return (
    <div className="flex min-h-[100dvh] flex-col bg-[rgb(var(--sift-bg))]">
      <SiteHeader />
      <main id="main" className="sift-app-main grid flex-1 lg:grid-cols-2">
        <div className="flex flex-col justify-center px-6 py-16 lg:px-16">
          <motion.div
            initial="hidden"
            animate="visible"
            variants={{
              hidden: {},
              visible: {
                transition: reduce ? undefined : { staggerChildren: 0.1, delayChildren: 0.08 },
              },
            }}
            className="mx-auto flex w-full max-w-[420px] flex-col gap-6"
          >
            <motion.div
              variants={{ hidden, visible }}
              transition={{ duration: reduce ? 0 : 0.45, ease: EASE }}
            >
              <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
              <p className="mt-2 text-sm text-[rgb(var(--sift-text-muted))]">{description}</p>
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
        <aside className="relative hidden border-l border-[rgb(var(--sift-border))] bg-[rgb(var(--sift-surface))] lg:flex lg:flex-col lg:justify-end lg:p-12">
          <p className="max-w-md text-3xl font-semibold tracking-tight text-[rgb(var(--sift-text))]">
            Document intelligence you can trust with a sealed contract.
          </p>
          <p className="mt-4 max-w-md text-sm text-[rgb(var(--sift-text-muted))]">
            Zitadel for people. API keys for machines. Citations for every answer.
          </p>
        </aside>
      </main>
      <SiteFooter />
    </div>
  );
}
