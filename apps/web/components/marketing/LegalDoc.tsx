import { SiteFooter } from "@/components/marketing/SiteFooter";
import { SiteHeader } from "@/components/marketing/SiteHeader";
import { HashLink } from "@/components/marketing/HashLink";
import { LEGAL_LINKS } from "@/components/marketing/legal";

const CONTACT = "contactabdullahahmed@gmail.com";
const EFFECTIVE = "13 August 2026";

export function LegalDoc({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-[100dvh] flex-col bg-[rgb(var(--sift-bg))]">
      <SiteHeader />
      <main id="main" className="sift-app-main mx-auto w-full max-w-[72ch] flex-1 px-6 pt-32 pb-24">
        <p className="text-xs font-medium tracking-wider text-[rgb(var(--sift-text-muted))] uppercase">
          sift
        </p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight md:text-4xl">{title}</h1>
        <p className="mt-4 text-base leading-relaxed text-[rgb(var(--sift-text-muted))]">
          {description}
        </p>
        <p className="mt-3 text-xs text-[rgb(var(--sift-text-muted))]">
          Effective {EFFECTIVE}. Contact:{" "}
          <a
            href={`mailto:${CONTACT}`}
            className="text-[rgb(var(--sift-text))] underline-offset-4 hover:underline"
          >
            {CONTACT}
          </a>
          . These pages are product terms for this release. They are not a substitute for advice
          from your own counsel.
        </p>
        <div className="mt-12 space-y-10 text-sm leading-[1.7] text-[rgb(var(--sift-text-muted))]">
          {children}
        </div>
        <nav
          aria-label="Other policies"
          className="mt-16 flex flex-wrap gap-x-6 gap-y-3 border-t border-[rgb(var(--sift-border-strong))] pt-8"
        >
          {LEGAL_LINKS.map((link) => (
            <HashLink key={link.href} href={link.href} className="text-xs">
              {link.label}
            </HashLink>
          ))}
        </nav>
      </main>
      <SiteFooter />
    </div>
  );
}

export function LegalSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h2 className="mb-3 text-base font-semibold tracking-tight text-[rgb(var(--sift-text))]">
        {title}
      </h2>
      <div className="space-y-3">{children}</div>
    </section>
  );
}

export function LegalCallout({ children }: { children: React.ReactNode }) {
  return (
    <aside className="rounded-xl border border-[rgb(var(--sift-border-strong))] bg-[rgb(var(--sift-text)_/_0.04)] p-4 text-sm leading-relaxed text-[rgb(var(--sift-text))]">
      {children}
    </aside>
  );
}

export function LegalList({ items }: { items: React.ReactNode[] }) {
  return (
    <ul className="list-disc space-y-2 pl-5">
      {items.map((item, i) => (
        <li key={i}>{item}</li>
      ))}
    </ul>
  );
}

export function LegalDisclaimer({ children }: { children: React.ReactNode }) {
  return (
    <p className="rounded-xl border border-[rgb(var(--sift-border-strong))] p-4 text-xs leading-relaxed font-medium tracking-wide text-[rgb(var(--sift-text))] uppercase">
      {children}
    </p>
  );
}
