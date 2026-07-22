# Legal Publication Approval

## Release candidate

- Policy version: `2026-07-21`
- Effective date: 21 July 2026
- Public index: `/legal`
- Documents: Privacy Notice, Client Terms, Worker Terms, Refund and Cancellation Policy, Grievance Process
- App-store deletion resource: `/legal/account-deletion/2026-07-21`

## Required configuration before deployment

- Set `NEXT_PUBLIC_LEGAL_ENTITY_NAME` to the registered operator name.
- Set `NEXT_PUBLIC_LEGAL_ENTITY_ADDRESS` to the registered operator address.
- Set and actively monitor `NEXT_PUBLIC_GRIEVANCE_EMAIL` and backend `GRIEVANCE_EMAIL`.
- Set backend `LEGAL_PUBLIC_BASE_URL` and mobile `EXPO_PUBLIC_LEGAL_BASE_URL` to the public admin origin followed by `/legal`.
- Confirm all versioned URLs return HTTP 200 without authentication.

## Approval checklist

| Review | Owner | Status |
|---|---|---|
| Privacy Notice, consent language, retention categories, and DPDP Rules commencement impact | Indian privacy counsel | Pending |
| Client Terms, governing law, liability, and contracting-document priority | Indian commercial counsel | Pending |
| Worker Terms, engagement classification, wages, benefits, safety, and non-waivable rights; must match the signed ANNAI-13 memo | Indian labour counsel | Pending |
| Cancellation windows, committed-cost rules, refund turnaround, taxes, and dispute handling | Product + Finance + counsel | Pending |
| Grievance officer identity, response service level, escalation authority, and monitored mailbox | Privacy officer + Operations | Pending |
| Registered operator name, address, GST identity, support details, and production domain | Product + Finance | Pending |
| Client and worker app-store privacy/deletion URLs | Mobile release owner | Pending |

## Acceptance evidence to verify

1. Sign in as a new client and a new worker.
2. Confirm access is paused before profile or application use.
3. Open every role-specific policy link from the consent screen.
4. Accept once and confirm `legal_acceptances` contains one row per required document with user, role, version, source, and the same acceptance time.
5. Repeat acceptance and confirm no rows are duplicated.
6. Change the registry version in a test build and confirm the app requires fresh acceptance.
7. Confirm all five links remain available from Privacy and data in both app variants and from the admin footer.

Do not mark the legal production gate complete until every pending owner has recorded approval and the deployed URLs have been checked.
