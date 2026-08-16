import type { Metadata } from "next";
import { LegalCallout, LegalDoc, LegalSection } from "@/components/marketing/LegalDoc";
import { HashLink } from "@/components/marketing/HashLink";

export const metadata: Metadata = {
  title: "Mission",
};

export default function MissionPage() {
  return (
    <LegalDoc
      title="Mission"
      description="Document intelligence with a sealed contract: retrieve the passage, cite it, or refuse. This page is intent. It is not a warranty."
    >
      <LegalCallout>
        Design goals on this page do not modify the{" "}
        <HashLink href="/terms">Terms of Service</HashLink>. If this page and the Terms
        conflict, the Terms control.
      </LegalCallout>

      <LegalSection title="The job">
        <p>
          People put sensitive PDFs into software — contracts, records, research — and need to
          know what is on the page without a model inventing a clause that is not there. sift
          exists to keep that work honest: retrieve the passage, cite it, or refuse.
        </p>
      </LegalSection>

      <LegalSection title="Four surfaces">
        <p>
          Upload into a tenant-scoped collection. Review extractions on the page before they
          become searchable truth when policy requires it. Search with retrieval that carries
          document, page, and chunk identity. Chat only with citations. One product, four
          surfaces, one rule we build toward: nothing reaches the thread without a source.
        </p>
      </LegalSection>

      <LegalSection title="What we build toward">
        <p>
          We build so that guesses are not dressed as citations, so that chat audits store a
          query hash instead of the raw question, and so that one tenant’s corpus is not mixed
          into another’s retrieval set through the product’s access path. We do not present a
          model as a lawyer, a clinician, or a witness. Those are engineering aims. They are
          not promises that every run succeeds. See{" "}
          <HashLink href="/ai">Use of AI</HashLink> and{" "}
          <HashLink href="/data">Data Policy</HashLink>.
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
