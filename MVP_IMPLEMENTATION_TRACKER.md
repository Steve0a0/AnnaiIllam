# MVP Implementation Tracker

This file tracks what is actually implemented, what is in progress, and what should happen next.

Use this as the day-to-day Jira-style project board. Use `MVP_SCOPE.md` and `ROADMAP.md` as the source of truth for what belongs in the MVP.

## Status Legend

- `TODO` - Not started.
- `IN_PROGRESS` - Currently being worked on.
- `NEEDS_REVIEW` - Built but needs review/testing.
- `DONE` - Implemented and verified enough for MVP.
- `BLOCKED` - Cannot proceed until the blocker is removed.
- `OUT_OF_SCOPE` - Not part of MVP unless explicitly requested.

## Current Focus

| Field | Value |
|---|---|
| Current phase | `Phase 9: Polish and Final Testing` |
| Current priority | MVP complete — full E2E smoke test passed 2026-05-08 |
| Next decision | Post-MVP polish, notifications, or Phase 10 roadmap items |
| Last updated | 2026-05-20 |

## Next Work Queue

| Priority | Status | Task | App | Notes |
|---|---|---|---|---|
| P0 | DONE | Run all three apps together and verify auth works end-to-end | All | E2E smoke test passed 2026-05-08 |
| P0 | DONE | Verify OTP login works for client and worker in mobile | Mobile | OTP login confirmed working in E2E test |
| P0 | DONE | Verify admin password login works | Admin | Admin login confirmed working |
| P1 | DONE | Add complaints screens to mobile (client + worker) | Mobile | Built 2026-05-08 and verified in E2E test |
| P1 | DONE | Verify worker check-in/out GPS flow works end-to-end | Mobile/Backend | GPS check-in/out confirmed working in E2E test |
| P1 | DONE | Verify assignment accept/decline flow works end-to-end | Mobile/Backend | Accept shift confirmed working in E2E test |
| P1 | DONE | Verify client requirement create + admin approve flow | Admin/Mobile | Full flow confirmed: create → review → quote → approve |
| P2 | DONE | Test worker onboarding flow (consent → ID upload → profile → under review) | Mobile | Full onboarding flow confirmed in E2E test |
| P2 | DONE | Verify admin requirement → quote → client approval flow | Admin/Mobile | Quote created by admin, approved by client in E2E test |
| P2 | DONE | Add missing sidebar nav items to admin (payroll, finance, reports, audit, SLA) | Admin | Fixed 2026-05-08 |
| P0 | DONE | Add first-admin seed command | Backend | `make seed-admin EMAIL=x PASSWORD=y` added 2026-05-20 |
| P0 | DONE | Verify and polish admin complaint detail page | Admin/Backend | `/complaints/[id]` shows complaint context, raised-by metadata, resolution notes, and direct resolve/reject actions |
| P0 | DONE | Verify and filter admin report sub-pages | Admin/Backend | `/reports/requirements`, `/reports/assignments`, and `/reports/complaints` show backend data with date/status filters and row counts |
| P0 | DONE | Add requirements and quote flow integration tests | Backend | `tests/test_requirements.py` covers create/list/detail, admin review, quote create, approve/reject, ownership, role checks, and invalid transitions |
| P0 | DONE | Add assignment flow integration tests | Backend | `tests/test_assignments.py` covers admin create/list/filter/status updates, worker accept/decline, ownership, role checks, gates, and invalid transitions |
| P0 | DONE | Add attendance flow integration tests | Backend | `tests/test_attendance.py` covers GPS check-in/out, geofence rejection, admin correction, locked payroll blocking, ownership, and role checks |
| P0 | DONE | Add payroll flow integration tests | Backend | `tests/test_payroll.py` covers run generation, deductions, all statuses, paid transition, locked-run enforcement, and role checks |
| P0 | DONE | Add GitHub Actions backend/admin CI | Backend/Admin | `.github/workflows/backend.yml` runs Ruff + pytest; `.github/workflows/admin.yml` runs ESLint + Next.js build on PRs and main/develop pushes |
| P0 | DONE | Wire Sentry error monitoring | Backend/Admin | FastAPI and Next.js Sentry SDKs are configured through env vars with request scrubbing and verified local lint/test/build checks |
| P0 | DONE | Add production deployment runbook | Docs/DevOps | `docs/DEPLOYMENT.md` covers env vars, managed PostgreSQL/Redis/S3, migrations, first admin seed, Docker/systemd deployment, DNS/TLS, smoke tests, rollback, and backups |
| P0 | DONE | Add PostgreSQL backup strategy | Backend/DevOps | `scripts.backup_postgres` runs `pg_dump`, uploads to S3, enforces retention, and is documented with cron/systemd scheduling plus restore steps |
| P0 | DONE | Add production Redis provisioning and smoke test workflow | Backend/DevOps | `scripts.check_redis` verifies production `REDIS_URL` with ping plus temporary TTL write/read/delete; deployment runbook covers ElastiCache/Redis Cloud setup and go-live gates |

## Phase Tracker

| Phase | Status | Backend | Admin | Mobile | Notes |
|---|---|---|---|---|---|
| Phase 1: Understand and Stabilise | DONE | DONE | DONE | DONE | Full code audit completed 2026-05-08 |
| Phase 2: Authentication and Role Routing | DONE | DONE | DONE | DONE | Confirmed working in E2E test 2026-05-08 |
| Phase 3: Client and Worker Management | DONE | DONE | DONE | DONE | Worker onboarding + client creation confirmed in E2E test |
| Phase 4: Job Request Flow | DONE | DONE | DONE | DONE | Create → review → quote → approve confirmed |
| Phase 5: Worker Assignment | DONE | DONE | DONE | DONE | Admin assign + worker accept confirmed |
| Phase 6: Attendance | DONE | DONE | DONE | DONE | GPS check-in/out + admin correction confirmed |
| Phase 7: Complaints | DONE | DONE | DONE | DONE | Client complaint + worker issue flow confirmed |
| Phase 8: Notifications | IN_PROGRESS | NEEDS_REVIEW | OUT_OF_SCOPE | TODO | Push token model + service exists; mobile FCM not confirmed |
| Phase 9: Polish and Final Testing | DONE | DONE | DONE | DONE | Full E2E smoke test passed 2026-05-08 |

## MVP Acceptance Checklist

| Status | Acceptance item | Source |
|---|---|---|
| DONE | Admin, Client, and Worker can log in successfully | `MVP_SCOPE.md` |
| DONE | Each role lands on the correct dashboard | `MVP_SCOPE.md` |
| DONE | Client can create and submit a worker request | `MVP_SCOPE.md` |
| DONE | Admin can approve or reject the request | `MVP_SCOPE.md` |
| DONE | Admin can assign workers to an approved request | `MVP_SCOPE.md` |
| DONE | Worker can accept or decline assigned job | `MVP_SCOPE.md` |
| DONE | Worker can check in and check out | `MVP_SCOPE.md` |
| DONE | Admin can verify attendance | `MVP_SCOPE.md` |
| DONE | Client can view request and attendance status | `MVP_SCOPE.md` |
| DONE | Client or worker can raise a complaint | `MVP_SCOPE.md` |
| DONE | Admin can resolve or reject a complaint | `MVP_SCOPE.md` |
| DONE | Role-based permissions are enforced on all API endpoints | `MVP_SCOPE.md` |
| DONE | No user can access data they should not see | `MVP_SCOPE.md` |
| DONE | Main flow works end to end without broken states | `MVP_SCOPE.md` |
| NEEDS_REVIEW | All screens have loading, empty, and error states | `MVP_SCOPE.md` |

## Blockers

| Status | Blocker | Impact | Next step |
|---|---|---|---|
| DONE | `apps/mobile-ui-lab/.env` was corrupt and 330 MB | `make serve` crashed with PowerShell OOM | Recreated `.env`; backup kept as `.env.corrupt-20260508` |
| DONE | Mobile app has no complaints screens | Phase 7 incomplete for mobile | Build client and worker complaint screens |
| DONE | Payroll, Finance, Reports, Audit, SLA pages exist but are NOT in admin sidebar | Admin nav is incomplete | Add missing items to `nav-main.tsx` nav groups |

## Audit Notes — 2026-05-08 Full Code Audit

### Backend (`apps/backend`)

- **25 SQLAlchemy models**: User, OtpCode, RefreshToken, WorkerProfile, ClientProfile, AdminProfile, WorkerDocument, Requirement, Quote, Assignment, WorkerInterest, Attendance, WorkerAvailability, ClientPayment, PayrollRun, PayrollItem, WorkerPayout, WorkerDeduction, Complaint, ComplaintSlaPolicy, WorkerIssue, Replacement, ClientRating, AuditLog, PushToken.
- **22 Alembic migrations** applied sequentially from users table to worker interests.
- **Auth**: OTP login for client/worker with phone; password login for admin. JWT access (30 min) + refresh (30 days). Rate limiting via Redis. Refresh token hashed and stored in DB.
- **Role RBAC**: `require_role()` dependency enforced on all protected routes.
- **Services layer**: 16 services — token, OTP, profile, payment, attendance, assignment, complaint, payroll, notification, storage, worker matching, social auth.
- **API routes**: 35+ route files grouped under `/api/v1/auth`, `/api/v1/client/*`, `/api/v1/worker/*`, `/api/v1/admin/*`, `/api/v1/me`.
- **Field encryption**: Fernet AES-128 on sensitive worker fields (UPI, bank account, IFSC).
- **Storage**: S3 + MinIO (local dev) for worker documents and selfies.
- **Tests**: Auth/security, admin seed, requirements/quote, assignment, attendance, payroll, finance/payment, and complaints now have focused pytest coverage. Backend CI runs the full suite plus Ruff.
- **Error monitoring**: Sentry SDK is wired in `app/core/monitoring.py`, initialized from `main.py`, and the generic exception handler captures unhandled exceptions when `SENTRY_DSN` is configured.
- **Deployment**: Production runbook lives at `docs/DEPLOYMENT.md`; Alembic now honors `DATABASE_URL` from the environment during production migrations.
- **Database backups**: `scripts.backup_postgres` creates custom-format PostgreSQL dumps, uploads them to S3, and deletes expired objects based on `BACKUP_RETENTION_DAYS`.
- **Redis production readiness**: `scripts.check_redis` verifies managed Redis connectivity from the backend runtime without logging credentials; deployment docs cover ElastiCache/Redis Cloud setup and `REDIS_URL` smoke tests.
- **Docker**: PostgreSQL 16 on port 5433 + MinIO on port 9000/9001.

### Admin Dashboard (`apps/admin`)

- **Next.js 16 App Router** with parallel route groups: `(auth)` and `(dashboard)`.
- **Pages**: dashboard, requirements (list + detail), assignments (list + detail), attendance, complaints (list + detail), payroll (list + detail), finance, workers, clients, settings, audit, SLA, reports (+ 3 sub-reports).
- **Auth**: Phone + password login → JWT stored in localStorage. Axios interceptor handles 401 + auto-refresh. Role guard redirects non-admin to `/login`.
- **OTP login is intentionally disabled** for admin — throws error if attempted.
- **State**: Zustand for auth + React Query for all server state (30s staleTime, 1 retry).
- **Error monitoring**: `@sentry/nextjs` is wired through App Router instrumentation (`src/instrumentation.ts`, `src/instrumentation-client.ts`) plus `global-error.tsx`; DSNs and sampling are env-driven.
- **Docker**: `apps/admin/Dockerfile` provides a multi-stage Next.js standalone production image.
- **Forms**: Create quote, create assignment, payroll run, add deduction, correct attendance, create replacement, update status (4 entities).
- **shadcn/ui**: Avatar, Badge, Button, Card, Collapsible, Dialog, DropdownMenu, Input, Label, ScrollArea, Select, Separator, Sheet, Sidebar, Textarea, Tooltip — all used correctly.
- **Gap**: Payroll, Finance, Reports, Audit, SLA routes exist but are NOT linked in the sidebar nav. You must navigate directly by URL.

### Mobile App (`apps/mobile-ui-lab`)

- **Expo SDK 54**, React Native 0.81.5, React 19 with New Architecture enabled.
- **Two app variants** selected via `EXPO_PUBLIC_APP_VARIANT` env var: `client` or `worker`.
- **Client screens**: WelcomeScreen, LoginScreen, VerifyOtpScreen, ProfileSetupScreen (auth); HomeScreen (stats + recent requests), RequestsScreen, RequestDetailScreen (timeline + quote approve/reject), CreateRequestScreen (4-step form).
- **Worker screens**: WelcomeScreen, LoginScreen, VerifyOtpScreen, ConsentScreen, VerifyIdentityScreen (ID + selfie S3 upload), BuildProfileScreen (skills/shifts/payment), ProfileSubmittedScreen, UnderReviewScreen, BiometricSetupScreen, BiometricCheckScreen (auth); HomeScreen (hero job card + week strip + availability toggle + browse jobs), JobsBoardScreen (best match / nearby / other + interest toggle), AvailabilityScreen (weekly calendar per-day status).
- **Worker HomeScreen** has: accept/decline assigned job, check-in/check-out with GPS, week strip calendar, availability toggle.
- **Auth**: OTP for both roles. Tokens in `expo-secure-store`. Axios interceptor handles 401 + refresh. Workers also have biometric (Face ID/Touch ID) per-session auth.
- **Gap: No complaints screens for client or worker in mobile.** No complaint raise, no complaint status tracking on mobile.
- **State**: Zustand for auth. No other global state.
- **Icons**: lucide-react-native. **UI**: Tamagui (worker), React Native core styles (client).

## How To Update This Tracker

When finishing work:

1. Update the relevant task status.
2. Add a short audit note if something important was learned.
3. Add blockers immediately when work cannot continue.
4. Keep detailed requirements in `MVP_SCOPE.md` and `ROADMAP.md`, not here.
