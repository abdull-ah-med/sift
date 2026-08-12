const CELLS = [
  {
    title: "Upload",
    body: "Private object storage. Files are hashed before they become documents in a collection.",
    span: "md:col-span-2",
  },
  {
    title: "Review",
    body: "Human sign-off on extractions before they become truth. Bounding boxes on the page, not a guess.",
    span: "md:col-span-1",
  },
  {
    title: "Search",
    body: "Hybrid retrieval with provenance. Every hit carries document, page, and chunk identity.",
    span: "md:col-span-1",
  },
  {
    title: "Cited chat",
    body: "Answers that cite chunks, or refuse. Hallucinated citations are dropped before they reach the thread.",
    span: "md:col-span-2",
  },
] as const;

/** Product-story bento — shadcn bento-1 structure, sift tokens. */
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
        {CELLS.map((cell) => (
          <article
            key={cell.title}
            className={`rounded-lg border border-[rgb(var(--sift-border))] bg-[rgb(var(--sift-surface))] p-6 ${cell.span}`}
          >
            <h3 className="text-sm font-medium">{cell.title}</h3>
            <p className="mt-2 text-sm text-[rgb(var(--sift-text-muted))]">{cell.body}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
