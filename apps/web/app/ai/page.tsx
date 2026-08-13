import type { Metadata } from "next";
import { LegalDoc, LegalSection } from "@/components/marketing/LegalDoc";
import { HashLink } from "@/components/marketing/HashLink";

export const metadata: Metadata = {
  title: "Use of AI",
};

export default function UseOfAiPage() {
  return (
    <LegalDoc
      title="Use of AI"
      description="sift uses models to extract, retrieve, and answer. Every answer that reaches a thread must cite a chunk, or sift refuses."
    >
      <LegalSection title="What the model is for">
        <p>
          Models in sift do three jobs: help parse documents into blocks, retrieve passages from
          your collection, and draft answers from those passages. They are not a general chatbot
          over the open web, and they are not a substitute for reading the source page.
        </p>
      </LegalSection>

      <LegalSection title="Cited or refused">
        <p>
          Collection chat answers from retrieved chunks. If the chunks are not enough, sift says
          so. Citations are required. Hallucinated citations are dropped before they reach the
          thread. You can open the cited page in review and see the bounding box, not a paraphrase
          presented as fact.
        </p>
      </LegalSection>

      <LegalSection title="Human review">
        <p>
          When collection policy requires it, extractions do not become searchable truth until a
          person confirms what the parser saw on the page. The review surface is the document, not
          a summary of the document.
        </p>
      </LegalSection>

      <LegalSection title="Your responsibility">
        <p>
          You remain responsible for the documents you put in a collection and for how you use
          model output. Treat answers as leads back to a source. Do not rely on an uncited claim.
        </p>
      </LegalSection>

      <LegalSection title="Related">
        <p>
          Audit hashing and tenant isolation are in the{" "}
          <HashLink href="/privacy">Privacy Policy</HashLink> and{" "}
          <HashLink href="/data">Data Policy</HashLink>.
        </p>
      </LegalSection>
    </LegalDoc>
  );
}
