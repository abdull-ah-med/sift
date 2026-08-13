import { SiteFooter } from "@/components/marketing/SiteFooter";
import { SiteHeader } from "@/components/marketing/SiteHeader";
import { HashLink } from "@/components/marketing/HashLink";
import { LEGAL_LINKS } from "@/components/marketing/legal";

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
