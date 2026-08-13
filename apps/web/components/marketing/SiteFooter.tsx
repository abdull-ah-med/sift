"use client";

import Link from "next/link";
import { Button, Separator } from "@sift/ui";
import FadeContent from "@/components/bits/FadeContent";
import { HashLink } from "@/components/marketing/HashLink";
import { LEGAL_LINKS } from "@/components/marketing/legal";

const COLUMNS = [
  {
    title: "Product",
    links: [
      { href: "/#product", label: "Product" },
      { href: "/#how-it-works", label: "How it works" },
      { href: "/collections", label: "Collections" },
    ],
  },
  {
    title: "App",
    links: [
      { href: "/login", label: "Sign in" },
      { href: "/invite", label: "Invite" },
    ],
  },
  {
    title: "Legal",
    links: LEGAL_LINKS,
  },
] as const;

/** Watermelon footer-4 structure, sift tokens. No fake newsletter. */
export function SiteFooter() {
  return (
    <footer className="mt-24 w-full bg-[rgb(var(--sift-bg))]">
      <FadeContent duration={0.4}>
        <div className="mx-auto max-w-7xl px-6 pt-16 pb-0 md:px-12">
          <div className="grid grid-cols-1 gap-12 lg:grid-cols-12 lg:gap-0">
            <div className="flex flex-col justify-between gap-6 lg:col-span-5 lg:pr-16">
              <p className="text-2xl font-semibold tracking-tight text-[rgb(var(--sift-text))]">
                sift
              </p>
              <div className="flex flex-col gap-5">
                <h2 className="text-3xl leading-tight font-semibold tracking-tight sm:text-4xl lg:text-5xl">
                  Document intelligence you can trust with a sealed contract.
                </h2>
                <p className="max-w-sm text-sm leading-relaxed text-[rgb(var(--sift-text-muted))]">
                  Upload, review, search, and chat. Every answer cites a chunk, or sift refuses.
                </p>
              </div>
            </div>

            <div className="flex flex-col gap-12 border-[rgb(var(--sift-border-strong))] lg:col-span-7 lg:border-l lg:pl-16">
              <div className="rounded-2xl border border-[rgb(var(--sift-border-strong))] bg-[rgb(var(--sift-text)_/_0.04)] p-8 shadow-[inset_0_1px_0_0_rgb(238_238_238_/_0.06)]">
                <div className="mb-5 flex flex-col gap-1">
                  <h3 className="text-base font-semibold text-[rgb(var(--sift-text))]">
                    Open a collection
                  </h3>
                  <p className="text-sm text-[rgb(var(--sift-text-muted))]">
                    Put the contracts in. Keep the citations.
                  </p>
                </div>
                <Button asChild className="rounded-full px-6">
                  <Link href="/signup">Get started</Link>
                </Button>
              </div>

              <div className="grid grid-cols-2 gap-8 sm:grid-cols-3">
                {COLUMNS.map((group) => (
                  <div key={group.title} className="flex flex-col gap-4">
                    <h4 className="text-xs font-semibold tracking-wider text-[rgb(var(--sift-text))] uppercase">
                      {group.title}
                    </h4>
                    <ul className="flex flex-col gap-3">
                      {group.links.map((link) => (
                        <li key={link.label}>
                          <HashLink href={link.href}>{link.label}</HashLink>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </FadeContent>

      <div className="mx-auto max-w-7xl px-6 md:px-12">
        <Separator className="mt-12 bg-[rgb(var(--sift-border-strong))] opacity-60" />
        <div className="flex items-center py-6">
          <p className="text-xs text-[rgb(var(--sift-text-muted))]">sift</p>
        </div>
      </div>
    </footer>
  );
}
