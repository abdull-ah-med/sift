const STEPS = [
  {
    n: "01",
    title: "Create a collection",
    body: "A tenant-scoped corpus with its own policy, documents, and chat sessions.",
  },
  {
    n: "02",
    title: "Upload the files",
    body: "PDFs land in object storage, parse into blocks, and wait for review when policy requires it.",
  },
  {
    n: "03",
    title: "Review extractions",
    body: "Confirm what the parser saw on the page. Nothing becomes searchable truth until you say so.",
  },
  {
    n: "04",
    title: "Search and chat",
    body: "Hybrid search and collection chat both return citations. If the chunks are not enough, sift says so.",
  },
] as const;

/** Sequential journey — numbered because the product path is ordered. */
export function HowItWorks() {
  return (
    <section id="how-it-works" className="mx-auto max-w-6xl px-6 py-24">
      <h2 className="text-2xl font-semibold tracking-tight md:text-3xl">How it works</h2>
      <ol className="mt-12 grid gap-8 md:grid-cols-2">
        {STEPS.map((step) => (
          <li key={step.n} className="flex gap-4">
            <span className="font-mono text-sm text-[rgb(var(--sift-text-muted))] tabular-nums">
              {step.n}
            </span>
            <div>
              <h3 className="text-sm font-medium">{step.title}</h3>
              <p className="mt-2 text-sm text-[rgb(var(--sift-text-muted))]">{step.body}</p>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
