# Annai Illam Staffing Platform

A three-sided B2B manpower/staffing management platform for industrial and temporary workforce operations.
Replaces WhatsApp, paper registers, and Excel sheets with a structured digital system.

## What It Does

| Role | Access | Responsibilities |
|---|---|---|
| **Admin** | Next.js web dashboard | Review requirements, assign workers, verify attendance, manage payroll, resolve complaints |
| **Client** | React Native mobile app | Create worker requests, track attendance, raise complaints |
| **Worker** | React Native mobile app | Accept jobs, GPS check-in/out, raise issues |

**Core flow:** Client requests workers → Admin approves + quotes → Client pays → Admin assigns → Worker GPS check-in/out → Admin verifies attendance → Payroll generated

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI + Python, PostgreSQL 16, Redis |
| Admin Web | Next.js 16 (App Router) + TypeScript, shadcn/ui |
| Mobile App | React Native + Expo SDK 54, Tamagui (worker) |
| Auth | JWT (30 min access / 30 day refresh) + OTP via MSG91 |
| File Storage | AWS S3 / MinIO (local dev) |
| Payments | Razorpay (gateway) + manual reference payment |
| Monitoring | Sentry (backend + admin) |

## Project Structure

```
apps/
  admin/          Next.js admin web dashboard
  backend/        FastAPI backend API
  mobile-ui-lab/  React Native mobile app (client + worker variants)
docs/
  PROJECT_SKILL.md          AI assistant reference and dev guide
  BUSINESS_RULES.md         Business logic source of truth
  TESTING_GUIDE.md          Test running guide
  MANUAL_QA_CHECKLIST.md    Full manual QA test scripts
  DEPLOYMENT.md             Production deployment runbook
  MVP_AND_PRODUCTION_READINESS.md  Historical audit and gap tracker
```

## Local Setup

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker (for PostgreSQL + MinIO)

### 1. Start the database and storage

```bash
cd apps/backend
docker-compose up -d
```

This starts PostgreSQL 16 on port 5433 and MinIO on port 9000.

### 2. Backend

```bash
cd apps/backend

# Create virtualenv and install
python -m venv venv
venv\Scripts\activate         # Windows
# source venv/bin/activate    # Mac/Linux

pip install -r requirements.txt

# Copy and fill env file
cp .env.example .env

# Run migrations
alembic upgrade head

# Seed the first admin user
make seed-admin EMAIL=admin@example.com PASSWORD=Admin@123 NAME="Admin"

# Start the API server
uvicorn app.main:app --reload
```

API runs at `http://localhost:8000`. OpenAPI docs at `http://localhost:8000/docs` (local only).

### 3. Admin Dashboard

```bash
cd apps/admin
npm install
cp .env.example .env.local
# Set NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1 in .env.local
npm run dev
```

Dashboard runs at `http://localhost:3000`.

### 4. Mobile App

```bash
cd apps/mobile-ui-lab
npm install
cp .env.example .env
# Set EXPO_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1 in .env

npm run clients    # Start client app (Expo)
npm run worker     # Start worker app (Expo)
```

## Key Environment Variables

### Backend (`.env`)

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | `postgresql+psycopg://USER:PASS@localhost:5433/annai_illam` |
| `REDIS_URL` | Yes | `redis://localhost:6379/0` |
| `JWT_SECRET_KEY` | Yes | Strong random secret (min 32 chars) |
| `FIELD_ENCRYPTION_KEY` | Yes | Fernet key for worker bank/UPI data |
| `APP_ENV` | Yes | `local` (enables OpenAPI docs + console OTP) |
| `S3_BUCKET`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | Yes | S3 or MinIO credentials |
| `SMS_PROVIDER` | No | `console` for local dev (OTP printed to terminal) |
| `SENTRY_DSN` | No | Leave empty to disable Sentry locally |

Generate a Fernet encryption key:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Admin (`.env.local`)

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000/api/v1` |
| `NEXT_PUBLIC_APP_ENV` | `local` |

### Mobile (`.env`)

| Variable | Description |
|---|---|
| `EXPO_PUBLIC_API_BASE_URL` | `http://localhost:8000/api/v1` |
| `EXPO_PUBLIC_APP_VARIANT` | `client` or `worker` (set by npm scripts) |

## Running Tests

```bash
# Backend tests
cd apps/backend
python -m pytest -v
python -m ruff check app tests scripts   # lint

# Admin build check
cd apps/admin
npm run lint && npm run build
```

## Useful Backend Commands

```bash
# Seed first admin user
make seed-admin EMAIL=admin@example.com PASSWORD=Admin@123 NAME="Admin"

# Create a migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# PostgreSQL backup to S3
python -m scripts.backup_postgres

# Verify Redis connectivity
python -m scripts.check_redis
```

## Project Docs

| Doc | Purpose |
|---|---|
| [docs/PROJECT_SKILL.md](docs/PROJECT_SKILL.md) | Architecture, how to work safely, common mistakes |
| [docs/BUSINESS_RULES.md](docs/BUSINESS_RULES.md) | Status lifecycles, permissions, enforcement rules |
| [docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md) | Test commands and critical test scenarios |
| [docs/MANUAL_QA_CHECKLIST.md](docs/MANUAL_QA_CHECKLIST.md) | Full manual QA test scripts |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Production deployment runbook |
| [AGENTS.md](AGENTS.md) | AI assistant rules and doc loading order |
| [PERMISSIONS_MATRIX.md](PERMISSIONS_MATRIX.md) | Full role-by-feature permissions table |

## Development Rules

- Do not rebuild `apps/mobile` — it was intentionally deleted. Use `apps/mobile-ui-lab`.
- Admin UI must use shadcn/ui — do not hand-build buttons, tables, dialogs, or inputs.
- All business rules enforced on the backend — frontend checks are UI-only.
- Every DB schema change requires an Alembic migration.
- Read `docs/PROJECT_SKILL.md` before making any significant code changes.
