import type { Metadata } from "next";
import { LegalDoc, LegalSection } from "@/components/marketing/LegalDoc";
import { HashLink } from "@/components/marketing/HashLink";

export const metadata: Metadata = {
  title: "Terms of Service",
};

export default function TermsPage() {
  return (
    <LegalDoc
      title="Terms of Service"
      description="Working terms for this release of sift. Counsel-reviewed terms will replace them before a public production launch."
    >
      <LegalSection title="The product">
        <p>
          sift is software for tenant-scoped document collections: upload, review, search, and
          cited chat. By using a hosted or self-managed deployment, you agree to use it only on
          documents you are allowed to store and only with people you are allowed to invite.
        </p>
      </LegalSection>

      <LegalSection title="Accounts and access">
        <p>
          Access is gated by tenant membership, collection ACL, and API scopes. You are responsible
          for the documents you put in a collection, for invite tokens you share, and for API keys
          you create. Do not share keys. Do not attempt to reach another tenant’s corpus.
        </p>
      </LegalSection>

      <LegalSection title="Acceptable use">
        <p>
          Do not use sift to process data you are not allowed to store. Do not interfere with
          isolation, audit hashing, or the review gate. Do not present an uncited model answer as
          a source of truth.
        </p>
      </LegalSection>

      <LegalSection title="Model output">
        <p>
          Chat and extraction are assistive. Answers that cannot be cited are refused. You remain
          responsible for decisions you make after reading a citation. See{" "}
          <HashLink href="/ai">Use of AI</HashLink>.
        </p>
      </LegalSection>

      <LegalSection title="Availability">
        <p>
          This release does not promise uptime, indemnities, or a service-level credit. If you
          operate the deployment, you set those terms with your users.
        </p>
      </LegalSection>
    </LegalDoc>
  );
}
