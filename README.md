# Annai Illam Staffing Platform

Annai Illam is a three-sided manpower/staffing management platform that connects a manpower supply company with their clients and workers.

## What Is This App?

This platform helps a manpower company manage clients, workers, job requests, worker assignments, attendance, and complaints — all in one place.

It replaces manual operations such as:

- WhatsApp messages and phone calls
- Excel attendance sheets
- Paper registers
- Manual complaint tracking

## Who Uses It

| Role | Who They Are | How They Access |
|---|---|---|
| Admin | Manpower company operations team | Next.js web dashboard |
| Client | Companies that hire workers (factories, warehouses, etc.) | React Native mobile app |
| Worker | The person deployed to job sites | React Native mobile app |

## Core MVP Flow

```
Client requests workers
  → Admin reviews the request
  → Admin approves or rejects
  → Admin assigns workers
  → Worker accepts or declines the job
  → Worker checks in and checks out
  → Admin verifies attendance
  → Client tracks job status
  → Client or worker raises complaint if needed
  → Admin resolves complaint
  → Job is completed
```

## Project Structure

```
annai-illam-platform/
│
├── apps/
│   ├── admin/              Next.js admin web dashboard
│   ├── backend/            FastAPI backend API
│   └── mobile-ui-lab/      React Native mobile app (Client + Worker)
│
├── README.md
├── PROJECT_BRIEF.md
├── MVP_SCOPE.md
├── TECH_STACK.md
├── CODEX_INSTRUCTIONS.md
└── ROADMAP.md
```

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI + Python |
| Database | PostgreSQL |
| Admin Web | Next.js + TypeScript |
| Mobile App | React Native + Expo + Tamagui |
| Auth | JWT tokens |
| Notifications | Firebase Cloud Messaging (FCM) |
| File Storage | AWS S3 / Cloudflare R2 |

## MVP Goal

The MVP is complete when this full flow works end to end:

1. Admin creates a client and workers
2. Client creates and submits a worker request
3. Admin approves the request and assigns workers
4. Worker accepts the job, checks in, and checks out
5. Admin verifies attendance
6. Client views job and attendance status
7. Complaints can be raised and resolved by all parties

## Not Included in MVP

The following are intentionally out of scope for Version 1:

- Invoice generation and payment tracking
- Salary automation
- Food and accommodation billing
- PDF report export
- Advanced analytics
- AI worker matching
- In-app chat
- Offline sync
- Multi-branch or multi-language support
- Worker document upload

## Development Rule

**Do not rebuild this project from scratch.**

Always inspect the existing files first and continue from the current architecture.

- Use `apps/backend` for FastAPI backend
- Use `apps/admin` for admin web dashboard
- Use `apps/mobile-ui-lab` for the mobile app