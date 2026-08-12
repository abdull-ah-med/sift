import type { Metadata } from "next";
import { SiteFooter } from "@/components/marketing/SiteFooter";
import { SiteHeader } from "@/components/marketing/SiteHeader";

export const metadata: Metadata = {
  title: "Terms",
};

export default function TermsPage() {
  return (
    <div className="flex min-h-[100dvh] flex-col">
      <SiteHeader />
      <main id="main" className="sift-app-main mx-auto w-full max-w-2xl flex-1 px-6 py-16">
        <h1 className="text-2xl font-semibold tracking-tight">Terms</h1>
        <div className="mt-6 space-y-4 text-sm text-[rgb(var(--sift-text-muted))]">
          <p>
            sift is software for tenant-scoped document collections: upload, review, search, and
            cited chat. You are responsible for the documents you put in a collection and for who
            you invite.
          </p>
          <p>
            Do not use sift to process data you are not allowed to store. Access is gated by
            tenant membership, collection ACL, and API scopes.
          </p>
          <p>
            These terms are a working stub for the current release. Counsel-reviewed terms will
            replace them before a public production launch.
          </p>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
