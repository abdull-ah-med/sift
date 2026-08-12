import { MarketingHero } from "@/components/marketing/MarketingHero";
import { SiteFooter } from "@/components/marketing/SiteFooter";
import { SiteHeader } from "@/components/marketing/SiteHeader";

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />
      <MarketingHero />
      <section className="mx-auto max-w-6xl px-6 pb-24">
        <h2 className="text-2xl font-semibold tracking-tight">One product story</h2>
        <p className="mt-3 max-w-2xl text-[rgb(var(--sift-text-muted))]">
          Upload sensitive PDFs, review extractions, search with hybrid retrieval, and chat with
          answers that cite the chunks they came from.
        </p>
      </section>
      <div className="mt-auto">
        <SiteFooter />
      </div>
    </div>
  );
}
