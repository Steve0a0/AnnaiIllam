# Annai Illam Platform — Project Skill

This is the primary reference file for any AI assistant or developer working on this codebase.
Read this before touching any code.

---

## What This Project Is

**Annai Illam** is a three-sided B2B staffing/manpower management platform for the Indian market
(Tamil Nadu focus). It replaces manual WhatsApp/Excel-based operations at a manpower supply company.

**Problem solved:** A manpower company manages client companies that need temporary workers, and
a pool of workers who are deployed to job sites. Today this is done via phone calls, WhatsApp,
and paper registers. This platform digitises and automates the entire operation.

**Three roles:**

| Role | Who they are | How they access |
|---|---|---|
| **Admin** | Manpower company operations staff | Next.js web dashboard |
| **Client** | Companies that hire workers (factories, warehouses, etc.) | React Native mobile app |
| **Worker** | The person deployed to a job site | React Native mobile app |

---

## Core Business Flow

```
1.  Client logs in (phone OTP)
2.  Client creates a manpower requirement
3.  Admin reviews the requirement and creates a quote (amount + advance payment)
4.  Client approves the quote and pays the advance (Razorpay or manual reference)
5.  Admin confirms payment → requirement moves to assigned state
6.  Admin assigns workers to the job
7.  Worker sees assignment, accepts or declines
8.  On shift day: worker GPS check-in (biometric gate + geofence validation)
9.  End of shift: worker GPS check-out
10. Admin verifies/corrects attendance records
11. Admin generates payroll run → locks run → workers get paid
12. Client or worker raises complaint if needed
13. Admin resolves or rejects the complaint
14. Job is marked completed
```

---

## Three Apps

### 1. Backend API (`apps/backend`)
- **Framework:** FastAPI (Python)
- **Database:** PostgreSQL 16 (port 5433 in docker-compose)
- **ORM:** SQLAlchemy 2.0 + Alembic migrations
- **API prefix:** `/api/v1`
- **OpenAPI docs:** only enabled when `APP_ENV=local`

**API route structure:**
```
/api/v1/auth/           — authentication (all roles)
/api/v1/admin/*         — admin-only endpoints
/api/v1/client/*        — client-only endpoints
/api/v1/worker/*        — worker-only endpoints
/api/v1/me              — profile for current user
/api/v1/health          — health check
/api/v1/ready           — readiness check (DB + Redis)
```

**Key backend folders:**
```
app/
├── api/            — route handlers (one file per module, ~35 files)
├── core/           — config, security, auth, rate limiting, encryption
├── db/             — database session, base
├── models/         — SQLAlchemy ORM models (25 models)
├── repositories/   — data access layer
├── schemas/        — Pydantic request/response schemas
├── services/       — business logic (16 services)
└── utils/          — helpers (geofence, audit, etc.)
migrations/         — Alembic migration files (22 migrations)
tests/              — pytest integration tests
scripts/            — seed_admin, backup_postgres, check_redis
```

**25 actual SQLAlchemy models:**
User, OtpCode, RefreshToken, WorkerProfile, ClientProfile, AdminProfile,
WorkerDocument, Requirement, Quote, Assignment, WorkerInterest, Attendance,
WorkerAvailability, ClientPayment, PayrollRun, PayrollItem, WorkerPayout,
WorkerDeduction, Complaint, ComplaintSlaPolicy, WorkerIssue, Replacement,
ClientRating, AuditLog, PushToken

### 2. Admin Dashboard (`apps/admin`)
- **Framework:** Next.js 16 App Router (TypeScript)
- **UI library:** shadcn/ui (required — never hand-build primitives)
- **State:** Zustand (auth) + React Query (server data)
- **Auth:** phone + password login only; OTP disabled for admin
- **Tokens:** JWT stored in localStorage under `admin_access_token`, `admin_refresh_token`, `admin_user`
- **HTTP client:** Axios with 401-interceptor + auto-refresh in `src/services/api-client.ts`

**Route groups:**
```
src/app/(auth)/login/       — login page
src/app/(dashboard)/        — all protected pages
  dashboard/
  requirements/             — job requirements list + detail
  assignments/              — worker assignment list + detail
  attendance/               — attendance lookup and verification
  payroll/                  — payroll run list + detail
  finance/                  — client payments + payroll queue
  complaints/               — complaint list + detail
  replacements/             — worker replacement tracking
  reports/requirements|assignments|complaints
  audit/                    — audit log
  sla/                      — SLA policies
  workers/                  — worker management
  clients/                  — client management
  admin-users/              — admin account management
  settings/                 — admin profile
```

**Key folders:**
```
src/features/{requirements,assignments,attendance,complaints,payroll,
              finance,reports,dashboard,auth,clients,workers}/
src/services/               — API service functions (one per domain)
src/types/                  — TypeScript domain types
src/store/auth-store.ts     — Zustand auth store
src/components/ui/          — shadcn/ui primitives (reuse these)
src/components/layout/sidebar.tsx — sidebar with 3 nav groups:
                                    Operations | Finance | Management
```

### 3. Mobile App (`apps/mobile-ui-lab`)
- **Framework:** Expo SDK 54, React Native 0.81.5, React 19
- **New Architecture:** enabled
- **App variant:** selected by `EXPO_PUBLIC_APP_VARIANT` env var (`client` | `worker`)
- **Entry point:** `App.tsx` → `ClientApp` or `WorkerApp`
- **Start commands:** `npm run clients` (client app) or `npm run worker` (worker app)
- **Token storage:** `expo-secure-store` (keys prefixed `client_*` or `worker_*`)
- **Worker UI:** Tamagui components
- **Client UI:** React Native core styles

**Key folders:**
```
src/apps/client/            — client app (navigation, screens)
src/apps/worker/            — worker app (navigation, screens)
src/shared/services/        — shared API services
src/shared/lib/http.ts      — shared Axios client (401 interceptor)
```

---

## Authentication

| Role | Method | Token storage |
|---|---|---|
| Admin | Phone + password (`POST /api/v1/auth/admin/login`) | localStorage |
| Client | Phone OTP (`/auth/client/request-otp` + `/verify-otp`) | expo-secure-store |
| Worker | Phone OTP (`/auth/worker/request-otp` + `/verify-otp`) + biometric gate | expo-secure-store |

**JWT:** Access token (30 min) + refresh token (30 days). Refresh token stored hashed in DB.
**RBAC:** `require_role()` FastAPI dependency enforced on every protected route in `app/api/dependencies/roles.py`.

**Worker onboarding (first login only):**
```
Phone → OTP → Consent → Upload ID + Selfie (S3) → Build Profile
→ Submitted (admin reviews) → Admin approves → Biometric setup → App
```

**Worker returning login:**
```
Phone → OTP → Biometric check → App
```

**Worker `onboarding_step` field values:**
- `null` — fresh worker, start from BuildProfile
- `identity_uploaded` — ID uploaded, continue profile
- `profile_submitted` — pending admin review
- `approved` — proceed to biometric setup or check

---

## Role-Based Access Control

All permissions enforced on the **backend**. Frontend role checks are UI-only.

| Resource | Admin | Client | Worker |
|---|---|---|---|
| All clients | Full CRUD | Own profile only | None |
| All workers | Full CRUD | See name+status on own jobs | Own profile only |
| Requirements | All | Own only | None |
| Approve requirement | Yes | No | No |
| Assign workers | Yes | No | No |
| Accept/decline assignment | No | No | Own only |
| Check in/out | No | No | Own active assignment |
| All attendance records | Full | Own jobs (read-only) | Own (read-only) |
| Verify attendance | Yes | No | No |
| Modify verified attendance | Super Admin only | No | No |
| Payroll | Full | No | Read-only (earnings) |
| Complaints | All | Own only | Own only (as issues) |
| Resolve complaints | Yes | No | No |
| Deactivate accounts | Super Admin only | No | No |

**Two admin sub-roles:**
- **Super Admin** — can do everything including: invite/deactivate admins, deactivate clients/workers, override verified attendance, manage settings
- **Ops Admin** — full operational access but cannot deactivate accounts or override verified records

---

## Security Architecture

- **Field-level encryption:** Fernet AES-128 on worker UPI ID, bank account, IFSC (`app/core/encryption.py`)
- **Rate limiting:** Redis-backed, applies to auth endpoints (`app/core/rate_limit.py`). Degrades gracefully if Redis unavailable.
- **GPS geofence:** Worker must be within 500m of job site to check in (Haversine in `app/utils/geofence.py`)
- **Worker documents:** Stored in private S3/MinIO bucket, served via signed URLs
- **Audit log:** All key admin actions written to `audit_logs` table (`app/utils/audit.py`)
- **Sentry:** Error monitoring wired for backend (`app/core/monitoring.py`) and admin (`src/instrumentation.ts`)

---

## How to Safely Make Code Changes

### Before editing any file

State in one sentence: which doc was read, which file is the target, what the change is, what is out of scope.

**Always check first:**
1. Read `.claude/PROJECT_MEMORY.md` for stable cached facts.
2. Read `AGENTS.md` for doc loading order and rules.
3. Read the relevant doc section (permissions, scope, business rules).
4. Inspect the existing file before modifying it.
5. Check if a test already covers the behavior you are changing.

### Backend changes

- Continue the existing architecture: API → service → repository → model pattern.
- Every new endpoint needs: `require_role()` dependency, ownership check, Pydantic schema, service logic.
- Every schema change needs an Alembic migration.
- Run `cd apps/backend && python -m pytest -v` after any backend change.
- Run `ruff check app tests scripts` for lint.

### Admin changes

- Always use shadcn/ui primitives from `src/components/ui/` — never hand-build buttons, inputs, dialogs, tables.
- Install missing components with `npx shadcn@latest add <component>`.
- Use React Query for all server state. Use Zustand only for auth.
- Run `npm run lint && npm run build` after changes.

### Mobile changes

- Client app uses React Native core styles. Worker app uses Tamagui. Do not mix.
- Add new screens to the correct `AppNavigator.tsx` file.
- Run TypeScript check or Expo start before reporting done.

---

## Common Mistakes to Avoid

1. **Using the wrong API URL pattern.** The actual pattern is `/api/v1/admin/*`, `/api/v1/client/*`, `/api/v1/worker/*` — not the generic patterns shown in the deleted `API_BLUEPRINT.md`.
2. **Adding features that already exist.** Run `grep` before building — payroll, finance, complaints, SLA, audit log, and reports are all fully implemented.
3. **Rebuilding `apps/mobile`.** That folder was deleted. Use `apps/mobile-ui-lab` only.
4. **Hand-building admin UI primitives.** shadcn/ui is required; check `src/components/ui/` first.
5. **Trusting frontend validation alone.** All business rules must be enforced in the backend service layer.
6. **Ignoring the MVP_SCOPE.md status values.** Use the exact enum strings — wrong status strings will break the state machine.
7. **Not adding an Alembic migration** when adding or modifying a model field.
8. **Modifying verified attendance records** without checking if the payroll run is locked first.
9. **Assuming the first admin exists.** Use `make seed-admin EMAIL=x PASSWORD=y NAME="Admin"` after fresh migrations.
10. **Using `apps/admin/AGENTS.md` or `apps/admin/CLAUDE.md` as sources of truth** — they both just point to root `AGENTS.md`.

---

## What to Always Check Before Editing

| Task type | Files to read first |
|---|---|
| New backend endpoint | `app/main.py`, the relevant API file, the service file |
| New admin page | Existing page in `src/app/(dashboard)/`, the feature folder, the service file |
| New mobile screen | The app navigator, existing screens in the same variant |
| Permission/access change | `PERMISSIONS_MATRIX.md`, `app/api/dependencies/roles.py` |
| Status transitions | `MVP_SCOPE.md` status values, the service layer that enforces transitions |
| Schema change | The model file, then `alembic upgrade head` plan |
| Attendance logic | `app/api/worker_attendance.py`, `app/utils/geofence.py` |
| Payroll logic | `app/api/admin_payroll.py`, payroll lock enforcement |
| Complaint resolution | `app/api/admin_complaints.py`, `src/features/complaints/` |

---

## Related Docs

| Doc | When to read |
|---|---|
| `AGENTS.md` | Every session — doc loading order and rules |
| `MVP_SCOPE.md` | When checking what is in scope, or looking up exact status values |
| `PERMISSIONS_MATRIX.md` | When adding/modifying role-gated features |
| `TECH_STACK.md` | When checking library/version decisions |
| `UI_DESIGN_SYSTEM.md` | When building new admin or mobile UI |
| `MVP_IMPLEMENTATION_TRACKER.md` | When checking current status, blockers, or next work queue |
| `docs/BUSINESS_RULES.md` | When implementing or verifying business logic |
| `docs/TESTING_GUIDE.md` | When writing or running tests |
| `docs/MANUAL_QA_CHECKLIST.md` | When doing manual QA or pre-release regression |
| `docs/DEPLOYMENT.md` | When deploying to production or staging |
| `.claude/PROJECT_MEMORY.md` | At the start of any session — cached stable facts |
