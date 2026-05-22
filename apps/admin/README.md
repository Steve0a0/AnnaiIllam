# Annai Illam Admin

Next.js 15 admin panel for Annai Illam manpower operations.

## Environment Setup

```bash
cp .env.example .env.local
```

Set the following in `.env.local`:

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Backend API base URL, e.g. `http://localhost:8000/api/v1` |
| `NEXT_PUBLIC_APP_ENV` | Environment name: `local`, `staging`, or `production` |

## Run Locally

```bash
# 1. Install dependencies
npm install

# 2. Copy and fill env file
cp .env.example .env.local

# 3. Start the backend (from apps/backend/)
uvicorn app.main:app --reload

# 4. Start the admin dev server
npm run dev
```

App runs at `http://localhost:3000`.

## Scripts

| Command | Purpose |
|---|---|
| `npm run dev` | Start development server |
| `npm run build` | Production build |
| `npm run start` | Serve production build |
| `npm run lint` | Run ESLint |

## Folder Structure

```
src/
├── app/
│   ├── (auth)/login/        # Login page (OTP flow)
│   └── (dashboard)/         # Protected dashboard routes
│       ├── dashboard/
│       ├── requirements/
│       ├── assignments/
│       ├── attendance/
│       ├── payroll/
│       ├── finance/
│       ├── complaints/
│       └── reports/
├── components/
│   ├── layout/              # Sidebar, Topbar, PageShell
│   ├── shared/              # PageHeader, EmptyState, ErrorState, ProtectedRoute
│   └── ui/                  # Button, Input, Textarea, Select, Badge, Card
├── constants/               # menu, roles, statuses
├── features/                # Feature-scoped components (added per module)
├── hooks/                   # Custom React hooks
├── lib/                     # http client, auth-storage, error helpers, utilities
├── services/                # API service files (one per domain)
├── store/                   # Zustand auth store
└── types/                   # TypeScript domain types
```

## Build

```bash
npm run build
npm run start
```
