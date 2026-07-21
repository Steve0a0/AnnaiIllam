# Production Hardening Tracker

This is the execution board for taking Annai Illam from the audited state to a controlled production release. It supplements `MVP_IMPLEMENTATION_TRACKER.md`; current code and test evidence override older done claims.

## Control Information

| Field | Value |
|---|---|
| Branch | `production-hardening` |
| Feature freeze | Active from 2026-07-20 |
| Release scope | Security, financial integrity, reliability, compliance, deployment, and verification only |
| Baseline owner | Tech Lead |
| Current gate | Gate 0 — baseline recorded |
| Next critical work | Product/Finance sign-off for `PROD-004`, then `PROD-005` and `PROD-006` |

## Feature Freeze Rules

- Do not add unrelated product features to `production-hardening`.
- Every change must reference a `PROD-NNN` ticket from this tracker.
- Emergency scope additions require Tech Lead and Product Owner approval.
- Database, payment, authentication, payroll, attendance, and infrastructure changes require the specialist approvals defined below.
- Existing uncommitted work that pre-dates this branch must not be silently included in a production-hardening commit; review and commit it separately.

## Role Ownership

Names can replace these role owners when the delivery team is confirmed. Until then, the named role is accountable and cannot be left unassigned.

| Area | Accountable owner | Required reviewers |
|---|---|---|
| Technical programme and release | Tech Lead | Product Owner, QA Lead |
| Backend/API/database | Backend Engineer | Tech Lead, QA Lead |
| Admin dashboard | Admin Frontend Engineer | Tech Lead, QA Lead |
| Mobile client/worker apps | Mobile Engineer | Tech Lead, QA Lead |
| Infrastructure and deployment | DevOps Engineer | Tech Lead, Security Reviewer |
| Test strategy and release evidence | QA Lead | Relevant engineering owner |
| Product rules and pilot scope | Product Owner | Operations Lead, Tech Lead |
| Privacy, contracts, labour law | Indian Legal/Privacy Counsel | Product Owner |
| GST, invoices, reconciliation | Finance Owner / Chartered Accountant | Backend Engineer, Product Owner |
| Security assessment and risk acceptance | Security Reviewer | Tech Lead, Executive Sponsor |

## Environment Approval Matrix

| Action | Required approval | Evidence required |
|---|---|---|
| Deploy to staging | Tech Lead + QA Lead | Green CI, migration plan, ticket acceptance evidence |
| Enable staging integrations | Tech Lead + integration owner | Environment-specific credentials and smoke test |
| Deploy production infrastructure | Tech Lead + DevOps Engineer | Network/IAM review, rollback and backup plan |
| Run production migration | Tech Lead + Backend Engineer + DevOps Engineer | Tested migration, backup, rollback/forward plan |
| Enable live Razorpay | Finance Owner + Product Owner + Tech Lead | Payment reconciliation and refund tests |
| Release client/worker store builds | Product Owner + Mobile Engineer + QA Lead | Signed build and device-matrix evidence |
| Start controlled pilot | Product Owner + Tech Lead + Legal + Finance | Gates 1–5 complete and written go-live record |
| Public production launch | Executive Sponsor plus all accountable owners | Pilot exit report, no open P0/P1-high risk |
| Accept an unresolved production risk | Executive Sponsor + affected specialist owner | Written scope, impact, mitigation, owner, expiry date |

## Verified Release Baseline — 2026-07-20

| Gate | Baseline result | Status | Required follow-up |
|---|---|---|---|
| Backend test collection | 763 tests collected | PASS | Keep collection stable and run full suite in CI |
| Backend high-risk subset | 145 passed, 8 warnings, 82.49 seconds | PASS | Add adversarial public-route/payment/scheduler tests |
| Full backend suite | Did not complete inside the four-minute audit window | UNVERIFIED | Establish bounded CI runtime and publish result |
| Backend Ruff | 58 findings, including undefined `old_worker_profile` | FAIL | `PROD-008` |
| Admin unit tests | 25/25 passed | PASS | Retain as a required gate |
| Admin ESLint | 2 errors and 8 warnings | FAIL | `PROD-019` |
| Admin production build | Undefined `queryClient` in workers page | FAIL | `PROD-019` |
| Mobile unit tests | 11/11 passed | PASS | Expand navigation/device coverage |
| Mobile TypeScript | Missing `neutralBg` token | FAIL | `PROD-020` |
| Admin production dependency audit | 0 known vulnerabilities | PASS | Automate in CI |
| Mobile production dependency audit | 0 known vulnerabilities | PASS | Automate in CI |
| Python vulnerability audit | `pip-audit` unavailable | UNVERIFIED | Add scanner in `PROD-002` |
| Tracked high-confidence secret scan | No match found | PASS | Add CI and container scans |

## Audit Corrections to Historical Status

- No-show handling requires review because its scheduler can run in every API worker and can evaluate workers before shift/grace time.
- Environment/secrets hardening is incomplete: production secrets management and Docker build-context exclusion are not implemented.
- API security headers do not establish admin-dashboard header coverage.
- The historical 763/763 backend pass is not a current release result.
- Current backend/admin/mobile release gates fail despite older CI/build claims.
- Push payload wiring does not prove delivery on physical devices.
- Load-test results are historical local evidence, not production capacity proof.

## Ticket Register

`TODO` means not started. `DONE` requires implementation, tests, documentation, tracker update, and acceptance evidence. All tickets have an accountable owner.

| Ticket | Priority | Status | Accountable owner | Summary |
|---|---|---|---|---|
| PROD-001 | P0 | DONE | Tech Lead | Create production hardening release baseline |
| PROD-002 | P0 | NEEDS_REVIEW | Tech Lead / DevOps Engineer | Gates implemented in-repo; GitHub branch ruleset activation remains external |
| PROD-003 | P0 Critical | DONE | Backend Engineer | User directory is super-admin-only, paginated, minimal, and covered by route-authentication regression tests |
| PROD-004 | P0 Critical | NEEDS_REVIEW | Backend Engineer / Product / Finance | Ledger implementation and tests complete; required Product/Finance sign-off remains pending |
| PROD-005 | P0 Critical | DONE | Backend Engineer | Authoritative rupees convert to paise only in the Razorpay adapter; real test-mode order verified |
| PROD-006 | P0 Critical | NEEDS_REVIEW | Backend Engineer | Row-locked callback/webhook reconciliation and race tests pass; interactive sandbox capture remains |
| PROD-007 | P0 | NEEDS_REVIEW | Backend / Admin / Mobile / Finance | Payment confirmations are receipts; issued GST invoices use their own immutable API/document. Finance acceptance required. |
| PROD-008 | P0 | TODO | Backend Engineer | Fix backend runtime and lint failures |
| PROD-009 | P0 High | DONE | Backend / DevOps | API workers contain no scheduler startup; one standalone scheduler replica owns all jobs |
| PROD-010 | P0 High | DONE | Backend Engineer / Product | No-shows require shift start plus configurable grace and are DB-idempotent |
| PROD-011 | P0 | DONE | Backend Engineer | One IST business-date helper owns attendance, no-show, quote-expiry, and related calendar decisions |
| PROD-012 | P1 | TODO | Backend / Database | Harden database constraints and lifecycle retention |
| PROD-013 | P1 High | DONE | Backend / Mobile | Google and Apple are explicitly opt-in, enabled providers require startup audiences, and cross-app tokens are rejected. |
| PROD-014 | P1 High | TODO | Backend / DevOps | Make critical rate limits fail safely |
| PROD-015 | P1 High | TODO | Backend / Mobile / DevOps | Secure document and selfie uploads |
| PROD-016 | P1 High | TODO | Backend / Admin | Harden admin session storage |
| PROD-017 | P1 | TODO | Admin / DevOps | Add admin web security headers |
| PROD-018 | P1 | TODO | Backend / Security | Redesign audit events |
| PROD-019 | P0 | DONE | Admin Frontend Engineer | ESLint, 25 unit tests, and Next.js production build pass |
| PROD-020 | P0 | DONE | Mobile Engineer | TypeScript and 11 mobile unit tests pass |
| PROD-021 | P1 | TODO | Mobile Engineer | Fix worker onboarding resume |
| PROD-022 | P0 | TODO | Mobile / DevOps / Product | Create separate client and worker production apps |
| PROD-023 | P1 | TODO | Mobile Engineer | Complete mobile permission configuration |
| PROD-024 | P1 | TODO | Admin / Mobile / QA | Remediate accessibility defects |
| PROD-025 | P0 | TODO | Product / Indian Legal Counsel | Decide business and worker legal classification |
| PROD-026 | P0 | NEEDS_REVIEW | Backend / Admin / Finance / CA | GST invoice snapshot, FY sequence, tax split, immutability, and shared document implemented. CA samples, e-invoice decision, and credit-note scope remain. |
| PROD-027 | P0 | TODO | Product / Backend / Admin / Mobile / Legal | Implement cancellation, refund, and dispute policy |
| PROD-028 | P0 | TODO | Legal / Product / Admin / Mobile | Publish privacy, terms, and grievance surfaces |
| PROD-029 | P0 | TODO | Backend / Admin / Mobile / Privacy Counsel | Implement DPDP consent and data-rights workflow |
| PROD-030 | P1 | TODO | Backend / Legal / DevOps | Implement retention and deletion controls |
| PROD-031 | P0 | TODO | Backend / Admin / DevOps | Add secure Docker build contexts |
| PROD-032 | P0 | TODO | DevOps Engineer | Provision staging infrastructure |
| PROD-033 | P0 | TODO | DevOps / Security | Configure production secrets and rotation |
| PROD-034 | P0 | TODO | DevOps Engineer | Configure DNS, TLS, WAF, and network controls |
| PROD-035 | P0 | TODO | DevOps / Backend / Product | Configure production integrations |
| PROD-036 | P0 | TODO | DevOps / Database | Automate backups and prove restoration |
| PROD-037 | P1 | TODO | DevOps / Tech Lead | Add observability and incident response |
| PROD-038 | P1 | TODO | DevOps Engineer | Create health-gated deployment and rollback pipeline |
| PROD-039 | P0 | TODO | Backend / QA | Add adversarial backend integration tests |
| PROD-040 | P1 | TODO | Admin / QA | Add admin end-to-end tests |
| PROD-041 | P0 Mobile Launch | TODO | Mobile / QA | Complete physical mobile device matrix |
| PROD-042 | P1 | TODO | Backend / DevOps / QA | Run performance and capacity tests |
| PROD-043 | P0 Public Launch | TODO | Security Reviewer / Engineering | Conduct independent security assessment |
| PROD-044 | P0 | TODO | Entire launch team | Run production dress rehearsal |
| PROD-045 | P0 | TODO | Product / Operations | Launch controlled pilot |
| PROD-046 | Final Gate | TODO | Executive Sponsor | Approve staged public production launch |

## Gate Status

| Gate | Status | Exit condition |
|---|---|---|
| Gate 0 — Baseline | DONE | Branch, freeze, owners, approvals, failing checks, and ticket register recorded |
| Gate 1 — Critical application safety | BLOCKED | Public PII, payment, backend runtime, and release-gate blockers fixed |
| Gate 2 — Security boundary | BLOCKED | Social auth, rate limits, uploads, admin sessions, headers, and audit hardened |
| Gate 3 — Legal/commercial | BLOCKED | Labour model, GST, privacy, consent, refunds, and retention approved |
| Gate 4 — Staging ready | BLOCKED | Green builds plus secure staging, integrations, backup and restore |
| Gate 5 — Pilot ready | BLOCKED | E2E, device, load, accessibility, and security verification complete |
| Gate 6 — Public production | BLOCKED | Pilot exit criteria and written cross-functional approval complete |

## Next Execution Order

1. Activate the `PROD-002` GitHub branch ruleset with the registered checks.
2. Complete the interactive Razorpay sandbox capture/webhook proof for `PROD-006` and obtain Product/Finance sign-off for `PROD-004`.
3. `PROD-008` — restore the backend Ruff gate.
4. `PROD-031` and `PROD-022` — secure builds and split mobile releases.

## PROD-002 Verification Evidence — 2026-07-20

Implemented:

- Backend CI now provisions PostgreSQL and Redis, pins Python 3.12.10, audits Python dependencies, runs Ruff, and runs the full pytest suite.
- Admin CI pins Node 22.19.0, uses `NEXT_PUBLIC_API_BASE_URL`, audits production dependencies, runs unit tests, lint, and the production build.
- Mobile CI pins Node 22.19.0, audits production dependencies, runs unit tests, and runs TypeScript with `--noEmit`.
- Security CI performs repository dependency/secret/misconfiguration scanning, pull-request dependency review, Python and JavaScript/TypeScript CodeQL analysis, and backend/admin container-image scans.
- Dependabot covers Python, both npm applications, GitHub Actions, and both Dockerfiles.
- Root runtime version files and production container images use the supported pinned versions.
- The pull-request template records scope, verification, risk, and rollback.
- `.github/BRANCH_PROTECTION.md` defines the exact required checks and GitHub ruleset procedure.

Verification:

- All workflow and Dependabot YAML files parse successfully.
- `git diff --check` passes.
- The first `production-hardening` GitHub Actions run registered all required check names. Both CodeQL jobs passed; dependency review correctly skipped because the event was a branch push rather than a pull request.
- The first run exposed a Redis health-command quoting defect and high/critical npm advisories. The follow-up fixes the Redis option, updates the admin/mobile lockfiles, pins patched Next.js, and overrides the vulnerable transitive mobile `ws` release.
- The exact admin and mobile production audit commands now exit successfully with no high or critical advisories.
- Backend vulnerable pins were upgraded as a compatible FastAPI/Starlette and pytest/pytest-asyncio set. `python -m pip_audit -r requirements.txt` reports no known vulnerabilities.
- Docker 29.6.1 is available, but local image builds were not run because PROD-031 has not yet excluded local environment files from Docker build contexts.
- Admin lint/build, mobile TypeScript, backend Ruff, and the full backend suite are green locally. The backend suite passes 796/796 tests against PostgreSQL and Redis after the dependency, scheduler, no-show, and timezone upgrades.
- A GitHub rerun is still required to verify the pushed results and identify any remaining container or repository scan findings.

## PROD-009 Verification Evidence — 2026-07-21

Implemented:

- API startup contains no scheduler import, lifespan hook, feature flag, or background task.
- `python -m app.scheduler_runner` is the only runtime entry point for scheduled jobs.
- Development and production deployment examples configure exactly one scheduler replica/process while API `WEB_CONCURRENCY` remains independently tunable.
- API readiness checks PostgreSQL and Redis only; it no longer reads process-local scheduler state.

Verification:

- Scheduler-process regression suite: 5/5 passed, including two API lifespans starting zero scheduler loops and one standalone process starting one loop.
- `docker compose config --quiet`: passed with one scheduler replica.
- Backend Ruff: passed.
- Full PostgreSQL/Redis backend suite: 794/794 passed.

## PROD-010 Verification Evidence — 2026-07-21

Implemented:

- No-show evaluation uses IST and waits for the first parsed `HH:MM` shift start plus `NO_SHOW_GRACE_PERIOD_MINUTES` (default 60).
- Missing/ambiguous shift starts fail safe and create no attendance record.
- Only accepted/active assignments inside their effective date window are eligible; cancelled and replaced assignments are excluded.
- Inserts use a savepoint and the `(assignment_id, attendance_date)` unique key so repeated or racing runs do not duplicate attendance or notifications.
- Alembic head `b7e1c42d9a60` repairs schema drift by deduplicating legacy rows and creating the unique constraint only when absent.

Verification:

- No-show regression suite: 15/15 passed, including 06:00 deploy safety, grace boundary, configurable grace, rerun idempotency, terminal assignments, and database duplicate rejection.
- Clean PostgreSQL migration from base to `b7e1c42d9a60`: passed; live constraint inspected as `UNIQUE (assignment_id, attendance_date)`.
- Focused Ruff: passed.
- Full PostgreSQL/Redis backend suite: 794/794 passed.

## PROD-011 Verification Evidence — 2026-07-21

Implemented:

- `business_date(at=None)` is the single Asia/Kolkata calendar-date helper; supplied naive timestamps are treated as stored UTC.
- Worker check-in stores its timestamp in UTC and derives `attendance_date` from that same timestamp in IST, so payroll periods aggregate the correct day.
- Attendance defaults, no-show evaluation, quote creation/expiry, worker matching, invoice due dates, and dashboard attendance alerts use the same helper.
- UTC timestamp storage remains unchanged.

Verification:

- Exact IST-midnight boundary coverage: 18:29:59 UTC remains the prior IST day and 18:30:00 UTC starts the next IST day.
- A 19:30 UTC check-in (01:00 IST) stores the next IST calendar date while retaining the naive UTC check-in timestamp.
- Focused attendance/payroll/no-show/quote suite: 104/104 passed.
- Backend Ruff: passed.
- Full PostgreSQL/Redis backend suite: 796/796 passed.

## PROD-005 and PROD-006 Verification Evidence — 2026-07-21

Implemented:

- The mobile callback verifies its signature with the server-stored order ID,
  then fetches the payment from Razorpay and requires `captured=true`,
  `status=captured`, INR, the expected order ID, and the exact ledger amount
  in paise.
- Mobile callbacks and `payment.captured` webhooks use one reconciliation
  service with `SELECT FOR UPDATE`, gateway-order/payment uniqueness, and a
  savepoint-protected flush.
- Callback-first and webhook-first delivery produce one paid ledger row.
  Duplicate webhooks, callbacks, and payment IDs do not change the ledger.
- The webhook signature is verified over the raw body. Razorpay event IDs are
  included in reconciliation audit events.
- The legacy synthetic webhook route is unavailable outside local test mode.
- The repeatable staging procedure is documented in
  `docs/RAZORPAY_SANDBOX_VERIFICATION.md`.

Verification:

- Authenticated Razorpay test-mode API call created a ₹1 order as 100 paise,
  currency INR, status `created`.
- Payment/ledger/transition suite: 71/71 passed.
- Full PostgreSQL/Redis backend suite: 802/802 passed.
- Backend Ruff and `git diff --check`: passed.
- Remaining external gate: complete interactive test Checkout, captured payment,
  mobile callback, and public staging webhook delivery/replay. Until retained
  evidence exists, PROD-006 remains `NEEDS_REVIEW`.

## ANNAI-7 Refund Execution Evidence — 2026-07-21

Implemented:

- Finance-admin-only refund approval targets an existing paid Razorpay payment.
- A pending, linked refund ledger row is committed before the external request
  and reserves both requirement-wide and source-payment refundable balance.
- Razorpay receives the whole-rupee amount converted to paise at the adapter
  boundary plus a durable X-Refund-Idempotency key.
- Processed API responses and signed refund.processed/refund.failed webhooks
  converge on one refund reconciliation service.
- Manual finance routes cannot create or confirm gateway refund rows.
- Duplicate approval clicks with the same key execute one gateway refund.

Verification:

- Payment ledger, finance, and dashboard suite: 80/80 passed.
- Full PostgreSQL/Redis backend suite: 809/809 passed.
- Backend Ruff: passed.
- A real sandbox refund still requires a captured test payment; the existing
  test order has not been paid and cannot be refunded.

## PROD-019 and PROD-020 Verification Evidence — 2026-07-21

Implemented:

- Admin render-time age calculation now uses React Query's stable update timestamp.
- Admin JSX copy passes the unescaped-entity rule.
- Worker review prefetching initializes its own React Query client.
- The admin quote payload type now matches the backend `worker_daily_rate` field.
- Mobile client colors include the typed `neutralBg` semantic token used by refunded-payment badges.

Verification:

- Admin `npm run lint`: passed with 0 errors and 8 non-blocking warnings.
- Admin `npm test`: 25/25 passed.
- Admin `npm run build`: passed, including TypeScript and 24 generated pages.
- Mobile `npx tsc --noEmit`: passed.
- Mobile `npm test -- --runInBand`: 11/11 passed.

Remaining acceptance step:

- Push the follow-up fixes, rerun the workflows, and activate the `main`/`develop` GitHub ruleset with the registered check names. No GitHub CLI or authenticated token is available in this workspace, so this server-side setting cannot be applied locally. Keep PROD-002 at `NEEDS_REVIEW` until the ruleset and a blocked-merge test pull request are evidenced.

## PROD-003 Verification Evidence — 2026-07-20

Implemented:

- `GET /api/v1/users` now requires the `super_admin` permission group.
- Client, worker, non-super-admin, missing, and invalid credentials cannot access the directory.
- The response is paginated and constrained by an explicit schema to `id`, `role`, `is_active`, and `created_at`; phone, email, and name are never returned.
- A regression test scans every registered API route and fails if a route becomes unauthenticated without being added to the explicit public-route allowlist.

Verification:

- `python -m pytest tests/test_users.py tests/test_permission_groups.py -v`: 29 passed.
- `python -m ruff check app/api/users.py app/schemas/user.py tests/test_users.py`: passed.
- `git diff --check`: passed.

## PROD-004 Verification Evidence — 2026-07-20

Implemented:

- `payment_ledger_service.py` is the single owner of quote totals, advance due,
  net paid, refunded, outstanding, and overpaid calculations.
- Client charge amount and model are derived from the approved quote and ledger;
  deprecated client hints cannot change the charge.
- Client receivables use documented integer whole INR rupees. Razorpay alone
  converts to integer paise at its adapter boundary.
- Payments have explicit advance, balance, adjustment, and refund purposes.
- New overpayments and excess refunds are rejected; duplicate gateway intents
  are reused and duplicate pending references are rejected.
- Payment success/admin verification changes only the ledger. Assignment and
  completion remain operational actions.
- The state diagram and approval record are in `docs/PAYMENT_LEDGER.md`.

Verification:

- `python -m pytest tests/test_payment_ledger.py tests/test_quote_amount_verification.py tests/test_payment_transitions.py -q`: 16 passed.
- `python -m pytest tests/test_finance_payments.py -q`: 49 passed.
- Combined payment and assignment-gate regression run: 67 passed.
- Full `tests/test_assignments.py`: 46 passed, 5 failed in pre-existing
  worker availability/capacity/replacement paths; the known undefined
  `old_worker_profile` runtime failure remains assigned to PROD-008.
- Product owner sign-off: PENDING.
- Finance owner sign-off: PENDING.
