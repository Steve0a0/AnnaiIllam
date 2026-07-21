Phase 0 — Freeze and Baseline
=============================

PROD-001 — Create production hardening release baseline
-------------------------------------------------------

**Priority:** P0**Owner:** Tech lead**Estimate:** 0.5 day**Dependencies:** None

**Work:**

*   Freeze new feature development.
    
*   Create a production-hardening branch or epic.
    
*   Record current failing checks.
    
*   Assign owners for backend, admin, mobile, infrastructure, QA, product, legal, and finance.
    
*   Define staging and production approval ownership.
    
*   Reclassify tracker items contradicted by the audit.
    

**Acceptance criteria:**

*   Every ticket below has an owner and status.
    
*   No unrelated feature work enters the release branch.
    
*   Current release-gate results are documented.
    

PROD-002 — Establish mandatory release gates
--------------------------------------------

**Priority:** P0**Owner:** Tech lead/DevOps**Estimate:** 1 day**Dependencies:** PROD-001

**Work:**

Require these checks on every pull request:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   # Backend  python -m ruff check app tests scripts  python -m pytest -v  # Admin  npm test  npm run lint  npm run build  # Mobile  npm test -- --runInBand  npx tsc --noEmit   `

Add dependency, secret, and container-image scanning. Prevent merge when any required check fails.

**Acceptance criteria:**

*   Main/develop branches require passing checks.
    
*   Backend CI provisions both PostgreSQL and Redis.
    
*   Admin CI uses NEXT\_PUBLIC\_API\_BASE\_URL.
    
*   A mobile CI workflow exists.
    
*   CI uses supported pinned Node and Python versions.
    

Phase 1 — Close Critical Security and Financial Defects
=======================================================

PROD-003 — Remove unauthenticated user-directory disclosure
-----------------------------------------------------------

**Priority:** P0/Critical**Owner:** Backend**Estimate:** 0.5 day**Dependencies:** PROD-001

**Work:**

*   Remove the public GET /api/v1/users endpoint or restrict it to an appropriate super-admin permission.
    
*   Return a paginated, minimal schema if the endpoint is genuinely needed.
    
*   Never expose phone/email to unauthorised roles.
    

**Acceptance criteria:**

*   Unauthenticated requests receive 401.
    
*   Client and worker tokens receive 403.
    
*   Only explicitly authorised administrators can access required fields.
    
*   Route-authentication regression test scans every router.
    

**Verification:**

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   python -m pytest tests/test_users.py tests/test_permission_groups.py -v   `

PROD-004 — Define the authoritative payment ledger and invariants
-----------------------------------------------------------------

**Priority:** P0/Critical**Owner:** Backend + Product + Finance**Estimate:** 1 day**Dependencies:** PROD-001

**Work:**

Document and encode:

*   Quote total.
    
*   Required advance.
    
*   Total paid.
    
*   Refunded amount.
    
*   Outstanding balance.
    
*   Payment purpose: advance, balance, adjustment, refund.
    
*   Valid requirement state for each payment.
    
*   Overpayment and duplicate-payment handling.
    
*   Whether payment success or admin approval advances each lifecycle state.
    

**Acceptance criteria:**

*   A single service owns all payable-amount calculations.
    
*   Client payloads never determine the authoritative charge.
    
*   Product and finance sign off the state diagram.
    
*   All APIs use integer paise internally or another single documented unit.
    

PROD-005 — Fix Razorpay order amount calculation
------------------------------------------------

**Priority:** P0/Critical**Owner:** Backend**Estimate:** 2 days**Dependencies:** PROD-004

**Work:**

*   Remove the client-controlled authoritative amount.
    
*   Load quote/payment history under a transaction.
    
*   Calculate the permitted advance or remaining balance server-side.
    
*   Reject zero, negative, excess, duplicate, stale, and invalid-state orders.
    
*   Return the server-calculated amount to mobile.
    

**Acceptance criteria:**

*   A client cannot create a ₹1 order for a larger balance.
    
*   Repeating partial payments cannot complete the requirement.
    
*   Paid plus refunded plus outstanding reconciles to the quote total.
    
*   Order notes include immutable internal IDs and payment purpose.
    

PROD-006 — Make payment verification and webhooks transactional
---------------------------------------------------------------

**Priority:** P0/Critical**Owner:** Backend**Estimate:** 3 days**Dependencies:** PROD-005

**Work:**

*   Process SDK verification and webhook capture through one idempotent service.
    
*   Lock payment/requirement rows during transition.
    
*   Validate Razorpay order amount and currency against local records.
    
*   Add unique event/payment constraints.
    
*   Prevent webhook and mobile callback races.
    
*   Only complete a requirement when the defined commercial and operational conditions are satisfied.
    

**Acceptance criteria:**

*   Duplicate webhook delivery has no additional effect.
    
*   Concurrent callback and webhook remain consistent.
    
*   Partial final payment does not complete a requirement.
    
*   Invalid amount/currency/order relationships are rejected and audited.
    
*   Reconciliation failures generate alerts.
    

**Required tests:**

*   ₹1 advance.
    
*   Two ₹1 payments.
    
*   Partial balance.
    
*   Overpayment.
    
*   Duplicate payment ID.
    
*   Duplicate webhook.
    
*   Webhook/callback concurrency.
    
*   Refunded payment.
    
*   Cancelled requirement.
    
*   Quote changed after order creation.
    

PROD-007 — Separate payment receipts from GST invoices
------------------------------------------------------

**Priority:** P0**Owner:** Backend + Admin + Mobile + Finance**Estimate:** 2 days**Dependencies:** PROD-004

**Work:**

*   Stop calling payment receipts “invoices.”
    
*   Use one invoice-numbering system.
    
*   Define when receipt vouchers, tax invoices, refunds, and credit notes are generated.
    
*   Update API schemas, email content, mobile labels, and downloads.
    

**Acceptance criteria:**

*   Payment IDs cannot create a second conflicting invoice sequence.
    
*   Client UI clearly distinguishes payment receipt and tax invoice.
    
*   Old records remain addressable after migration.
    

PROD-008 — Fix backend runtime and lint failures
------------------------------------------------

**Priority:** P0**Owner:** Backend**Estimate:** 1–2 days**Dependencies:** PROD-003–006 where overlapping

**Work:**

*   Fix undefined old\_worker\_profile in reassignment notifications.
    
*   Remove duplicate/unused imports and invalid f-strings.
    
*   Resolve all current Ruff findings.
    
*   Exercise reassignment success and notification failure.
    

**Acceptance criteria:**

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   python -m ruff check app tests scripts   `

passes with zero findings, and reassignment does not raise an unhandled exception.

Gate 1 — Critical Application Safety
====================================

Gate 1 passes only when:

*   Public PII route is closed.
    
*   Payment invariants and adversarial tests pass.
    
*   Receipts and invoices are separated.
    
*   Backend Ruff passes.
    
*   Full backend suite passes.
    

No network-accessible demo before this gate.

Phase 2 — Attendance, Scheduling, and Data Integrity
====================================================

PROD-009 — Move scheduler out of API workers
--------------------------------------------

**Priority:** P0/High**Owner:** Backend + DevOps**Estimate:** 3–4 days**Dependencies:** PROD-002

**Work:**

*   Disable scheduler startup in ordinary API processes.
    
*   Create a dedicated scheduler/worker entry point.
    
*   Add PostgreSQL advisory locking or Redis distributed locking.
    
*   Make every scheduled job idempotent.
    
*   Track job name, scheduled time, start/end time, result, and error.
    
*   Ensure deployments/restarts do not rerun completed daily work.
    

**Acceptance criteria:**

*   Starting two API replicas does not start two schedulers.
    
*   Starting two scheduler replicas results in one job execution.
    
*   Scheduler failure is visible in readiness/monitoring.
    
*   Redeployment does not duplicate notifications or state transitions.
    

PROD-010 — Correct no-show timing
---------------------------------

**Priority:** P0/High**Owner:** Backend + Product**Estimate:** 2 days**Dependencies:** PROD-009

**Work:**

*   Store or derive scheduled shift start/end times.
    
*   Define a configurable no-show grace period.
    
*   Evaluate no-show only after shift start plus grace.
    
*   Exclude cancelled/replaced/ineligible assignments.
    
*   Allow admin review/correction.
    
*   Notify the affected worker and admin without changing payroll prematurely.
    

**Acceptance criteria:**

*   Morning deployment cannot mark all workers absent.
    
*   No-show processing is idempotent.
    
*   Early, late, overnight, and cancelled shifts are tested.
    
*   Corrections produce audit records.
    

PROD-011 — Implement timezone-aware business dates
--------------------------------------------------

**Priority:** P0**Owner:** Backend**Estimate:** 2–3 days**Dependencies:** PROD-010

**Work:**

*   Store timezone-aware UTC timestamps.
    
*   Introduce a central Asia/Kolkata business-date service.
    
*   Remove direct date.today() and naive datetime.utcnow() from business logic.
    
*   Define date attribution for overnight shifts.
    
*   Review attendance, payroll, invoice, scheduler, quote expiry, and SLA code.
    

**Acceptance criteria:**

*   IST midnight and UTC-day boundaries are tested.
    
*   One business date is used consistently across attendance and payroll.
    
*   No new naive datetime use appears in business code.
    
*   Existing data migration strategy is documented.
    

PROD-012 — Harden database constraints and lifecycle retention
--------------------------------------------------------------

**Priority:** P1**Owner:** Backend/Database**Estimate:** 3–5 days**Dependencies:** PROD-004, PROD-011

**Work:**

*   Add check constraints for important statuses and nonnegative money.
    
*   Add indexes based on real query paths.
    
*   Replace destructive cascade behaviour for financial, attendance, payroll, and audit records.
    
*   Introduce soft deletion where required.
    
*   Add financial-year invoice sequence support.
    

**Acceptance criteria:**

*   Invalid statuses and negative monetary values fail at the database layer.
    
*   Deactivating a user preserves required operational/financial records.
    
*   Migration passes from an empty database and a representative populated copy.
    
*   Rollback/forward strategy is documented.
    

Phase 3 — Authentication, Upload, and Privacy Hardening
=======================================================

PROD-013 — Enforce social-login audiences
-----------------------------------------

**Priority:** P1/High**Owner:** Backend + Mobile**Estimate:** 1 day**Dependencies:** None

**Work:**

*   Require Google and Apple client IDs when social login is enabled.
    
*   Validate issuer, audience, expiry, and platform-specific claims.
    
*   Disable the provider if configuration is incomplete.
    
*   Rate-limit by IP/account/device rather than token prefix.
    

**Acceptance criteria:**

*   Token issued for another application is rejected.
    
*   Missing production audience prevents application startup or disables the route.
    
*   Client and worker app audiences are independently tested.
    

PROD-014 — Make critical rate limits fail safely
------------------------------------------------

**Priority:** P1/High**Owner:** Backend + DevOps**Estimate:** 2 days**Dependencies:** Production Redis design

**Work:**

Protect:

*   OTP request/verification.
    
*   Admin login.
    
*   Social login.
    
*   Token refresh.
    
*   Payment order/verification.
    
*   Upload URL generation and local uploads.
    
*   Bulk import/export.
    
*   Complaints and interest spam.
    

**Acceptance criteria:**

*   Limit violation returns 429 with retry information.
    
*   Redis outage fails closed for authentication and payment mutation.
    
*   /ready reports Redis failure.
    
*   Alert fires when limiter storage is unavailable.
    

PROD-015 — Secure document and selfie uploads
---------------------------------------------

**Priority:** P1/High**Owner:** Backend + Mobile + DevOps**Estimate:** 4–6 days**Dependencies:** Object-storage architecture

**Work:**

*   Enforce maximum size in presigned conditions and reverse proxy.
    
*   Bind upload keys to user, document type, and one-time upload session.
    
*   Verify object existence, content length, checksum, content type, and magic bytes.
    
*   Re-encode supported images and strip metadata.
    
*   Add antivirus/quarantine flow for documents.
    
*   Prevent cross-user object-key submission.
    
*   Require the authorised selfie bucket/domain in production.
    

**Acceptance criteria:**

*   Oversized, unsupported, nonexistent, external, and cross-user objects are rejected.
    
*   Uploads remain private.
    
*   Unverified objects cannot become active KYC documents.
    
*   Security events are audited without logging document content.
    

PROD-016 — Harden admin session storage
---------------------------------------

**Priority:** P1/High**Owner:** Backend + Admin**Estimate:** 4–6 days**Dependencies:** Architecture decision

**Work:**

Preferred design:

*   Secure, HttpOnly, SameSite refresh cookie.
    
*   Short-lived access token held in memory.
    
*   CSRF defence for cookie-authenticated mutations.
    
*   Refresh rotation and reuse detection.
    
*   Session/device list and revocation.
    
*   Idle and absolute session expiry.
    

**Acceptance criteria:**

*   Refresh token is not readable through browser JavaScript.
    
*   Refresh reuse revokes the token family.
    
*   CSRF tests cover every cookie-authenticated mutation.
    
*   Logout revokes server session and clears local state.
    

PROD-017 — Add admin web security headers
-----------------------------------------

**Priority:** P1**Owner:** Admin + DevOps**Estimate:** 1–2 days**Dependencies:** PROD-016

**Work:**

Add and verify:

*   Content-Security-Policy.
    
*   HSTS.
    
*   Frame restrictions.
    
*   Referrer policy.
    
*   Permissions policy.
    
*   nosniff.
    
*   Safe caching for authenticated pages.
    

**Acceptance criteria:**

*   Headers appear on production responses.
    
*   CSP does not require broad unsafe-eval.
    
*   Clickjacking test fails to frame the admin.
    
*   Sentry and required APIs remain functional.
    

PROD-018 — Redesign audit events
--------------------------------

**Priority:** P1**Owner:** Backend + Security**Estimate:** 4–6 days**Dependencies:** PROD-012

**Work:**

*   Record actor, role, request ID, IP, entity type/ID, action, result, and timestamp as structured columns.
    
*   Write the audit event in the same transaction or through a transactional outbox.
    
*   Redact phone, email, tokens, bank details, documents, and signatures.
    
*   Restrict audit access and define retention.
    
*   Track sensitive reads as well as writes where appropriate.
    

**Acceptance criteria:**

*   Rolled-back mutations cannot produce misleading “success” audit records.
    
*   Every finance, payroll, KYC, permission, and status mutation records an actor.
    
*   Logs and Sentry events pass PII-redaction tests.
    

Gate 2 — Security Boundary
==========================

Gate 2 requires:

*   Social audiences enforced.
    
*   Critical rate limiting operational.
    
*   Uploads and selfies validated.
    
*   Admin session design hardened.
    
*   Security headers deployed.
    
*   Audit/PII controls tested.
    

Phase 4 — Repair Frontend and Mobile Release Gates
==================================================

PROD-019 — Restore admin production build
-----------------------------------------

**Priority:** P0**Owner:** Admin**Estimate:** 1 day**Dependencies:** None

**Work:**

*   Define/use queryClient correctly on the workers page.
    
*   Fix Date.now() during render.
    
*   Fix unescaped text.
    
*   Address remaining meaningful warnings.
    
*   Correct CI API environment-variable name.
    

**Acceptance criteria:**

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   npm test  npm run lint  npm run build   `

all pass from a clean install.

PROD-020 — Restore mobile type safety
-------------------------------------

**Priority:** P0**Owner:** Mobile**Estimate:** 1 day**Dependencies:** None

**Work:**

*   Correct the missing neutralBg token.
    
*   Review billing-state types.
    
*   Add TypeScript to mobile CI.
    

**Acceptance criteria:**

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   npm test -- --runInBand  npx tsc --noEmit   `

both pass.

PROD-021 — Fix worker onboarding resume
---------------------------------------

**Priority:** P1**Owner:** Mobile**Estimate:** 2 days**Dependencies:** PROD-020

**Work:**

*   Hydrate the persisted completion state.
    
*   Map every backend onboarding step to its correct navigator/screen.
    
*   Resume identity\_uploaded at profile creation.
    
*   Handle rejected/resubmission and approved/biometric states.
    
*   Add session-expiry recovery without losing onboarding progress.
    

**Acceptance criteria:**

For every onboarding step, killing and reopening the app returns to the correct screen without a redundant login.

PROD-022 — Create separate client and worker production apps
------------------------------------------------------------

**Priority:** P0**Owner:** Mobile + DevOps/Product**Estimate:** 3–5 days**Dependencies:** PROD-020

**Work:**

Create separate configurations for:

*   Display name.
    
*   Icon/splash.
    
*   Android package.
    
*   iOS bundle identifier.
    
*   URL scheme.
    
*   OAuth client IDs.
    
*   Push credentials.
    
*   EAS development/preview/production profiles.
    
*   API environment.
    
*   Secure-storage namespace.
    
*   Store listing and privacy URLs.
    

**Acceptance criteria:**

*   Client and worker Android AABs build independently.
    
*   Client and worker iOS archives build independently.
    
*   Installation of one does not overwrite the other.
    
*   OAuth/deep links open the correct app.
    
*   Production builds cannot silently default to a variant.
    

PROD-023 — Complete mobile permission configuration
---------------------------------------------------

**Priority:** P1**Owner:** Mobile**Estimate:** 2 days**Dependencies:** PROD-022

**Work:**

*   Configure camera/photo, location, biometric, and notification permission text.
    
*   Remove duplicate iOS background-mode values.
    
*   Verify generated manifests/plists.
    
*   Add denial, limited permission, and settings-redirection states.
    

**Acceptance criteria:**

*   Store builds declare only required permissions.
    
*   Denied permissions produce usable recovery journeys.
    
*   Client app does not request worker-only permissions unnecessarily.
    

PROD-024 — Accessibility remediation
------------------------------------

**Priority:** P1**Owner:** Admin + Mobile + Design/QA**Estimate:** 5–8 days**Dependencies:** PROD-019–023

**Work:**

*   Label all interactive controls.
    
*   Add roles, states, hints, and logical focus order.
    
*   Replace inaccessible hidden OTP input.
    
*   Enforce minimum touch targets.
    
*   Increase undersized worker typography.
    
*   Add admin skip link and keyboard support.
    
*   Validate colour contrast and error announcements.
    

**Acceptance criteria:**

*   Critical mobile journeys work with TalkBack and VoiceOver.
    
*   Admin works keyboard-only and at 200% zoom.
    
*   No critical accessibility defect remains in login, onboarding, payment, assignment, attendance, complaint, or payroll journeys.
    

Phase 5 — Finance, Privacy, and Legal Product Work
==================================================

These tickets can run in parallel with Phases 2–4, but must finish before live customers.

PROD-025 — Obtain formal business and worker classification decision
--------------------------------------------------------------------

**Priority:** P0**Owner:** Founders/Product + Indian labour counsel**Estimate:** External; 1–3 weeks**Dependencies:** None

**Required decisions:**

*   Is Annai Illam employer, contractor, aggregator, marketplace, or intermediary?
    
*   Who contracts with and pays workers?
    
*   Who is responsible for supervision, replacement, workplace safety, and statutory benefits?
    
*   What are the client/principal-employer obligations?
    
*   What wage, overtime, leave, gratuity, EPF, ESI, and insurance rules apply?
    
*   What licences/registrations and records are required?
    

**Acceptance criteria:**

*   Written legal memo and approved operating model.
    
*   Client and worker agreements reflect the model.
    
*   Product/payroll requirements are documented as follow-up tickets.
    

PROD-026 — Implement GST-compliant invoices and credit notes
------------------------------------------------------------

**Priority:** P0**Owner:** Backend + Admin + Finance/CA**Estimate:** 5–8 days plus CA review**Dependencies:** PROD-007, PROD-012

**Work:**

Support:

*   Supplier legal identity, address, GSTIN.
    
*   Recipient identity and GSTIN snapshot.
    
*   Financial-year sequence.
    
*   Invoice date and service period.
    
*   SAC/service description.
    
*   Place of supply and state code.
    
*   Taxable value.
    
*   CGST/SGST or IGST split.
    
*   Total tax and invoice value.
    
*   Advance adjustment.
    
*   Credit/refund notes.
    
*   Immutable issued invoice snapshots.
    

**Acceptance criteria:**

*   CA approves sample intrastate and interstate invoices.
    
*   Simultaneous invoice generation produces unique sequences.
    
*   Issued invoices cannot be silently rewritten.
    
*   Client can download the same canonical invoice from mobile/admin/email.
    

PROD-027 — Implement cancellation, refund, and dispute policy
-------------------------------------------------------------

**Priority:** P0**Owner:** Product + Backend + Admin + Mobile + Legal**Estimate:** 5–7 days**Dependencies:** PROD-004–007

**Work:**

*   Define cancellation windows and fees.
    
*   Define refund eligibility and approval.
    
*   Add refund states and Razorpay refund reference.
    
*   Add credit-note generation.
    
*   Add admin review and client tracking.
    
*   Reconcile refunded amounts against payment balance.
    
*   Define complaint versus commercial dispute ownership.
    

**Acceptance criteria:**

*   A refund cannot exceed paid refundable balance.
    
*   Partial/full refunds are idempotent.
    
*   Client sees status and expected timeline.
    
*   Finance can reconcile payment, refund, invoice, and credit note.
    

PROD-028 — Publish privacy, terms, and grievance surfaces
---------------------------------------------------------

**Priority:** P0**Owner:** Legal/Product + Admin/Mobile**Estimate:** 3–5 engineering days plus legal drafting**Dependencies:** PROD-025

**Work:**

Publish:

*   Privacy notice.
    
*   Client terms.
    
*   Worker terms/engagement agreement.
    
*   Cancellation/refund policy.
    
*   Grievance contact/process.
    
*   Data-retention summary.
    
*   Account deletion request instructions.
    

**Acceptance criteria:**

*   Links work before consent and from every application.
    
*   Documents are versioned.
    
*   Acceptance records document version, timestamp, role, and purpose.
    
*   Store listings use the same URLs.
    

PROD-029 — Implement DPDP consent and data-rights workflow
----------------------------------------------------------

**Priority:** P0**Owner:** Backend + Admin + Mobile + Privacy counsel**Estimate:** 5–8 days**Dependencies:** PROD-028

**Work:**

*   Version consent notices.
    
*   Store purpose-specific consent evidence.
    
*   Support access, correction, erasure, and grievance requests.
    
*   Create admin request-management queue.
    
*   Apply identity verification and approval rules.
    
*   Preserve legally required finance/employment records while deleting unnecessary data.
    
*   Record completion and response deadlines.
    

**Acceptance criteria:**

*   User can submit a request from the product or published process.
    
*   Admin can track it end to end.
    
*   Deletion does not erase legally required invoice/payroll records.
    
*   A completed request has an auditable outcome.
    

PROD-030 — Implement retention and deletion controls
----------------------------------------------------

**Priority:** P1**Owner:** Backend + Privacy/Legal + DevOps**Estimate:** 4–6 days**Dependencies:** PROD-012, PROD-029

**Work:**

*   Create a retention matrix by data class.
    
*   Expire OTPs, refresh tokens, device tokens, rejected uploads, logs, and temporary selfies.
    
*   Archive/preserve statutory financial and employment records.
    
*   Apply S3 lifecycle policies.
    
*   Add safe deletion/anonymisation jobs.
    

**Acceptance criteria:**

*   Automated jobs are idempotent and observable.
    
*   Legal hold prevents deletion.
    
*   Staging test proves records are retained/deleted as designed.
    
*   Backups have aligned expiration rules.
    

Gate 3 — Legal and Commercial Readiness
=======================================

Required evidence:

*   Business/worker model signed off.
    
*   Client and worker agreements approved.
    
*   GST invoice samples approved by CA.
    
*   Privacy/terms/refund/grievance content published.
    
*   Consent and rights workflows operational.
    
*   Retention schedule implemented.
    

Phase 6 — Production Infrastructure
===================================

PROD-031 — Add secure Docker build contexts
-------------------------------------------

**Priority:** P0**Owner:** Backend/Admin + DevOps**Estimate:** 1 day**Dependencies:** None

**Work:**

Add .dockerignore files excluding:

*   .env\*.
    
*   Credentials and signing keys.
    
*   Virtual environments.
    
*   node\_modules.
    
*   Build/cache directories.
    
*   Native build output.
    
*   Tests and local tools not required at runtime.
    
*   Git metadata.
    
*   Uploaded/local data.
    

**Acceptance criteria:**

*   Image built from a directory containing local .env does not contain it.
    
*   Image secret scan passes.
    
*   Backend and admin run as non-root.
    
*   Images use immutable dependency lock files.
    

PROD-032 — Provision staging infrastructure
-------------------------------------------

**Priority:** P0**Owner:** DevOps**Estimate:** 3–5 days**Dependencies:** PROD-009 architecture

**Recommended resources:**

*   App VM/container service.
    
*   Managed PostgreSQL 16.
    
*   Managed TLS Redis/Valkey.
    
*   Private India-region S3 buckets.
    
*   DNS and TLS.
    
*   Secret manager.
    
*   Container registry.
    
*   Sentry/logging/uptime monitoring.
    

**Acceptance criteria:**

*   Database and Redis are not publicly reachable.
    
*   Application uses least-privilege identities.
    
*   /health and /ready behave correctly.
    
*   Infrastructure configuration is repeatable and documented.
    

PROD-033 — Configure production secrets and key rotation
--------------------------------------------------------

**Priority:** P0**Owner:** DevOps/Security**Estimate:** 2 days**Dependencies:** PROD-032

**Work:**

Store and rotate:

*   JWT signing secret.
    
*   Field encryption key.
    
*   Database and Redis credentials.
    
*   S3 credentials/role.
    
*   Razorpay keys and webhook secret.
    
*   MSG91 credentials.
    
*   Email credentials.
    
*   Google/Apple audiences.
    
*   Sentry credentials.
    
*   Admin bootstrap secret.
    

**Acceptance criteria:**

*   No production secret is stored in Git, images, CI logs, or tickets.
    
*   Rotation runbook exists.
    
*   Application can restart after credential rotation.
    
*   Access to secrets is audited.
    

PROD-034 — Configure DNS, TLS, WAF, and network controls
--------------------------------------------------------

**Priority:** P0**Owner:** DevOps**Estimate:** 2–3 days**Dependencies:** PROD-032

**Acceptance criteria:**

*   HTTP redirects to HTTPS.
    
*   HSTS is enabled after verification.
    
*   Backend accepts traffic only through approved ingress.
    
*   PostgreSQL/Redis/S3 access is restricted.
    
*   TLS renewal is automatic.
    
*   Edge limits protect auth, payments, and uploads.
    

PROD-035 — Configure production integrations
--------------------------------------------

**Priority:** P0**Owner:** DevOps + Backend + Product**Estimate:** 3–5 days**Dependencies:** PROD-033–034

Configure and verify:

*   Razorpay live/test separation and webhook.
    
*   MSG91 sender, OTP template, DLT requirements.
    
*   Transactional email domain, SPF, DKIM, DMARC.
    
*   Apple/Google OAuth.
    
*   Push credentials for both apps.
    
*   S3 CORS/lifecycle/encryption.
    
*   Sentry projects and release tagging.
    

**Acceptance criteria:**

*   Each integration has a smoke test and owner.
    
*   Credentials are environment-specific.
    
*   Provider failures produce actionable alerts and safe user errors.
    

PROD-036 — Automate backups and prove restoration
-------------------------------------------------

**Priority:** P0**Owner:** DevOps/Database**Estimate:** 2–3 days**Dependencies:** PROD-032–033

**Work:**

*   Schedule encrypted daily backups.
    
*   Configure retention and lifecycle.
    
*   Monitor job success, age, and size.
    
*   Restore into an isolated database.
    
*   Validate row counts and core application flow.
    
*   Record recovery point and recovery time objectives.
    

**Acceptance criteria:**

*   At least seven consecutive scheduled backups succeed before launch.
    
*   A restore drill passes.
    
*   Backup deletion permissions are narrowly scoped.
    
*   Restore evidence and timing are recorded.
    

PROD-037 — Add observability and incident response
--------------------------------------------------

**Priority:** P1**Owner:** DevOps + Tech lead**Estimate:** 3–4 days**Dependencies:** PROD-032

Monitor:

*   API availability, latency, and error rate.
    
*   Database/Redis connectivity and saturation.
    
*   Scheduler heartbeat/job failures.
    
*   Payment reconciliation and webhook failures.
    
*   OTP/email/push failures.
    
*   Upload failures/storage growth.
    
*   Backup age.
    
*   Queue/background-job failures.
    
*   Mobile/admin crash rates.
    

**Acceptance criteria:**

*   Critical alerts reach an accountable person within five minutes.
    
*   Alert runbooks identify diagnosis and rollback actions.
    
*   Test alerts are acknowledged.
    
*   PII is scrubbed from logs and monitoring.
    

PROD-038 — Create health-gated deployment and rollback pipeline
---------------------------------------------------------------

**Priority:** P1**Owner:** DevOps**Estimate:** 3–5 days**Dependencies:** PROD-002, PROD-031–037

**Work:**

*   Build immutable Git-SHA images.
    
*   Scan images.
    
*   Run migration as a separate job.
    
*   Deploy API, scheduler, and admin independently.
    
*   Wait for readiness before traffic switch.
    
*   Preserve previous images.
    
*   Require approval for production.
    
*   Add documented rollback and forward-migration handling.
    

**Acceptance criteria:**

*   A failed readiness check stops deployment.
    
*   Previous application version can be restored.
    
*   Migration incompatibility strategy is documented.
    
*   Staging and production use the same pipeline shape.
    

Gate 4 — Staging Ready
======================

Gate 4 requires:

*   Every application release gate green.
    
*   Staging infrastructure operational.
    
*   Payment test mode end-to-end.
    
*   Scheduler singleton verified.
    
*   TLS, secrets, monitoring, and backups working.
    
*   Restore drill passed.
    
*   Legal/commercial Gate 3 complete.
    

A controlled internal business trial can begin after this gate.

Phase 7 — End-to-End Quality and Security Verification
======================================================

PROD-039 — Add adversarial backend integration tests
----------------------------------------------------

**Priority:** P0**Owner:** Backend/QA**Estimate:** 4–6 days**Dependencies:** All backend P0 fixes

Cover:

*   Authentication matrix for every route.
    
*   Payment tampering and concurrency.
    
*   Scheduler idempotency.
    
*   IST boundary attendance.
    
*   Upload abuse.
    
*   Wrong social audiences.
    
*   Invoice concurrency.
    
*   Audit transaction integrity.
    
*   Retention/deletion.
    
*   Permission-group mutations.
    

**Acceptance criteria:**

*   Full 763+ test suite completes within a documented CI budget.
    
*   No test depends on external production services.
    
*   Flaky tests are not accepted.
    

PROD-040 — Add admin end-to-end tests
-------------------------------------

**Priority:** P1**Owner:** Admin/QA**Estimate:** 4–6 days**Dependencies:** PROD-019

Use Playwright or equivalent for:

*   Login/refresh/logout.
    
*   Worker review.
    
*   Requirement review and quote.
    
*   Assignment/replacement.
    
*   Attendance approval/correction.
    
*   Payment reconciliation.
    
*   Invoice/refund.
    
*   Payroll.
    
*   Complaint resolution.
    
*   Permission restrictions.
    

**Acceptance criteria:**

*   Critical-path suite runs in CI against an isolated backend/database.
    
*   Screens assert loading, empty, success, validation, and server-error states.
    

PROD-041 — Complete physical mobile device matrix
-------------------------------------------------

**Priority:** P0 for mobile launch**Owner:** Mobile/QA**Estimate:** 5–8 days**Dependencies:** PROD-021–024, PROD-035

Test at minimum:

*   Low/mid-range Android.
    
*   Current Android.
    
*   One supported iPhone.
    
*   Weak/unstable network.
    
*   GPS indoors/outdoors.
    
*   Camera and gallery.
    
*   Biometric available/unavailable/changed.
    
*   Notifications foreground/background/terminated.
    
*   OAuth and deep links.
    
*   App update and logout.
    
*   Onboarding kill/reopen at every step.
    
*   Payment success/cancel/failure.
    
*   Check-in/out and complaint workflows.
    

**Acceptance criteria:**

*   No critical or high defect is open.
    
*   Evidence includes device/OS, steps, expected, actual, screenshot/video, and logs.
    

PROD-042 — Run performance and capacity tests
---------------------------------------------

**Priority:** P1**Owner:** Backend/DevOps/QA**Estimate:** 3–5 days**Dependencies:** Staging data and monitoring

Test:

*   100, 500, 1,000 and target pilot concurrency.
    
*   OTP and login bursts.
    
*   Requirement list/search.
    
*   Worker matching.
    
*   Check-in peaks.
    
*   Admin dashboards.
    
*   Payment webhook bursts.
    
*   Payroll generation.
    
*   Large reports/exports.
    

**Acceptance criteria:**

*   Target p95 and error-rate budgets are agreed and met.
    
*   Database queries and indexes are profiled.
    
*   Pool sizes and timeouts are documented.
    
*   Autoscaling/capacity thresholds are known.
    

PROD-043 — Conduct independent security assessment
--------------------------------------------------

**Priority:** P0 for public launch**Owner:** External security tester + engineering**Estimate:** 1–2 weeks elapsed**Dependencies:** Feature-complete staging

Scope:

*   OWASP API Top 10.
    
*   Web/admin penetration testing.
    
*   Mobile storage/network/reverse-engineering review.
    
*   Authorization and ownership.
    
*   Payment manipulation.
    
*   OTP/session abuse.
    
*   Upload handling.
    
*   Cloud/IAM/storage configuration.
    
*   Dependency/container/secrets review.
    

**Acceptance criteria:**

*   All critical/high issues remediated and retested.
    
*   Accepted medium risks have owner and deadline.
    
*   Final report is stored securely.
    

Gate 5 — Pilot Ready
====================

Required:

*   Full automated suite green.
    
*   Admin E2E green.
    
*   Physical-device matrix passed.
    
*   Load target passed.
    
*   No critical/high security issue open.
    
*   Operational team trained.
    
*   Backup and rollback rehearsed.
    

Launch a limited Chennai pilot with:

*   Small controlled client group.
    
*   Capped worker count.
    
*   Daily payment reconciliation.
    
*   Daily operational review.
    
*   Named support contact.
    
*   Manual monitoring of attendance, refunds, and payroll.
    
*   Razorpay live mode only after finance approval.
    

Phase 8 — Pilot and Public Launch
=================================

PROD-044 — Run production dress rehearsal
-----------------------------------------

**Priority:** P0**Owner:** Entire launch team**Estimate:** 2 days**Dependencies:** Gate 5

Execute with synthetic accounts:

1.  Client signup/profile.
    
2.  Requirement creation.
    
3.  Admin review and quote.
    
4.  Advance payment.
    
5.  Worker onboarding/approval.
    
6.  Worker matching and assignment.
    
7.  Acceptance.
    
8.  GPS/selfie check-in/out.
    
9.  Attendance approval.
    
10.  Final payment.
    
11.  GST invoice.
    
12.  Payroll/disbursement.
    
13.  Complaint.
    
14.  Refund and credit note.
    
15.  Account-data request.
    
16.  Backup and restore.
    
17.  Application rollback.
    

**Acceptance criteria:**

*   Every step has evidence.
    
*   Payment, invoice, payroll, and audit records reconcile.
    
*   Alerts and notifications arrive.
    
*   Rollback and restore meet agreed objectives.
    

PROD-045 — Launch controlled pilot
----------------------------------

**Priority:** P0**Owner:** Product/Operations**Estimate:** 2–4 weeks observation**Dependencies:** PROD-044

**Pilot controls:**

*   Invite-only users.
    
*   Daily capacity limit.
    
*   Manual worker/client verification.
    
*   Daily payment and payroll reconciliation.
    
*   Daily error/security review.
    
*   Weekly access review.
    
*   Direct support channel.
    
*   Feature flags/kill switches for payments and check-in.
    

**Exit criteria:**

*   Two consecutive weeks without critical incidents.
    
*   Payment reconciliation is exact.
    
*   Backup jobs remain healthy.
    
*   Support SLAs are met.
    
*   Crash/error rates remain within target.
    
*   Pilot feedback has no unresolved launch-blocking issue.
    

PROD-046 — Public production launch
-----------------------------------

**Priority:** Final gate**Owner:** Executive launch owner**Estimate:** 1 day plus monitoring**Dependencies:** Successful pilot

**Acceptance criteria:**

*   Written go-live approval from engineering, operations, finance, legal/privacy, and product.
    
*   Store releases approved.
    
*   Production status/support pages published.
    
*   On-call coverage active.
    
*   Rollback owner available.
    
*   Monitoring war room active for the first 24–48 hours.
    

Use a staged rollout:

*   5%.
    
*   20%.
    
*   50%.
    
*   100%.
    

Pause automatically for payment mismatch, elevated error rate, scheduler failure, database saturation, or critical mobile crash.

Gate 6 — Public Production Ready
================================

The platform is production-ready only when:

*   PROD-001 through PROD-046 are complete or explicitly risk-accepted.
    
*   Zero P0/Critical or P1/High security findings remain.
    
*   CI is fully green from a clean checkout.
    
*   Legal, labour, GST, privacy, and payment decisions are signed off.
    
*   Backup restoration and rollback are proven.
    
*   Client and worker apps are separate signed store applications.
    
*   Pilot exit criteria are met.
    

Recommended Sprint Breakdown
----------------------------

SprintPrimary ticketsOutcomeSprint 1PROD-001–008, 019–020, 031Critical leaks/payment/build defects closedSprint 2PROD-009–018, 021–023Scheduler, time, auth, uploads, mobile variants hardenedSprint 3PROD-025–030 alongside 024Legal, GST, privacy, refunds, accessibilitySprint 4PROD-032–038Staging infrastructure and deployment automationSprint 5PROD-039–043E2E, device, performance, and security verificationSprint 6PROD-044–045Dress rehearsal and controlled pilotLaunchPROD-046Staged public release

The immediate implementation order should be **PROD-003 → PROD-004 → PROD-005 → PROD-006 → PROD-009 → PROD-010 → PROD-008/019/020 → PROD-031/022**. Those are the shortest path to eliminating the current catastrophic risks and restoring a buildable release.

10:17 PMApprove for me

5.6 SolHighIDE contextWork locallyLocal