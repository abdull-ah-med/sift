"use client";

import { FileUp, MessageSquareQuote, ScanLine, Search, ShieldCheck } from "lucide-react";
import { Card, CardContent } from "@sift/ui";
import AnimatedContent from "@/components/bits/AnimatedContent";
import SplitText from "@/components/bits/SplitText";

const ICON_FRAME = "mb-2 size-fit rounded-lg p-px";
const ICON_WELL =
  "flex h-10 w-10 items-center justify-center rounded-lg border border-[rgb(var(--sift-border-strong))] bg-[rgb(var(--sift-text)_/_0.04)]";
const CHIP_FRAME = "inline-flex rounded-lg p-0.5";
const CHIP =
  "inline-flex items-center rounded-md border border-[rgb(var(--sift-border-strong))] bg-[rgb(var(--sift-text)_/_0.04)] px-2 py-1 text-[10px] font-medium text-[rgb(var(--sift-text-muted))]";
const CARD =
  "rounded-xl border border-[rgb(var(--sift-border-strong))] bg-[rgb(var(--sift-surface)/0.42)] shadow-[inset_0_1px_0_0_rgb(238_238_238_/_0.06)] ring-0 transition-[border-color] duration-150 ease-[var(--ease-out)] hover:border-[rgb(238_238_238_/_0.22)]";
const STAT =
  "flex items-center justify-between rounded-md border border-[rgb(var(--sift-border-strong))] bg-[rgb(var(--sift-text)_/_0.04)] px-3 py-2 text-xs";

/** Watermelon feature-1 bento, lucide, sift copy. No fake uptime. */
export function FeatureBento() {
  return (
    <section id="product" className="flex w-full scroll-mt-32 flex-col items-center px-6 py-16 md:px-12">
      <div className="mb-12 flex w-full max-w-3xl justify-center">
        <SplitText
          tag="h2"
          text="One product, four surfaces that stay honest about the corpus."
          className="text-3xl leading-[0.98] font-semibold tracking-tight md:text-5xl"
          textAlign="center"
          splitType="words"
          delay={40}
          duration={0.45}
          ease="power2.out"
          from={{ opacity: 0, y: 12 }}
          to={{ opacity: 1, y: 0 }}
        />
      </div>
      <div className="grid w-full max-w-7xl grid-cols-1 gap-4 md:grid-cols-3">
        <AnimatedContent delay={0} duration={0.4} distance={12}>
          <Card className={CARD}>
            <CardContent className="p-6">
              <div className={ICON_FRAME}>
                <div className={ICON_WELL}>
                  <FileUp size={20} strokeWidth={1.5} className="text-[rgb(var(--sift-text-muted))]" aria-hidden />
                </div>
              </div>
              <h3 className="text-lg font-medium">Upload</h3>
              <p className="mb-3 mt-1 text-sm text-[rgb(var(--sift-text-muted))]">
                Private object storage. Files are hashed before they become documents in a collection.
              </p>
              <div className={CHIP_FRAME}>
                <span className={CHIP}>Hashed at rest</span>
              </div>
            </CardContent>
          </Card>
        </AnimatedContent>

        <AnimatedContent delay={0.05} duration={0.4} distance={12}>
          <Card className={CARD}>
            <CardContent className="p-6">
              <div className={ICON_FRAME}>
                <div className={ICON_WELL}>
                  <ScanLine size={20} strokeWidth={1.5} className="text-[rgb(var(--sift-text-muted))]" aria-hidden />
                </div>
              </div>
              <h3 className="mb-1 text-lg font-medium">Review</h3>
              <p className="mb-3 text-sm text-[rgb(var(--sift-text-muted))]">
                Human sign-off on extractions before they become truth. Bounding boxes on the page, not a
                guess.
              </p>
              <div className={CHIP_FRAME}>
                <span className={CHIP}>Page-grounded</span>
              </div>
            </CardContent>
          </Card>
        </AnimatedContent>

        <AnimatedContent delay={0.1} duration={0.4} distance={12} className="row-span-2 h-full">
          <Card className={`${CARD} flex h-full flex-col justify-between`}>
            <CardContent className="p-6">
              <div className={`${ICON_FRAME} mb-3`}>
                <div className={ICON_WELL}>
                  <MessageSquareQuote
                    size={20}
                    strokeWidth={1.5}
                    className="text-[rgb(var(--sift-text-muted))]"
                    aria-hidden
                  />
                </div>
              </div>
              <h3 className="mb-2 text-lg font-medium">Cited chat</h3>
              <p className="mb-6 text-sm text-[rgb(var(--sift-text-muted))]">
                Answers that cite chunks, or refuse. Hallucinated citations are dropped before they reach
                the thread.
              </p>
              <div className="space-y-3">
                <div className={STAT}>
                  <span className="text-[rgb(var(--sift-text-muted))]">Citations</span>
                  <span className="font-medium">Required</span>
                </div>
                <div className={STAT}>
                  <span className="text-[rgb(var(--sift-text-muted))]">Tenant isolation</span>
                  <span className="font-medium">RLS</span>
                </div>
                <div className={STAT}>
                  <span className="text-[rgb(var(--sift-text-muted))]">Review gate</span>
                  <span className="font-medium">Policy</span>
                </div>
              </div>
            </CardContent>
            <div className="px-6 pb-6">
              <div className={CHIP_FRAME}>
                <span className={CHIP}>No hallucinated citations</span>
              </div>
            </div>
          </Card>
        </AnimatedContent>

        <AnimatedContent delay={0.15} duration={0.4} distance={12}>
          <Card className={CARD}>
            <CardContent className="p-6">
              <div className={ICON_FRAME}>
                <div className={ICON_WELL}>
                  <Search size={20} strokeWidth={1.5} className="text-[rgb(var(--sift-text-muted))]" aria-hidden />
                </div>
              </div>
              <h3 className="mb-1 text-lg font-medium">Search</h3>
              <p className="mb-3 text-sm text-[rgb(var(--sift-text-muted))]">
                Hybrid retrieval with provenance. Every hit carries document, page, and chunk identity.
              </p>
              <div className={CHIP_FRAME}>
                <span className={CHIP}>Hybrid retrieval</span>
              </div>
            </CardContent>
          </Card>
        </AnimatedContent>

        <AnimatedContent delay={0.2} duration={0.4} distance={12}>
          <Card className={CARD}>
            <CardContent className="p-6">
              <div className={ICON_FRAME}>
                <div className={ICON_WELL}>
                  <ShieldCheck
                    size={20}
                    strokeWidth={1.5}
                    className="text-[rgb(var(--sift-text-muted))]"
                    aria-hidden
                  />
                </div>
              </div>
              <h3 className="mb-1 text-lg font-medium">Sealed by default</h3>
              <p className="mb-3 text-sm text-[rgb(var(--sift-text-muted))]">
                Collections stay in your tenant. Chat audits store a query hash, not the raw question.
              </p>
              <div className={CHIP_FRAME}>
                <span className={CHIP}>Hash, not plaintext</span>
              </div>
            </CardContent>
          </Card>
        </AnimatedContent>
      </div>
    </section>
  );
}
