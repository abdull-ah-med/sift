import type { Metadata } from "next";
import { LegalDoc, LegalSection } from "@/components/marketing/LegalDoc";
import { HashLink } from "@/components/marketing/HashLink";

export const metadata: Metadata = {
  title: "Data Policy",
};

export default function DataPolicyPage() {
  return (
    <LegalDoc
      title="Data Policy"
      description="What sift stores, what it hashes, and how collection data is isolated. This is the product summary for the current release."
    >
      <LegalSection title="Collections">
        <p>
          A collection is a tenant-scoped corpus: documents, parse blocks, review decisions, search
          index, and chat sessions. Files land in private object storage and are hashed before they
          become documents. Nothing in another tenant’s collection is visible through the product.
        </p>
      </LegalSection>

      <LegalSection title="Row-level isolation">
        <p>
          Database access for collection data is enforced with tenant row-level security. API
          routes require the caller’s tenant, collection ACL, and the matching API scope. Wrong
          tenant and wrong scope are denied.
        </p>
      </LegalSection>

      <LegalSection title="Hashes, not plaintext questions">
        <p>
          Search and chat write a SHA-256 query hash into the audit record, plus identifiers. The
          raw question and the retrieved chunk text are not stored in that audit payload. API keys
          are shown once at creation and are not logged.
        </p>
      </LegalSection>

      <LegalSection title="Retention and deletion">
        <p>
          Workspace admins control who is in the tenant and which collections exist. Deleting a
          document or collection through the product removes it from that workspace’s corpus. This
          page does not invent a retention schedule; use the product controls, or contact the
          operator who hosts your deployment.
        </p>
      </LegalSection>

      <LegalSection title="Related">
        <p>
          Identity and audit hashing: <HashLink href="/privacy">Privacy Policy</HashLink>. Model
          behavior: <HashLink href="/ai">Use of AI</HashLink>.
        </p>
      </LegalSection>
    </LegalDoc>
  );
}
