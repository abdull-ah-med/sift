import type { Metadata } from "next";
import {
  LegalCallout,
  LegalDisclaimer,
  LegalDoc,
  LegalList,
  LegalSection,
} from "@/components/marketing/LegalDoc";
import { HashLink } from "@/components/marketing/HashLink";

export const metadata: Metadata = {
  title: "Data Policy",
};

export default function DataPolicyPage() {
  return (
    <LegalDoc
      title="Data Policy"
      description="How collection data is stored, isolated, hashed, and sent to configured processors. This is an operational policy, not a certification."
    >
      <LegalSection title="1. Roles">
        <p>
          You own the documents you put in a collection. The operator of the deployment
          processes them to provide the service. The software author does not become the owner
          of your corpus by running or publishing sift.
        </p>
      </LegalSection>

      <LegalSection title="2. What a collection holds">
        <LegalList
          items={[
            "Object bytes in private object storage, with a content hash recorded before the file becomes a document.",
            "Parse blocks, page geometry, and review decisions.",
            "Chunk text and dense embeddings in the application database and, when enabled, a vector index.",
            "Chat sessions and turns, with citations to chunk identifiers.",
            "Audit rows for search and chat that store a SHA-256 query hash and identifiers, not the raw question or the retrieved chunk text.",
          ]}
        />
      </LegalSection>

      <LegalSection title="3. Isolation">
        <p>
          Collection rows are intended to be readable only under the caller’s tenant, via
          row-level security, collection ACL, and API scopes. Wrong tenant and wrong scope are
          denied. Isolation is a control. It is not a guarantee against misconfiguration,
          stolen credentials, or a vulnerability.
        </p>
      </LegalSection>

      <LegalSection title="4. Processors that may see content">
        <p>
          To embed and to chat, the deployment sends text to services the operator configures.
          That typically includes chunk text (embeddings) and retrieved passages plus the user
          prompt (chat). Those processors may be outside the operator’s network. Their
          retention, training, and subprocessors are not controlled by this policy.
        </p>
        <p>
          If you cannot accept that transfer, do not enable a hosted inference API, and do not
          put those documents in that deployment.
        </p>
      </LegalSection>

      <LegalSection title="5. What we do not do with your corpus">
        <LegalList
          items={[
            "sift does not sell your documents.",
            "sift does not use your documents to train a sift-owned foundation model.",
            "sift does not put raw questions or chunk text into the search/chat audit payload; it stores a query hash.",
            "sift does not mix one tenant’s collection into another tenant’s retrieval set through the product’s access path.",
          ]}
        />
      </LegalSection>

      <LegalSection title="6. Deletion">
        <p>
          Deleting a document or collection in the product removes it from that workspace’s
          live corpus. Indexes and object bytes are deleted as the jobs and storage layer
          allow. Operator backups, logs, and configured inference-provider copies are outside
          that live corpus. If you need a documented purge across backups, that is an
          operational agreement with the operator, not something this page can promise for
          every host.
        </p>
      </LegalSection>

      <LegalSection title="7. Security measures we actually ship">
        <LegalList
          items={[
            "Tenant RLS on collection data paths.",
            "Collection ACL and API scopes on routes.",
            "Query hashing in search and chat audits.",
            "API keys shown once; not written to application logs as secrets.",
            "Optional OpenTelemetry, off by default, which the operator must configure so exporters do not receive raw corpus text.",
          ]}
        />
        <p>
          We do not claim SOC 2, ISO 27001, HIPAA, or GDPR certification on this page. If you
          need those, you obtain them for your deployment.
        </p>
      </LegalSection>

      <LegalSection title="8. Customer instructions">
        <p>
          For document content, the operator processes on the tenant admin’s instructions:
          upload, parse, review, embed, search, chat, delete. Unlawful instructions will be
          refused to the extent the product can detect them. You remain liable for the content.
        </p>
      </LegalSection>

      <LegalCallout>
        Related: <HashLink href="/privacy">Privacy Policy</HashLink> (people and accounts),{" "}
        <HashLink href="/ai">Use of AI</HashLink> (models),{" "}
        <HashLink href="/terms">Terms of Service</HashLink> (risk allocation).
      </LegalCallout>

      <LegalDisclaimer>
        This policy describes intended data handling. It does not expand warranties or
        liability beyond the Terms of Service. No security or isolation statement is a
        guarantee against loss, disclosure, or unavailability.
      </LegalDisclaimer>
    </LegalDoc>
  );
}
