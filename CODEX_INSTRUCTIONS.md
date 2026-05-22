# Codex Instructions

## Project Name

Annai Illam Staffing Platform

---

## What We Are Building

A three-sided manpower/staffing management platform with:

- **Admin** — manpower company operations team (Next.js web dashboard)
- **Client** — companies that hire workers (React Native mobile app)
- **Worker** — people deployed to job sites (React Native mobile app)
- **Backend** — FastAPI REST API serving all three surfaces

---

## Most Important Rule

**This is not a payroll app in MVP.**
**This is not a marketplace app in MVP.**
**This is not a chat app in MVP.**
**This is not a finance app in MVP.**

The MVP is an **operations management app** for manpower staffing.

---

## Core MVP Flow

The first version must support this exact flow:

```
1.  Client logs in
2.  Client creates a worker request
3.  Client submits the request
4.  Admin receives notification
5.  Admin reviews the request
6.  Admin approves or rejects the request
7.  Admin assigns workers to the approved request
8.  Worker sees assigned job
9.  Worker accepts or declines the job
10. Worker checks in at the job site (GPS verified)
11. Worker checks out after the shift
12. Admin verifies attendance
13. Client views job and attendance status
14. Client or worker raises complaint if needed
15. Admin resolves or rejects the complaint
16. Job is marked completed
```

---

## Existing Repository

**This project already has code. Do not recreate it.**

Current structure:

```
apps/admin          Next.js admin web dashboard
apps/backend        FastAPI backend API
apps/mobile-ui-lab  React Native mobile app (Client + Worker)
```

---

## Before Coding — Always Do This First

Before making any code changes:

1. Read this file fully
2. Read `README.md`
3. Read `PROJECT_BRIEF.md`
4. Read `MVP_SCOPE.md`
5. Read `TECH_STACK.md`
6. Read `ROADMAP.md`
7. Inspect the relevant existing files in the target app
8. Summarise what you are changing and why
9. State what is intentionally out of scope
10. Confirm how this fits the MVP

---

## Backend Instructions

**Path:** `apps/backend`

**Framework:** FastAPI. Do not change this.

Before changing backend code, inspect:

```
apps/backend/app/main.py
apps/backend/app/api/
apps/backend/app/core/
apps/backend/app/db/
apps/backend/app/models/
apps/backend/app/repositories/
apps/backend/app/schemas/
apps/backend/app/services/
apps/backend/app/utils/
apps/backend/tests/
apps/backend/requirements.txt
apps/backend/alembic.ini
```

**Backend must include:**

- Models (SQLAlchemy)
- Schemas (Pydantic)
- Routes / API endpoints
- Services (business logic)
- Repositories (if pattern already exists)
- Alembic migrations
- Pytest tests
- Permission checks on every protected endpoint

**Backend rules:**

- Use FastAPI. Do not convert to Django or any other framework.
- Continue using the existing architecture and folder structure.
- Do not introduce new backend frameworks.
- Validate all input using Pydantic schemas.
- Enforce permissions in the backend. Never trust frontend checks only.
- Do not hardcode business data.
- Use environment variables for all config and secrets.

---

## Admin Web Instructions

**Path:** `apps/admin`

Before changing admin code, inspect:

```
apps/admin/src/app/
apps/admin/src/components/
apps/admin/src/constants/
apps/admin/src/features/
apps/admin/src/hooks/
apps/admin/src/lib/
apps/admin/src/services/
apps/admin/src/store/
apps/admin/src/types/
```

**Admin app must support:**

- Dashboard with stats and pending actions
- Client management
- Worker management
- Job request management (approve / reject)
- Worker assignment
- Attendance verification
- Complaint management

**Admin UI library:** shadcn/ui (built on Radix UI + Tailwind CSS)

Use shadcn/ui components for all admin UI. Install via `npx shadcn@latest add <component>`. Components live in `apps/admin/src/components/ui/`. Do not build buttons, inputs, dialogs, tables, or form fields from scratch.

**Admin UI must be:**

- Clean and not cluttered
- Modern and data-rich
- Table-based for list views
- Easy to filter and search
- Status-driven with clear status badges
- Not overloaded with features

---

## Mobile Instructions

**Path:** `apps/mobile-ui-lab`

**This is the main mobile app.**

The deleted `apps/mobile` folder must not be recreated unless explicitly requested.

Before changing mobile code, inspect:

```
apps/mobile-ui-lab/src/
apps/mobile-ui-lab/src/apps/
apps/mobile-ui-lab/src/components/
apps/mobile-ui-lab/src/screens/
apps/mobile-ui-lab/src/shared/
apps/mobile-ui-lab/App.tsx
apps/mobile-ui-lab/package.json
apps/mobile-ui-lab/tamagui.config.ts
apps/mobile-ui-lab/gluestack-ui.config.ts
```

**Mobile app must support two roles:**

**Client:**
- Login
- Dashboard
- Create worker request
- View requests and status
- View assigned workers
- View attendance status
- Raise and view complaints
- Profile

**Worker:**
- Login with phone OTP
- Onboarding flow (first time only — see Worker Auth Flow below)
- Dashboard (today's job + check-in button)
- My jobs
- Job detail
- Accept / decline job
- Check in / check out
- Attendance history
- Raise and view complaints
- Profile

### Worker Auth Flow

**First-time worker onboarding (one-time only):**

```
1. Enter phone number
2. Enter OTP
3. Build profile (name, city, skills, availability)
4. Consent screen (document retention + privacy consent)
5. Government ID upload + selfie
6. Submitted — pending admin approval
7. Admin approves worker
8. Worker opens app → Biometric setup (one-time)
9. Worker reaches dashboard
```

**Every login after first approval:**

```
1. Enter phone number
2. Enter OTP
3. Biometric check (Face ID / fingerprint)
4. Worker reaches dashboard
```

**Onboarding step tracking** — the `onboarding_step` field on the backend tracks where a worker is:

| Value | Meaning |
|---|---|
| `null` | Fresh worker, start from Build Profile |
| `identity_uploaded` | ID uploaded, waiting for profile build step (resume at Build Profile) |
| `profile_submitted` | Profile submitted, pending admin review |
| `approved` | Admin approved — proceed to biometric setup or biometric check |

**Biometric state** — `biometricSetupDone` is stored in secure on-device storage:
- `false` (default) → show BiometricSetupScreen after first approval (one-time)
- `true` → show BiometricCheckScreen on every subsequent login session

---

## MVP Entities

Only these models are required in MVP:

```
User
ClientCompany
WorkerProfile
JobRequest
Shift
WorkerAssignment
AttendanceRecord
Complaint
Notification
```

**Do not add finance, salary, or invoice models unless explicitly requested.**

---

## Features Not Included in MVP

Do not build these unless explicitly asked:

```
Invoice generation
Salary automation
Payment gateway
Food and accommodation billing
PDF reports
Advanced analytics
AI worker matching
In-app chat
Offline sync
Multi-branch support
Multi-language support
Automated payroll disbursement
Third-party HR integrations
Marketplace features
Worker rating system
```

---

## Access Control Rules

### Admin

Admin can manage all MVP data:

- All clients
- All workers
- All job requests
- All assignments
- All attendance records
- All complaints

### Client

Client can only access:

- Own company profile
- Own job requests
- Workers assigned to own jobs only
- Attendance for own jobs only
- Own complaints

Client cannot:

- Access another client's data
- Assign workers
- Modify attendance
- See sensitive worker personal data
- Access admin features

### Worker

Worker can only access:

- Own profile
- Own job assignments
- Own attendance records
- Own complaints

Worker cannot:

- See other workers' data
- See client billing information
- Access admin features
- Modify verified attendance records

---

## Status Values — Use These Exactly

### Job Request Status

```
DRAFT
SUBMITTED
UNDER_REVIEW
APPROVED
REJECTED
WORKERS_ASSIGNED
IN_PROGRESS
COMPLETED
CANCELLED
```

### Worker Assignment Status

```
ASSIGNED
ACCEPTED
DECLINED
REPLACED
COMPLETED
```

### Attendance Status

```
NOT_STARTED
CHECKED_IN
CHECKED_OUT
VERIFIED
ABSENT
LATE
```

### Complaint Status

```
OPEN
IN_REVIEW
RESOLVED
REJECTED
```

---

## UI/UX Rules

**Overall product feel:**

- Modern
- Clean
- Professional
- Simple
- Trustworthy
- Easy for non-technical users

### Admin UX

Admin is web-first. Use:

- Sidebar navigation
- Dashboard KPI cards
- Data tables with filters and search
- Status badges on every record
- Detail pages on row click
- Action buttons with confirmation modals

Dashboard must show:

- Pending requests
- Active jobs
- Workers on shift today
- Attendance needing verification
- Open complaints

### Client UX

Client is mobile-first. Focus on:

- Creating worker requests quickly
- Viewing request status clearly
- Seeing which workers are assigned
- Tracking attendance status
- Raising complaints easily

Screens must feel professional and reassuring.

### Worker UX

Worker app must be **extremely simple**.

Worker dashboard must show:

- Today's job (company, location, shift time)
- Current check-in status
- One large, obvious Check In or Check Out button

The worker must be able to check in within 20 seconds of opening the app.

---

## Development Rules

When implementing any feature:

- Work only on the requested phase
- Keep changes small and focused
- Reuse existing project patterns and folder structure
- Do not introduce unrelated features
- Do not introduce a new framework
- Do not hardcode business data
- Add input validation on all forms and APIs
- Add permission checks on all protected endpoints
- Add tests where possible
- Update documentation if behaviour changes
- Keep naming clear and consistent
- Use the status values from this document exactly
- Handle loading, empty, and error states in all UI screens

---

## Security Rules

- Do not commit `.env` files
- Do not expose tokens in code or logs
- Do not expose passwords in code or logs
- Do not expose API keys
- Keep all secrets in environment variables
- Validate all input on the backend
- Do not trust frontend-only validation
- Enforce permissions in backend APIs on every request
- Never rely on frontend checks alone for security
- Never expose sensitive worker data (bank details, full ID) to clients

---

## Testing Rules

### Backend tests must cover

- Happy path
- Invalid input (missing fields, wrong types)
- Unauthorized access (no token)
- Wrong role access (token present but wrong role)
- Object ownership (user accessing another user's data)
- Invalid status transitions
- Required field validation

### Frontend tests must cover

- Correct role routing after login
- API error handling
- Loading state
- Empty state
- Error state
- Successful action confirmation

---

## Response Format for Development Requests

When responding to a development task, always start with:

1. **What I understood** — restate the task clearly
2. **Which app/folder will be changed** — `apps/backend`, `apps/admin`, or `apps/mobile-ui-lab`
3. **Which files will be inspected** — list the files to read first
4. **Which files will likely be modified** — list the files to change
5. **What is intentionally out of scope** — what will not be built
6. **How this fits the MVP** — confirm alignment with the roadmap phase

Then proceed with implementation.

---

## Final Reminder

**Do not overbuild.**

**Do not add Version 2 features into Version 1.**

**Do not recreate the deleted `apps/mobile` folder.**

**The goal is to finish a stable, working MVP first.**