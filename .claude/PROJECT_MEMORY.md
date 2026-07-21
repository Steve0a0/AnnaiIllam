# Project Memory

## Stable Notes

- Main apps: backend `apps/backend`, admin `apps/admin`, mobile `apps/mobile-ui-lab`.
- Do not use or recreate `apps/mobile` unless explicitly requested.
- Admin UI must use shadcn/ui from `apps/admin/src/components/ui`.
- Mobile app uses Expo/React Native/Tamagui (worker) and React Native core styles (client) in `apps/mobile-ui-lab`.
- Backend uses FastAPI in `apps/backend`.
- First admin account can be created/reset with `cd apps/backend && make seed-admin EMAIL=x PASSWORD=y NAME="Admin"`; implementation is `apps/backend/scripts/seed_admin.py`.
- Admin complaint detail route exists at `apps/admin/src/app/(dashboard)/complaints/[id]/page.tsx`; resolution controls live in `apps/admin/src/features/complaints/update-complaint-status-form.tsx`.
- Admin report sub-pages exist at `/reports/requirements`, `/reports/assignments`, and `/reports/complaints`; filters use `apps/admin/src/features/reports/report-filters.tsx` and backend query params in `apps/backend/app/api/admin_reports.py`.
- Requirements and quote integration coverage lives in `apps/backend/tests/test_requirements.py`; it covers client create/list/detail, admin review, quote create, approve/reject, ownership, role checks, duplicate quote, and invalid transitions.
- Assignment integration coverage lives in `apps/backend/tests/test_assignments.py`; it covers admin create/list/filter/status updates, worker accept/decline, ownership, role checks, payment/availability gates, duplicate active assignment rejection, capacity enforcement, payment gate bypass audit, and document expiry warnings. (38 tests as of P2-6)
- Attendance integration coverage lives in `apps/backend/tests/test_attendance.py`; it covers GPS check-in/out, geofence failures, admin correction, locked payroll correction blocking, ownership, and role checks.
- Payroll integration coverage lives in `apps/backend/tests/test_payroll.py`; it covers run generation from attendance, deductions, all run statuses, paid transition, locked-run enforcement, platform margin calculation, and role checks. (28 tests as of P2-7)
- GitHub Actions CI lives in `.github/workflows/backend.yml` and `.github/workflows/admin.yml`; backend runs Ruff plus full pytest, admin runs ESLint plus `next build`.
- Sentry error monitoring is wired for backend/admin. Backend config is `apps/backend/app/core/monitoring.py`; admin App Router instrumentation is `apps/admin/src/instrumentation.ts` and `apps/admin/src/instrumentation-client.ts`. DSNs are env-driven and empty values disable Sentry locally.
- Production deployment runbook is `docs/DEPLOYMENT.md`; it covers env vars, managed PostgreSQL/Redis/S3, migrations, first admin seed, Docker/systemd deployment, DNS/TLS, smoke tests, rollback, and backups.
- Alembic production migrations honor `DATABASE_URL` from the environment via `apps/backend/migrations/env.py`.
- PostgreSQL backup command is `cd apps/backend && python -m scripts.backup_postgres`; it runs `pg_dump`, uploads to S3, and prunes by `BACKUP_RETENTION_DAYS`.
- Redis production connectivity can be verified with `cd apps/backend && python -m scripts.check_redis`; it redacts credentials and checks ping plus temporary TTL write/read/delete.
- `apps/mobile-ui-lab/.env` was recreated after a corrupt 330 MB file caused `serve.ps1` to run out of memory. A backup exists as `.env.corrupt-20260508`.
- Use `MVP_IMPLEMENTATION_TRACKER.md` for current status, blockers, next queue, and Jira-style MVP project tracking.
- `GET /api/v1/users` is restricted to `super_admin`, returns a paginated minimal directory without phone/email/name, and is covered by `apps/backend/tests/test_users.py`, including a router-wide authentication regression test.
- Feature 3 (Worker Replacement) done: `POST /admin/assignments/{id}/replace` in `admin_assignments.py`. New columns `replacement_reason` + `replaced_by_assignment_id` on `Assignment` model; migration `y1z2a3b4c5d6`. Tests in `tests/test_worker_replacement.py` (8 tests). Duplicate-assignment check runs BEFORE availability check (order matters — assigned worker is unavailable by design).

## Backend Architecture (audited 2026-05-08)

- 25 SQLAlchemy models, 22 Alembic migrations — schema is complete and comprehensive.
- Auth: OTP (phone) for client/worker; phone + password for admin. JWT access (30 min) + refresh (30 days). Refresh token stored hashed in DB.
- RBAC via `require_role()` FastAPI dependency on all protected routes (`app/api/dependencies/roles.py`).
- Services layer: 16 services in `app/services/`. Repositories in `app/repositories/`. Clean separation.
- Field-level encryption (Fernet) on sensitive worker fields: UPI, bank account, IFSC.
- S3 + MinIO for document/selfie file storage.
- Rate limiting uses Redis (`app/core/rate_limit.py`). In tests, the rate limit key persists across test methods (Redis not reset between tests). Use `@patch("app.api.<router>.check_rate_limit")` when a test class calls the same rate-limited endpoint more than ~18 times in a session.
- PostgreSQL 16 on port 5433 (docker-compose). MinIO on ports 9000/9001.
- Tests: only a single placeholder test exists (`tests/test_auth.py`). No real coverage.
- API prefix: `/api/v1`. OpenAPI docs only enabled in `APP_ENV=local`.

## Admin Dashboard Architecture (audited 2026-05-08)

- Next.js 16 App Router with route groups: `(auth)` for `/login`, `(dashboard)` for all protected pages.
- Auth: phone + password only. OTP login intentionally disabled (throws error). JWT stored in localStorage under keys `admin_access_token`, `admin_refresh_token`, `admin_user`.
- Axios interceptor in `src/services/api-client.ts` handles 401 + auto-refresh.
- State: Zustand (`src/store/auth-store.ts`) for auth; React Query for all server data.
- All 16+ pages are built, routed, and sidebar-linked. Payroll, Finance, Reports, Audit Log, SLA Policies all added to sidebar in `src/components/layout/sidebar.tsx` (fixed 2026-05-08).
- Feature folders: `src/features/{requirements,assignments,attendance,complaints,payroll,finance,reports,dashboard,auth}/` — each has components + React Query hooks.
- shadcn/ui primitives in `src/components/ui/` — reuse these; do not hand-build primitives.

## Mobile App Architecture (audited 2026-05-08)

- Expo SDK 54, React Native 0.81.5, React 19, New Architecture enabled.
- App variant selected by `EXPO_PUBLIC_APP_VARIANT` env var (`client` | `worker`). Entry: `App.tsx` → `ClientApp` or `WorkerApp`.
- Scripts: `npm run clients` or `npm run worker` to start each variant.
- Google sign-in uses `expo-auth-session/providers/google`; native redirects use the app bundle/package scheme (`com.annaiillam:/oauthredirect`), so `apps/mobile-ui-lab/app.json` must register `com.annaiillam` alongside the public `annai-illam` scheme.
- Secure token storage via `expo-secure-store`. Keys prefixed: `client_*` vs `worker_*`.
- Worker app has biometric (Face ID/Touch ID) per-session auth via `expo-local-authentication`.
- Worker onboarding is multi-stage: phone OTP → consent → ID/selfie S3 upload → build profile → under review (admin approves) → biometric setup → app.
- Worker HomeScreen is the core operational screen: hero job card (accept/decline, GPS check-in/out), week strip calendar, availability toggle, browse jobs button.
- GPS check-in/out uses `expo-location`. File uploads use presigned S3 URLs with local multipart fallback.
- **Known gap: No complaints screens exist in mobile for either client or worker.** FIXED 2026-05-08 — see below.

## Mobile Complaints / Issues (built 2026-05-08)

**Backend addition:** `GET /client/complaints` added to `apps/backend/app/api/client_complaints.py` — returns all complaints across all client requirements, sorted newest first.

**Shared services:**
- `apps/mobile-ui-lab/src/shared/services/client-complaints.service.ts` — `listAll()`, `create()`
- `apps/mobile-ui-lab/src/shared/services/worker-issues.service.ts` — `list()`, `create()`

**Client screens** (React Native core style, matches existing clientStyles):
- `ComplaintsScreen.tsx` — list all complaints, badge with status + severity, navigate to detail
- `RaiseComplaintScreen.tsx` — pick requirement + type + severity + description form
- `ComplaintDetailScreen.tsx` — full detail + resolution notes

**Worker screens** (Tamagui style, matches existing worker screens):
- `IssuesScreen.tsx` — list all worker issues
- `RaiseIssueScreen.tsx` — pick assignment (optional) + issue type + description
- `IssueDetailScreen.tsx` — full detail + resolution notes

**Navigation:**
- Client nav types: added `Complaints`, `RaiseComplaint: { requirementId? }`, `ComplaintDetail: { complaintId }`
- Worker nav types: added `Issues`, `RaiseIssue`, `IssueDetail: { issueId }`
- Both AppNavigators updated with new stack screens.

## Admin Attendance Page (built 2026-05-20)

- `apps/admin/src/app/(dashboard)/attendance/page.tsx` — full implementation replacing the stub. Supports lookup by Requirement ID (fetches all assignments → parallel attendance fetch → unified table with worker names) or Assignment ID (single fetch, worker name shown as "Worker #id").
- New hook: `apps/admin/src/features/attendance/use-attendance-lookup.ts` — `useAttendanceLookup(mode, id)` React Query hook.
- New type: `EnrichedAttendanceItem` in `apps/admin/src/types/attendance.ts` — AttendanceItem + worker_name + assignment_id + requirement_id.
- Verify action: one-click approve via `PATCH /admin/attendance/{id}`. Correct action: shadcn Dialog wrapping existing `CorrectAttendanceForm`.
- Summary stat cards: Total | Verified | Pending | Absent.
- Pre-existing TS errors in `src/__tests__/auth-store.test.ts` (MOCK_USER missing email/name) are unrelated and pre-date this work.

## Admin Sidebar (fixed 2026-05-08)

- `apps/admin/src/components/layout/sidebar.tsx` — navGroups now has 3 groups: Operations, Finance (Payroll + Finance), Management (Complaints, Reports, Audit Log, SLA Policies, Admin Users, Settings). All 5 previously missing nav links now present. Blocker cleared.

## Client App Navigation (refactored 2026-05-15)

- Migrated from flat single Stack to bottom tab navigator: Home · Jobs · Complaints · Profile.
- Stack types: `ClientTabParamList`, `HomeStackParamList`, `JobsStackParamList`, `ComplaintsStackParamList`, `ProfileStackParamList`.
- `ClientAppStackParamList` is now a backward-compat alias for `HomeStackParamList`.
- `JobsStackParamList` includes `CreateRequest` (accessible from RequestsScreen).
- Cross-tab navigation from AssignedWorkers → ComplaintsTab uses `navigation.getParent<any>().navigate('ComplaintsTab', { screen: ... })`.
- Cross-tab navigation from HomeScreen uses a second `useNavigation<TabNavigation>()` cast.

## Client Profile (2026-05-15)

- `GET /client/profile` now returns phone (from User) + new preference fields.
- `PATCH /client/profile` accepts: industry, email, default_job_category, food_preference (bool), accommodation_preference (bool), standing_notes.
- New migration: `h1i2j3k4l5m6_add_client_profile_preferences.py` (down_revision: g1h2i3j4k5l6).
- Service: `src/shared/services/client-profile.service.ts`.
- Screen: `ClientProfileScreen.tsx` — view mode (3 InfoCard sections) + slide-up Modal edit sheet.

## AssignedWorkers Screen (2026-05-15)

- Route: `AssignedWorkers: { requirementId: number }` in both `HomeStackParamList` and `JobsStackParamList`.
- Entry points: HomeScreen active-job card chip, RequestDetail "View all workers" button.
- Features: summary strip (assigned/in/absent), per-worker attendance pill, check-in/out times, multi-day streak dots (up to 14 days), "Raise complaint" cross-tab shortcut.

## Hardening Status (HARD-1 complete, 2026-05-29)

- `apps/backend/app/core/config.py` — production validator now rejects weak `JWT_SECRET_KEY` (< 32 chars or placeholder), weak `PAYMENT_WEBHOOK_SECRET`, CORS wildcard `*`, and missing S3 config when `S3_BUCKET` is set.
- `apps/backend/app/core/security_headers.py` — added `X-XSS-Protection: 1; mode=block`.
- `apps/backend/app/api/auth.py` — admin login rate limit tightened from 10 to 5 per 5 minutes.
- `apps/backend/tests/test_auth.py` — `TestAdminLogin` and `TestTokenRefresh` now use `@patch("app.api.auth.check_rate_limit")` class decorator (test login logic, not rate limiting). `TestLogout._login` uses context manager patch. Total real rate-limit increments in the session is 3 (e2e + test_me), within the limit of 5.
- `apps/admin/.gitignore` — now excludes `.env*` (belt-and-suspenders; root already covers it).
- `apps/mobile-ui-lab/.gitignore` — now excludes `.env` and `.env.*` (was only `.env*.local`).
- `apps/mobile-ui-lab/.env.example` — created; covers all required env vars.
- `apps/backend/.env.example` — fully rewritten with descriptions, format hints, and REQUIRED/OPTIONAL labels for all ~30 vars.
- `apps/admin/.env.example` — fully rewritten with descriptions.
- `apps/admin/src/lib/env.ts` — throws at startup if `NEXT_PUBLIC_API_BASE_URL` is missing in production (`NODE_ENV=production` + `APP_ENV != local`).
- **NOTE**: `apps/mobile-ui-lab/.env` contains a real Google Maps API key (`AIzaSy...`). File is git-ignored (confirmed). Key MUST be restricted in Google Cloud Console to the app bundle IDs.

## MVP Status (as of 2026-05-08)

**FULL E2E SMOKE TEST PASSED.** All MVP acceptance criteria verified manually on 2026-05-08.

Confirmed working:
- Admin, client, worker login (OTP + password)
- Worker onboarding (consent → ID upload → profile → admin approve)
- Client creates requirement → admin reviews → admin quotes → client approves
- Admin assigns worker → worker accepts shift → GPS check-in → GPS check-out
- Admin corrects/approves attendance
- Client views request + attendance status
- Client raises complaint → admin resolves
- Worker raises issue

Remaining gap (not blocking MVP):
- **No real backend tests** — only a placeholder test. The test suite is effectively empty.
- **Push notifications (Phase 8)** — push token model exists; FCM integration on mobile not confirmed.

## Flow Bug Fixes — Priority 1 (fixed 2026-05-28)

Four core-flow bugs fixed as part of a structured audit. 111 backend tests pass after fixes.

- **Fix 1 — `canCreateQuote` re-quote gate** (`apps/admin/src/features/requirements/requirement-detail-view.tsx:93`): Changed condition from `!requirement.quote` to `!requirement.quote || ["rejected","expired"].includes(requirement.quote.status)`. Unblocks admin re-quoting after a client rejects the first quote.
- **Fix 2 — Mobile timeline status mismatch** (`apps/mobile-ui-lab/src/apps/client/screens/RequestDetailScreen.tsx:33`): Changed `"assigned"` to `"workers_assigned"` in the timeline array. Requirement progress indicator was stuck at "Approved" forever after workers were assigned.
- **Fix 3 superseded by PROD-004 (2026-07-20)**: Payment confirmation never changes operational requirement state. Aggregate confirmed advance unlocks the assignment API; Operations/Admin owns assignment and completion transitions. Tests live in `tests/test_payment_transitions.py`.
- **Fix 4 — Half-day attendance never set `in_progress`** (`apps/backend/app/api/worker_attendance.py:281-333`): Added same assignment-activation + requirement lifecycle block that `worker_check_in` uses. Jobs where workers only use half-day reporting can now reach `completed`. Tests appended to `tests/test_attendance.py` as `TestHalfDayLifecycleTrigger` (5 tests).

## Flow Bug Fixes — Priority 2 (fixed 2026-05-28)

- **Fix 5 — Check-in bypasses state machine** (`worker_attendance.py:143-146`): Added `validate_requirement_transition()` guard before `build_checkin_attendance`. Removed redundant second `get_requirement_by_id` call inside the lifecycle block. Tests: `TestCheckInStateMachineGuard` in `test_attendance.py` (4 tests).
- **Fix 6 — Worker decline reverts requirement without state machine** (`worker_assignments.py:117-118`): Wrapped `requirement.status = APPROVED` with `validate_requirement_transition()` + try/except HTTPException. Tests: `TestWorkerDeclineStateMachineGuard` in `test_assignments.py` (2 tests).
- **Fix 7 — `salary_amount` leaked to client** (`client_requirements.py:210`): Removed `salary_amount` from client-facing assignment projection. Also removed from `ClientRequirementDetail` TypeScript type in `apps/mobile-ui-lab/src/shared/services/client-requirements.service.ts`. Tests: `TestClientRequirementDetailSalaryLeakage` in `test_requirements.py` (1 test).
- **Fix 8 — Assignment status update had no transition validation** (`admin_assignments.py:309-386`): Added `ASSIGNMENT_TRANSITIONS` dict and `validate_assignment_transition()` to `app/core/assignment_constants.py`. Imported and called in `update_assignment_status()`. Terminal states (completed, cancelled, replaced) cannot be exited. Tests: `TestAssignmentStatusTransitionGuard` in `test_assignments.py` (4 tests).
- **Fix 9 superseded by PROD-004**: `payment_ledger_service.py` calculates aggregate advance due and the assignment API enforces it.

## PROD-004 Payment Ledger (2026-07-20)

- Client quote/payment APIs use integer whole INR rupees; Razorpay converts to paise only at its adapter boundary.
- `app/services/payment_ledger_service.py` owns quote total, advance, paid, refund, outstanding, and overpayment calculations.
- Client amount/payment-model fields are compatibility hints only and never authoritative.
- Payment purposes are advance, balance, adjustment, and refund.
- Product and Finance approval of `docs/PAYMENT_LEDGER.md` is still required before PROD-004 can be DONE.

## PROD-019 / PROD-020 Release Gates (2026-07-21)

- Admin ESLint passes with 0 errors; 8 warnings remain non-blocking.
- Admin tests pass 25/25 and the Next.js production build completes.
- Mobile TypeScript passes and mobile tests pass 11/11.
- Backend dependency audit passes with no known vulnerabilities after upgrading the coupled FastAPI/Starlette and pytest/pytest-asyncio dependency sets; the full backend suite passes 802/802 tests.
- FastAPI 0.139 uses lazy included routers. Router-wide security tests must inspect each included router's `effective_route_contexts()` as well as direct `APIRoute` entries.
- Scheduled jobs run only through `python -m app.scheduler_runner`; API startup has no scheduler hooks. Deploy exactly one scheduler replica independently of API `WEB_CONCURRENCY`.
- No-show flagging parses the first `HH:MM` from assignment/requirement shift text, waits `NO_SHOW_GRACE_PERIOD_MINUTES` (default 60), and fails safe when no start time is parseable. Attendance is unique by assignment and business date; migration `b7e1c42d9a60` repairs drifted databases.
- `app.utils.time.business_date(at=None)` is the single Asia/Kolkata calendar-date helper. Naive inputs are treated as stored UTC; attendance check-ins retain UTC timestamps but derive `attendance_date` in IST, which payroll aggregates.
- Razorpay mobile callbacks and `payment.captured` webhooks reconcile through `payment_reconciliation_service.py` under row locks. Captured status, INR, exact paise amount, order ID, and globally unique payment ID are enforced; the synthetic webhook is local-only.
- Admin build fixes include a stable React Query timestamp for requirement age,
  local `useQueryClient()` initialization in `WorkerReviewPanel`, and
  `worker_daily_rate` in `CreateQuotePayload`.
- Mobile `clientStyles.C` now defines the semantic `neutralBg` token.
- **Fix 10 — Worker phone update had no uniqueness check** (`admin_people.py:755-759`): Added `get_user_by_phone` lookup before setting new phone; raises HTTP 409 if another account already uses it. Phone is `.strip()`-normalised before comparison. Tests: `TestWorkerPhoneUniqueness` in `tests/test_people.py` (4 tests).

## Admin Clients Page (implemented 2026-05-08)

- **Layer 1** (polish): `apps/admin/src/app/(dashboard)/clients/page.tsx` — shadcn table with search, proper LoadingState/EmptyState/ErrorState, company avatar, row hover actions.
- **Layer 2** (full CRUD): backend endpoints in `apps/backend/app/api/admin_people.py`:
  - `GET /admin/people/clients` — now returns `phone` and `is_active` per client (joins Users).
  - `POST /admin/people/clients` — creates User (role=client) + ClientProfile.
  - `PATCH /admin/people/clients/{id}` — updates ClientProfile fields (all fields required, gst_number nullable).
  - `POST /admin/people/clients/{id}/deactivate` — sets user.is_active = False.
- **Frontend dialogs** in `apps/admin/src/features/clients/`: `create-client-dialog.tsx`, `edit-client-dialog.tsx`, `deactivate-client-dialog.tsx`, `index.ts`.
- **Types** in `apps/admin/src/types/people.ts`: `AdminClient` now has `phone` and `is_active`; added `AdminClientCreatePayload`, `AdminClientUpdatePayload`, `AdminClientMutationResponse`.
- **Service** in `apps/admin/src/services/people.service.ts`: `createClient`, `updateClient`, `deactivateClient` added.
- **Layer 3** (detail page): `GET /admin/people/clients/{id}` returns profile + requirements list. Frontend: `apps/admin/src/app/(dashboard)/clients/[id]/page.tsx` (thin route) + `apps/admin/src/features/clients/client-detail-view.tsx` (profile card, stats sidebar, clickable requirements table linking to `/requirements/{id}`). List rows in `clients/page.tsx` navigate to detail on click; action buttons stop propagation. Types: `AdminClientRequirement`, `AdminClientDetail`, `AdminClientDetailResponse` in `types/people.ts`. Service: `getClientById` in `people.service.ts`. Clients page is now fully complete for MVP.

## Assignment Matching / Modal (fixed 2026-05-08)

- `apps/backend/app/services/worker_matching_service.py` treats broad worker shift preferences like `Full Day`, `General`, and `Morning` as compatible with general 09:00-18:00 requests.
- `apps/admin/src/features/assignments/create-assignment-form.tsx` shows compact ready/blocked/selected counts, a single `Ready to assign` group, and clearer blocked-worker fix text.

## Truncated File Repairs (May 2026)
All pre-existing truncated files have been repaired and TypeScript is now error-free (0 errors):
- `src/shared/lib/http.ts` — completed axios interceptor with token refresh logic
- `src/shared/services/worker-onboarding.service.ts` — added `submitProfile`, `submitIdentity` methods; fixed `res.data.data.local_key` (Envelope wraps in `.data`)
- `src/apps/client/navigation/AppNavigator.tsx` — completed (was cut off mid-function signature)
- `src/apps/client/navigation/AuthNavigator.tsx` — completed (was cut off mid-JSX)
- `src/apps/client/screens/HomeScreen.tsx` — completed StyleSheet
- `src/apps/worker/screens/auth/BiometricCheckScreen.tsx` — completed JSX + local StyleSheet
- `src/apps/worker/screens/auth/BiometricSetupScreen.tsx` — completed local StyleSheet
- `src/apps/worker/screens/auth/BuildProfileScreen.tsx` — added chipActive, chipTextActive, toggleBank, toggleBankText, spacerBottom styles
- `src/apps/worker/screens/auth/UnderReviewScreen.tsx` — added waitRow, waitText, waitBold, contactText, contactLink, logoutBtn, logoutText styles
- `src/apps/worker/screens/auth/VerifyIdentityScreen.tsx` — added fileName, fileRemove styles

## Key Type Fixes
- `ClientAppStackParamList.RaiseComplaint` changed from `undefined` to `{ requirementId?: number }` — ComplaintsScreen passes `{}`, RaiseComplaintScreen uses optional param
- `ClientAppStackParamList.RequestDetail` uses `requirementId` (not `requestId`) — matches RequestDetailScreen usage
- `Envelope<T>` type: response is `res.data.data` not `res.data` — `axios` wraps the HTTP body in `res.data`, then our Envelope wraps the payload in `.data`
