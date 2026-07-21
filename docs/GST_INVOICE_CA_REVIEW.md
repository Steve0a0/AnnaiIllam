# GST Tax Invoice Release Review

Status: **CA review required — not approved for production issuance**

## Configuration to approve

Finance and the Chartered Accountant must approve and configure:

- supplier legal name, registered address, GSTIN, state, and state code;
- the SAC for staffing/manpower services and the applicable GST rate;
- authorised signatory wording;
- whether the requirement work state is the correct place of supply for each service scenario;
- whether reverse charge applies to any supplied service;
- whether Annai Illam meets the current e-invoice mandate and therefore needs IRN/QR integration before launch.

Do not insert a real GSTIN into source control. Store these values in the staging and production secret/configuration systems.

## Required sample review

Use staging data with no real client personal information.

1. Create one completed Tamil Nadu requirement for a Tamil Nadu recipient and issue it. Confirm the document contains equal CGST and SGST, with no IGST.
2. Create one completed requirement whose place-of-supply state differs from the supplier state and issue it. Confirm the document contains IGST, with no CGST or SGST.
3. For each sample, verify supplier and recipient identity, GSTIN/state-code consistency, consecutive financial-year number, invoice date, SAC, description, taxable value, rates, tax amounts, total, place of supply, reverse-charge declaration, and signatory.
4. Download the same invoice through the admin and client/mobile endpoints and retain the emailed copy. Verify all three byte hashes match the API `content_sha256` value.
5. Attempt an update and delete against each issued invoice. Both must be rejected.

## Sign-off record

| Sample | Invoice number | SHA-256 | Reviewer | Date | Result / notes |
|---|---|---|---|---|---|
| Intrastate |  |  |  |  |  |
| Interstate |  |  |  |  |  |

Production issuance stays blocked until both rows are approved and the e-invoice applicability decision is recorded.

Any invoice issued before this snapshot migration is a legacy record, not proof of GST compliance. Finance must retain it unchanged and decide with the CA whether it needs cancellation plus a compliant replacement or another documented correction process.

## Engineering scope boundary

This implementation creates GST tax-invoice snapshots; it does not submit invoices to an Invoice Registration Portal, generate an IRN/QR code, file GST returns, select the legally correct SAC/rate, or implement credit/debit notes. Those require separate approved work when applicable.
