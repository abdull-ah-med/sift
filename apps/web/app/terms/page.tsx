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
  title: "Terms of Service",
};

export default function TermsPage() {
  return (
    <LegalDoc
      title="Terms of Service"
      description="These terms govern access to sift software and any deployment that presents these pages. Using the service is acceptance."
    >
      <LegalSection title="1. Parties and agreement">
        <p>
          These Terms are between you (the individual or organisation using sift) and Abdullah
          Ahmed, who authors the software, together with the operator of the deployment you
          actually use if that is not the author. The sift source is licensed under Apache
          License 2.0. These Terms add conditions for using the product, a hosted instance, and
          model features. If you do not agree, do not use the service.
        </p>
        <p>
          You represent that you have authority to bind your organisation. If you invite others,
          you are responsible for their use.
        </p>
      </LegalSection>

      <LegalSection title="2. The service">
        <p>
          sift provides tenant-scoped document collections: upload, review, search, and cited
          chat. Features, models, and uptime may change. We may suspend or modify the service
          for security, law, or operations. No service-level agreement applies unless you have
          a separate signed writing.
        </p>
      </LegalSection>

      <LegalSection title="3. Accounts, keys, and access">
        <p>
          Access is gated by the identity provider, tenant membership, collection ACL, and API
          scopes. You must keep credentials, API keys, and invite tokens secret. You are
          responsible for all activity under your tenant. We may disable keys or accounts that
          we reasonably believe are compromised or abusive.
        </p>
      </LegalSection>

      <LegalSection title="4. Customer content">
        <p>
          You retain ownership of documents you upload. You grant the operator a limited licence
          to host, parse, embed, retrieve, display, and delete that content solely to provide
          the service to you. You represent that you have all rights and consents needed, that
          the content is lawful to store, and that it does not infringe others’ rights.
        </p>
      </LegalSection>

      <LegalSection title="5. Acceptable use">
        <LegalList
          items={[
            "Do not upload data you are not allowed to store (including other people’s personal data without a basis).",
            "Do not probe, bypass, or disable tenant isolation, ACL, audit hashing, or review gates.",
            "Do not use the service to commit crime, to violate export or sanctions rules, or to build a competing model by scraping the service.",
            "Do not present model output as a human professional opinion or as an uncited source of truth.",
            "Do not use the service for decisions that law requires a qualified human to make, unless a qualified human has verified the source page.",
          ]}
        />
      </LegalSection>

      <LegalSection title="6. Artificial intelligence">
        <LegalCallout>
          Chat and extraction are AI systems. You are not speaking to a person. Outputs can be
          false, incomplete, or wrongly cited. You must verify the source document before any
          consequential use. Full notice: <HashLink href="/ai">Use of AI</HashLink>.
        </LegalCallout>
        <p>
          Model features depend on inference and embedding providers the operator configures.
          Those providers’ terms apply to data they receive. sift does not warrant their
          accuracy, confidentiality, or availability. Cite-or-refuse behaviour is a design
          goal, not a warranty that every answer is correct or that every relevant passage was
          retrieved.
        </p>
      </LegalSection>

      <LegalSection title="7. Intellectual property">
        <p>
          sift software, marks, and product copy remain ours or our licensors’. Apache 2.0
          governs the source. You get no right to our marks. We get no ownership of your
          documents. Model output is provided to you as-is; we do not warrant that you own it
          or that it is free of third-party claims.
        </p>
      </LegalSection>

      <LegalSection title="8. Third parties">
        <p>
          Identity, storage, databases, embeddings, inference, and observability may be provided
          by third parties. We are not responsible for their acts or outages except as a
          separate written agreement says. Your use of those parties is also under their terms.
        </p>
      </LegalSection>

      <LegalSection title="9. Fees">
        <p>
          Unless you have a separate order form, the software is provided without a
          subscription fee from the author. An operator may charge you under a separate
          contract. Taxes are yours.
        </p>
      </LegalSection>

      <LegalSection title="10. Term and termination">
        <p>
          These Terms last while you use the service. We may suspend or terminate access
          immediately for breach, risk, or law. You may stop using the service and delete your
          collections. Sections that by nature should survive (including 4, 6, 11–16) survive
          termination.
        </p>
      </LegalSection>

      <LegalSection title="11. Disclaimers">
        <LegalDisclaimer>
          To the maximum extent permitted by law, the service, software, documentation, model
          output, citations, extractions, embeddings, and all related information are provided
          “as is” and “as available”, with all faults, without warranties of any kind, whether
          express, implied, or statutory, including merchantability, fitness for a particular
          purpose, title, non-infringement, accuracy, completeness, availability, or that the
          service will be error-free, secure, or uninterrupted. We do not warrant that retrieval
          is complete, that citations are correct, that review gates were followed, or that
          model output is suitable for any decision. You use the service at your sole risk.
        </LegalDisclaimer>
      </LegalSection>

      <LegalSection title="12. Limitation of liability">
        <LegalDisclaimer>
          To the maximum extent permitted by law, we, the operator, and our suppliers will not
          be liable for any indirect, incidental, special, consequential, exemplary, or
          punitive damages, or for lost profits, lost revenue, lost data, cost of substitute
          services, or damages arising from reliance on model output, citations, or
          extractions, even if advised of the possibility. Our total liability for all claims
          arising out of these terms or the service is limited to the greater of (a) the
          amounts you paid to us for the service in the twelve months before the claim or (b)
          one hundred US dollars (US $100). These limits are an essential basis of the bargain
          and apply to all theories of liability. Some jurisdictions do not allow certain
          exclusions; in those jurisdictions our liability is limited to the maximum extent
          permitted.
        </LegalDisclaimer>
      </LegalSection>

      <LegalSection title="13. Indemnity">
        <p>
          You will defend, indemnify, and hold harmless the author, the operator, and their
          personnel from claims, damages, and costs (including reasonable legal fees) arising
          out of: your content; personal data of others that you upload; your prompts and
          outputs you publish or rely on; your users and invitees; your breach of these Terms
          or law; and your failure to verify model output against the source before
          consequential use. We may assume exclusive defence at your expense.
        </p>
      </LegalSection>

      <LegalSection title="14. Disputes">
        <p>
          Contact contactabdullahahmed@gmail.com first and allow 30 days to try to resolve a
          dispute informally. To the extent permitted by law, you bring claims only in your
          individual capacity, not as a plaintiff or class member in a class or representative
          action. These Terms are governed by the laws applicable at the operator’s principal
          place of business, excluding conflict-of-law rules, except that Apache 2.0 continues
          to govern the source. Courts at that place have exclusive jurisdiction, except that
          we may seek injunctive relief anywhere to protect the service or tenants.
        </p>
      </LegalSection>

      <LegalSection title="15. Changes">
        <p>
          We may update these Terms by posting a new version on this page with a new effective
          date. Continued use after the effective date is acceptance. If you do not agree, stop
          using the service and delete your collections.
        </p>
      </LegalSection>

      <LegalSection title="16. General">
        <p>
          If a provision is unenforceable, the rest remains in force. Failure to enforce is not
          a waiver. You may not assign these Terms without our consent; we may assign them in a
          reorganisation. These Terms, the{" "}
          <HashLink href="/privacy">Privacy Policy</HashLink>,{" "}
          <HashLink href="/data">Data Policy</HashLink>,{" "}
          <HashLink href="/ai">Use of AI</HashLink>, and Apache 2.0 are the entire agreement
          for the service unless a signed writing says otherwise. In a conflict, a signed order
          form controls, then these Terms, then the policies. Marketing copy does not modify
          these Terms.
        </p>
      </LegalSection>
    </LegalDoc>
  );
}
