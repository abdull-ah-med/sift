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
  title: "Use of AI",
};

export default function UseOfAiPage() {
  return (
    <LegalDoc
      title="Use of AI"
      description="You are interacting with an AI system. Outputs can be wrong even when a citation is attached. Verify the page before you rely on anything."
    >
      <LegalCallout>
        Collection chat, extraction, and related drafts are produced by a model, not by a
        person. This notice is given at the latest when you open those surfaces. It is not
        obvious that a cited answer is correct. Treat every answer as a pointer back to a
        source you must read.
      </LegalCallout>

      <LegalSection title="1. What the system does">
        <p>
          Models in a sift deployment may: parse documents into blocks, embed chunks, retrieve
          passages, and draft answers from those passages. They are not a search engine over the
          open web. They are not a lawyer, clinician, auditor, or witness.
        </p>
      </LegalSection>

      <LegalSection title="2. Cite or refuse is a design, not a guarantee">
        <p>
          The product is built so that a chat answer that reaches the thread should cite chunk
          identifiers, and so that answers without a usable citation are marked insufficient.
          Filters attempt to drop citations that were not retrieved. That design reduces some
          failures. It does not eliminate them.
        </p>
        <LegalList
          items={[
            "Retrieval can miss the relevant page.",
            "A cited chunk can be the wrong span, an incomplete clause, or an outdated exhibit.",
            "A model can still misread a cited passage.",
            "Review gates apply only when collection policy requires them, and only to the extent a person actually reviews.",
          ]}
        />
      </LegalSection>

      <LegalSection title="3. Human review before consequential use">
        <p>
          You must have a qualified person verify model output against the source document
          before you use it for any consequential purpose, including legal advice, medical or
          clinical decisions, credit, employment, insurance, eligibility, safety, or any
          decision that produces legal or similarly significant effects. If you skip that
          review, you assume the risk.
        </p>
      </LegalSection>

      <LegalSection title="4. Not professional advice">
        <p>
          Nothing the model produces is legal, medical, tax, accounting, investment, or other
          professional advice. Citations do not make it advice. Your use of outputs is at your
          sole risk.
        </p>
      </LegalSection>

      <LegalSection title="5. Who runs the model">
        <p>
          Chat generation runs only if the operator has configured an inference API. Embeddings
          run on the embedding service the operator configures. Retrieved text and prompts leave
          the application and are processed by that provider under that provider’s terms,
          retention, and location. sift does not control those providers and does not warrant
          their practices. If no chat model is configured, the product refuses to invent an
          answer.
        </p>
      </LegalSection>

      <LegalSection title="6. Training">
        <p>
          sift does not use your documents to train a sift-owned foundation model. Configured
          inference and embedding providers have their own terms. Read those terms before you
          enable a provider. If you require that a provider not train on your prompts, that is
          a contract you make with that provider, not a promise this page can make for them.
        </p>
      </LegalSection>

      <LegalSection title="7. Your role under AI law">
        <p>
          You (or your organisation) decide the use case. You are the deployer of the system
          for that use. High-risk uses, prohibited uses, and transparency duties that apply to
          your sector remain yours. This page does not classify sift as high-risk or as
          exempt. We disclose that interaction is with a model so that fact is not hidden in
          marketing.
        </p>
      </LegalSection>

      <LegalSection title="8. Accuracy representations">
        <p>
          We do not represent that outputs are the best possible, complete, current, or free of
          error. We represent how the product is designed (retrieve, cite, or refuse). If
          marketing copy and this page conflict, this page and the{" "}
          <HashLink href="/terms">Terms of Service</HashLink> control.
        </p>
      </LegalSection>

      <LegalDisclaimer>
        Model output is probabilistic. You will not rely on it as a sole source of truth. We
        are not liable for decisions you make after reading an answer, a citation, or an
        extraction, except as the Terms of Service expressly allow. Human verification of the
        source page is a condition of use for consequential decisions.
      </LegalDisclaimer>
    </LegalDoc>
  );
}
