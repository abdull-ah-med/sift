import type { Metadata } from "next";
import { LegalDoc, LegalSection } from "@/components/marketing/LegalDoc";
import { HashLink } from "@/components/marketing/HashLink";

export const metadata: Metadata = {
  title: "Mission",
};

export default function MissionPage() {
  return (
    <LegalDoc
      title="Mission"
      description="Document intelligence you can trust with a sealed contract."
    >
      <LegalSection title="The job">
        <p>
          People put sensitive PDFs into software and need to know what is in them — contracts,
          records, research — without a model inventing a clause that is not on the page. sift’s
          job is to keep that work honest: retrieve the passage, cite it, or refuse.
        </p>
      </LegalSection>

      <LegalSection title="Four surfaces">
        <p>
          Upload into a tenant-scoped collection. Review extractions on the page before they become
          truth. Search with hybrid retrieval that carries document, page, and chunk identity. Chat
          only with citations. One product, four surfaces, one rule: nothing reaches the thread
          without a source.
        </p>
      </LegalSection>

      <LegalSection title="What we will not do">
        <p>
          We will not dress a guess as a citation. We will not store raw questions in chat audits
          when a hash will do. We will not mix one tenant’s corpus with another’s. We will not
          pretend a model is a lawyer, a clinician, or a witness.
        </p>
      </LegalSection>

      <LegalSection title="How to start">
        <p>
          Open a collection. Put the contracts in. Keep the citations.{" "}
          <HashLink href="/signup">Get started</HashLink>
          {" · "}
          <HashLink href="/#product">Product</HashLink>
        </p>
      </LegalSection>
    </LegalDoc>
  );
}
