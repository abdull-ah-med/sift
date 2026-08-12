import { FileUp, MessageSquareQuote, ScanLine, Search } from "lucide-react";
import { Card, CardContent } from "@sift/ui";

const CELLS = [
  {
    title: "Upload",
    body: "Private object storage. Files are hashed before they become documents in a collection.",
    icon: FileUp,
    span: "md:col-span-2",
  },
  {
    title: "Review",
    body: "Human sign-off on extractions before they become truth. Bounding boxes on the page, not a guess.",
    icon: ScanLine,
    span: "md:col-span-1",
  },
  {
    title: "Search",
    body: "Hybrid retrieval with provenance. Every hit carries document, page, and chunk identity.",
    icon: Search,
    span: "md:col-span-1",
  },
  {
    title: "Cited chat",
    body: "Answers that cite chunks, or refuse. Hallucinated citations are dropped before they reach the thread.",
    icon: MessageSquareQuote,
    span: "md:col-span-2",
  },
] as const;

/** Feature grid — watermelon feature-1 structure, lucide, sift copy. */
export function FeatureBento() {
  return (
    <section id="product" className="mx-auto max-w-6xl px-6 py-24">
      <h2 className="max-w-2xl text-2xl font-semibold tracking-tight md:text-3xl">
        One product, four surfaces that stay honest about the corpus.
      </h2>
      <p className="mt-3 max-w-2xl text-[rgb(var(--sift-text-muted))]">
        sift is built for collections you cannot afford to leak or misquote.
      </p>
      <div className="mt-12 grid gap-4 md:grid-cols-3">
        {CELLS.map((cell) => {
          const Icon = cell.icon;
          return (
            <Card key={cell.title} className={cell.span}>
              <CardContent className="flex h-full flex-col gap-4 p-6">
                <Icon
                  size={20}
                  strokeWidth={1.5}
                  className="text-[rgb(var(--sift-text-muted))]"
                  aria-hidden
                />
                <h3 className="text-sm font-medium">{cell.title}</h3>
                <p className="text-sm text-[rgb(var(--sift-text-muted))]">{cell.body}</p>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </section>
  );
}
