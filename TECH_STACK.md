# Tech Stack

## Critical Rule

This is an existing project.

**Do not rebuild the project from scratch.**

**Do not switch frameworks unless explicitly requested.**

Before making any technical changes, inspect the current project files and follow the existing architecture.

---

## Project Structure

```
annai-illam-platform/
│
├── apps/
│   ├── admin/              Next.js admin web dashboard
│   ├── backend/            FastAPI backend API
│   └── mobile-ui-lab/      React Native mobile app
│
├── README.md
├── PROJECT_BRIEF.md
├── MVP_SCOPE.md
├── TECH_STACK.md
├── CODEX_INSTRUCTIONS.md
└── ROADMAP.md
```

---

## Backend

**Path:** `apps/backend`

**Framework:** FastAPI (Python)

### Libraries and Tools

| Tool | Purpose |
|---|---|
| FastAPI | API framework |
| SQLAlchemy | ORM and database models |
| Alembic | Database migrations |
| Pydantic | Request and response schema validation |
| Pytest | Backend testing |
| python-jose | JWT token handling |
| passlib | Password hashing |

### Backend Structure

```
apps/backend/
├── app/
│   ├── main.py             FastAPI app entry point
│   ├── api/                Route handlers grouped by module
│   ├── core/               Config, security, dependencies
│   ├── db/                 Database session and base
│   ├── models/             SQLAlchemy ORM models
│   ├── repositories/       Data access layer
│   ├── schemas/            Pydantic request/response schemas
│   ├── services/           Business logic
│   └── utils/              Shared helpers
├── migrations/             Alembic migration files
├── tests/                  Pytest tests
├── requirements.txt
└── alembic.ini
```

### Backend Responsibilities

The backend handles:

- Authentication and JWT tokens
- Role-based access control
- Client management
- Worker management
- Job request lifecycle
- Shift management
- Worker assignment
- Attendance tracking
- Complaint handling
- In-app notifications
- All database access
- Input validation
- Business rule enforcement
- Backend tests

### Backend Rules

- Use FastAPI. Do not convert to Django or any other framework.
- Continue using the existing backend architecture and folder structure.
- Use Pydantic schemas for all request and response validation.
- Use SQLAlchemy models for all database entities.
- Use services for all business logic.
- Use repositories if the pattern already exists in the project.
- Add Alembic migrations for every database schema change.
- Add Pytest tests for all important business logic.
- Do not hardcode business data or configuration.
- Do not expose secrets or API keys in code.
- Use environment variables for all configuration.

---

## Admin Web App

**Path:** `apps/admin`

**Framework:** Next.js with TypeScript

### Admin Structure

```
apps/admin/
└── src/
    ├── app/                Next.js App Router pages
    ├── components/         Reusable UI components
    ├── constants/          App-wide constants and config
    ├── features/           Feature-based modules
    ├── hooks/              Custom React hooks
    ├── lib/                Shared utilities and helpers
    ├── services/           API service functions
    ├── store/              State management
    └── types/              TypeScript type definitions
```

### Admin Responsibilities

The admin web app handles:

- Admin login and authentication
- Dashboard with key stats and pending actions
- Client management (create, view, edit, deactivate)
- Worker management (create, view, edit, deactivate)
- Job request management (view, approve, reject)
- Worker assignment to jobs and shifts
- Attendance verification
- Complaint management

### Admin UI Library

**shadcn/ui** — component library built on Radix UI primitives and Tailwind CSS.

Use shadcn/ui components for all admin UI elements: buttons, inputs, dialogs, tables, badges, dropdowns, cards, and form fields. Do not build these from scratch.

Install components via the shadcn CLI:

```bash
npx shadcn@latest add <component>
```

Components live in `apps/admin/src/components/ui/`.

### Admin UI Rules

The admin interface should be:

- **Web-first** — designed for desktop browser use
- **Data-rich** — tables, filters, search, and detail views
- **Clean** — not cluttered, clear visual hierarchy
- **Status-driven** — every record shows its current status clearly
- **Action-oriented** — common actions are always visible and reachable

Dashboard should focus on:

- Pending requests needing review
- Active jobs currently in progress
- Workers on shift today
- Attendance records needing verification
- Open complaints needing resolution

---

## Mobile App

**Path:** `apps/mobile-ui-lab`

**Framework:** React Native with Expo

**UI Library:** Tamagui

> **Important:** This is the main mobile app. The deleted `apps/mobile` folder should not be recreated unless explicitly requested.

### Mobile Structure

```
apps/mobile-ui-lab/
├── src/
│   ├── apps/               Role-based app entry points
│   ├── components/         Shared UI components
│   ├── screens/            All screen components
│   └── shared/             Shared hooks, services, utils
├── App.tsx                 Root component
├── package.json
├── tamagui.config.ts       Tamagui design system config
└── gluestack-ui.config.ts  Gluestack config if used
```

### Mobile Responsibilities

**Client role:**

- Login
- Dashboard (active jobs, recent activity)
- Create worker request (step-by-step form)
- View own requests and status
- View assigned workers for own jobs
- View attendance status for own jobs
- Raise and track complaints
- Profile management

**Worker role:**

- Login with phone OTP
- Dashboard (today's job, check-in button)
- View assigned jobs
- Accept or decline job
- View job detail (location, shift, reporting info)
- Check in and check out (GPS verified)
- View own attendance history
- Raise and track complaints
- Profile management

### Mobile UI Rules

The mobile app must be:

- **Simple** — minimal steps for every action
- **Clean** — no visual clutter
- **Fast** — common actions complete in under 3 taps
- **Clear** — non-technical users must understand everything immediately

**Worker app must be extremely simple.**

Worker dashboard should show:

- Today's job (company, location, shift time)
- Current check-in status
- One large, obvious Check In or Check Out button

Worker should be able to check in within 20 seconds of opening the app.

**Client app should feel professional and trustworthy** — appropriate for a business manager or HR professional.

---

## Database

**Type:** PostgreSQL

**Why:** Relational data (workers → jobs → attendance → salary) requires strong relational integrity. PostgreSQL handles complex joins, JSON fields for flexible data like skill tags, and scales reliably.

---

## Notifications

**Push notifications:** Firebase Cloud Messaging (FCM)

The FastAPI backend sends push notifications via FCM when key events occur. React Native apps register an FCM device token on login.

**Email:** SendGrid or Resend for invite links and critical alerts.

---

## File Storage

**Provider:** AWS S3 or Cloudflare R2

Used for:

- Worker profile photos
- Identity documents
- Complaint attachments
- Generated invoice PDFs (future)

FastAPI generates signed URLs for secure time-limited access.

---

## Authentication

**Method:** JWT (JSON Web Tokens)

| Role | Login Method |
|---|---|
| Admin | Email and password (invite-only account creation) |
| Client | Email and password |
| Worker | Phone number and OTP |

Token refresh is handled on the backend. Expired tokens redirect to login.

---

## Architecture Overview

```
React Native (Client App)   ──┐
React Native (Worker App)   ──┤──→  FastAPI Backend API  ──→  PostgreSQL
Next.js (Admin Web App)     ──┘            │
                                           ├──→  FCM (Push Notifications)
                                           ├──→  SendGrid (Email)
                                           └──→  S3 / R2 (File Storage)
```

One FastAPI backend serves all three frontends. Each request is authenticated and role-checked on the backend regardless of which surface made the request.

---

## Environment Rules

- Do not commit `.env` files to version control
- Use `.env.example` with safe placeholder values
- Keep all secrets in environment variables
- Do not expose API keys in code or logs
- Do not expose private tokens
- Never print sensitive data (passwords, tokens, bank details) in logs

---

## Testing Rules

**Backend tests must cover:**

- Happy path for each endpoint
- Invalid input (missing fields, wrong types)
- Unauthorized access (no token)
- Wrong role access (correct token, wrong role)
- Object ownership checks (user accessing another user's data)
- Invalid status transitions
- Required field validation

**Frontend tests must cover:**

- Correct role routing after login
- API error handling (network error, 4xx, 5xx)
- Loading state display
- Empty state display
- Error state display
- Successful action confirmation

---

## Recommended Development Order

1. Understand and inspect existing code before changing anything
2. Stabilise authentication and role-based routing
3. Build client and worker profile management
4. Build job request flow (create, submit, approve, reject)
5. Build worker assignment (assign, accept, decline)
6. Build attendance (check-in, check-out, verify)
7. Build complaints
8. Add notifications
9. Polish empty states, error states, loading states
10. Final end-to-end testing