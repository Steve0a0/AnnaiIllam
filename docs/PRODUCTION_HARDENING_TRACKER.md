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
| Next critical work | `PROD-003` public user-directory disclosure, with `PROD-002` release gates in parallel |

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
| PROD-003 | P0 Critical | TODO | Backend Engineer | Remove unauthenticated user-directory disclosure |
| PROD-004 | P0 Critical | TODO | Backend Engineer / Product / Finance | Define authoritative payment ledger and invariants |
| PROD-005 | P0 Critical | TODO | Backend Engineer | Fix Razorpay order amount calculation |
| PROD-006 | P0 Critical | TODO | Backend Engineer | Make payment verification and webhooks transactional |
| PROD-007 | P0 | TODO | Backend / Admin / Mobile / Finance | Separate payment receipts from GST invoices |
| PROD-008 | P0 | TODO | Backend Engineer | Fix backend runtime and lint failures |
| PROD-009 | P0 High | TODO | Backend / DevOps | Move scheduler out of API workers |
| PROD-010 | P0 High | TODO | Backend Engineer / Product | Correct no-show timing |
| PROD-011 | P0 | TODO | Backend Engineer | Implement timezone-aware business dates |
| PROD-012 | P1 | TODO | Backend / Database | Harden database constraints and lifecycle retention |
| PROD-013 | P1 High | TODO | Backend / Mobile | Enforce social-login audiences |
| PROD-014 | P1 High | TODO | Backend / DevOps | Make critical rate limits fail safely |
| PROD-015 | P1 High | TODO | Backend / Mobile / DevOps | Secure document and selfie uploads |
| PROD-016 | P1 High | TODO | Backend / Admin | Harden admin session storage |
| PROD-017 | P1 | TODO | Admin / DevOps | Add admin web security headers |
| PROD-018 | P1 | TODO | Backend / Security | Redesign audit events |
| PROD-019 | P0 | TODO | Admin Frontend Engineer | Restore admin production build |
| PROD-020 | P0 | TODO | Mobile Engineer | Restore mobile type safety |
| PROD-021 | P1 | TODO | Mobile Engineer | Fix worker onboarding resume |
| PROD-022 | P0 | TODO | Mobile / DevOps / Product | Create separate client and worker production apps |
| PROD-023 | P1 | TODO | Mobile Engineer | Complete mobile permission configuration |
| PROD-024 | P1 | TODO | Admin / Mobile / QA | Remediate accessibility defects |
| PROD-025 | P0 | TODO | Product / Indian Legal Counsel | Decide business and worker legal classification |
| PROD-026 | P0 | TODO | Backend / Admin / Finance / CA | Implement GST-compliant invoices and credit notes |
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

1. `PROD-003` — close the public user-directory disclosure.
2. Activate the `PROD-002` GitHub branch ruleset after the workflows run once.
3. `PROD-004` through `PROD-006` — repair financial invariants.
4. `PROD-009` through `PROD-011` — repair scheduler and time handling.
5. `PROD-008`, `PROD-019`, and `PROD-020` — make all applications releasable.
6. `PROD-031` and `PROD-022` — secure builds and split mobile releases.

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
- The exact admin and mobile production audit commands now exit successfully with no high or critical advisories. A GitHub rerun is required to verify the pushed result.
- Docker 29.6.1 is available, but local image builds were not run because PROD-031 has not yet excluded local environment files from Docker build contexts.
- Existing Ruff, admin lint/build, and mobile TypeScript failures are expected to keep the new gates red until PROD-008, PROD-019, and PROD-020 are resolved.

Remaining acceptance step:

- Push the follow-up fixes, rerun the workflows, and activate the `main`/`develop` GitHub ruleset with the registered check names. No GitHub CLI or authenticated token is available in this workspace, so this server-side setting cannot be applied locally. Keep PROD-002 at `NEEDS_REVIEW` until the ruleset and a blocked-merge test pull request are evidenced.
