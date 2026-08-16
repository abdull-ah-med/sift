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
  title: "Privacy Policy",
};

export default function PrivacyPage() {
  return (
    <LegalDoc
      title="Privacy Policy"
      description="Who processes which data, for what purpose, and what we do not put in logs. If you self-host, you are the controller for that deployment."
    >
      <LegalSection title="1. Who is responsible">
        <p>
          The sift software is authored by Abdullah Ahmed. For a deployment you operate yourself,
          you (the operator) are the controller of personal data processed on that instance. For a
          deployment we operate, we process account data as controller and process documents you
          upload as processor on your instructions. Contact: contactabdullahahmed@gmail.com.
        </p>
        <p>
          Documents you upload often contain personal data about other people. You are the
          controller of that content. You warrant that you have a lawful basis to store it and to
          permit processing described in this policy and the{" "}
          <HashLink href="/data">Data Policy</HashLink>.
        </p>
      </LegalSection>

      <LegalSection title="2. Categories of data">
        <LegalList
          items={[
            "Account and identity data from the identity provider (in the default deployment, Zitadel): subject identifier, email, name, tokens.",
            "Workspace data: tenant membership, collection ACL, invite tokens, API key identifiers. The secret is shown once at creation and is not logged.",
            "Customer documents: files, parse blocks, bounding boxes, review decisions, embeddings, chat turns, citations.",
            "Audit records: request identifiers, collection id, SHA-256 query hash. Audit payloads do not store the raw question or chunk text.",
            "Browser storage: API URL, API key, and access token in local storage on the device you use to sign in; invite tokens in session storage.",
            "Optional operations telemetry if the operator enables it: traces and metrics. Configure exporters so they do not receive raw questions, chunks, or document bytes.",
          ]}
        />
      </LegalSection>

      <LegalSection title="3. Purposes">
        <p>
          We process data to authenticate you, isolate tenants, store and retrieve your corpus,
          run review, search, and cited chat, keep an audit trail, secure the service, and
          communicate about the account. We do not sell personal data. We do not use your
          documents to train a sift-owned foundation model.
        </p>
      </LegalSection>

      <LegalSection title="4. Legal bases (where a privacy law applies)">
        <p>
          Processing that is necessary to provide the service is for performance of a contract
          with you or your organisation. Security, abuse prevention, and audit hashing are
          legitimate interests in keeping tenants isolated and investigating incidents. Where a
          law requires consent, the operator of the deployment is responsible for collecting it.
          Special-category or sensitive content in your PDFs is processed only because you
          uploaded it; do not upload it unless you are allowed to.
        </p>
      </LegalSection>

      <LegalSection title="5. Recipients">
        <p>
          Data is disclosed only as needed to run the deployment you use:
        </p>
        <LegalList
          items={[
            "The identity provider that issues and validates sign-in.",
            "Object storage, the application database, and the vector index for your collections.",
            "The embedding service and, when chat is configured, the inference API the operator enables. Retrieved passages and prompts are sent to that API so a model can draft an answer. That provider’s terms and retention apply to what it receives.",
            "Infrastructure and observability vendors the operator configures.",
            "Authorities if required by law.",
          ]}
        />
        <p>
          International transfers follow the operator’s choice of region and vendor. We do not
          claim a specific adequacy decision for every possible host.
        </p>
      </LegalSection>

      <LegalSection title="6. Retention">
        <p>
          Account and collection data remain until an admin deletes them in the product or the
          operator deletes the deployment. Browser storage remains until you clear it or sign
          out where the product offers that. Backups, if the operator keeps them, last as long as
          that operator’s backup schedule. We do not invent a fixed retention period for
          self-hosted instances.
        </p>
      </LegalSection>

      <LegalSection title="7. Your rights">
        <p>
          Depending on applicable law, you may have rights to access, correct, delete, restrict,
          or export personal data, to object, and to complain to a supervisory authority. For
          account data, contact the operator or contactabdullahahmed@gmail.com. For personal data
          inside documents you did not upload, contact the tenant that holds the collection.
        </p>
        <p>
          sift does not make solely automated decisions that produce legal or similarly
          significant effects about you. Chat and extraction are assistive. See{" "}
          <HashLink href="/ai">Use of AI</HashLink>.
        </p>
      </LegalSection>

      <LegalSection title="8. Children">
        <p>
          The service is not directed at children. Do not create an account for anyone under 16,
          or under 18 where your law requires it.
        </p>
      </LegalSection>

      <LegalSection title="9. Security">
        <p>
          Tenant row-level security, collection ACL, and API scopes gate access. Chat and search
          audits store a query hash, not the raw question. These are design controls, not a
          promise that the service is invulnerable. You must protect keys, invites, and devices.
        </p>
      </LegalSection>

      <LegalCallout>
        A privacy notice cannot create a warranty. Security and isolation are described so you
        can decide whether to use the product. Liability and disclaimers are in the{" "}
        <HashLink href="/terms">Terms of Service</HashLink>.
      </LegalCallout>

      <LegalDisclaimer>
        Nothing in this policy is legal, medical, or regulatory advice. If a privacy statute
        applies to your use, you remain responsible for your own compliance, including notices
        to the people whose data appears in your documents.
      </LegalDisclaimer>
    </LegalDoc>
  );
}
