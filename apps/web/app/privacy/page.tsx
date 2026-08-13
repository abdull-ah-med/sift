import type { Metadata } from "next";
import { LegalDoc, LegalSection } from "@/components/marketing/LegalDoc";
import { HashLink } from "@/components/marketing/HashLink";

export const metadata: Metadata = {
  title: "Privacy Policy",
};

export default function PrivacyPage() {
  return (
    <LegalDoc
      title="Privacy Policy"
      description="How sift handles identity, documents, and audit records in this release. This is the product summary, not a counsel-reviewed contract."
    >
      <LegalSection title="What this page covers">
        <p>
          sift is software for tenant-scoped document collections. This page describes what the
          product stores, what it hashes, and what it does not write into audit logs. A
          counsel-reviewed policy will replace it before a public production launch.
        </p>
      </LegalSection>

      <LegalSection title="Documents stay in your tenant">
        <p>
          Files you upload become documents in a collection you control. Collection data is isolated
          by tenant. Access is gated by tenant membership, collection ACL, and API scopes. Other
          tenants cannot read your corpus through the product.
        </p>
      </LegalSection>

      <LegalSection title="What audits record">
        <p>
          Search and chat audits store a query hash and identifiers (collection, request). They do
          not store the raw question or chunk text. Chat answers that cannot be cited are refused;
          hallucinated citations are dropped before they reach the thread.
        </p>
      </LegalSection>

      <LegalSection title="Authentication">
        <p>
          People sign in with Zitadel. Machines use API keys. Keys are shown once at creation and
          are not logged. You are responsible for who you invite into a tenant and which keys you
          issue.
        </p>
      </LegalSection>

      <LegalSection title="Related">
        <p>
          How models are used is described in <HashLink href="/ai">Use of AI</HashLink>. What is
          stored, hashed, and isolated is described in{" "}
          <HashLink href="/data">Data Policy</HashLink>.
        </p>
      </LegalSection>
    </LegalDoc>
  );
}
