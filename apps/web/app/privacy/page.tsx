import type { Metadata } from "next";
import { SiteFooter } from "@/components/marketing/SiteFooter";
import { SiteHeader } from "@/components/marketing/SiteHeader";

export const metadata: Metadata = {
  title: "Privacy",
};

export default function PrivacyPage() {
  return (
    <div className="flex min-h-[100dvh] flex-col">
      <SiteHeader />
      <main id="main" className="sift-app-main mx-auto w-full max-w-2xl flex-1 px-6 py-16">
        <h1 className="text-2xl font-semibold tracking-tight">Privacy</h1>
        <div className="mt-6 space-y-4 text-sm text-[rgb(var(--sift-text-muted))]">
          <p>
            sift is built so document contents stay in your tenant. Chat audits store a query hash
            and identifiers, not the raw question or chunk text.
          </p>
          <p>
            Authentication uses Zitadel for people and API keys for machines. Keys are shown once
            at creation and are not logged.
          </p>
          <p>
            This page is the product privacy summary for the current release. A counsel-reviewed
            policy will replace it before a public production launch.
          </p>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
