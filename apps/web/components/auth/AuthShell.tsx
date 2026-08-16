"use client";

import Image from "next/image";
import FadeContent from "@/components/bits/FadeContent";
import { SiteFooter } from "@/components/marketing/SiteFooter";
import { SiteHeader } from "@/components/marketing/SiteHeader";

/** Split auth-07: form column + inset rounded picture pane. */
export function AuthShell({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-[rgb(var(--sift-bg))]">
      <SiteHeader />
      <main id="main" className="sift-app-main">
        <div className="grid min-h-[100dvh] lg:grid-cols-2">
          <div className="flex min-h-[100dvh] items-center justify-center px-6 pt-28 pb-16 md:px-10">
            <FadeContent delay={0} duration={0.4} threshold={0} className="w-full max-w-[420px]">
              <p className="mb-8 text-center text-lg font-semibold tracking-tight text-[rgb(var(--sift-text))]">
                sift
              </p>
              <div className="mb-8 text-center">
                <h1 className="mb-2 text-3xl font-semibold tracking-tight md:text-4xl">{title}</h1>
                <p className="text-sm leading-relaxed text-[rgb(var(--sift-text-muted))]">
                  {description}
                </p>
              </div>
              <div className="flex flex-col gap-4">{children}</div>
            </FadeContent>
          </div>
          <div className="hidden min-h-[100dvh] p-6 pt-28 pb-6 lg:flex">
            <aside className="relative flex w-full flex-col justify-end overflow-hidden rounded-[2rem] border border-[rgb(var(--sift-border-strong))]">
              <Image
                src="/noise-gradient.png"
                alt=""
                fill
                sizes="50vw"
                className="object-cover"
                priority
              />
              <div
                className="absolute inset-0 bg-gradient-to-t from-[rgb(var(--sift-bg))] via-[rgb(var(--sift-bg)_/_0.35)] to-transparent"
                aria-hidden
              />
              <div className="relative z-10 p-10">
                <p className="max-w-md text-3xl font-semibold tracking-tight text-[rgb(var(--sift-text))]">
                  Document intelligence you can trust with a sealed contract.
                </p>
                <p className="mt-4 max-w-md text-sm leading-relaxed text-[rgb(var(--sift-text-muted))]">
                  Zitadel for people. API keys for machines. Citations for every answer.
                </p>
              </div>
            </aside>
          </div>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
