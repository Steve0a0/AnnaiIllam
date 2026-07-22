# Worker Classification Decision and Follow-up Tickets

## Decision record

Complete this section only from the signed legal memo. Do not infer answers from product terminology or source code.

| Field | Decision |
|---|---|
| Counsel / firm | Pending |
| Engagement confirmed | Pending |
| Matter reference and secure location | Pending |
| Memo date and version | Pending |
| Law considered current through | Pending |
| Legal entity covered | Pending |
| Pilot states and worker categories covered | Pending |
| Selected operating model by category | Pending |
| Annai Illam legal role | Pending |
| Client legal role | Pending |
| Worker legal status | Pending |
| EPF responsibility | Pending |
| ESI responsibility | Pending |
| Wage and deduction rules | Pending |
| Required registrations/licences | Pending |
| Prohibited pilot scenarios | Pending |
| Memo review/expiry trigger | Pending |

### Approvals

| Approval | Name | Date | Evidence |
|---|---|---|---|
| External labour counsel signature | Pending | Pending | Signed memo |
| Product Owner factual acceptance | Pending | Pending | Written approval |
| Finance payroll acceptance | Pending | Pending | Written approval |
| Executive Sponsor operating-model approval | Pending | Pending | Written approval |
| Tech Lead implementation scope acceptance | Pending | Pending | Activated ticket list |

## Conditional follow-up ticket register

These tickets are prepared but remain `BLOCKED` until the signed memo supplies exact obligations. After receipt, replace every bracketed field with the memo citation and move only applicable tickets to `TODO`.

### ANNAI-13A - Align client and worker agreements

**Priority:** P0  
**Owner:** Legal + Product  
**Dependency:** Signed ANNAI-13 memo  
**Activate when:** Every selected model.

**Work:** Replace provisional role language with counsel-approved agreements; add responsibility allocation, wages/rates, safety, benefits, deductions, grievance, suspension/termination, and assignment-specific terms. Version and record acceptance.

**Done when:** Counsel approves both agreements; every active user has accepted the applicable version; app, sales, and operational language match the memo.

### ANNAI-13B - Complete registrations and coverage matrix

**Priority:** P0  
**Owner:** Legal + Finance + Operations  
**Dependency:** Signed ANNAI-13 memo  
**Activate when:** Counsel identifies any registration, licence, insurance, or filing.

**Work:** Record `[obligation, responsible entity, threshold, state, registration number, renewal/filing frequency, evidence owner]`; complete pre-pilot registrations and client/principal-employer evidence.

**Done when:** No pilot assignment can be created in an uncovered state/category/client model; evidence is approved by counsel.

### ANNAI-13C - Encode statutory payroll and contribution rules

**Priority:** P0  
**Owner:** Backend + Finance  
**Dependency:** ANNAI-13A/13B decisions  
**Activate when:** The memo assigns wage, EPF, ESI, tax, welfare-fund, overtime, leave, bonus, gratuity, or other payroll duties to Annai Illam.

**Work:** Add server-owned, effective-dated configuration and calculations for `[memo-defined wage base, thresholds, employer/worker contributions, overtime/rest/holiday rules, permitted deductions, rounding, caps]`; snapshot inputs and outputs per payroll item.

**Done when:** Finance-approved examples at every threshold and boundary reconcile exactly; client payloads cannot choose statutory amounts; recalculation is audited and locked after approval.

### ANNAI-13D - Generate compliant payslips, registers, and returns

**Priority:** P0  
**Owner:** Backend + Admin + Finance  
**Dependency:** ANNAI-13C  
**Activate when:** The memo requires wage slips, contribution records, muster/attendance registers, returns, or nomination/member identifiers.

**Work:** Generate `[memo-required documents and fields]`, preserve immutable period snapshots, add filing/export workflow, and restrict sensitive identifiers.

**Done when:** Counsel/Finance approve one complete period and the evidence can be reproduced from stored records.

### ANNAI-13E - Enforce client/principal-employer compliance

**Priority:** P0  
**Owner:** Backend + Admin + Operations + Legal  
**Dependency:** Signed ANNAI-13 memo  
**Activate when:** A client/principal employer has registration, supervision, facility, wage, safety, or contribution duties.

**Work:** Capture required client/worksite evidence and validity dates; block assignment when missing; provide responsibility acknowledgement and compliance exports.

**Done when:** Ineligible or expired clients/worksites cannot receive workers and the responsible parties can retrieve required evidence.

### ANNAI-13F - Implement worker employment/engagement lifecycle

**Priority:** P0  
**Owner:** Backend + Admin + Mobile + Operations  
**Dependency:** Signed ANNAI-13 memo  
**Activate when:** Counsel requires offer/engagement letters, probation, leave, notice, benefits, nomination, injury reporting, or termination process.

**Work:** Implement only the memo-required lifecycle states, effective dates, approvals, worker notices, documents, and audit evidence.

**Done when:** Counsel-approved scenarios cover onboarding through exit without an operator bypassing a statutory step.

### ANNAI-13G - Remediate historical classification exposure

**Priority:** P0 confidential  
**Owner:** Executive Sponsor + Legal + Finance  
**Dependency:** Signed ANNAI-13 memo  
**Activate when:** Counsel identifies pre-pilot or historical exposure.

**Work:** Follow counsel's privileged remediation plan for `[period, population, registration, contribution, wage, document, notification, reserve]`. Keep privileged advice out of the source repository.

**Done when:** Counsel signs off remediation or written risk acceptance is approved with owner and expiry.

### ANNAI-13H - Add classification change controls

**Priority:** P1  
**Owner:** Product + Legal + Tech Lead  
**Dependency:** Signed ANNAI-13 memo  
**Activate when:** Every selected model.

**Work:** Create a pre-change legal review gate for new state, worker category, client type, supervision model, rate model, headcount/wage threshold, or agreement version.

**Done when:** Release and operations checklists prevent expansion outside the memo's scope and record the approving advice.

