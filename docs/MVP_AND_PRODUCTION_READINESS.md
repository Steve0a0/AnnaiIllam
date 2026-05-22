# MVP and Production Readiness Report

## Changelog
| Date | Changes |
|---|---|
| 2026-05-20 | GAP-030 resolved — added `tests/test_worker_onboarding.py` (50 tests, all passing): covers GET /status, POST /upload-url (invalid content/document type), POST /identity (idempotent resubmit), POST /profile (step guard, encrypted UPI, doc linking, photo URL, re-submit updates same record), POST /admin/people/workers/{id}/approve (404/403/401/422 double-approve), POST /admin/people/workers/{id}/reject (422 wrong step, short reason, docs rejected with remarks, rewind to identity_uploaded, re-profile-and-approve flow), and full happy-path end-to-end. Discovered: admin people router prefix is /admin/people not /admin. |
| 2026-05-20 | GAP-025 resolved — scheduler.py: added `_on_task_done` callback that auto-restarts task on unexpected exit and emits CRITICAL log; tracks `last_run_at`/`last_error` state; `get_scheduler_status()` exposes liveness; `GET /api/v1/ready` returns 503 and includes "scheduler" in errors when task is not alive. Note: Celery migration deferred to post-MVP (ROADMAP) for multi-process deployments. 254 tests pass. |
| 2026-05-20 | GAP-023 verified — EarningsScreen fully implemented and correctly wired: calls `GET /worker/payroll` + `GET /worker/payroll/payouts`, types match API shapes exactly, JWT auth attached via axios interceptor with variant-prefixed secure-store keys, auto-refresh on 401; screen shows hero net amount, paid date badge, stats chips, paginated history sorted newest-first, total received, payout ref/date per card; no code changes required |
| 2026-05-20 | GAP-022 resolved — added `GET /admin/replacements` list endpoint (paginated, status filter) + repo helper; added `ReplacementListItem`/`ReplacementListResponse` types, `getAllReplacements` service method, `useReplacements` hook; built `/replacements` admin page with status filter, full table, inline status-update Select+Save per row; added Replacements sub-nav under Complaints in sidebar |
| 2026-05-20 | GAP-021 resolved — backend already had CSV export via `?format=csv` on all report endpoints; wired admin UI: added `downloadRequirementsCsv`, `downloadAssignmentsCsv`, `downloadComplaintsCsv` to `reportsService` (authenticated blob download), replaced disabled "Export (Coming Soon)" buttons with live "Export CSV" buttons with loading state on all 3 report pages |
| 2026-05-20 | GAP-014 resolved - added managed Redis production provisioning guidance, `REDIS_URL` examples, backend Redis connectivity check command, smoke-test gate, and unit tests |
| 2026-05-20 | GAP-013 resolved - added PostgreSQL backup-to-S3 command, Docker support for pg_dump, backup env vars, retention handling, scheduler/restore runbook, and unit tests |
| 2026-05-20 | GAP-012 resolved - added production deployment runbook covering env vars, migrations, Docker/systemd deployment, Redis, S3, DNS/TLS, smoke tests, rollback, and backups |
| 2026-05-20 | GAP-011 resolved - wired Sentry error monitoring for FastAPI and Next.js with env-driven DSNs, request data scrubbing, and verified backend/admin builds |
| 2026-05-20 | GAP-010 resolved — added GitHub Actions backend CI (Ruff + pytest) and admin CI (ESLint + Next.js build) for PRs and pushes |
| 2026-05-20 | GAP-009 resolved — added 51 complaint integration tests covering complaint creation (all types/severities/ownership/role checks), replacement requests, admin listing with SLA breach info, admin status transitions (all 4 statuses), SLA policy CRUD, and SLA breach detection |
| 2026-05-20 | GAP-008 resolved — added 41 finance/payment integration tests covering Razorpay order creation, webhook signature verification (valid/invalid/duplicate), manual payment recording (all statuses), client payment status update, requirement auto-transition, worker payout creation, payout status update, and list endpoints |
| 2026-05-20 | GAP-007 resolved - added payroll integration tests covering run generation, deductions, all statuses, paid transition, and locked-run enforcement |
| 2026-05-20 | GAP-006 resolved - added attendance integration tests covering GPS check-in/out, geofence failures, admin correction, locked payroll blocking, ownership, and role checks |
| 2026-05-20 | GAP-005 resolved - added assignment integration tests covering admin create/read/status updates, worker accept/decline, role checks, ownership, and assignment gates |
| 2026-05-20 | GAP-004 resolved - added requirements/quote integration tests covering creation, review, quote, approval/rejection, ownership, and invalid transitions |
| 2026-05-20 | GAP-003/GAP-027 resolved — verified report sub-pages and added date/status filters plus row counts |
| 2026-05-20 | GAP-002 resolved — verified and polished admin complaint detail page with direct review, resolve, and reject/close actions |
| 2026-05-20 | GAP-001 resolved — added idempotent admin seed script, Makefile target, README docs, and tests |
| 2026-05-20 | Initial audit — full codebase review across backend, admin, and mobile |

---

## 1. Executive Summary

### What This Project Is
Annai Illam is a staffing and manpower management platform for the Indian market. It connects clients who need temporary workers (security guards, housekeeping, construction workers, etc.) with a vetted pool of workers. The platform has three distinct surfaces:
- **Backend API** — FastAPI (Python) REST API on PostgreSQL + Redis
- **Admin Dashboard** — Next.js web application for admin staff
- **Mobile App** — React Native / Expo app with two variants: one for clients, one for workers

The business flow is: client creates a manpower requirement → admin reviews and quotes → client approves and pays advance → admin assigns workers → workers check in/out with GPS + biometric → admin runs payroll → workers get paid.

### What Is Already Working
Based on direct code inspection:
- Admin email/password login with JWT, refresh tokens, and access token blocklisting
- Phone OTP login for clients and workers (SMS via MSG91, console in dev)
- Full worker onboarding: OTP → consent → identity document upload (S3/MinIO/local) → profile → admin review → approve/reject
- Social auth scaffolding (Google, Apple) — service exists but flows need verification
- Requirements (manpower requests) creation by clients and full admin management
- Quote flow: admin creates quote, client approves, payment advance required
- Payment: Razorpay gateway + manual record entry by admin, webhook handling
- Assignment creation by admin, worker accept/decline
- GPS + biometric check-in/check-out from the worker mobile app
- Admin attendance view, correction, approval (locked against payroll periods)
- Payroll run generation from attendance, deductions, status management, bulk payout
- Finance page: incoming payment confirmation, payroll queue
- Complaints: client raises complaints, admin reviews and resolves
- Worker issues: worker raises issues, admin sees them
- SLA policies: configurable response/resolution targets per severity
- Audit log: all key admin actions logged to DB and visible in admin
- Push notifications via Expo Push API (non-blocking, token-registered)
- Field-level encryption for worker bank/UPI details (Fernet/AES)
- Rate limiting on OTP and auth endpoints (Redis-backed)
- Background scheduler for cleanup of expired OTPs and revoked tokens
- Security headers middleware, CORS configuration
- Admin dashboard with real-time stats (requirements, assignments, attendance, complaints)
- All major admin pages built (workers, requirements, assignments, attendance, payroll, finance, complaints, audit, SLA, settings, reports)
- Worker mobile app: home with week strip, check-in/out with GPS+biometric, attendance history calendar, jobs board, issues, earnings screen, profile + availability
- Client mobile app: home, create request, request detail, assigned workers, complaints, payment confirm, invoice detail, rate requirement, profile

### What Is Incomplete
- Test coverage is much stronger for core backend flows. Auth/security, admin seeding, requirements/quote, assignment, attendance, payroll, finance/payment, and complaints are now covered; broader worker/client API coverage and E2E tests are still missing.
- No Docker Compose for full-stack local dev (backend has one for DB + MinIO, but there is no root-level orchestration)
- No deployment pipeline/release automation beyond PR CI checks; production deployment runbook now exists
- Redis production provisioning is documented and verifiable with `scripts.check_redis`, but the real production `REDIS_URL` still has to be configured and smoke-tested in the target environment
- Social auth (Google/Apple) wired at API level but mobile login screens for these are not visible — needs live verification
- Sentry error monitoring is wired for backend/admin, but production DSNs and external alert routing still need to be configured
- No end-to-end test suite
- Worker payroll view on mobile shows an `EarningsScreen` — confirmed the screen exists but needs backend payroll data linked
- No formal API documentation beyond OpenAPI (disabled in non-local environments)
- `admin_maintenance.py` router is imported and registered in `main.py` but the file was not audited

### Demo Readiness
**Yes, conditionally.** The core flow (login → create requirement → quote → payment → assign worker → check-in/out → view attendance → run payroll → finance) is fully implemented in code. A scripted demo using the admin panel and mobile app would work if the environment is set up correctly with PostgreSQL, Redis, and MinIO.

### MVP Launch Readiness
**No.** Blockers: no automated end-to-end test suite, no production Sentry DSN smoke test, and no confirmed social auth mobile screens.

### Production Readiness
**No.** Blockers: no uptime alerting/log aggregation, no rate limiting on most non-auth endpoints, no E2E tests, no load testing, and no provisioned production infrastructure.

### Readiness Scores

| Area | Score |
|---|---:|
| MVP Readiness | 7/10 |
| Production Readiness | 6/10 |
| Backend Readiness | 8/10 |
| Frontend/Admin Readiness | 7/10 |
| Mobile App Readiness | 7/10 |
| Auth & Security Readiness | 8/10 |
| Database Readiness | 8/10 |
| Testing Readiness | 7/10 |
| DevOps/Deployment Readiness | 7/10 |

### Completion

| Area | Completion % |
|---|---:|
| Overall MVP Completion | 72% |
| Overall Production Completion | 52% |

---

## 2. Product Understanding From Code

**Product**: Annai Illam is a B2B staffing marketplace platform focused on India. The name and design suggest Tamil Nadu as the primary market, with city/state fields on all relevant models.

**Users**:
- **Admin** — company staff who manage the entire workflow. Login via email/password. They review workers, create quotes, create assignments, manage payroll, resolve complaints. There is a single admin role with full permissions.
- **Client** — businesses that hire workers. Login via phone OTP or Google/Apple. They post manpower requirements, receive and approve/reject quotes, pay advance, raise complaints, rate completed requirements.
- **Worker** — individuals who take up assignments. Login via phone OTP. They go through a multi-step onboarding (consent → ID upload → profile → admin approval → biometric setup). Once approved, they see their assignments, check in/out with GPS and biometric, track attendance, view earnings, raise issues.

**Main Business Workflows** (from code evidence):
1. **Worker Supply Side**: Worker downloads app → OTP login → consent → upload govt ID + selfie → fill profile (skills, experience, availability, UPI/bank) → submitted to admin → admin approves or rejects → on approval, worker goes to biometric setup → worker is now in the pool
2. **Client Demand Side**: Client downloads app → OTP login → creates requirement (category, location, start date, number of workers, duration, food/accommodation needs) → admin reviews → admin creates quote (amount, advance, payment model) → client approves quote → client pays advance via Razorpay or UPI/bank reference → admin confirms payment → requirement transitions to "assigned"
3. **Operations**: Admin creates assignment (links worker to requirement with role, shift, salary) → worker sees assignment in app → worker accepts/declines → on assigned day, worker checks in with GPS + biometric → worker checks out → admin views attendance, corrects if needed
4. **Payroll**: Admin creates payroll run for a date range → system auto-calculates gross from attendance × daily rate → admin can add deductions → admin locks run → admin marks run as paid (creates worker payout records) → finance page shows confirmation and payroll queue
5. **Escalation**: Client raises complaint linked to requirement/assignment → admin sees it in complaints page → admin can resolve with notes → SLA policies define response/resolution hours per severity

**Technology Evidence**:
- FastAPI (Python 3.12-style type hints), SQLAlchemy 2.0, Alembic migrations, PostgreSQL, Redis
- Next.js admin with Zustand state, React Query, shadcn/ui, Tailwind CSS
- React Native + Expo + Tamagui + React Navigation for mobile
- Razorpay for payments, Expo Push API for notifications, MSG91 for SMS, S3/MinIO for storage
- Field-level AES-128 encryption (Fernet) for payment details

---

## 3. Current Implemented Features

| Feature / Module | What is implemented | Evidence / File Path | Status | Notes |
|---|---|---|---|---|
| Admin Login | Email + password, JWT access + refresh tokens, token rotation, access token blocklist on logout | `apps/backend/app/api/auth.py` | ✅ Implemented | Rate limited, generic error messages |
| Client OTP Login | Phone OTP request/verify, new user creation, role mismatch prevention | `apps/backend/app/api/auth.py` | ✅ Implemented | SMS via MSG91, console in dev |
| Worker OTP Login | Same as client OTP, separate endpoint | `apps/backend/app/api/auth.py` | ✅ Implemented | |
| Social Auth | Google ID token + Apple sign-in endpoints | `apps/backend/app/api/auth_social.py` | 🟡 Partially implemented | Mobile screens for these not confirmed |
| JWT Security | Access + refresh token pair, JTI in both tokens, refresh rotation, revoked token blocklist | `apps/backend/app/core/security.py`, `app/services/token_service.py` | ✅ Implemented | |
| Rate Limiting | Redis-backed rate limiting on OTP request, OTP verify, admin login, refresh, token hash | `apps/backend/app/core/rate_limit.py` | ✅ Implemented | Only applied to auth endpoints |
| Field-level Encryption | Fernet AES-128 encryption for worker UPI ID, bank account, IFSC | `apps/backend/app/core/encryption.py`, `app/api/worker_onboarding.py` | ✅ Implemented | Required in staging/production |
| Security Headers | Middleware adding security headers to all responses | `apps/backend/app/core/security_headers.py` | ✅ Implemented | |
| Worker Onboarding — Consent | Consent screen, terms display | `apps/mobile-ui-lab/src/apps/worker/screens/auth/ConsentScreen.tsx` | ✅ Implemented | |
| Worker Onboarding — Identity Upload | Presigned S3 URL generation, local upload fallback, document recording | `apps/backend/app/api/worker_onboarding.py` | ✅ Implemented | Local fallback for dev |
| Worker Onboarding — Profile Submit | Profile creation with encrypted payment fields, links documents, step = "profile_submitted" | `apps/backend/app/api/worker_onboarding.py` | ✅ Implemented | |
| Worker Onboarding — Biometric Setup | Mobile biometric setup screen after admin approval | `apps/mobile-ui-lab/src/apps/worker/screens/auth/BiometricSetupScreen.tsx` | ✅ Implemented | |
| Admin Worker Review | List workers by onboarding step, approve/reject with reason, view documents | `apps/admin/src/app/(dashboard)/workers/page.tsx`, `apps/backend/app/api/admin_people.py` | ✅ Implemented | |
| Admin Worker Availability Toggle | Mark worker available/on-leave | `apps/admin/src/app/(dashboard)/workers/page.tsx` | ✅ Implemented | |
| Bulk Worker Import | CSV paste and import from admin | `apps/admin/src/app/(dashboard)/workers/page.tsx` | ✅ Implemented | |
| Worker Document Viewing | Admin can view uploaded documents via presigned URL or local download | `apps/admin/src/app/(dashboard)/workers/page.tsx` | ✅ Implemented | |
| Client Profile | Create/update client profile, contact name, company name, type | `apps/backend/app/api/client_profile.py` | ✅ Implemented | |
| Client Creates Requirement | Full requirement form: category, workers, location, dates, food/accommodation, budget, geofence | `apps/backend/app/api/client_requirements.py`, `apps/mobile-ui-lab/src/apps/client/screens/CreateRequestScreen.tsx` | ✅ Implemented | |
| Admin Requirements List | Paginated list with status filter | `apps/backend/app/api/admin_requirements.py`, `apps/admin/src/app/(dashboard)/requirements/page.tsx` | ✅ Implemented | |
| Admin Requirement Detail + Quote | Mark under review, create quote (amount, advance, payment model, validity) | `apps/backend/app/api/admin_requirements.py` | ✅ Implemented | |
| Client Quote Approval | Client approves/rejects quote | `apps/backend/app/api/client_requirements.py` | ✅ Implemented | Needs mobile screen verification |
| Client Payment — Razorpay | Create Razorpay order, verify webhook signature, update payment status | `apps/backend/app/api/client_payments.py`, `apps/backend/app/api/payment_webhooks.py`, `apps/backend/app/services/razorpay_service.py` | ✅ Implemented | |
| Client Payment — Manual/Reference | Client submits UTR/bank reference, admin verifies | `apps/backend/app/api/admin_finance.py` | ✅ Implemented | |
| Payment Auto-transitions Requirement | When admin marks payment "paid" and advance exists, requirement auto-moves to "assigned" | `apps/backend/app/api/admin_finance.py` | ✅ Implemented | |
| Admin Assignment Creation | Create assignment linking worker to requirement with role, shift, salary | `apps/backend/app/api/admin_assignments.py` | ✅ Implemented | |
| Admin Assignment List | List all assignments with filter and search | `apps/admin/src/app/(dashboard)/assignments/page.tsx` | ✅ Implemented | |
| Worker Assignment Accept/Decline | Worker sees assignment, accepts or declines | `apps/backend/app/api/worker_assignments.py`, `apps/mobile-ui-lab/src/apps/worker/screens/HomeScreen.tsx` | ✅ Implemented | |
| Worker GPS Check-in | GPS location collected, geofence validation against requirement site coordinates | `apps/backend/app/api/worker_attendance.py`, `apps/backend/app/utils/geofence.py` | ✅ Implemented | |
| Worker Biometric Gate | `expo-local-authentication` used before check-in and check-out | `apps/mobile-ui-lab/src/apps/worker/screens/HomeScreen.tsx` | ✅ Implemented | |
| Worker GPS Check-out | GPS on check-out, biometric gate | `apps/mobile-ui-lab/src/apps/worker/screens/HomeScreen.tsx` | ✅ Implemented | |
| Admin Attendance View/Correct | View by requirement ID or assignment ID, verify, correct status and notes | `apps/backend/app/api/admin_attendance.py`, `apps/admin/src/app/(dashboard)/attendance/page.tsx` | ✅ Implemented | Locked against payroll periods |
| Payroll Run Generation | Auto-generates payroll items from attendance × daily salary | `apps/backend/app/api/admin_payroll.py` | ✅ Implemented | |
| Payroll Deductions | Admin adds deductions per item, net amount recalculated | `apps/backend/app/api/admin_payroll.py` | ✅ Implemented | |
| Payroll Status Management | Draft → Generated → Locked → Paid transitions, locked runs block edits | `apps/backend/app/api/admin_payroll.py` | ✅ Implemented | |
| Worker Payout Creation | Create individual payout or bulk-pay entire run | `apps/backend/app/api/admin_finance.py` | ✅ Implemented | |
| Finance Dashboard | Incoming payments tab, payroll queue tab, confirm/reject advance, transfer all | `apps/admin/src/app/(dashboard)/finance/page.tsx` | ✅ Implemented | |
| Client Complaints (Raise) | Client raises complaint linked to requirement/assignment, type + severity + description | `apps/backend/app/api/client_complaints.py`, `apps/mobile-ui-lab/src/apps/client/screens/RaiseComplaintScreen.tsx` | ✅ Implemented | |
| Admin Complaints List | View all complaints with type, severity, status | `apps/admin/src/app/(dashboard)/complaints/page.tsx` | ✅ Implemented | |
| Admin Complaint Resolution | Admin can resolve complaints with notes | `apps/backend/app/api/admin_complaints.py` | ✅ Implemented | |
| Worker Issues (Raise) | Worker raises issue | `apps/backend/app/api/worker_issues.py`, `apps/mobile-ui-lab/src/apps/worker/screens/RaiseIssueScreen.tsx` | ✅ Implemented | |
| SLA Policies | Configurable response/resolution hours per complaint severity, admin edits | `apps/backend/app/api/admin_sla.py`, `apps/admin/src/app/(dashboard)/sla/page.tsx` | ✅ Implemented | |
| Audit Log | All key actions written to `audit_logs` table and returned in admin UI | `apps/backend/app/utils/audit.py`, `apps/backend/app/api/admin_audit.py`, `apps/admin/src/app/(dashboard)/audit/page.tsx` | ✅ Implemented | Sensitive keys redacted |
| Push Notifications | Expo Push API, non-blocking background tasks, token registration | `apps/backend/app/services/notification_service.py`, `apps/backend/app/api/push_tokens.py` | ✅ Implemented | Token deactivated on logout |
| Document Storage | S3/MinIO presigned URLs, local fallback for dev | `apps/backend/app/services/storage_service.py` | ✅ Implemented | |
| Background Scheduler | In-process async loop cleans expired OTPs and revoked tokens every 24h | `apps/backend/app/core/scheduler.py` | ✅ Implemented | |
| Admin Dashboard Stats | Live counts: requirements, assignments, attendance present/absent, complaints, missing attendance alerts | `apps/backend/app/api/admin_dashboard.py`, `apps/admin/src/app/(dashboard)/dashboard/page.tsx` | ✅ Implemented | |
| Reports Page | Requirements, assignments, and complaints sub-reports with date/status filters and row counts | `apps/admin/src/app/(dashboard)/reports/page.tsx`, `apps/admin/src/app/(dashboard)/reports/requirements/page.tsx`, `apps/admin/src/app/(dashboard)/reports/assignments/page.tsx`, `apps/admin/src/app/(dashboard)/reports/complaints/page.tsx` | ✅ Implemented | CSV/PDF export remains P2 |
| Settings — Change Password | Admin can change their password | `apps/admin/src/app/(dashboard)/settings/page.tsx` | ✅ Implemented | |
| Worker Attendance History (Mobile) | Calendar view, summary tiles, streak counter, monthly records list | `apps/mobile-ui-lab/src/apps/worker/screens/AttendanceHistoryScreen.tsx` | ✅ Implemented | |
| Worker Earnings Screen (Mobile) | Screen exists | `apps/mobile-ui-lab/src/apps/worker/screens/EarningsScreen.tsx` | 🟡 Partially implemented | Content detail not read |
| Worker Availability (Mobile) | Set available/not available | `apps/mobile-ui-lab/src/apps/worker/screens/AvailabilityScreen.tsx` | ✅ Implemented | |
| Worker Jobs Board (Mobile) | Browse available jobs | `apps/mobile-ui-lab/src/apps/worker/screens/JobsBoardScreen.tsx` | ✅ Implemented | |
| Client Home Screen (Mobile) | Dashboard showing requirements, quick actions | `apps/mobile-ui-lab/src/apps/client/screens/HomeScreen.tsx` | ✅ Implemented | |
| Client Create Request (Mobile) | Full requirement creation form | `apps/mobile-ui-lab/src/apps/client/screens/CreateRequestScreen.tsx` | ✅ Implemented | |
| Client Payment Confirm (Mobile) | Payment confirmation screen | `apps/mobile-ui-lab/src/apps/client/screens/PaymentConfirmScreen.tsx` | ✅ Implemented | |
| Client Rate Requirement (Mobile) | Rating screen after completion | `apps/mobile-ui-lab/src/apps/client/screens/RateRequirementScreen.tsx` | ✅ Implemented | |
| Client Billing Overview (Mobile) | Billing overview screen | `apps/mobile-ui-lab/src/apps/client/screens/BillingOverviewScreen.tsx` | ✅ Implemented | |
| Admin Replacements | Replacement request tracking | `apps/backend/app/api/admin_replacements.py` | 🟡 Partially implemented | Admin UI page not found in routes |
| Worker Interest / Job Matching | Workers express interest in requirements, admin sees interested workers | `apps/backend/app/api/worker_jobs.py`, `apps/backend/app/api/admin_requirements.py` | ✅ Implemented | |

---

## 4. End-to-End Flow Review

### Flow: Admin Login
| Step | Current Implementation | File/API Evidence | Status | Gap |
|---|---|---|---|---|
| Admin enters email + password | LoginForm component calls POST /api/v1/auth/admin/login | `apps/admin/src/features/auth`, `apps/backend/app/api/auth.py` | ✅ Working | None |
| Server validates credentials | Rate limit checked, bcrypt verify, generic error if wrong | `apps/backend/app/api/auth.py` | ✅ Working | None |
| Tokens returned and stored | access_token + refresh_token returned, stored in Zustand + localStorage via authStorage | `apps/admin/src/store/auth-store.ts` | ✅ Working | None |
| Redirect to dashboard | useEffect on login page detects token and redirects | `apps/admin/src/app/(auth)/login/page.tsx` | ✅ Working | None |
| Auto-refresh on 401 | Axios interceptor rotates tokens | `apps/admin/src/services/api-client.ts` | Unclear from code | api-client.ts not read |

### Flow: Worker Onboarding
| Step | Current Implementation | File/API Evidence | Status | Gap |
|---|---|---|---|---|
| Phone OTP request | POST /auth/worker/request-otp, SMS via MSG91 or console | `apps/backend/app/api/auth.py` | ✅ Working | None |
| OTP verify | POST /auth/worker/verify-otp, creates User if new | `apps/backend/app/api/auth.py` | ✅ Working | None |
| Navigate to OTP screen | WelcomeScreen → VerifyOtpScreen | `apps/mobile-ui-lab/src/apps/worker/screens/auth/` | ✅ Working | None |
| Consent screen | Worker accepts terms | `apps/mobile-ui-lab/src/apps/worker/screens/auth/ConsentScreen.tsx` | ✅ Working | None |
| ID document upload | Get presigned URL → upload to S3 → POST /worker/onboarding/identity | `apps/backend/app/api/worker_onboarding.py` | ✅ Working | Local fallback for dev |
| Verify identity step | VerifyIdentityScreen on mobile | `apps/mobile-ui-lab/src/apps/worker/screens/auth/VerifyIdentityScreen.tsx` | ✅ Working | None |
| Profile build | BuildProfileScreen → POST /worker/onboarding/profile with encrypted payment | `apps/backend/app/api/worker_onboarding.py` | ✅ Working | None |
| Profile submitted screen | UnderReviewScreen shown | `apps/mobile-ui-lab/src/apps/worker/screens/auth/UnderReviewScreen.tsx` | ✅ Working | None |
| Admin reviews profile | Worker appears in workers page with "profile_submitted" filter | `apps/admin/src/app/(dashboard)/workers/page.tsx` | ✅ Working | None |
| Admin approves | POST /admin/people/workers/{id}/approve | `apps/backend/app/api/admin_people.py` | ✅ Working | Approval sends push notification |
| Admin rejects | POST /admin/people/workers/{id}/reject with reason | `apps/backend/app/api/admin_people.py` | ✅ Working | None |
| Biometric setup | BiometricSetupScreen runs after approval detected | `apps/mobile-ui-lab/src/apps/worker/screens/auth/BiometricSetupScreen.tsx` | ✅ Working | None |
| Worker reaches home screen | Main app navigator unlocked after biometric setup | `apps/mobile-ui-lab/src/apps/worker/navigation/AppNavigator.tsx` | ✅ Working | None |

### Flow: Client Creates Requirement
| Step | Current Implementation | File/API Evidence | Status | Gap |
|---|---|---|---|---|
| Client OTP login | POST /auth/client/request-otp + /auth/client/verify-otp | `apps/backend/app/api/auth.py` | ✅ Working | None |
| Client profile setup | POST /client/profile | `apps/backend/app/api/client_profile.py` | ✅ Working | None |
| Create requirement form | CreateRequestScreen on mobile | `apps/mobile-ui-lab/src/apps/client/screens/CreateRequestScreen.tsx` | ✅ Working | None |
| POST requirement to API | POST /client/requirements | `apps/backend/app/api/client_requirements.py` | ✅ Working | None |
| Admin sees requirement | Requirements page shows status "submitted" | `apps/admin/src/app/(dashboard)/requirements/page.tsx` | ✅ Working | None |

### Flow: Admin Reviews Requirement → Quote → Client Approves
| Step | Current Implementation | File/API Evidence | Status | Gap |
|---|---|---|---|---|
| Admin marks under review | POST /admin/requirements/{id}/mark-review | `apps/backend/app/api/admin_requirements.py` | ✅ Working | None |
| Admin creates quote | POST /admin/requirements/{id}/quote with amount, advance, payment model | `apps/backend/app/api/admin_requirements.py` | ✅ Working | None |
| Requirement transitions to "quoted" | Auto on quote creation | `apps/backend/app/api/admin_requirements.py` | ✅ Working | None |
| Client notified | Push notification via notification_service | Unclear — push call not confirmed in this path | ⚠️ Risky | Push may not fire on quote creation |
| Client approves quote | POST /client/requirements/{id}/approve-quote | `apps/backend/app/api/client_requirements.py` | ✅ Working | Need mobile screen verification |
| Requirement moves to "approved" | On quote approval | `apps/backend/app/api/client_requirements.py` | ✅ Working | None |

### Flow: Client Pays Advance → Admin Confirms → Requirement Assigned
| Step | Current Implementation | File/API Evidence | Status | Gap |
|---|---|---|---|---|
| Client initiates Razorpay order | POST /client/payments/create-order | `apps/backend/app/api/client_payments.py` | ✅ Working | None |
| Client pays in mobile app | PaymentConfirmScreen | `apps/mobile-ui-lab/src/apps/client/screens/PaymentConfirmScreen.tsx` | ✅ Working | None |
| Razorpay webhook fires | POST /webhooks/payment, signature verified | `apps/backend/app/api/payment_webhooks.py`, `apps/backend/app/services/webhook_security.py` | ✅ Working | None |
| Manual reference payment | Client submits UTR, admin sees in finance | `apps/backend/app/api/admin_finance.py` | ✅ Working | None |
| Admin confirms payment | PATCH /admin/finance/client-payments/{id}/status → "paid" | `apps/backend/app/api/admin_finance.py` | ✅ Working | None |
| Requirement auto-transitions to "assigned" | On paid status when quote has advance_amount > 0 | `apps/backend/app/api/admin_finance.py` | ✅ Working | Finance page shows toast notification |

### Flow: Admin Creates Assignment
| Step | Current Implementation | File/API Evidence | Status | Gap |
|---|---|---|---|---|
| Admin selects requirement and worker | Assignment creation form | `apps/admin/src/app/(dashboard)/requirements/[id]/page.tsx` | 🟡 Partial | Requirement detail page not fully read |
| POST /admin/assignments | Creates assignment record | `apps/backend/app/api/admin_assignments.py` | ✅ Working | None |
| Worker receives push notification | enqueue_push_to_user on assignment creation | `apps/backend/app/api/admin_assignments.py` | ✅ Working | None |

### Flow: Worker GPS Check-in/Check-out
| Step | Current Implementation | File/API Evidence | Status | Gap |
|---|---|---|---|---|
| Worker sees assignment on home screen | Load assignments on focus | `apps/mobile-ui-lab/src/apps/worker/screens/HomeScreen.tsx` | ✅ Working | None |
| Worker taps Check In | GPS permission requested, location captured | `apps/mobile-ui-lab/src/apps/worker/screens/HomeScreen.tsx` | ✅ Working | None |
| Location preview modal shown | Static Google Map image (if API key set) | `apps/mobile-ui-lab/src/apps/worker/screens/HomeScreen.tsx` | ✅ Working | Falls back gracefully if no Maps key |
| Biometric authentication | expo-local-authentication before submitting | `apps/mobile-ui-lab/src/apps/worker/screens/HomeScreen.tsx` | ✅ Working | None |
| POST /worker/attendance/check-in | Lat/long sent, geofence validated server-side | `apps/backend/app/api/worker_attendance.py`, `apps/backend/app/utils/geofence.py` | ✅ Working | None |
| Worker taps Check Out | Biometric gate, GPS captured, POST /worker/attendance/check-out | `apps/mobile-ui-lab/src/apps/worker/screens/HomeScreen.tsx` | ✅ Working | None |

### Flow: Admin Views/Corrects Attendance
| Step | Current Implementation | File/API Evidence | Status | Gap |
|---|---|---|---|---|
| Admin enters Requirement ID or Assignment ID | Attendance page search | `apps/admin/src/app/(dashboard)/attendance/page.tsx` | ✅ Working | None |
| Records displayed with check-in/out times | Table with hours calculation | `apps/admin/src/app/(dashboard)/attendance/page.tsx` | ✅ Working | None |
| Admin verifies a record | PATCH /admin/attendance/{id} → status "approved" | `apps/backend/app/api/admin_attendance.py` | ✅ Working | Locked if payroll is locked |
| Admin corrects status/notes | Dialog opens CorrectAttendanceForm | `apps/admin/src/app/(dashboard)/attendance/page.tsx` | ✅ Working | None |

### Flow: Payroll Run Creation + Approval
| Step | Current Implementation | File/API Evidence | Status | Gap |
|---|---|---|---|---|
| Admin creates payroll run with date range | POST /admin/payroll/runs | `apps/backend/app/api/admin_payroll.py` | ✅ Working | None |
| System generates items from active assignments | Loops assignments, counts attendance, calculates gross | `apps/backend/app/api/admin_payroll.py` | ✅ Working | None |
| Admin reviews items and adds deductions | POST /admin/payroll/deductions | `apps/backend/app/api/admin_payroll.py` | ✅ Working | Locked run blocks edits |
| Admin locks run | PATCH /admin/payroll/runs/{id}/status → "locked" | `apps/backend/app/api/admin_payroll.py` | ✅ Working | None |
| Admin approves payout | PATCH /admin/payroll/runs/{id}/status → "approved" | `apps/backend/app/api/admin_payroll.py` | ✅ Working | None |
| Finance page bulk transfer | POST /admin/finance/payroll-queue/{id}/mark-paid creates payout records | `apps/backend/app/api/admin_finance.py` | ✅ Working | None |

### Flow: Complaint Life Cycle
| Step | Current Implementation | File/API Evidence | Status | Gap |
|---|---|---|---|---|
| Client raises complaint | POST /client/complaints | `apps/backend/app/api/client_complaints.py`, `apps/mobile-ui-lab/src/apps/client/screens/RaiseComplaintScreen.tsx` | ✅ Working | None |
| Admin sees complaint in list | GET /admin/complaints | `apps/admin/src/app/(dashboard)/complaints/page.tsx` | ✅ Working | None |
| Admin views detail and resolves | `/complaints/{id}` detail page shows complaint context and direct resolution actions | `apps/admin/src/app/(dashboard)/complaints/[id]/page.tsx`, `apps/admin/src/features/complaints/update-complaint-status-form.tsx` | ✅ Working | None |
| SLA tracking | SLA policies define hours, backend tracks but no auto-escalation found | `apps/backend/app/api/admin_sla.py` | 🟡 Partial | No auto-escalation logic |

### Flow: Reports Generation
| Step | Current Implementation | File/API Evidence | Status | Gap |
|---|---|---|---|---|
| Admin opens reports | Reports page shows 3 card links | `apps/admin/src/app/(dashboard)/reports/page.tsx` | ✅ Working | None |
| Admin views sub-report | Requirements, assignments, and complaints sub-pages render real backend data with filters | `apps/admin/src/app/(dashboard)/reports/*/page.tsx`, `apps/backend/app/api/admin_reports.py` | ✅ Working | None |
| Export to CSV/PDF | Backend supports CSV via `format=csv`; UI still labels export as coming soon | `apps/backend/app/api/admin_reports.py` | 🟡 Partial | UI export remains P2 |

---

## 5. MVP Scope Based on Current Code

| MVP Feature | Current Status | Required for MVP? | Gap | Priority |
|---|---|---|---|---|
| Admin login | ✅ Implemented | Yes | None | Done |
| Worker OTP login | ✅ Implemented | Yes | None | Done |
| Client OTP login | ✅ Implemented | Yes | None | Done |
| Worker onboarding (full flow) | ✅ Implemented | Yes | None | Done |
| Admin worker review/approve/reject | ✅ Implemented | Yes | None | Done |
| Client create requirement | ✅ Implemented | Yes | None | Done |
| Admin review + quote | ✅ Implemented | Yes | None | Done |
| Client quote approval | ✅ Implemented | Yes | Needs mobile screen verification | P1 |
| Client payment (Razorpay) | ✅ Implemented | Yes | None | Done |
| Client payment (manual/UTR) | ✅ Implemented | Yes | None | Done |
| Admin payment confirmation | ✅ Implemented | Yes | None | Done |
| Admin create assignment | ✅ Implemented | Yes | None | Done |
| Worker accept/decline assignment | ✅ Implemented | Yes | None | Done |
| Worker GPS + biometric check-in | ✅ Implemented | Yes | None | Done |
| Worker GPS + biometric check-out | ✅ Implemented | Yes | None | Done |
| Admin attendance view + correction | ✅ Implemented | Yes | None | Done |
| Payroll run generation | ✅ Implemented | Yes | None | Done |
| Finance dashboard (payments + payroll) | ✅ Implemented | Yes | None | Done |
| Client raises complaint | ✅ Implemented | Yes | None | Done |
| Admin resolves complaint | ✅ Implemented | Yes | Complaint detail page verified with direct resolve action | Done |
| Worker raises issue | ✅ Implemented | Yes | None | Done |
| Push notifications | ✅ Implemented | Yes | Not all events fire pushes | P1 |
| Audit log | ✅ Implemented | Yes | None | Done |
| Reports | ✅ Implemented | Yes | Sub-pages verified with date/status filters and row counts | Done |
| Admin seeding mechanism | ✅ Implemented | Yes | `make seed-admin EMAIL=x PASSWORD=y` creates or updates first admin | Done |
| Test coverage (auth) | ✅ Implemented | Yes | None for MVP auth | Done |
| Test coverage (core flows) | ✅ Implemented | Yes | Requirements/quote, assignment, attendance, payroll, finance/payment, and complaints covered; broader worker/client API tests can follow | Done |
| Social auth mobile screens | 🟡 Unclear | No (nice to have) | Google/Apple login not confirmed working end-to-end | P2 |
| Replacement requests UI | ❌ Not found | No | Backend exists, no admin UI page found | P2 |
| Export reports (CSV/PDF) | ❌ Not implemented | No | Not in scope | P2 |

---

## 6. Production Readiness Checklist

| Category | Requirement | Current Status | Gap | Priority | Done? |
|---|---|---|---|---|---|
| **Auth** | Password hashing (bcrypt) | ✅ Implemented | None | — | Yes |
| **Auth** | JWT expiry + rotation | ✅ Implemented | None | — | Yes |
| **Auth** | Access token blocklist | ✅ Implemented | None | — | Yes |
| **Auth** | Rate limiting (auth endpoints) | ✅ Implemented | Not on all endpoints | P1 | Partial |
| **Auth** | Admin user seeding | ✅ Implemented | `make seed-admin` and `python -m scripts.seed_admin` supported | — | Yes |
| **Config** | Environment variable validation at startup | ✅ Implemented | None | — | Yes |
| **Config** | Production secrets management | ❌ Not set up | No AWS Secrets Manager, Key Vault integration | P0 | No |
| **Config** | CORS locked to production origins | ✅ Config enforces | Set BACKEND_CORS_ORIGINS in prod | P0 | Partial |
| **Database** | Alembic migrations | ✅ Implemented | 27 migration files | — | Yes |
| **Database** | Connection pool | ✅ Implemented (pool_pre_ping) | Not tuned for production load | P1 | Partial |
| **Database** | Backups | ✅ Implemented | `scripts.backup_postgres` uploads daily pg_dump backups to S3 with retention; scheduler must be enabled in production | P0 | Partial |
| **Database** | Index coverage | ✅ Most indexed | Not audited for query plans | P1 | Partial |
| **Storage** | S3 in production | ✅ Config ready | Needs real AWS credentials in prod | P0 | Partial |
| **Storage** | Local upload disabled in production | ✅ Enforced in code | None | — | Yes |
| **Payments** | Razorpay webhook signature verification | ✅ Implemented | Needs PAYMENT_WEBHOOK_SECRET in prod | P0 | Partial |
| **SMS** | Real SMS provider (MSG91) in production | ✅ Config enforces | Needs MSG91_AUTH_KEY + TEMPLATE_ID | P0 | Partial |
| **Encryption** | Field encryption in production | ✅ Config enforces | Needs FIELD_ENCRYPTION_KEY in prod | P0 | Partial |
| **Monitoring** | Error monitoring (Sentry or similar) | ✅ Implemented | Backend/admin Sentry SDKs wired; set SENTRY_DSN/NEXT_PUBLIC_SENTRY_DSN in production | P0 | Partial |
| **Monitoring** | Structured logging | 🟡 Partial | Python logging configured, no centralized log aggregation | P1 | Partial |
| **Monitoring** | Health check endpoint | ✅ Implemented | GET /api/v1/health exists | — | Yes |
| **Monitoring** | Uptime monitoring | ❌ Not found | No uptime monitoring configured | P1 | No |
| **Monitoring** | Alerting on critical failures | ❌ Not found | No alerting | P1 | No |
| **DevOps** | Dockerfile (backend) | ✅ Exists | `apps/backend/Dockerfile` | — | Yes |
| **DevOps** | Dockerfile (admin) | ✅ Exists | `apps/admin/Dockerfile` multi-stage Next.js build exists | — | Yes |
| **DevOps** | Docker Compose (full stack) | 🟡 Partial | Only backend services (DB + MinIO) | P1 | Partial |
| **DevOps** | CI/CD pipeline | ✅ Implemented | Backend Ruff + pytest and admin lint/build workflows added | — | Yes |
| **DevOps** | Deployment documentation | ✅ Implemented | `docs/DEPLOYMENT.md` covers production deployment and smoke tests | — | Yes |
| **DevOps** | Redis in production | ✅ Provisioning path documented | `scripts.check_redis` verifies managed Redis connectivity; set and smoke-test real `REDIS_URL` in production | P0 | Partial |
| **DevOps** | HTTPS / TLS | ❌ Not configured | No TLS config found | P0 | No |
| **Testing** | Auth tests | ✅ Implemented | test_auth.py, test_security.py | — | Yes |
| **Testing** | API integration tests (core flows) | ✅ Implemented | Requirements/quote, assignment, attendance, payroll, finance/payment, and complaints covered | — | Yes |
| **Testing** | E2E tests | ❌ Not implemented | None | P1 | No |
| **Testing** | Load testing | ❌ Not implemented | None | P1 | No |
| **Security** | SQL injection protection | ✅ SQLAlchemy ORM | ORM prevents injection | — | Yes |
| **Security** | XSS protection | ✅ Security headers | CSP headers via middleware | — | Yes |
| **Security** | CSRF | ✅ JWT-based (no cookies) | Stateless JWT, no CSRF risk | — | Yes |
| **Security** | Sensitive data logging | ✅ Audit redacts secrets | None | — | Yes |
| **Security** | Rate limiting (all endpoints) | ❌ Only auth | Business endpoints unprotected | P1 | No |
| **Mobile** | App signing for iOS/Android | ❌ Not configured | Not in scope of this audit | P0 (for mobile launch) | No |
| **Mobile** | OTA update strategy | ❌ Not configured | No Expo EAS config found | P1 | No |

---

## 7. Gap Tracker

| Gap ID | Gap / Issue | Current Status | Priority | Score Impact | How to Fix | Acceptance Criteria | Owner | Updated Status |
|---|---|---|---|---|---|---|---|---|
| GAP-001 | No admin user seeding mechanism | ✅ Resolved | P0 | MVP Blocker cleared | Added idempotent `scripts.seed_admin` CLI and `make seed-admin` target | `make seed-admin` or `python -m scripts.seed_admin` creates/updates an admin user without duplicates | Dev | Resolved — TICKET-008 |
| GAP-002 | Complaint detail page in admin may not exist | ✅ Resolved | P0 | MVP Blocker cleared | Verified `/complaints/[id]/page.tsx` and polished detail/resolution UI | Admin can open a complaint, see details, enter resolution notes, and click Resolve | Dev | Resolved — TICKET-009 |
| GAP-003 | Reports sub-pages (/reports/requirements, /reports/assignments, /reports/complaints) not verified | ✅ Resolved | P0 | MVP Blocker cleared | Verified and updated sub-report pages with real backend data, date/status filters, and row counts | Each sub-page shows a filterable table of the relevant entity | Dev | Resolved — TICKET-010 |
| GAP-004 | Zero test coverage for requirements flow | ✅ Resolved | P0 | Testing gap partially cleared | Added `tests/test_requirements.py` with integration coverage for create/list/detail, admin review, quote creation, client approval/rejection, ownership, role checks, duplicate quote, and invalid transitions | `pytest tests/test_requirements.py -v` passes | Dev | Resolved — TICKET-011 |
| GAP-005 | Zero test coverage for assignment flow | ✅ Resolved | P0 | Testing gap partially cleared | Added `tests/test_assignments.py` with integration coverage for admin create/list/filter/read, all supported admin status updates, worker accept/decline, ownership, role checks, payment gate, availability gate, and duplicate active assignment rejection | `pytest tests/test_assignments.py -v` passes | Dev | Resolved — TICKET-012 |
| GAP-006 | Zero test coverage for attendance flow | ✅ Resolved | P0 | Testing gap partially cleared | Added `tests/test_attendance.py` with integration coverage for GPS check-in/check-out, geofence failure, missing GPS, duplicate check-in, no-open-checkout, admin list/correction, locked payroll block, ownership, and role checks | `pytest tests/test_attendance.py -v` passes | Dev | Resolved — TICKET-012 |
| GAP-007 | Zero test coverage for payroll | ✅ Resolved | P0 | Testing gap partially cleared | Added `tests/test_payroll.py` with integration coverage for payroll run generation from attendance, zero-attendance generation, duplicate generation rejection, deductions, net recalculation, all supported statuses, paid transition, locked deduction blocking, locked status-change blocking, locked generation blocking, and role checks | `pytest tests/test_payroll.py -v` passes | Dev | Resolved — TICKET-013 |
| GAP-008 | Zero test coverage for finance/payment | ✅ Resolved | P0 | Testing: 9/10 | Write tests for Razorpay order creation, webhook handling, manual payment recording, status update | Tests cover all payment status flows | Dev | Resolved 2026-05-20 |
| GAP-009 | Zero test coverage for complaints | ✅ Resolved | P1 | Testing: 9/10 | Write tests for complaint creation, admin resolution, SLA policy update | All complaint status flows tested | Dev | Resolved 2026-05-20 |
| GAP-010 | No CI/CD pipeline | ✅ Resolved | P0 | DevOps gap partially cleared | Added GitHub Actions backend workflow running `ruff check app tests scripts` and `pytest -v`, plus admin workflow running `npm run lint` and `npm run build` on PRs and main/develop pushes | PRs run backend tests/lint and admin build checks | Dev/DevOps | Resolved — TICKET-014 |
| GAP-011 | No error monitoring (Sentry) | ✅ Resolved | P0 | Production gap partially cleared | Installed Sentry SDKs in FastAPI and Next.js; configured env-driven DSNs, request scrubbing, FastAPI exception capture, and App Router/global error capture | Unhandled backend/admin exceptions are sent to Sentry when DSNs are configured | Dev/DevOps | Resolved — TICKET-015 |
| GAP-012 | No production deployment guide / runbook | ✅ Resolved | P0 | DevOps gap partially cleared | Added `docs/DEPLOYMENT.md` covering env vars, managed PostgreSQL/Redis/S3, migrations, first admin seed, Docker Compose, systemd, DNS/TLS, smoke tests, rollback, and backups | Runbook allows a new engineer to deploy from scratch | Dev/DevOps | Resolved — TICKET-016 |
| GAP-013 | No database backup strategy | ✅ Resolved | P0 | Production gap partially cleared | Added `scripts.backup_postgres` for pg_dump-to-S3 backups, backup env vars, Docker pg_dump support, retention cleanup, scheduler examples, restore instructions, and tests | Daily backups can be stored in S3 with retention policy once scheduled in production | DevOps | Resolved — TICKET-019 |
| GAP-014 | Redis not provisioned for production | ✅ Resolved | P0 | Production gap partially cleared | Added managed Redis provisioning guidance for ElastiCache/Redis Cloud, production `REDIS_URL` examples, backend `scripts.check_redis`, Makefile target, smoke-test gate, and unit tests | Redis can be provisioned and verified from the backend runtime before go-live | DevOps | Resolved — TICKET-020 |
| GAP-015 | HTTPS/TLS not configured | ❌ Open | P0 | Production: 3/10 | Set up nginx reverse proxy with Let's Encrypt or use a load balancer with TLS termination | All traffic served over HTTPS | DevOps | Open |
| GAP-016 | Admin Dockerfile missing | ✅ Resolved | P1 | DevOps gap partially cleared | Verified existing `apps/admin/Dockerfile` multi-stage Next.js standalone build | Admin app builds and runs in a container | Dev | Resolved — verified existing |
| GAP-017 | Rate limiting only on auth endpoints | ❌ Open | P1 | Security: partial | Apply rate limiting to admin bulk operations and public-facing mobile endpoints | Critical endpoints have rate limits | Dev | Open |
| GAP-018 | Social auth (Google/Apple) end-to-end not verified | 🟡 Open | P1 | MVP Partial | Manually test Google and Apple sign-in on mobile; fix any integration issues | Worker/client can log in with Google and Apple | Dev | Open |
| GAP-019 | Push notifications not fired for all key events | 🟡 Open | P1 | Mobile Partial | Audit all key events (quote sent, payment confirmed, assignment created, complaint resolved) and ensure push is called | Workers and clients receive push for all relevant events | Dev | Open |
| GAP-020 | No Expo EAS / mobile release configuration | ❌ Open | P1 | Mobile: 7/10 | Set up EAS Build for iOS and Android; configure app signing | Mobile app can be built and distributed | Dev/DevOps | Open |
| GAP-021 | Reports have no data export (CSV/PDF) | ✅ Resolved | P2 | MVP: 9/10 | Implement CSV export on backend for requirements, assignments, payroll | Admin can download CSV from each report | Dev | Resolved 2026-05-20 |
| GAP-022 | Admin replacements has no UI page | ✅ Resolved | P2 | MVP: 9/10 | Build /admin-users/ or a replacements list page | Admin can view and manage worker replacement requests | Dev | Resolved 2026-05-20 |
| GAP-023 | Worker Earnings screen content not verified | ✅ Verified | P1 | Mobile: 9/10 | Read and verify EarningsScreen.tsx connects to payroll API | Worker can see their payroll history and net earnings | Dev | Verified 2026-05-20 |
| GAP-024 | No structured secrets management | ❌ Open | P1 | Production: 3/10 | Use AWS Secrets Manager or similar; do not rely solely on .env in production | Secrets rotatable without code changes | DevOps | Open |
| GAP-025 | Scheduler runs in-process (no celery/background worker) | ✅ Resolved | P2 | Production: 3/10 | Added auto-restart on unexpected exit, CRITICAL log on task death, `last_run_at`/`last_error` state, and scheduler liveness check in `GET /api/v1/ready` (503 if task not alive) | Background tasks do not fail silently | Dev | Resolved 2026-05-20 |
| GAP-026 | No connection pool tuning for production | 🟡 Open | P1 | Database: 7/10 | Set `pool_size`, `max_overflow`, `pool_timeout` in SQLAlchemy engine config | Database handles concurrent load without connection errors | Dev | Open |
| GAP-027 | Admin reports: sub-report pages may be missing | ✅ Resolved | P0 | MVP Blocker cleared | Verified `/reports/requirements`, `/reports/assignments`, and `/reports/complaints` exist and build successfully | Each report page shows a working data table | Dev | Resolved — TICKET-010 |
| GAP-028 | No uptime monitoring or alerting | ❌ Open | P1 | Production: 3/10 | Set up Pingdom/Better Uptime on the health endpoint; alert on downtime | On-call team is notified within 5 minutes of downtime | DevOps | Open |
| GAP-029 | Refresh token auto-rotation not verified in admin | 🟡 Open | P1 | Auth: 8/10 | Read and verify api-client.ts has 401 interceptor that calls /auth/refresh | Admin sessions do not expire mid-use | Dev | Open |
| GAP-030 | No test for worker onboarding flow | ✅ Resolved | P1 | Testing: 2/10 | Write integration tests for the onboarding step machine (consent → identity → profile → approved) | All onboarding steps tested against the in-memory DB | Dev | Resolved 2026-05-20 |

---

## 8. Resolved Gap Tracker

| Gap ID | Resolved Gap | Fix Summary | Evidence / File Path | Date Fixed | Score Updated |
|---|---|---|---|---|---|
| RESOLVED-001 | Admin attendance page (TICKET-007) | Admin attendance page with verify/correct built | `apps/admin/src/app/(dashboard)/attendance/page.tsx` | Before 2026-05-20 | Yes |
| RESOLVED-002 | Admin login tests (TICKET-002) | test_auth.py covers admin login, wrong password, inactive admin, schema validation | `apps/backend/tests/test_auth.py` | Before 2026-05-20 | Yes |
| RESOLVED-003 | Payment gate bypass checkbox (TICKET-004) | Finance page shows confirm/reject only for advance payments (`is_advance` flag) | `apps/admin/src/app/(dashboard)/finance/page.tsx` | Before 2026-05-20 | Yes |
| RESOLVED-004 | Auth store consolidation (TICKET-005) | Single `useAuthStore` with `isHydrated`, `setAuth`, `hydrateAuth`, `clearAuth` | `apps/admin/src/store/auth-store.ts` | Before 2026-05-20 | Yes |
| RESOLVED-005 | Worker detail page (TICKET-007) | WorkerReviewPanel in workers page shows full profile, documents, approve/reject actions | `apps/admin/src/app/(dashboard)/workers/page.tsx` | Before 2026-05-20 | Yes |
| RESOLVED-006 | Finance advance-only confirmation | Finance page shows confirm/reject actions only when `is_advance === true && payment_status === "pending"` | `apps/admin/src/app/(dashboard)/finance/page.tsx` | Before 2026-05-20 | Yes |
| RESOLVED-007 | Access token blocklist on logout | Logout endpoint revokes both refresh token and blocklists access token JTI | `apps/backend/app/api/auth.py`, `apps/backend/app/models/revoked_access_token.py` | Before 2026-05-20 | Yes |
| RESOLVED-008 | Geofence validation on check-in | Haversine calculation in geofence.py, used in worker attendance check-in | `apps/backend/app/utils/geofence.py`, `apps/backend/app/api/worker_attendance.py` | Before 2026-05-20 | Yes |
| RESOLVED-009 | Payroll lock enforcement | Locked payroll runs block attendance correction, deduction, and status change | `apps/backend/app/api/admin_payroll.py`, `apps/backend/app/api/admin_attendance.py` | Before 2026-05-20 | Yes |
| RESOLVED-010 | Push token deactivation on logout | pushTokenService.deactivate() called on worker mobile logout | `apps/mobile-ui-lab/src/apps/worker/screens/HomeScreen.tsx` | Before 2026-05-20 | Yes |
| RESOLVED-011 | Admin user seeding mechanism (TICKET-008) | Idempotent admin seed CLI and Makefile target added; duplicate creation prevented; README documented | `apps/backend/scripts/seed_admin.py`, `apps/backend/Makefile`, `apps/backend/README.md`, `apps/backend/tests/test_seed_admin.py` | 2026-05-20 | Yes |
| RESOLVED-012 | Admin complaint detail page (TICKET-009) | Complaint detail route verified; detail screen now shows context, resolution notes, and direct Mark In Review / Resolve / Reject Close actions using shadcn UI primitives | `apps/admin/src/app/(dashboard)/complaints/[id]/page.tsx`, `apps/admin/src/features/complaints/complaint-detail-view.tsx`, `apps/admin/src/features/complaints/update-complaint-status-form.tsx` | 2026-05-20 | Yes |
| RESOLVED-013 | Admin report sub-pages (TICKET-010) | Requirements, assignments, and complaints report pages verified and updated with real backend data, date/status filters, row counts, loading/error/empty states | `apps/admin/src/app/(dashboard)/reports/requirements/page.tsx`, `apps/admin/src/app/(dashboard)/reports/assignments/page.tsx`, `apps/admin/src/app/(dashboard)/reports/complaints/page.tsx`, `apps/admin/src/features/reports/report-filters.tsx`, `apps/backend/app/api/admin_reports.py` | 2026-05-20 | Yes |
| RESOLVED-014 | Requirements and quote flow tests (TICKET-011) | Added backend integration tests for client requirement creation/list/detail, admin review, quote creation, quote approval/rejection, ownership checks, role checks, duplicate quote handling, and invalid transitions | `apps/backend/tests/test_requirements.py`, `apps/backend/app/api/admin_requirements.py` | 2026-05-20 | Yes |
| RESOLVED-015 | Assignment flow tests (TICKET-012 partial) | Added backend integration tests for admin assignment create/list/filter/read/status updates, worker accept/decline, ownership checks, role checks, payment and availability gates, and duplicate active assignment rejection; fixed decline status flush so requirements reopen when the last open assignment is declined | `apps/backend/tests/test_assignments.py`, `apps/backend/app/api/admin_assignments.py`, `apps/backend/app/api/worker_assignments.py` | 2026-05-20 | Yes |
| RESOLVED-016 | Attendance flow tests (TICKET-012) | Added backend integration tests for worker GPS check-in/check-out, geofence rejection, missing GPS, duplicate check-in, no-open-checkout, admin list/correction, locked payroll correction blocking, ownership checks, and role checks | `apps/backend/tests/test_attendance.py`, `apps/backend/app/api/worker_attendance.py`, `apps/backend/app/api/admin_attendance.py` | 2026-05-20 | Yes |
| RESOLVED-017 | Payroll flow tests (TICKET-013 partial) | Added backend integration tests for payroll generation from active assignments and attendance, zero-attendance item creation, duplicate generation rejection, deductions and net recalculation, all supported run statuses, paid transition, locked deduction/status/generation blocking, and role checks | `apps/backend/tests/test_payroll.py` | 2026-05-20 | Yes |
| RESOLVED-018 | Finance/payment flow tests (TICKET-013) | Added backend integration tests for Razorpay order creation, webhook signature verification, duplicate webhook handling, manual payment recording, payment status updates, requirement auto-transition, worker payouts, payout status updates, and finance list endpoints | `apps/backend/tests/test_finance_payments.py` | 2026-05-20 | Yes |
| RESOLVED-019 | Complaint and SLA flow tests | Added backend integration tests for complaint creation, replacement requests, admin listing/detail/status transitions, SLA policy management, and SLA breach detection | `apps/backend/tests/test_complaints.py` | 2026-05-20 | Yes |
| RESOLVED-020 | GitHub Actions CI (TICKET-014) | Added separate backend and admin CI workflows. Backend runs Ruff and pytest; admin runs ESLint and Next.js build on pull requests and main/develop pushes. | `.github/workflows/backend.yml`, `.github/workflows/admin.yml` | 2026-05-20 | Yes |
| RESOLVED-021 | Sentry error monitoring (TICKET-015) | Wired Sentry for FastAPI and Next.js with env-driven DSNs, release/environment/sample-rate settings, sensitive request data scrubbing, generic backend exception capture, App Router request instrumentation, and admin global error capture. | `apps/backend/app/core/monitoring.py`, `apps/backend/app/core/exceptions.py`, `apps/admin/src/instrumentation.ts`, `apps/admin/src/instrumentation-client.ts`, `apps/admin/src/app/global-error.tsx` | 2026-05-20 | Yes |
| RESOLVED-022 | Production deployment runbook (TICKET-016) | Added deployment runbook covering production architecture, environment variables, PostgreSQL, Redis, S3, Razorpay, MSG91, Docker image builds, migrations, first admin seed, Docker Compose, systemd, DNS/TLS, smoke tests, rollback, backups, and go-live gates. | `docs/DEPLOYMENT.md`, `apps/backend/migrations/env.py` | 2026-05-20 | Yes |
| RESOLVED-023 | Admin Dockerfile verification | Verified the existing multi-stage Next.js standalone Dockerfile for the admin dashboard and corrected the readiness report. | `apps/admin/Dockerfile` | 2026-05-20 | Yes |
| RESOLVED-024 | PostgreSQL backup strategy (TICKET-019) | Added a `pg_dump` to S3 backup command with retention cleanup, backup environment variables, backend Docker support for `pg_dump`, deployment runbook scheduling/restore instructions, and unit tests for backup key/retention helpers. | `apps/backend/scripts/backup_postgres.py`, `apps/backend/tests/test_backup_postgres.py`, `apps/backend/Dockerfile`, `docs/DEPLOYMENT.md` | 2026-05-20 | Yes |
| RESOLVED-025 | Redis production readiness (TICKET-020) | Added managed Redis provisioning guidance, safe `REDIS_URL` examples, runtime Redis check command, Makefile target, deployment smoke-test/go-live gates, and unit tests for Redis URL handling. | `apps/backend/scripts/check_redis.py`, `apps/backend/tests/test_check_redis.py`, `apps/backend/Makefile`, `apps/backend/.env.example`, `docs/DEPLOYMENT.md` | 2026-05-20 | Yes |

---

## 9. Score Calculation Logic

### Weighting Model

| Area | Weight | What Drives the Score |
|---|---|---|
| Backend Readiness | 25% | API completeness, data models, security, error handling |
| Frontend/Admin Readiness | 20% | Page completeness, service integration, UX |
| Mobile App Readiness | 20% | Screen completeness, navigation, native integrations |
| Auth & Security Readiness | 15% | Token strategy, encryption, rate limiting |
| Database Readiness | 10% | Migrations, schema design, indexes |
| Testing Readiness | 5% | Coverage breadth, CI integration |
| DevOps/Deployment Readiness | 5% | Docker, CI/CD, runbook |

### Score Breakdown

**Backend Readiness: 8/10**
- All major API modules present (+3)
- Security, encryption, rate limiting on auth (+2)
- Webhook signature verification (+1)
- Scheduler for cleanup (+0.5)
- Sentry error monitoring wired (+1)
- Missing: no rate limiting on business endpoints (-0.5), social auth unverified (-0.5), no E2E tests (-0.5)

**Frontend/Admin Readiness: 7/10**
- 13 dashboard pages/sections built (+4)
- Finance page with full payment and payroll queue (+2)
- Audit log, SLA policy, settings (+1)
- Missing: no E2E tests (-1)

**Mobile App Readiness: 7/10**
- Full worker onboarding (8 screens) (+2)
- GPS + biometric check-in/out working (+2)
- Client flow screens (home, create, request detail, payment, complaints) (+2)
- Attendance history calendar (+1)
- Missing: earnings screen detail unverified (-0.5), social auth unverified (-0.5), no EAS config (-1)

**Auth & Security Readiness: 8/10**
- bcrypt, JWT, refresh rotation, token blocklist (+3)
- Field-level encryption (+1)
- Rate limiting on auth (+1)
- Security headers (+0.5)
- Generic error messages (+0.5)
- Missing: rate limiting on non-auth endpoints (-1), social auth unverified (-0.5), token refresh in admin not verified (-0.5)

**Database Readiness: 8/10**
- 27 Alembic migrations (+3)
- Well-structured models with FKs, indexes, constraints (+2)
- Field-level encryption for sensitive data (+1)
- S3 backup command and restore/scheduling runbook exist (+1)
- Missing: production backup job not yet enabled, pool not tuned (-0.5), no query plan audit (-0.5)

**Testing Readiness: 7/10**
- test_auth.py covers OTP flow and admin login comprehensively (+1)
- test_security.py covers pure functions (+0.5)
- conftest.py well-structured with SQLite in-memory (+0.5)
- Requirements, assignment, attendance, payroll, finance/payment, and complaints integration tests added (+4)
- Missing: broad worker/client API coverage, E2E suite, and load tests (-2)

**DevOps/Deployment Readiness: 7/10**
- Dockerfile for backend exists (+1)
- Dockerfile for admin exists (+1)
- docker-compose.yml for dev infrastructure (+0.5)
- serve.sh and serve.ps1 for local dev (+0.5)
- GitHub Actions backend/admin CI exists (+1)
- Sentry SDK wiring exists for backend/admin (+1)
- Production deployment runbook exists (+1)
- Database backup automation command exists (+1)
- Redis production provisioning and verification command exists (+1)
- Missing: no deployment automation, no provisioned TLS, no uptime alerting/log aggregation, no production Redis smoke test yet (-3)

**MVP Readiness: 7/10** — Core business logic, major backend integration tests, CI, Sentry wiring, and a production deployment runbook are implemented, but E2E automation and production smoke testing are still missing.

**Production Readiness: 6/10** — Business logic, Sentry wiring, CI, deployment documentation, a database backup command, and Redis provisioning verification are there, but production infrastructure is still missing: scheduled backup enablement, TLS configuration, uptime alerting/log aggregation, production Redis smoke testing, and rate limiting on remaining business endpoints.

---

## 10. Priority Action Plan

### P0 — Must Fix Before Demo / MVP

| Task | Why it matters | Files likely involved | Acceptance Criteria |
|---|---|---|---|
| Add E2E test suite | Core flows are covered at API level but not through real user journeys | Playwright/Appium or equivalent | Login → requirement → quote → payment → assignment → attendance → payroll smoke path runs automatically |

### P1 — Must Fix Before Production

| Task | Why it matters | Files likely involved | Acceptance Criteria |
|---|---|---|---|
| Run production Redis smoke test | Rate limiting is Redis-dependent and fails open if Redis is unavailable | `apps/backend/scripts/check_redis.py`, production secret manager | `python -m scripts.check_redis` and `/api/v1/ready` pass with production `REDIS_URL` |
| Configure HTTPS/TLS | All traffic is plaintext without it | nginx config or load balancer TLS config | All HTTP redirected to HTTPS |
| Enable database backup schedule in production | Backup command exists but must be scheduled against production infra | `scripts.backup_postgres`, cron/systemd timer from `docs/DEPLOYMENT.md` | Daily automated PostgreSQL backups appear in S3 and restore drill passes |
| Tune SQLAlchemy connection pool | Concurrent load will exhaust default pool | `apps/backend/app/db/session.py` | Under load test, no connection pool exhaustion |
| Verify and fix refresh token interceptor in admin | Session expires mid-use is bad UX | `apps/admin/src/services/api-client.ts` | Admin stays logged in through token expiry |
| Verify worker Earnings screen content | Workers need to see their payroll data | `apps/mobile-ui-lab/src/apps/worker/screens/EarningsScreen.tsx` | Earnings screen shows payroll history with net amounts |
| Apply rate limiting to business endpoints | DoS risk on unprotected endpoints | `apps/backend/app/api/admin_requirements.py`, `client_requirements.py`, etc. | Rate limits on all public-facing and sensitive endpoints |
| Write tests for complaints and SLA | Untested money flow | `apps/backend/tests/test_complaints.py`, `test_sla.py` | Tests cover complaint lifecycle, SLA policy CRUD |
| Verify social auth end-to-end | If enabled, must work | `apps/mobile-ui-lab/src/apps/client/screens/auth/`, `apps/backend/app/api/auth_social.py` | Google and Apple sign-in work on device |
| Ensure push notifications fire for all key events | Workers miss important alerts | `apps/backend/app/api/admin_assignments.py`, `admin_requirements.py`, `client_requirements.py` | Push fires on assignment creation, quote sent, payment confirmed, complaint resolved |

### P2 — Improve After MVP

| Task | Why it matters | Files likely involved | Acceptance Criteria |
|---|---|---|---|
| Export reports to CSV | Useful for clients and internal | `apps/backend/app/api/admin_reports.py`, admin reports pages | CSV download button works on each report page |
| Build admin replacements UI page | Backend is implemented, UI is missing | `apps/admin/src/app/(dashboard)/replacements/page.tsx` (new) | Admin can view, approve, and reject replacement requests |
| Implement SLA auto-escalation | Passive SLA tracking is incomplete | `apps/backend/app/core/scheduler.py` | Overdue complaints are flagged/escalated automatically |
| Move background tasks to Celery | In-process scheduler is fragile at scale | New `celery_app.py`, Redis as broker | Background tasks survive server restarts |
| Set up Expo EAS for mobile releases | No mobile release path | `apps/mobile-ui-lab/eas.json` | iOS and Android builds produced via EAS |
| Uptime monitoring and alerting | Silent failures are production risk | Infra task (Pingdom, BetterUptime) | On-call team alerted within 5 minutes of downtime |
| Load testing | Unknown production capacity | Locust or k6 scripts | System handles 100 concurrent users without errors |
| Structured log aggregation | Scattered logs are hard to diagnose | CloudWatch or Datadog integration | All logs searchable in a central dashboard |

---

## 11. Developer Tickets

### TICKET-008: Create Admin User Seeding Script
**Priority:** P0
**Related Gap:** GAP-001
**Status:** Resolved 2026-05-20
**Description:** There is no mechanism to create the first admin user. A new deployment has no way to log in to the admin panel. A seed script or Makefile target is required.
**Files likely involved:**
- `apps/backend/Makefile`
- `apps/backend/scripts/seed_admin.py`
**Acceptance Criteria:**
- `make seed-admin EMAIL=admin@example.com PASSWORD=SomePass123!` creates an admin user with bcrypt-hashed password
- Script is idempotent — running it twice does not create duplicate users
- Script is documented in the README
**Testing Required:** `pytest tests/test_seed_admin.py -v` passed

---

### TICKET-009: Verify and Build Complaint Detail Page
**Priority:** P0
**Related Gap:** GAP-002
**Status:** Resolved 2026-05-20
**Description:** The admin complaints list links to `/complaints/${item.id}` but the existence of that route was not confirmed during audit. If missing, the resolve action is broken.
**Files likely involved:**
- `apps/admin/src/app/(dashboard)/complaints/[id]/page.tsx` (verify or create)
- `apps/admin/src/services/complaints.service.ts`
- `apps/backend/app/api/admin_complaints.py`
**Acceptance Criteria:**
- Navigating to `/complaints/{id}` shows the complaint detail: type, severity, description, raised by, assignment context
- Admin can enter resolution notes and click Resolve
- On resolve, status changes to "resolved" and is reflected immediately
- Toast or success message confirms the action
**Testing Required:** `npm run lint` passed with unrelated warnings; `npm run build` passed and includes dynamic route `/complaints/[id]`

---

### TICKET-010: Verify Reports Sub-Pages
**Priority:** P0
**Related Gap:** GAP-003, GAP-027
**Status:** Resolved 2026-05-20
**Description:** The reports index page shows links to `/reports/requirements`, `/reports/assignments`, and `/reports/complaints`, but these sub-pages were not confirmed to exist in the codebase. If they are missing, the reports section is non-functional.
**Files likely involved:**
- `apps/admin/src/app/(dashboard)/reports/requirements/page.tsx` (verify/create)
- `apps/admin/src/app/(dashboard)/reports/assignments/page.tsx` (verify/create)
- `apps/admin/src/app/(dashboard)/reports/complaints/page.tsx` (verify/create)
- `apps/admin/src/services/reports.service.ts`
- `apps/backend/app/api/admin_reports.py`
**Acceptance Criteria:**
- Each sub-page renders a table with real data
- Basic filtering (by date range, status) works
- Row count is shown at the bottom
- Empty state handled gracefully
**Testing Required:** `ruff check app/api/admin_reports.py`, `npm run lint`, and `npm run build` passed

---

### TICKET-011: Write Integration Tests — Requirements and Quote Flow
**Priority:** P0
**Related Gap:** GAP-004
**Status:** Resolved 2026-05-20
**Description:** The core business flow (requirement creation → review → quote → approval) has zero test coverage. A regression in this flow would not be caught.
**Files likely involved:**
- `apps/backend/tests/test_requirements.py`
- `apps/backend/app/api/admin_requirements.py`
**Acceptance Criteria:**
- Tests cover: client creates requirement, admin marks under review, admin creates quote, client approves quote
- Tests cover error paths: duplicate quote, wrong status transitions, mismatched IDs
- All tests run with `pytest` and pass with SQLite in-memory
**Testing Required:** `pytest tests/test_requirements.py -v` passed; `ruff check tests/test_requirements.py app/api/admin_requirements.py` passed

---

### TICKET-012: Write Integration Tests — Assignment and Attendance
**Priority:** P0
**Related Gap:** GAP-005, GAP-006
**Status:** Resolved 2026-05-20
**Description:** The check-in/out flow is a core product differentiator and has zero coverage.
**Files likely involved:**
- `apps/backend/tests/test_assignments.py`
- `apps/backend/tests/test_attendance.py`
- `apps/backend/app/api/admin_assignments.py`
- `apps/backend/app/api/worker_assignments.py`
- `apps/backend/app/api/worker_attendance.py`
- `apps/backend/app/api/admin_attendance.py`
**Acceptance Criteria:**
- Tests cover: admin creates assignment, worker accepts, worker declines, worker check-in with GPS, geofence rejection, check-out, admin correction, correction blocked by locked payroll
- Tests use the existing SQLite in-memory conftest setup
**Testing Required:** `pytest tests/test_assignments.py -v` passed; `pytest tests/test_attendance.py -v` passed; `ruff check tests/test_assignments.py app/api/admin_assignments.py app/api/worker_assignments.py` passed; `ruff check tests/test_attendance.py app/api/worker_attendance.py app/api/admin_attendance.py` passed.

---

### TICKET-013: Write Integration Tests — Payroll and Payment
**Priority:** P0
**Related Gap:** GAP-007, GAP-008
**Status:** Fully resolved 2026-05-20 — payroll coverage complete (`tests/test_payroll.py`); payment/finance coverage complete (`tests/test_finance_payments.py`, 41 tests)
**Description:** Payroll and payment logic are financially critical and have zero test coverage.
**Files likely involved:**
- `apps/backend/tests/test_payroll.py`
- `apps/backend/tests/test_payments.py` (new)
**Acceptance Criteria:**
- Tests cover: payroll run creation, item generation, deduction addition, status transitions, locked run blocking edits, manual payment recording, status updates, requirement auto-transition on paid advance
- Tests cover: Razorpay webhook signature verification (valid + invalid)
**Testing Required:** Payroll portion: `pytest tests/test_payroll.py -v` passed. Payment/finance portion: `pytest tests/test_finance_payments.py -v` — 41 passed.

---

### TICKET-014: Set Up GitHub Actions CI/CD
**Priority:** P0
**Related Gap:** GAP-010
**Status:** Resolved 2026-05-20
**Description:** There was no CI/CD pipeline. Every merge to main was unvalidated. A minimal CI now runs backend tests/lint and admin lint/build on every PR.
**Files likely involved:**
- `.github/workflows/backend.yml`
- `.github/workflows/admin.yml`
**Acceptance Criteria:**
- On every PR, backend tests run with `pytest` against SQLite in-memory (no real DB needed)
- `ruff` lint check runs and fails on violations
- Next.js admin `next build` check runs
- All checks must pass before merge
- Redis is mocked or skipped in CI (rate limiter gracefully fails open)
**Testing Required:** Local workflow-equivalent checks passed: `python -m ruff check app tests scripts`, `python -m pytest -v` (240 passed), `npm run lint`, and `npm run build`

---

### TICKET-015: Wire Sentry Error Monitoring
**Priority:** P1
**Related Gap:** GAP-011
**Status:** Resolved 2026-05-20
**Description:** Production errors were invisible. Sentry is now wired in FastAPI and Next.js with DSNs and sampling configured through environment variables.
**Files likely involved:**
- `apps/backend/app/main.py`
- `apps/backend/app/core/monitoring.py`
- `apps/backend/app/core/exceptions.py`
- `apps/backend/requirements.txt`
- `apps/admin/src/instrumentation.ts`
- `apps/admin/src/instrumentation-client.ts`
- `apps/admin/src/app/global-error.tsx`
- `apps/admin/package.json`
**Acceptance Criteria:**
- Unhandled FastAPI exceptions appear in Sentry with full traceback and request context
- Unhandled React errors appear in Sentry
- No sensitive data (tokens, passwords) is captured in breadcrumbs
- SENTRY_DSN is read from environment variable, not hardcoded
**Testing Required:** Local code/build checks passed: `python -m ruff check app tests scripts`, `python -m pytest -v` (240 passed), `npm run lint`, and `npm run build`. Production DSN smoke test remains required after Sentry project credentials are configured.

---

### TICKET-016: Production Deployment Runbook
**Priority:** P1
**Related Gap:** GAP-012
**Status:** Resolved 2026-05-20
**Description:** A production deployment runbook now documents how to deploy the system without undocumented tribal knowledge.
**Files likely involved:**
- `docs/DEPLOYMENT.md`
- `apps/backend/migrations/env.py`
**Acceptance Criteria:**
- Runbook covers: prerequisites, environment variable setup, database provisioning + migration, Redis provisioning, S3 bucket setup, backend Docker deployment, admin deployment, nginx TLS configuration, first admin user creation, smoke test checklist
- A junior engineer can follow it without help
**Testing Required:** Documentation sanity check passed; `apps/backend/migrations/env.py` now honors `DATABASE_URL` for production migrations. A dry run by a team member who was not involved in writing it is still recommended before go-live.

---

### TICKET-017: Verify Worker Earnings Screen
**Priority:** P1
**Related Gap:** GAP-023
**Description:** The worker EarningsScreen.tsx exists in the navigation but its content was not audited. Workers need to see their payroll history and net earnings.
**Files likely involved:**
- `apps/mobile-ui-lab/src/apps/worker/screens/EarningsScreen.tsx`
- `apps/mobile-ui-lab/src/shared/services/worker-payroll.service.ts`
- `apps/backend/app/api/worker_payroll.py`
**Acceptance Criteria:**
- EarningsScreen shows a list of payroll items with: period, attendance days, gross amount, deductions, net amount
- Data is loaded from GET /worker/payroll/items
- Empty state shown if no payroll history
- Loading and error states handled
**Testing Required:** Manual device test with seeded payroll data

---

### TICKET-018: Rate Limiting on Business Endpoints
**Priority:** P1
**Related Gap:** GAP-017
**Description:** Rate limiting is only applied to auth endpoints. Business endpoints (requirement creation, complaint submission, file upload) are unprotected from abuse.
**Files likely involved:**
- `apps/backend/app/api/client_requirements.py`
- `apps/backend/app/api/client_complaints.py`
- `apps/backend/app/api/worker_onboarding.py`
- `apps/backend/app/core/rate_limit.py`
**Acceptance Criteria:**
- Clients are rate-limited to 10 requirement creations per hour
- Clients are rate-limited to 5 complaint submissions per hour
- Worker document upload limited to 10 per hour
- Rate limit responses return 429 with a clear message
**Testing Required:** Write a test that hits the limit and verifies 429 response

---

### TICKET-019: PostgreSQL Backup Strategy
**Priority:** P0
**Related Gap:** GAP-013
**Status:** Resolved 2026-05-20
**Description:** The project had no automated database backup strategy. A `pg_dump` to S3 backup command now exists with retention cleanup and production scheduling/restore instructions.
**Files likely involved:**
- `apps/backend/scripts/backup_postgres.py`
- `apps/backend/tests/test_backup_postgres.py`
- `apps/backend/Dockerfile`
- `apps/backend/.env.example`
- `docs/DEPLOYMENT.md`
**Acceptance Criteria:**
- Backup command creates a PostgreSQL custom-format dump
- Backup command uploads the dump to S3-compatible storage
- Backup command deletes objects older than the configured retention window
- Production runbook shows cron/systemd scheduling and restore drill steps
**Testing Required:** `pytest tests/test_backup_postgres.py -v` passed; `ruff check scripts/backup_postgres.py tests/test_backup_postgres.py` passed. Production scheduling and restore drill remain required after infrastructure is provisioned.

---

### TICKET-020: Redis Production Readiness
**Priority:** P0
**Related Gap:** GAP-014
**Status:** Resolved 2026-05-20
**Description:** Production Redis provisioning is now documented and verifiable. The backend has a runtime Redis check command that confirms `REDIS_URL` can connect, ping, and perform a temporary TTL write/read/delete from the same environment that runs the API.
**Files likely involved:**
- `apps/backend/scripts/check_redis.py`
- `apps/backend/tests/test_check_redis.py`
- `apps/backend/Makefile`
- `apps/backend/.env.example`
- `docs/DEPLOYMENT.md`
**Acceptance Criteria:**
- Runbook explains managed Redis setup for ElastiCache and Redis Cloud
- Production `REDIS_URL` examples use `rediss://` when TLS is enabled
- `python -m scripts.check_redis` verifies ping plus write/read/delete without logging credentials
- Go-live gate requires the Redis check and `/api/v1/ready` to pass
**Testing Required:** `pytest tests/test_check_redis.py -v` passed; `ruff check scripts/check_redis.py tests/test_check_redis.py` passed. Actual production Redis provisioning and smoke test remain required in the target infrastructure.

---

## 12. Test Coverage Plan

| Area | Current Test Coverage | Missing Tests | Priority |
|---|---|---|---|
| Auth — OTP flow | ✅ Comprehensive (test_auth.py) | None needed | Done |
| Auth — Admin login | ✅ Comprehensive (test_auth.py) | None needed | Done |
| Auth — Token refresh + rotation | ✅ Comprehensive (test_auth.py) | None needed | Done |
| Auth — Logout + blocklist | ✅ Comprehensive (test_auth.py) | None needed | Done |
| Security functions | ✅ Comprehensive (test_security.py) | None needed | Done |
| Requirements — Create, list, detail | ✅ Covered (`test_requirements.py`) | None for MVP flow; broader validation fuzzing can come later | Done |
| Requirements — Admin review, quote, approval | ✅ Covered (`test_requirements.py`) | None for MVP flow; quote notification tests can come later | Done |
| Assignments — CRUD, worker decisions | ✅ Covered (`test_assignments.py`) | None for MVP assignment flow; replacement-specific tests can come later | Done |
| Attendance — Check-in, check-out, geofence | ✅ Covered (`test_attendance.py`) | None for MVP attendance flow; time-window/late policy tests can come later | Done |
| Attendance — Locked payroll block | ✅ Covered (`test_attendance.py`) | None for MVP attendance lock behavior | Done |
| Payroll — Run generation, deductions | ✅ Covered (`test_payroll.py`) | None for MVP payroll generation and deduction flow | Done |
| Payroll — Status transitions | ✅ Covered (`test_payroll.py`) | None for MVP run status and lock behavior | Done |
| Payments — Razorpay order + webhook | ✅ Covered (`test_finance_payments.py`) | None for MVP payment flow | Done |
| Payments — Manual recording | ✅ Covered (`test_finance_payments.py`) | None for MVP manual payment flow | Done |
| Complaints — Create, resolve, SLA | ✅ Covered (`test_complaints.py`) | None for MVP complaint/SLA flow | Done |
| Worker onboarding — Full step machine | ❌ None | test_onboarding.py: consent → identity → profile → approved | P1 |
| Worker profile — Update, availability | ❌ None | test_worker_profile.py: update availability, profile fields | P1 |
| Client profile — Create, update | ❌ None | test_client_profile.py: create, update fields | P2 |
| Worker issues — Create, view | ❌ None | test_worker_issues.py: create and list | P2 |
| Admin dashboard — Stats accuracy | ❌ None | test_admin_dashboard.py: counts match seeded data | P2 |
| Admin audit log — Events recorded | ❌ None | test_audit.py: verify events written to DB | P2 |

---

## 13. Retesting Checklist After Every Fix

After any code change, run the following:

- [ ] Run all backend tests: `cd apps/backend && pytest -v`
- [ ] Run ruff lint: `cd apps/backend && ruff check .`
- [ ] Run Next.js build: `cd apps/admin && npm run build`
- [ ] Manual smoke test: admin login → requirements page loads → attendance page loads → finance page loads
- [ ] If touching auth: run test_auth.py, test_security.py, test_auth_schemas.py
- [ ] If touching requirements/quote/assignment: run test_requirements.py, test_quotes.py, test_assignments.py
- [ ] If touching attendance: run test_attendance.py, check geofence logic
- [ ] If touching payroll: run test_payroll.py, verify locked run blocks edits
- [ ] If touching payments: run test_payments.py, verify webhook signature check
- [ ] If touching mobile: check that VerifyOtpScreen, HomeScreen, AttendanceHistoryScreen render without errors in Expo dev
- [ ] If touching migrations: run `alembic upgrade head` on a clean DB and verify no errors
- [ ] If touching environment config: verify `settings = Settings()` still loads with test env vars
- [ ] If touching security: verify access token blocklist on logout still works
- [ ] If touching encryption: verify field-level encryption/decryption round-trip
- [ ] If touching scheduler: verify cleanup runs without raising exceptions

---

## 14. How to Update This File Going Forward

1. **After every developer ticket is closed**, add a row to Section 8 (Resolved Gap Tracker) with the fix summary and evidence path.
2. **When a gap is fixed**, update Section 7 (Gap Tracker) — change `Updated Status` from `Open` to `Resolved — TICKET-NNN`.
3. **When new features are built**, add rows to Section 3 (Current Implemented Features) with the status and evidence.
4. **After each sprint or milestone**, update the Readiness Scores in Section 1 based on actual progress.
5. **When new tests are written**, update Section 12 (Test Coverage Plan) to mark areas as covered.
6. **When deploying to production**, update the Production Readiness Checklist in Section 6.
7. **Add a row to the Changelog** (Section top) for every significant update to this document.
8. This file lives at `f:\Projects\annai-illam-platform\docs\MVP_AND_PRODUCTION_READINESS.md`. Commit it to version control so it is tracked alongside code changes.
9. Do not delete resolved gaps — keep them in Section 8 as a historical record of what was fixed.

---

## 15. Final Verdict

### What Is Good
The backend architecture is solid and well-structured. FastAPI with SQLAlchemy 2.0, Alembic migrations, field-level encryption, Redis rate limiting, JWT with refresh rotation, and access token blocklisting represent a mature and thoughtful implementation. The code follows consistent patterns: repository layer, service layer, schema validation, audit logging on all key actions, and security-conscious decisions throughout (generic error messages, OTP only exposed in local env, production config validated at startup).

The admin UI is feature-complete for the MVP scope. All 13 major sections are built, components follow shadcn/ui conventions, and the Zustand state management is clean. The finance page (with advance confirmation and payroll queue) is a genuinely good implementation.

The mobile app is impressive in scope. The worker home screen with GPS + biometric check-in/out, the week strip calendar, and the full onboarding flow (8 screens from OTP to biometric setup) are production-quality implementations. The client app covers the full requirement creation and complaint lifecycle.

### What Is Incomplete
Test coverage is now meaningful for the critical backend flows. Auth/security, requirements/quote, assignment, attendance, payroll, finance/payment, and complaints are covered. Broader worker/client APIs and end-to-end user journeys still need automated coverage.

The first-admin bootstrap gap has been closed with an idempotent seed command.

### What Is Risky
- Social auth (Google/Apple) is wired at the API level but its mobile integration has not been confirmed working end-to-end.
- The admin session management (refresh token auto-rotation on 401) was not verified in the api-client.ts file — sessions could expire silently.
- Push notifications fire in some flows (assignment creation) but not consistently across all user-facing events. Workers and clients may miss important notifications.

### What Blocks MVP
1. No automated end-to-end suite for the full user journey
2. No production smoke-test dry run using the deployment runbook

### What Blocks Production
Everything that blocks MVP, plus:
- No TLS/HTTPS configuration
- No production Redis smoke test completed in the target infrastructure
- No production backup schedule/restore drill completed
- No rate limiting on business endpoints
- No uptime alerting/log aggregation
- No load testing data

### What to Do Next (In Order)
1. Add an automated E2E smoke suite for the core flow (2–3 days)
2. Dry-run the production deployment runbook in staging (0.5–1 day)
3. Set up TLS, configure production `REDIS_URL`, enable backup schedule, and run Redis/backup restore drills (1–2 days)
4. Configure Sentry DSNs in production and run an error-monitoring smoke test (1 hour)

With focused effort, this platform can reach MVP-ready status in approximately 2 weeks of sprint work. Production readiness would require an additional 2–3 weeks of infrastructure and testing work.
