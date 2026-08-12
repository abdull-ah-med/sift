import { FileUp, MessageSquareQuote, ScanLine, Search, ShieldCheck } from "lucide-react";
import { Card, CardContent } from "@sift/ui";

const ICON_WELL =
  "mb-3 flex size-10 items-center justify-center rounded-lg border border-[rgb(var(--sift-border))] bg-[rgb(var(--sift-bg))]";
const CHIP =
  "inline-flex items-center rounded-md border border-[rgb(var(--sift-border))] bg-[rgb(var(--sift-bg))] px-2 py-1 text-[10px] font-medium text-[rgb(var(--sift-text-muted))]";

/** Watermelon feature-1 grid, lucide, sift copy. No fake uptime. */
export function FeatureBento() {
  return (
    <section id="product" className="flex w-full flex-col items-center px-6 py-24">
      <h2 className="mb-12 max-w-3xl text-center text-2xl font-semibold tracking-tight md:text-3xl">
        One product, four surfaces that stay honest about the corpus.
      </h2>
      <div className="grid w-full max-w-6xl grid-cols-1 gap-4 md:grid-cols-3">
        <Card className="rounded-xl">
          <CardContent className="p-6">
            <div className={ICON_WELL}>
              <FileUp size={20} strokeWidth={1.5} className="text-[rgb(var(--sift-text-muted))]" aria-hidden />
            </div>
            <h3 className="text-lg font-medium">Upload</h3>
            <p className="mb-3 mt-1 text-sm text-[rgb(var(--sift-text-muted))]">
              Private object storage. Files are hashed before they become documents in a collection.
            </p>
            <span className={CHIP}>Hashed at rest</span>
          </CardContent>
        </Card>

        <Card className="rounded-xl">
          <CardContent className="p-6">
            <div className={ICON_WELL}>
              <ScanLine size={20} strokeWidth={1.5} className="text-[rgb(var(--sift-text-muted))]" aria-hidden />
            </div>
            <h3 className="text-lg font-medium">Review</h3>
            <p className="mb-3 mt-1 text-sm text-[rgb(var(--sift-text-muted))]">
              Human sign-off on extractions before they become truth. Bounding boxes on the page, not a
              guess.
            </p>
            <span className={CHIP}>Page-grounded</span>
          </CardContent>
        </Card>

        <Card className="row-span-2 flex flex-col justify-between rounded-xl">
          <CardContent className="p-6">
            <div className={ICON_WELL}>
              <MessageSquareQuote
                size={20}
                strokeWidth={1.5}
                className="text-[rgb(var(--sift-text-muted))]"
                aria-hidden
              />
            </div>
            <h3 className="text-lg font-medium">Cited chat</h3>
            <p className="mb-6 mt-1 text-sm text-[rgb(var(--sift-text-muted))]">
              Answers that cite chunks, or refuse. Hallucinated citations are dropped before they reach
              the thread.
            </p>
            <div className="space-y-3">
              <div className="flex items-center justify-between rounded-md bg-[rgb(var(--sift-bg))] px-3 py-2 text-xs">
                <span className="text-[rgb(var(--sift-text-muted))]">Citations</span>
                <span className="font-medium">Required</span>
              </div>
              <div className="flex items-center justify-between rounded-md bg-[rgb(var(--sift-bg))] px-3 py-2 text-xs">
                <span className="text-[rgb(var(--sift-text-muted))]">Tenant isolation</span>
                <span className="font-medium">RLS</span>
              </div>
              <div className="flex items-center justify-between rounded-md bg-[rgb(var(--sift-bg))] px-3 py-2 text-xs">
                <span className="text-[rgb(var(--sift-text-muted))]">Review gate</span>
                <span className="font-medium">Policy</span>
              </div>
            </div>
          </CardContent>
          <div className="px-6 pb-6">
            <span className={CHIP}>No hallucinated citations</span>
          </div>
        </Card>

        <Card className="rounded-xl">
          <CardContent className="p-6">
            <div className={ICON_WELL}>
              <Search size={20} strokeWidth={1.5} className="text-[rgb(var(--sift-text-muted))]" aria-hidden />
            </div>
            <h3 className="text-lg font-medium">Search</h3>
            <p className="mb-3 mt-1 text-sm text-[rgb(var(--sift-text-muted))]">
              Hybrid retrieval with provenance. Every hit carries document, page, and chunk identity.
            </p>
            <span className={CHIP}>Hybrid retrieval</span>
          </CardContent>
        </Card>

        <Card className="rounded-xl">
          <CardContent className="p-6">
            <div className={ICON_WELL}>
              <ShieldCheck size={20} strokeWidth={1.5} className="text-[rgb(var(--sift-text-muted))]" aria-hidden />
            </div>
            <h3 className="text-lg font-medium">Sealed by default</h3>
            <p className="mb-3 mt-1 text-sm text-[rgb(var(--sift-text-muted))]">
              Collections stay in your tenant. Chat audits store a query hash, not the raw question.
            </p>
            <span className={CHIP}>Hash, not plaintext</span>
          </CardContent>
        </Card>
      </div>
    </section>
  );
}
