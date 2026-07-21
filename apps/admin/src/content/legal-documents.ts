export const LEGAL_VERSION = "2026-07-21";
export const LEGAL_EFFECTIVE_DATE = "21 July 2026";
const isProduction = process.env.NEXT_PUBLIC_APP_ENV === "production";

function legalIdentityValue(name: string, value: string | undefined, localFallback: string) {
  if (isProduction && !value?.trim()) {
    throw new Error(`${name} must be configured before publishing production legal pages.`);
  }
  return value?.trim() || localFallback;
}

export const LEGAL_ENTITY_NAME = legalIdentityValue(
  "NEXT_PUBLIC_LEGAL_ENTITY_NAME",
  process.env.NEXT_PUBLIC_LEGAL_ENTITY_NAME,
  "Annai Illam Staffing Platform",
);
export const LEGAL_ENTITY_ADDRESS = legalIdentityValue(
  "NEXT_PUBLIC_LEGAL_ENTITY_ADDRESS",
  process.env.NEXT_PUBLIC_LEGAL_ENTITY_ADDRESS,
  "Tamil Nadu, India",
);
export const GRIEVANCE_EMAIL = process.env.NEXT_PUBLIC_GRIEVANCE_EMAIL ?? "privacy@annaiillam.in";

export type LegalSection = { heading: string; paragraphs?: string[]; bullets?: string[] };
export type LegalDocument = {
  slug: string;
  title: string;
  summary: string;
  audience: string;
  sections: LegalSection[];
};

export const legalDocuments: LegalDocument[] = [
  {
    slug: "privacy",
    title: "Privacy Notice",
    summary: "How we collect, use, disclose, retain, and protect personal data.",
    audience: "Clients, workers, and visitors",
    sections: [
      {
        heading: "1. Who we are",
        paragraphs: [
          `${LEGAL_ENTITY_NAME} operates the Annai Illam staffing platform from ${LEGAL_ENTITY_ADDRESS}. This notice explains how personal data is handled when you use our client app, worker app, administration services, or support channels.`,
        ],
      },
      {
        heading: "2. Information we collect",
        bullets: [
          "Account and contact information, including name, phone number, email, and login identifiers.",
          "Client profile, company, billing, service requirement, complaint, and communication information.",
          "Worker identity, eligibility, skills, availability, assignment, attendance, location check-in, payroll, and payout information.",
          "Identity documents and selfies submitted for verification.",
          "Payment and transaction references. Payment card or UPI credentials are handled by the payment provider and are not stored by us unless expressly shown.",
          "Device, security, diagnostic, audit, and notification information needed to operate and protect the service.",
        ],
      },
      {
        heading: "3. Why we use it",
        bullets: [
          "Create and secure accounts, verify identity, and prevent impersonation or fraud.",
          "Match staffing requirements, manage assignments and attendance, and calculate payments or payroll.",
          "Issue quotes, invoices, receipts, refunds, and statutory financial records.",
          "Provide support, resolve complaints and grievances, and send service notifications.",
          "Meet legal, tax, accounting, labour, security, and audit obligations.",
          "Improve reliability and user experience using limited operational analytics.",
        ],
        paragraphs: [
          "Where consent is required, you may withdraw it for future processing. Withdrawal does not invalidate earlier lawful processing and may prevent us from providing features that require the data.",
        ],
      },
      {
        heading: "4. Sharing and service providers",
        paragraphs: [
          "We share only what is needed with authorised staff, matched clients or workers, payment and refund providers, cloud hosting and object-storage providers, identity or communication providers, professional advisers, and public authorities where required by law. We do not sell personal data.",
          "A client does not receive a worker's government ID or bank details. A worker does not receive a client's payment credentials. Access is limited by role and operational need.",
        ],
      },
      {
        heading: "5. Storage and security",
        paragraphs: [
          "We use access controls, encryption in transit, protected object storage, audit logging, and other proportionate safeguards. No system is completely risk-free. Please report suspected misuse immediately.",
          "Service providers may process data from locations where they operate. We apply contractual and technical safeguards appropriate to the information and applicable law.",
        ],
      },
      {
        heading: "6. Retention and deletion",
        paragraphs: [
          "We retain account and operational data only while needed for the purposes above. Approved deletion requests remove or anonymise personal account, profile, session, and identity-document data where possible. Invoices, payment, payroll, fraud-prevention, dispute, and audit records may be retained for periods required by applicable law or to establish legal claims.",
          "See the account deletion page for the in-app and web request routes.",
        ],
      },
      {
        heading: "7. Your choices and rights",
        bullets: [
          "Access a summary or request an export of your personal data.",
          "Correct inaccurate or incomplete information.",
          "Request erasure of data that is no longer required, subject to lawful retention.",
          "Withdraw consent for future consent-based processing.",
          "Nominate another person where applicable and raise a grievance about our handling of your data.",
        ],
        paragraphs: [
          `Use Privacy and data in the app or email ${GRIEVANCE_EMAIL}. We may verify your identity before acting on a request.`,
        ],
      },
      {
        heading: "8. Children and account eligibility",
        paragraphs: [
          "The worker service is not intended for anyone under 18. A client account must be used by a person legally able to act for themselves or the named organisation. Contact us if you believe an ineligible person has provided data.",
        ],
      },
      {
        heading: "9. Changes and contact",
        paragraphs: [
          `Material changes are published as a new dated version and may require fresh acceptance. Privacy and grievance questions can be sent to ${GRIEVANCE_EMAIL}.`,
        ],
      },
    ],
  },
  {
    slug: "client-terms",
    title: "Client Terms",
    summary: "Rules for clients requesting and managing staffing services.",
    audience: "Client account holders",
    sections: [
      { heading: "1. Account authority", paragraphs: ["You confirm that your account information is accurate and that you are authorised to act for the client organisation. Keep login codes and devices secure and notify us promptly of unauthorised access."] },
      { heading: "2. Staffing requests and quotes", paragraphs: ["A request is not confirmed until the platform records the required approval and payment state. Worker availability is not guaranteed before confirmation. The accepted quote, approved changes, and applicable invoice form the commercial record for a requirement."] },
      {
        heading: "3. Client responsibilities",
        bullets: [
          "Provide a lawful and reasonably safe workplace, accurate duties, location, dates, shift times, and required skills.",
          "Provide site instructions, supervision, safety equipment, facilities, and incident reporting required for the assignment.",
          "Treat workers fairly and do not request unlawful, unsafe, discriminatory, or materially different work.",
          "Use platform complaints, replacement, attendance, and approval processes accurately and in good faith.",
        ],
      },
      { heading: "4. Charges and payment", paragraphs: ["Authoritative charges are calculated by the platform from the approved quote and recorded adjustments. Client-entered amounts do not change the amount due. Taxes, advance requirements, payment purpose, and balance are shown before payment. Do not pay the same order more than once."] },
      { heading: "5. Cancellations, replacements, and refunds", paragraphs: ["Cancellation and refund outcomes depend on the accepted quote, work already performed, committed worker costs, approved adjustments, and the Refund and Cancellation Policy. Submit requests through the platform so the decision and any gateway refund can be audited."] },
      { heading: "6. Acceptable use and confidentiality", paragraphs: ["Do not scrape worker data, bypass platform controls, misuse identity information, interfere with the service, or use the platform for unlawful recruitment. Protect confidential worker and platform information and use it only for the relevant assignment."] },
      { heading: "7. Suspension and service limits", paragraphs: ["We may restrict an account or requirement to protect users, investigate fraud or safety issues, respond to non-payment, or comply with law. Planned and emergency maintenance may temporarily affect availability."] },
      { heading: "8. Law, disputes, and contact", paragraphs: [`These terms are governed by applicable Indian law. Any signed order, master agreement, or invoice-specific term takes priority where it expressly conflicts with these platform terms. Raise questions or grievances at ${GRIEVANCE_EMAIL}.`] },
    ],
  },
  {
    slug: "worker-terms",
    title: "Worker Terms",
    summary: "Rules for workers onboarding, accepting assignments, and recording work.",
    audience: "Worker account holders",
    sections: [
      { heading: "1. Eligibility and truthful information", paragraphs: ["You must be at least 18 and legally eligible for the work you accept. Submit accurate identity, skills, experience, availability, attendance, payout, and contact information. Do not let another person use your account or complete identity checks for you."] },
      { heading: "2. Verification and assignments", paragraphs: ["Account approval and identity verification do not guarantee an assignment. Review the role, location, shift, pay information, and safety requirements before accepting. Tell us promptly if you cannot attend or if the work materially differs from the assignment."] },
      {
        heading: "3. Attendance and workplace conduct",
        bullets: [
          "Use check-in and check-out honestly and only for your own attendance at the assigned location.",
          "Follow lawful site and safety instructions and report injury, danger, harassment, or prohibited conduct.",
          "Treat clients, other workers, and staff respectfully and protect confidential information.",
          "Do not submit false documents, attendance, expenses, complaints, or payout details.",
        ],
      },
      { heading: "4. Pay and deductions", paragraphs: ["The assignment and payroll record show the applicable rate, verified attendance, approved adjustments, and payout status. Raise discrepancies promptly through the app. Deductions or withholding will be made only where authorised by the relevant arrangement or required by law."] },
      { heading: "5. Your legal status", paragraphs: ["These app terms do not by themselves decide whether a worker is an employee, agency worker, contractor, or another legally recognised category. That status and its benefits are determined by the applicable engagement documents and law. Nothing here removes a statutory wage, safety, social-security, or other non-waivable right."] },
      { heading: "6. Account action and leaving the platform", paragraphs: ["We may pause or restrict access while investigating identity, safety, fraud, attendance, or conduct concerns. You may request account deletion, but payroll, tax, dispute, and audit records may be retained where legally required."] },
      { heading: "7. Law and grievances", paragraphs: [`These terms are governed by applicable Indian law and do not replace any signed engagement document. Report pay, safety, conduct, privacy, or access concerns through the app or at ${GRIEVANCE_EMAIL}.`] },
    ],
  },
  {
    slug: "refund-cancellation",
    title: "Refund and Cancellation Policy",
    summary: "How cancellations, overpayments, and approved refunds are handled.",
    audience: "Clients",
    sections: [
      { heading: "1. Scope", paragraphs: ["This policy applies to client payments recorded for staffing requirements. The accepted quote or written order may contain requirement-specific cancellation terms that take priority where clearly stated."] },
      { heading: "2. Requesting cancellation", paragraphs: ["Submit a cancellation through the platform as soon as possible and include the requirement and reason. A request is not final until its status is confirmed. We may contact you to verify scope, work already performed, and committed costs."] },
      {
        heading: "3. Refund assessment",
        bullets: [
          "Before work or non-recoverable commitments begin, an approved refund may include the eligible paid amount less disclosed non-refundable or already-incurred costs.",
          "After work begins, completed work, verified attendance, committed worker costs, taxes, and approved adjustments are reconciled before any refund.",
          "Duplicate payments and confirmed overpayments are returned or applied to an outstanding balance according to the client's instruction and the payment ledger.",
          "A refund cannot exceed the captured, unreimbursed amount for the relevant payment.",
        ],
      },
      { heading: "4. Method and timing", paragraphs: ["Approved online-payment refunds are initiated through the original payment provider where supported. Banks and payment providers control the time before funds appear. Manual payment refunds require verified beneficiary details and finance approval. The platform records the refund reference and status."] },
      { heading: "5. Disputes and contact", paragraphs: [`If the result appears incorrect, raise a payment dispute in the app with the payment reference and supporting evidence. Escalations can be sent to ${GRIEVANCE_EMAIL}. Do not send full card, bank password, PIN, or OTP details.`] },
    ],
  },
  {
    slug: "grievance",
    title: "Grievance Process",
    summary: "How to raise and escalate privacy, service, pay, or safety concerns.",
    audience: "Clients and workers",
    sections: [
      { heading: "1. What you can raise", paragraphs: ["You may raise concerns about privacy, account access, discrimination, safety, attendance, pay, billing, refunds, conduct, service quality, or an earlier support outcome. Emergencies and immediate danger should also be reported to the appropriate emergency or public authority."] },
      {
        heading: "2. How to submit",
        bullets: [
          "Use the relevant complaint, issue, dispute, or Privacy and data option in the app.",
          `Email ${GRIEVANCE_EMAIL} when you cannot access the app or need to escalate an outcome.`,
          "Include your account phone or email, the relevant requirement or assignment reference, dates, a clear description, and safe supporting evidence.",
        ],
      },
      { heading: "3. What happens next", paragraphs: ["We record the grievance, restrict access to authorised reviewers, verify identity where necessary, investigate the available records, and communicate an outcome or request more information. Urgent safety, identity, and payment risks are prioritised. We aim to respond within the period required by applicable law and any published service level."] },
      { heading: "4. Fairness and confidentiality", paragraphs: ["Good-faith grievances do not justify retaliation. Information is shared only with people who need it to investigate, protect users, or comply with law. Knowingly false or abusive reports may be handled under the applicable account terms."] },
      { heading: "5. Escalation", paragraphs: ["Reply to the outcome with the reason you disagree and any new evidence. Privacy grievances may be escalated to the competent authority after the internal grievance route is exhausted where applicable. Other statutory, labour, consumer, police, or court remedies remain available according to law."] },
    ],
  },
  {
    slug: "account-deletion",
    title: "Account Deletion",
    summary: "How clients and workers can request deletion from the app or web.",
    audience: "Client and worker account holders",
    sections: [
      { heading: "Request in the app", paragraphs: ["Open Profile, choose Privacy and data, then choose Request account deletion. Your account remains active while an authorised administrator verifies and reviews the request."] },
      { heading: "Request without the app", paragraphs: [`Email ${GRIEVANCE_EMAIL} with the subject "Account deletion request". State whether you use the client or worker app and provide the phone number or email on the account. Do not attach identity documents unless our privacy team asks through a verified channel.`] },
      { heading: "What is deleted or retained", paragraphs: ["After approval, login details, active sessions, personal profile fields, and identity documents are deleted or anonymised where possible. Invoices, payment, payroll, fraud-prevention, dispute, and audit records may remain for the period required by applicable law, with identifying data reduced where possible."] },
    ],
  },
];

export const primaryLegalDocuments = legalDocuments.filter((document) => document.slug !== "account-deletion");

export function getLegalDocument(slug: string) {
  return legalDocuments.find((document) => document.slug === slug);
}
