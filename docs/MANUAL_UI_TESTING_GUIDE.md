# Annai Illam — Manual End-to-End UI Testing Guide

> Generated after full codebase inspection: June 2026
> Apps: Admin Web (`localhost:3000`), Backend API (`localhost:8000`), Mobile (Expo dev client)

---

## Part 1 — Project Understanding

### What is this application?

Annai Illam is a **staffing/manpower platform** that connects **clients** (companies or households that need workers) with **workers** (domestic staff, labourers, security guards, etc.), managed by an **admin team**.

The platform has three separate applications:
- **Admin Web Dashboard** — Next.js app for admin staff to manage the entire business
- **Client Mobile App** — React Native app for clients to create job requests and track them
- **Worker Mobile App** — React Native app for workers to accept jobs, check in/out, track earnings

---

### Who are the users?

| Role | Login Method | App | What they do |
|------|-------------|-----|-------------|
| **Super Admin** | Email + password | Admin web | Everything — full control |
| **Ops Admin** | Email + password | Admin web | Operations — cannot deactivate users or change system settings |
| **Client** | Phone + OTP (mobile login) | Mobile app | Create job requests, view assigned workers, pay invoices, raise complaints |
| **Worker** | Phone + OTP | Mobile app | Accept jobs, check in/out via GPS, view earnings, raise issues |

---

### What can each role do?

**Super Admin:**
- Everything Ops Admin can do
- Invite and deactivate admin accounts
- Modify verified attendance
- Deactivate client and worker accounts
- Change SLA policies and system settings
- View audit log

**Ops Admin:**
- Review and approve/reject job requests
- Send quotes to clients
- Assign workers to approved jobs
- Verify attendance records
- Handle complaints and disputes
- Run payroll
- Confirm client payments

**Client (mobile):**
- Create worker requests (step-by-step form)
- Save as draft or submit immediately
- Accept or reject a quote sent by admin
- Cancel own requests
- View assigned workers (name, skill, check-in status only)
- View attendance status for own jobs (read-only)
- View and pay invoices (Razorpay gateway or manual UTR transfer)
- Rate the service after completion
- Raise complaints and disputes
- Edit own company profile

**Worker (mobile):**
- Onboard with full profile, consent, ID upload
- Accept or decline job assignments
- Check in and check out (GPS-verified against job site)
- View own attendance history
- View own earnings and payment history
- Set availability (days and shifts)
- Raise issues (worker complaints)
- Edit own profile

---

### Full business flow (start to finish)

```
[CLIENT] Creates requirement (job request) → saves DRAFT or submits → status: SUBMITTED
     ↓
[ADMIN] Sees new request on dashboard → opens it → marks UNDER_REVIEW
     ↓
[ADMIN] Sends a quote (price, rate per worker, advance amount, payment model) → status: QUOTED
     ↓
[CLIENT] Receives notification → opens request → accepts or rejects quote
   → Accepted: status: APPROVED
   → Rejected: stays at QUOTED (admin can re-quote)
     ↓
[ADMIN] Assigns workers to the approved job → status: WORKERS_ASSIGNED
     ↓
[WORKER] Receives notification → opens Jobs tab → accepts or declines assignment
   → Declined: admin sees it on Replacements page → assigns replacement worker
     ↓
[WORKER] On shift day → opens app → check in (GPS verified against job site) → status: IN_PROGRESS
     ↓
[WORKER] End of shift → checks out
     ↓
[ADMIN] Reviews attendance → verifies, marks absent, or marks late
     ↓
[ADMIN] Marks job as COMPLETED
     ↓
[ADMIN] Creates invoice → client receives notification
     ↓
[CLIENT] Opens invoice → pays via Razorpay gateway OR records UTR reference for bank transfer
     ↓
[ADMIN] Confirms client payment
     ↓
[ADMIN] Runs payroll → calculates worker pay from verified attendance
     ↓
[ADMIN] Records worker disbursements
     ↓
[CLIENT] Rates the service (1–5 stars + comment) — optional
     ↓
Job is fully closed.

At any stage: Client or Worker can raise a Complaint.
After completion: Client can raise a Dispute.
```

---

### Important modules and their APIs

| Module | Admin UI Route | API Prefix |
|--------|---------------|------------|
| Dashboard | `/dashboard` | `GET /admin/dashboard/summary`, `GET /admin/dashboard/alerts` |
| Job Requests | `/requirements`, `/requirements/[id]` | `GET/POST /admin/requirements`, `POST /admin/requirements/{id}/mark-review`, `/approve`, `/reject`, `/quote` |
| Assignments | `/assignments`, `/assignments/[id]` | `GET /admin/assignments`, `GET/POST /admin/requirements/{id}/assign` |
| Workers | `/workers`, `/workers/[id]` | `GET /admin/people/workers`, `POST /admin/people/workers`, `PATCH /admin/people/workers/{id}` |
| Clients | `/clients`, `/clients/[id]` | `GET /admin/people/clients`, `POST /admin/people/clients`, `PATCH /admin/people/clients/{id}` |
| Attendance | `/attendance` | `GET /admin/attendance`, `POST /admin/attendance/{id}/verify`, `/absent`, `/late` |
| Complaints | `/complaints`, `/complaints/[id]` | `GET /admin/complaints`, `POST /admin/complaints/{id}/in-review`, `/resolve`, `/reject` |
| Replacements | `/replacements` | `GET /admin/complaints/replacements` |
| Disputes | `/disputes`, `/disputes/[id]` | `GET /admin/disputes`, `POST /admin/disputes/{id}/resolve`, `/close` |
| Finance | `/finance` | `GET /admin/finance/client-payments`, `POST /admin/finance/client-payments/{id}/confirm` |
| Payroll | `/payroll`, `/payroll/[id]` | `GET /admin/payroll/runs`, `POST /admin/payroll/runs`, `POST /admin/payroll/runs/{id}/items/{item_id}/...` |
| Reports | `/reports/requirements`, `/reports/assignments`, `/reports/complaints` | `GET /admin/reports/*` |
| Audit Log | `/audit` | `GET /admin/audit` |
| SLA Policies | `/sla` | `GET /admin/sla`, `PUT /admin/sla/{severity}` |
| Admin Users | `/admin-users` | `GET /admin/people/admins`, `POST /admin/people/admins` |
| Settings | `/settings` | `PATCH /me/password`, `POST /auth/logout` |

---

### Status values

**Job Request (Requirement):**
`DRAFT` → `SUBMITTED` → `UNDER_REVIEW` → `QUOTED` → `APPROVED` → `WORKERS_ASSIGNED` → `IN_PROGRESS` → `COMPLETED`
(Also: `REJECTED`, `CANCELLED` at various stages)

**Worker Assignment:**
`ASSIGNED` → `ACCEPTED` or `DECLINED` → (if accepted, eventually) `COMPLETED`
(Also: `REPLACED` when a declined worker is swapped)

**Attendance:**
`NOT_STARTED` → `CHECKED_IN` → `CHECKED_OUT` → `VERIFIED`
(Override: `ABSENT`, `LATE`)

**Complaint:**
`OPEN` → `IN_REVIEW` → `RESOLVED` or `REJECTED`

**Dispute:**
`OPEN` → `UNDER_REVIEW` → `RESOLVED` or `CLOSED`

---

## Part 0 — Fresh Start: Wipe and Rebuild Everything

> Run this section first. Every test in this guide assumes you are starting from a completely empty database with a freshly-seeded superuser. Do not skip this.

### Step 1 — Stop the backend (if running)

```powershell
# Kill any Python process on port 8000
Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty OwningProcess |
  ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
```

### Step 2 — Drop and recreate the database

```powershell
cd f:\Projects\annai-illam-platform\apps\backend

.\venv\Scripts\python.exe -c "
import psycopg
conn = psycopg.connect('postgresql://postgres:annaiillamdb@localhost:5433/postgres', autocommit=True)
cur = conn.cursor()
cur.execute(\"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='annai_illam' AND pid <> pg_backend_pid()\")
cur.execute('DROP DATABASE IF EXISTS annai_illam')
cur.execute('CREATE DATABASE annai_illam')
conn.close()
print('Database wiped and recreated.')
"
```

> **Warning:** This permanently deletes all data — workers, clients, requirements, attendance, invoices, everything. This is intentional for a clean test run.

### Step 3 — Run all migrations

```powershell
cd f:\Projects\annai-illam-platform\apps\backend
$env:DATABASE_URL = "postgresql+psycopg://postgres:annaiillamdb@localhost:5433/annai_illam"
.\venv\Scripts\alembic.exe upgrade head
```

**Expected output:** Alembic applies all migrations. Final line shows `Running upgrade ... -> i9j0k1l2m3n4`.

### Step 4 — Create the superuser from scratch

```powershell
cd f:\Projects\annai-illam-platform\apps\backend
.\venv\Scripts\python.exe -m scripts.seed_admin `
  --email admin@annai-illam.test `
  --password Admin@12345 `
  --name "Super Admin"
```

**Expected output:** `Admin user created: admin@annai-illam.test`

You now have **one account** in the entire system:

| Role | Email | Password |
|------|-------|----------|
| Super Admin | `admin@annai-illam.test` | `Admin@12345` |

All other accounts (Ops Admin, Clients, Workers) are created during testing.

### Step 5 — Start the backend

```powershell
cd f:\Projects\annai-illam-platform\apps\backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Expected output:** `Application startup complete.` on port 8000.

### Step 6 — Start the admin web

```powershell
cd f:\Projects\annai-illam-platform\apps\admin
npm run dev
```

**Expected:** Admin web available at `http://localhost:3000`.

### Step 7 — Verify the setup

Open `http://localhost:8000/api/v1/health` — should return `{ "status": "ok" }`.

Then go to `http://localhost:3000` and log in with `admin@annai-illam.test` / `Admin@12345`.

**If login succeeds and dashboard loads — you are ready to begin testing.**

---

## Part 2 — Test Accounts Reference

All accounts are created during testing — none pre-exist after the fresh start.

| Role | Credential | When Created |
|------|-----------|-------------|
| Super Admin | `admin@annai-illam.test` / `Admin@12345` | Part 0 — seed script |
| Ops Admin | email of your choice / password of your choice | Test Route 26 |
| Client | Phone number of your choice | Test Route 5 (admin creates) + Test Route 6 (client logs in) |
| Worker | Phone number of your choice | Test Route 3 (worker self-registers) |

> In local dev, OTP is **not sent via SMS**. It is printed to the backend console (`uvicorn` terminal). Watch that terminal during mobile login.

> Admin API base: `http://localhost:8000/api/v1`
> Admin web: `http://localhost:3000`
> Mobile: Expo dev client on emulator or device

---

## Part 3 — Individual Manual Test Routes

---

### Test Route 1 — Admin Login and Dashboard Access

**Priority:** Critical
**User Role:** Admin
**Precondition:** Part 0 completed — fresh DB, migrations run, seed_admin.py executed, backend on port 8000, admin web on port 3000

| Step | Action | Expected Result | Bug Watch |
|------|--------|----------------|-----------|
| 1 | Open `http://localhost:3000` | Redirects to `/login` | Blank page, 404, no redirect |
| 2 | Leave fields blank, click Sign In | Validation message appears on both fields | No error shown, form submits |
| 3 | Enter wrong email + wrong password, click Sign In | Error: "Invalid credentials" or similar | App crashes, blank error |
| 4 | Enter correct admin email + password, click Sign In | Redirects to `/dashboard` | Stays on login, 500 error |
| 5 | Check the dashboard loads stats | Stats cards show numbers (may be 0 for empty data) | Blank cards, console 500 errors |
| 6 | Check Priority Actions section | Cards for "Review submitted requests", "Assign workers to approved jobs", "Verify attendance" appear | Empty section, JS error |
| 7 | Refresh the browser | User stays logged in on `/dashboard` | Redirect to login (token not persisted) |
| 8 | Manually visit `http://localhost:3000/` (root) | Redirected to `/dashboard` | Goes to login again |
| 9 | Click avatar / Settings in sidebar | Goes to `/settings` | Navigation broken |
| 10 | Open a new tab, navigate to `http://localhost:3000/dashboard` | Dashboard loads without login prompt | Asked to login again |

**Expected Result:** Admin logs in once and stays logged in. Dashboard shows stats and priority actions.

**Bugs to watch:**
- JWT token not saved to localStorage / cookie
- Token saved but not sent on refresh
- Dashboard shows 0 for everything even with seeded data
- Console errors on dashboard (N+1 API calls visible in network tab)

---

### Test Route 2 — Role-Based Access Control

**Priority:** Critical
**User Role:** Admin, Client, Worker
**Precondition:** All three role accounts exist; apps are running

| Step | Action | Expected Result | Bug Watch |
|------|--------|----------------|-----------|
| 1 | While logged in as Admin, go to `/workers` | Page loads with worker list | 403, blank page |
| 2 | As Admin, manually type a client-only API call in browser DevTools: `GET /api/v1/client/requirements` with admin token | 403 Forbidden | Returns data — CRITICAL security bug |
| 3 | As Admin, call a worker-only API: `POST /api/v1/worker/attendance/check-in` | 403 Forbidden | Returns 200 — CRITICAL security bug |
| 4 | Without logging in, visit `http://localhost:3000/dashboard` directly | Redirected to `/login` | Dashboard loads without auth |
| 5 | Without logging in, visit `http://localhost:3000/requirements` | Redirected to `/login` | Page loads without auth |
| 6 | In mobile (client), log in as a client user | Lands on client Home screen | Lands on wrong screen |
| 7 | As client in mobile, manually deep-link to a worker-only screen (if any) | Navigator prevents it | Worker screen opens for client |
| 8 | As Ops Admin (not Super Admin), try to deactivate a worker via API directly | 403 Forbidden | Succeeds — CRITICAL permission bug |

**Expected Result:** Every role can only access screens and APIs belonging to their role.

---

### Test Route 3 — Worker Registration and Onboarding (Mobile)

**Priority:** Critical
**User Role:** New Worker (no account yet)
**Precondition:** Backend running; mobile app open on worker flow

| Step | Action | Expected Result | Bug Watch |
|------|--------|----------------|-----------|
| 1 | Open mobile app on worker flow | Welcome screen shows | Blank screen, JS error |
| 2 | Tap "Get Started" or "Login" | Goes to Login screen with phone number field | Navigation broken |
| 3 | Enter a valid phone number, tap Send OTP | "OTP sent" message; in dev, OTP shown or logged | Error: "User not found" for new number |
| 4 | Enter wrong OTP (e.g. 000000), tap Verify | Error: "Invalid OTP" | Proceeds with wrong OTP — security bug |
| 5 | Enter the correct OTP | Navigates to Build Profile screen (new user) | Navigates directly to dashboard |
| 6 | On Build Profile: leave name empty, tap Next | Validation error on name field | Proceeds without name |
| 7 | Fill in name, city, state, pick ≥1 skill, pick experience, pick ≥1 available day and shift | All fields accepted | Dropdowns not saving, multi-select broken |
| 8 | Fill in UPI ID field | Field accepts text | Field missing, crash |
| 9 | Tap Submit | Goes to Consent screen | Stays on build profile, spinner hangs |
| 10 | On Consent screen, scroll to bottom, accept consent | Proceeds to Verify Identity screen | Accept button not visible without scroll |
| 11 | On Verify Identity: upload government ID image | Image preview appears | Camera/picker doesn't open, crash |
| 12 | Upload selfie | Selfie preview appears | Crash or "permission denied" |
| 13 | Tap Submit | "Profile Submitted" confirmation screen | API error, no navigation |
| 14 | Profile Submitted screen shows "Pending admin review" | Waiting state shown correctly | Shows dashboard early |
| 15 | Log out and log in again before admin approves | "Under Review" screen shown | Lands on dashboard (skipping approval check) |

**Expected Result:** Worker completes full onboarding and waits for admin approval.

**Bugs to watch:**
- OTP bypass possible
- Profile submitted without mandatory fields
- Navigation jumps past consent or verify identity steps
- Under review screen not shown if token is still valid

---

### Test Route 4 — Admin Approves a New Worker

**Priority:** Critical
**User Role:** Admin
**Precondition:** A worker has submitted their profile (Test Route 3 done)

| Step | Action | Expected Result | Bug Watch |
|------|--------|----------------|-----------|
| 1 | In admin web, go to `/workers` | Worker list shows | List empty, page error |
| 2 | Find the new worker with status "pending" | Worker appears in list | Worker not visible (filtering issue) |
| 3 | Click on the worker to open detail page | Worker profile opens with ID documents | 404, broken link |
| 4 | View uploaded government ID document | Image or download link shown | "No document" even after upload |
| 5 | Click "Approve" button | Worker status changes to "verified" | Button missing, no action |
| 6 | Check that worker receives push notification (check console/logs) | Notification enqueued in logs | No notification logged |
| 7 | Log in to mobile as that worker again | "Biometric Setup" screen shown (first time after approval) | Lands on Under Review again |
| 8 | On Biometric Setup: tap "Enable Biometric Access" | Device biometric prompt appears | Crash, or skips to dashboard |
| 9 | Complete biometric setup | Worker lands on Dashboard | Dashboard blank, restart needed |
| 10 | On next login (biometric check): authenticate with fingerprint/face | Lands directly on Dashboard | OTP asked again instead of biometric |
| 11 | To reject instead: click "Reject" on a different worker | Rejection reason dialog opens | No dialog, instant reject without reason |
| 12 | Enter rejection reason, confirm | Worker status set to rejected; worker sees rejection message on app | Rejected without reason shown |

**Expected Result:** Admin can approve or reject workers. Approved worker goes through biometric setup once.

---

### Test Route 5 — Admin Creates a Client

**Priority:** High
**User Role:** Admin
**Precondition:** Logged in as admin

| Step | Action | Expected Result | Bug Watch |
|------|--------|----------------|-----------|
| 1 | Go to `/clients` | Client list loads | Page error |
| 2 | Click "Add Client" or equivalent button | Create client form/dialog opens | No add button, dialog doesn't open |
| 3 | Leave phone number empty, submit | Validation error | Submits with empty phone |
| 4 | Enter duplicate phone number (already used), submit | Error: "Phone already registered" | Creates duplicate account |
| 5 | Fill in all fields: phone, company name, contact name, city, state, type | Form accepts all | Some fields ignored |
| 6 | Submit | Client created; appears in list | Success toast but not in list; no toast at all |
| 7 | Click on the new client | Client detail page opens | 404 |
| 8 | Click "Edit" | Edit form opens with existing values pre-filled | Form opens blank |
| 9 | Change city, save | City updated, success toast | Old city still shown after save |
| 10 | Try to deactivate as Ops Admin | Should fail (403) — only Super Admin can deactivate | Ops Admin can deactivate — permissions bug |

**Expected Result:** Admin can create and edit clients. Only Super Admin can deactivate.

---

### Test Route 6 — Client Login (Mobile)

**Priority:** Critical
**User Role:** Client
**Precondition:** Client account created by admin (Test Route 5)

| Step | Action | Expected Result | Bug Watch |
|------|--------|----------------|-----------|
| 1 | Open mobile app on client flow, tap Welcome | Welcome screen opens | Blank |
| 2 | Enter phone number, tap Send OTP | OTP sent (shown in dev) | Error: user not found |
| 3 | Enter correct OTP | If new client: goes to Profile Setup. If returning: goes to Home | Wrong screen |
| 4 | On Profile Setup (new client): fill company name, contact name, city | Form accepts | Fields missing |
| 5 | Submit profile | Lands on Client Home screen | 400 error, stays on setup |
| 6 | Client Home shows dashboard summary: active jobs count, recent requirements | Summary cards visible | All zeros even with active data |
| 7 | Pull down to refresh | Summary reloads | Spinner stuck |
| 8 | Go offline (airplane mode), open app | Stale data shown with "Offline" or "Last updated" banner | App shows blank/crash |
| 9 | Come back online, refresh | Fresh data loads, stale banner disappears | Banner stays, data stale |

**Expected Result:** Client logs in, sets up profile, sees dashboard summary.

---

### Test Route 7 — Client Creates a Job Request (Mobile)

**Priority:** Critical
**User Role:** Client
**Precondition:** Client logged in and has profile set up

| Step | Action | Expected Result | Bug Watch |
|------|--------|----------------|-----------|
| 1 | On Home screen, tap "Create Request" or "+" button | Create Request screen opens (step-by-step form) | No button, wrong screen |
| 2 | Step 1 — Job Type: leave category empty, tap Next | Validation error | Proceeds without category |
| 3 | Select "General Labour" as category | Selected | No visual feedback on selection |
| 4 | Step 2 — Location: type a location in the search field | Google Places suggestions appear | No suggestions, crash (check API key) |
| 5 | Select a suggestion | City/state auto-filled | Fields remain empty |
| 6 | Step 3 — Workers: set number of workers to 0, tap Next | Validation: must be ≥ 1 | 0 workers allowed |
| 7 | Set to 3 workers | Accepted | |
| 8 | Step 4 — Schedule: pick a past date as start date | Validation error | Past date accepted |
| 9 | Pick a future date, select duration 30 days | Accepted | |
| 10 | Step 5 — Shift: pick "General: 09:00-18:00" | Selected | |
| 11 | Step 6 — Requirements: toggle Food Required, Accommodation Required | Both toggles work | Toggle state not saved |
| 12 | Set budget amount | Field accepts number | Text accepted in number field |
| 13 | Final step: tap "Save as Draft" | Success message; request appears in My Requests with DRAFT status | No status shown, toast missing |
| 14 | Open the draft request | Edit button visible; all fields pre-filled | Blank form on re-open |
| 15 | Edit the number of workers, save | Updated value shown | Old value shown |
| 16 | Tap "Submit Request" on the draft | Confirmation dialog | No dialog, immediate submit |
| 17 | Confirm submission | Status changes to SUBMITTED; success toast | Status still shows DRAFT |
| 18 | Try to edit after submission | Edit button should be disabled/hidden | Submitted request still editable |
| 19 | Try to cancel the submitted request | Cancel option available | No cancel option |
| 20 | Confirm cancellation | Status changes to CANCELLED | Status stays as SUBMITTED |

**Expected Result:** Client creates a request, saves as draft, edits it, submits it.

**Bugs to watch:**
- Google Places API key not set (no suggestions)
- Past start date allowed
- Draft not saved properly (lost on navigation)
- Submit with missing required fields
- Status not updating after submit

---

### Test Route 8 — Admin Reviews and Approves a Request

**Priority:** Critical
**User Role:** Admin
**Precondition:** Client has submitted a request (Test Route 7)

| Step | Action | Expected Result | Bug Watch |
|------|--------|----------------|-----------|
| 1 | On admin dashboard, check Priority Actions | "Review submitted requests" count > 0 | Still shows 0 (cache issue) |
| 2 | Click the card or go to `/requirements` | Requirements list loads | Blank list even with submitted request |
| 3 | Filter by "Submitted" | Only submitted requests shown | Filter has no effect |
| 4 | Click on the submitted request | Detail page loads with all fields | 404 error |
| 5 | Check all submitted fields are displayed | Category, location, workers, schedule, shift, budget all visible | Some fields missing |
| 6 | Click "Mark as Under Review" | Status changes to UNDER_REVIEW; button disappears | Button stays, no status change |
| 7 | In Requests list, verify badge shows "Under Review" | Badge updated | Badge still shows "Submitted" |
| 8 | Back on detail page, click "Reject" | Dialog opens asking for rejection reason | Dialog missing, instant reject |
| 9 | Type a rejection reason, confirm | Status → REJECTED; reason stored | No reason stored, no confirmation |
| 10 | Create a new submitted request to test approve flow | New request in SUBMITTED status | |
| 11 | Mark it under review, then click "Send Quote" | Quote form opens with fields: amount, rate per worker, advance, payment model, valid until, terms | Form blank, wrong dialog |
| 12 | Leave quoted_amount empty, submit quote | Validation error | Quote sent without amount |
| 13 | Fill in all quote fields, submit | Status → QUOTED; quote details shown on detail page | No status change |
| 14 | Check client mobile app shows a notification | Notification appears in client app | No notification |
| 15 | Admin re-opens requirement — quote section visible | Quote panel shows with Accept/Reject buttons on client side | Quote not shown |

**Expected Result:** Admin marks requests under review, sends quote, sees status update.

---

### Test Route 9 — Client Accepts or Rejects a Quote (Mobile)

**Priority:** Critical
**User Role:** Client
**Precondition:** Admin has sent a quote (Test Route 8)

| Step | Action | Expected Result | Bug Watch |
|------|--------|----------------|-----------|
| 1 | Open client app, go to Requests tab | Requirement shows QUOTED status | Still shows UNDER_REVIEW |
| 2 | Tap on the requirement | Detail screen opens; Quote section visible at bottom | No quote section shown |
| 3 | Quote section shows: total amount, rate per worker, advance amount, payment model, valid until | All quote fields displayed | Some missing |
| 4 | Check if quote has expired (past valid_until date) | Quote should show "Expired" state | Expired quote still shows Accept button |
| 5 | Tap "Reject Quote" | Confirmation dialog | Immediate reject without confirmation |
| 6 | Confirm rejection | Status stays UNDER_REVIEW (or back to earlier); admin can re-quote | Status goes to wrong state |
| 7 | Admin sends another quote | New quote visible in client app | Old quote shown |
| 8 | Client taps "Accept Quote" | Confirmation dialog | No dialog |
| 9 | Confirm acceptance | Status → APPROVED; success toast | No status change |
| 10 | If advance payment required: "Pay Advance" button appears | Button visible | Button missing |
| 11 | Tap "Pay Advance" | Invoice detail screen opens showing advance amount | Blank invoice |

**Expected Result:** Client accepts quote; status moves to APPROVED.

---

### Test Route 10 — Admin Assigns Workers to an Approved Job

**Priority:** Critical
**User Role:** Admin
**Precondition:** Requirement is in APPROVED status; at least one verified worker exists

| Step | Action | Expected Result | Bug Watch |
|------|--------|----------------|-----------|
| 1 | Go to `/requirements`, filter by "Approved" | Approved requirement visible | No filter for Approved |
| 2 | Click on the requirement | Detail page with "Assign Workers" section | No assignment section on Approved status |
| 3 | In Assign Workers section, search for a worker | Worker list filtered by name/skill/city | Search does nothing |
| 4 | Try to assign an unavailable worker | Warning shown | Unavailable worker assigned silently |
| 5 | Select a verified, available worker | Worker card highlighted | No selection state |
| 6 | Set shift/role for the worker if prompted | Fields appear for shift details | No shift fields |
| 7 | Click "Assign" | Worker assigned; status → WORKERS_ASSIGNED | Status not updating |
| 8 | Assign a second worker to same job | Both workers shown in assignment list | Second assignment replaces first |
| 9 | Try to assign same worker twice to same job | Error: "Already assigned" | Duplicate assignment created |
| 10 | In `/assignments` list, verify new assignments appear | Assignments shown with ASSIGNED status | List empty |
| 11 | Click on an assignment | Assignment detail opens with worker info, requirement info | 404 |
| 12 | Try to remove an assignment from detail | Remove button present | No remove button |
| 13 | Confirm removal | Assignment removed; re-appears as replaceable | Assignment stays, no feedback |

**Expected Result:** Admin assigns workers; status moves to WORKERS_ASSIGNED.

---

### Test Route 11 — Worker Accepts or Declines a Job (Mobile)

**Priority:** Critical
**User Role:** Worker
**Precondition:** Worker has been assigned to a job (Test Route 10); worker app open

| Step | Action | Expected Result | Bug Watch |
|------|--------|----------------|-----------|
| 1 | Open worker app Home screen | "You have a new assignment" card visible, or Jobs tab has a badge | No notification visible |
| 2 | Go to Jobs tab | Assignment listed with ASSIGNED status | Empty jobs list |
| 3 | Tap on the job | Job Detail screen opens with: location, shift time, role, food/accommodation info | Blank detail screen |
| 4 | Check location is shown with map link or address | Address visible | No location shown |
| 5 | Check shift details shown | Shift time and dates visible | No shift info |
| 6 | Tap "Decline" | Confirmation dialog | Immediate decline |
| 7 | Confirm decline | Status → DECLINED; job removed from list | Still shown in list |
| 8 | Admin sees replacement needed (check admin replacements page) | Replacement request visible at `/replacements` | Not visible |
| 9 | Admin assigns a replacement worker | New worker assigned | Error, no replacement flow |
| 10 | Second worker opens app, accepts the job | Tap "Accept" | Accept button missing |
| 11 | Confirm acceptance | Status → ACCEPTED; job moves to accepted state | No state change |
| 12 | On Home screen, job summary card shows for today | Today's job card visible on Home | Card not showing |

**Expected Result:** Worker accepts a job; it appears on their Home dashboard for the shift day.

---

### Test Route 12 — Worker Check-In and Check-Out (Mobile)

**Priority:** Critical — requires GPS/physical device
**User Role:** Worker
**Precondition:** Worker has ACCEPTED assignment; shift date is today; device has GPS

| Step | Action | Expected Result | Bug Watch |
|------|--------|----------------|-----------|
| 1 | On shift day, open worker Home | Today's job card shown with "Check In" button | No card, or button disabled before shift |
| 2 | Tap "Check In" with GPS disabled | Permission prompt or error | Checks in without GPS (geofence bypass) |
| 3 | Enable GPS, tap "Check In" | Location captured | GPS error even with permission |
| 4 | If location is outside geofence (> radius): | Error: "You are not at the job site" | Allows check-in from anywhere |
| 5 | If selfie required: camera opens | Camera permission prompt appears, then camera | Camera crash |
| 6 | Take selfie, confirm | Selfie uploaded | Upload fails, no feedback |
| 7 | Confirm check-in | Success toast; "Checked In" status shown; Check Out button appears | Success toast but no status change |
| 8 | Try to check in again (double check-in) | Error: "Already checked in today" | Creates duplicate attendance record |
| 9 | At end of shift, tap "Check Out" | Check Out button visible | Not visible after check-in |
| 10 | If geofence required: must be at job site | Same geofence validation | Checkout allowed from anywhere |
| 11 | Confirm checkout | Attendance status → CHECKED_OUT | Stays CHECKED_IN |
| 12 | Go to Attendance History tab | Today's record shows with check-in and check-out times | Record missing |

**Expected Result:** Worker checks in and out. GPS verified (if geofence enabled). Attendance record created.

**GPS Note:** This test requires a physical device or emulator with mocked GPS coordinates near the job site.

---

### Test Route 13 — Admin Verifies Attendance

**Priority:** Critical
**User Role:** Admin
**Precondition:** Workers have checked in and out (Test Route 12); attendance records exist

| Step | Action | Expected Result | Bug Watch |
|------|--------|----------------|-----------|
| 1 | Go to `/attendance` | Attendance list loads; defaults to today's date | Shows blank list even with records |
| 2 | Check the date filter defaults to today | Today's date pre-selected | No date filter |
| 3 | Filter by requirement_id | Records filtered to that job | Filter has no effect |
| 4 | Filter by status "CHECKED_OUT" | Only checked-out records shown | Shows all statuses |
| 5 | Click "Verify" on a CHECKED_OUT record | Status → VERIFIED; button changes | No button, status not updating |
| 6 | Bulk verify (if available) | Multiple records verified at once | Only single verify works |
| 7 | Mark a CHECKED_IN record as "Absent" | Dialog for reason | Absent without reason |
| 8 | Mark a late arrival | Status → LATE | No LATE status available |
| 9 | Try to modify a VERIFIED record as Ops Admin | Should fail (only Super Admin can modify verified) | Ops Admin can modify — permissions bug |
| 10 | Super Admin modifies a VERIFIED record | Correction dialog with reason | No correction option |
| 11 | Check audit log after verification actions | Audit log shows verify/absent/late events | No audit entries |

**Expected Result:** Admin can verify, override attendance. Verified records locked for Ops Admin.

---

### Test Route 14 — Admin Completes a Job

**Priority:** Critical
**User Role:** Admin
**Precondition:** All attendance verified; job is IN_PROGRESS

| Step | Action | Expected Result | Bug Watch |
|------|--------|----------------|-----------|
| 1 | Go to `/requirements`, find IN_PROGRESS requirement | Requirement shows IN_PROGRESS badge | Not found |
| 2 | Open requirement detail | "Mark as Completed" button visible | No complete button shown for IN_PROGRESS |
| 3 | Click "Mark as Completed" | Confirmation dialog | Immediate completion |
| 4 | Confirm | Status → COMPLETED | Status not changing |
| 5 | Verify client mobile shows COMPLETED status | Request detail shows COMPLETED timeline | Old status cached |
| 6 | Verify workers see COMPLETED on their Jobs screen | Job shows completed | Still shows as active |
| 7 | Check that Rating prompt appears for client | After completion, "Rate this service" prompt appears in client app | No rating prompt |

**Expected Result:** Job is marked complete. All parties see final status.

---

### Test Route 15 — Admin Creates Invoice and Client Pays

**Priority:** High
**User Role:** Admin, then Client
**Precondition:** Job is COMPLETED; quote exists

| Step | Action | Expected Result | Bug Watch |
|------|--------|----------------|-----------|
| 1 | Admin: go to requirement detail for COMPLETED job | "Create Invoice" button visible | No invoice section |
| 2 | Click "Create Invoice" | Invoice generated with number (INV-2026-0001), GST, total | Error creating invoice |
| 3 | Invoice number is unique and follows pattern INV-YEAR-XXXX | Correct format | Duplicate invoice number |
| 4 | Invoice appears in client mobile app | Client sees invoice in Request Detail | No invoice shown |
| 5 | Client: tap on invoice | Invoice Detail screen opens: subtotal, GST, total, due date | Blank invoice screen |
| 6 | Payment model is "platform_bills_client" | Pay button visible | No pay button (wrong payment model) |
| 7 | Tap "Pay via Razorpay" | Razorpay checkout WebView opens | WebView crash, blank checkout |
| 8 | Complete test payment (use Razorpay test card) | Payment success webhook fires; payment confirmed | Webhook not received (check ngrok/tunnel setup) |
| 9 | Alternatively: select "Pay via Bank Transfer" | UTR reference input appears | No bank transfer option |
| 10 | Enter a UTR reference (e.g. "UPI12345ABC"), tap Confirm | Payment record created with PENDING status | Error or no record |
| 11 | Admin: go to `/finance` tab "Incoming Payments" | Payment appears with PENDING status | Payment not visible |
| 12 | Admin: click "Confirm" on the payment | Status → PAID; success toast | Confirm button missing |
| 13 | Admin: click "Reject" on a pending payment | Status → FAILED; reason logged | No reject option |
| 14 | Client: check payment history in app | Payment shows as confirmed | Still shows pending |

**Expected Result:** Invoice created, client pays, admin confirms. Payment flow end to end.

**Note:** Razorpay webhook requires a publicly accessible URL (ngrok or tunnel). For local testing, use manual UTR flow instead.

---

### Test Route 16 — Admin Payroll for Workers

**Priority:** High
**User Role:** Admin
**Precondition:** Job COMPLETED; attendance verified

| Step | Action | Expected Result | Bug Watch |
|------|--------|----------------|-----------|
| 1 | Go to `/payroll` | "Ready to Pay" list shows completed requirements | Empty list |
| 2 | Click on a completed requirement | Navigate to payroll detail for that requirement | 404 |
| 3 | In `/payroll/[id]`, view workers and their attendance summary | Each worker shows verified days, absent days, gross amount | Worker list empty |
| 4 | Add a deduction (e.g. advance deduction) | Deduction form opens with type and amount | No deduction option |
| 5 | Save deduction | Net amount recalculated | Gross shown but net not updating |
| 6 | Click "Lock and Run Payroll" | Payroll run created; items locked | Lock has no effect |
| 7 | Try to modify attendance after payroll locked | Should fail: "Payroll locked for this period" | Modification allowed after lock |
| 8 | In `/finance` Payroll Queue tab | Payroll run appears with worker items | Queue empty |
| 9 | Trigger disbursement for one worker | Disbursement queued | Error or no feedback |
| 10 | Mark run as PAID | Run status → PAID | Status not updating |
| 11 | Worker: check Earnings tab in mobile | Earnings showing with amount and dates | Blank earnings |
| 12 | Worker: check Payments tab | Payment record visible | No payment records |

**Expected Result:** Admin runs payroll; workers see earnings in app.

---

### Test Route 17 — Raise and Resolve a Complaint

**Priority:** High
**User Role:** Client (or Worker), then Admin
**Precondition:** Active or completed job exists

| Step | Action | Expected Result | Bug Watch |
|------|--------|----------------|-----------|
| 1 | Client mobile: go to Complaints tab | Complaints list (may be empty) | Page crash |
| 2 | Tap "Raise Complaint" | Form opens with: type, description, severity, optional requirement link | Form blank |
| 3 | Leave description empty, tap Submit | Validation error | Complaint submitted without description |
| 4 | Fill in description, select severity (High), submit | Complaint created with OPEN status | Error 400 |
| 5 | Complaint appears in Complaints tab with OPEN badge | Visible in list | Not visible |
| 6 | Admin: go to `/complaints` | All complaints visible including new one | New complaint not showing |
| 7 | Click on the complaint | Detail page opens with full info | 404 |
| 8 | Click "Mark as In Review" | Status → IN_REVIEW | No button |
| 9 | Click "Resolve" | Resolution form opens; enter resolution notes | Form missing |
| 10 | Submit resolution | Status → RESOLVED; client notified | Status not changing |
| 11 | Client: check complaint in app | Shows RESOLVED with resolution notes | Still shows OPEN |
| 12 | Admin: click "Reject" on a different complaint | Rejection dialog | No reject option |
| 13 | Confirm rejection | Status → REJECTED | Status not updating |
| 14 | Worker: go to Issues tab, tap "Raise Issue" | Issue form opens | Crash |
| 15 | Submit a worker issue | Issue created | 400 error |

**Expected Result:** Both client and worker can raise complaints/issues. Admin can review and resolve them.

---

### Test Route 18 — Raise and Resolve a Dispute (Client)

**Priority:** High
**User Role:** Client, then Admin
**Precondition:** Completed requirement exists

| Step | Action | Expected Result | Bug Watch |
|------|--------|----------------|-----------|
| 1 | Client mobile: open a COMPLETED requirement detail | "Raise Dispute" option visible | Option missing |
| 2 | Tap Raise Dispute | Dispute form opens | Navigation crash |
| 3 | Enter dispute reason, submit | Dispute created with OPEN status | 400 error |
| 4 | Admin: go to `/disputes` | Dispute visible in list | Not visible |
| 5 | Filter by "Open" | Only open disputes shown | Filter broken |
| 6 | Open dispute detail | Shows requirement info, dispute reason, client name | 404 |
| 7 | Click "Mark Under Review" | Status → UNDER_REVIEW | No action |
| 8 | Click "Resolve" with resolution notes | Status → RESOLVED | Missing resolve option |
| 9 | Click "Close" (without resolving) | Status → CLOSED | No close option |

**Expected Result:** Dispute raised, admin resolves or closes it.

---

### Test Route 19 — Worker Replacement Flow

**Priority:** High
**User Role:** Admin
**Precondition:** A worker has DECLINED an assignment

| Step | Action | Expected Result | Bug Watch |
|------|--------|----------------|-----------|
| 1 | Go to `/replacements` | List of replacement requests visible | Empty page |
| 2 | Find the DECLINED assignment | Shows original worker name, requirement, decline reason | No decline reason shown |
| 3 | In the original requirement detail, assignment shows DECLINED | Badge: DECLINED | Badge: ASSIGNED (stale) |
| 4 | Admin re-assigns by picking a new worker | Assignment form opens for replacement | No replacement option in detail view |
| 5 | Assign new worker | New assignment created; old one marked REPLACED | Error creating replacement |
| 6 | Check `/assignments` — original shows REPLACED, new shows ASSIGNED | Status correct | Both show ASSIGNED |

---

### Test Route 20 — Dashboard Stats and Alerts

**Priority:** High
**User Role:** Admin
**Precondition:** Some data exists (requirements, workers, attendance)

| Step | Action | Expected Result | Bug Watch |
|------|--------|----------------|-----------|
| 1 | Go to `/dashboard` | Stat cards show: pending requests, active jobs, workers on shift, open complaints | All zeros even with data |
| 2 | Stat: "Pending Requests" matches count at `/requirements` filtered by SUBMITTED | Numbers match | Numbers different |
| 3 | Stat: "Workers On Shift" matches CHECKED_IN attendance for today | Numbers match | Doesn't match |
| 4 | Alerts section: "Missing Attendance" shows workers with no check-in today | Correct alert count | Over/under counting |
| 5 | Click a Priority Action card | Navigates to the correct page with pre-filter | No navigation |
| 6 | Check Recent Activity section | Shows latest actions in time order | Blank or wrong order |
| 7 | Refresh the dashboard | Data reloads | Stale data (no refresh) |

---

### Test Route 21 — Search, Filter, and Sort

**Priority:** High
**User Role:** Admin

| Step | Action | Expected Result | Bug Watch |
|------|--------|----------------|-----------|
| 1 | Requirements page: type a category in search box | List filters in real-time | No filtering |
| 2 | Search by requirement ID (e.g. "12") | Only that requirement shown | All results returned |
| 3 | Search by city | Only requirements from that city | No match |
| 4 | Click status filter "Submitted" | Only submitted shown | Filter resets on click |
| 5 | Combine search text + status filter | Both filters applied | One overrides the other |
| 6 | Clear search text | All requirements (filtered by status) return | List stays filtered |
| 7 | Workers page: search by name | Workers filtered by name | No match |
| 8 | Workers page: search by city | Workers from that city | No match |
| 9 | Assignments page: filter by "Declined" | Only declined assignments shown | All statuses shown |
| 10 | SLA-breached requirements sorted to top | Red badge requirements appear at top | Random order |

---

### Test Route 22 — Form Validation

**Priority:** Medium
**User Role:** Admin, Client

| Step | Action | Expected Result | Bug Watch |
|------|--------|----------------|-----------|
| 1 | Admin login: submit empty email + password | "Required" errors on both fields | Submits empty |
| 2 | Admin login: enter valid email, wrong password format (no @) | Validation error before API call | Hits API with bad email |
| 3 | Create worker: phone with letters (abc123) | Validation error | Letters accepted in phone field |
| 4 | Create requirement (client): workers = 0 | "Must be at least 1" error | 0 workers submitted |
| 5 | Create requirement: start date in the past | Validation error | Past date accepted |
| 6 | Send quote: amount = 0 | Validation error | 0-amount quote created |
| 7 | Change password: new password < 8 chars | Validation error | Short password accepted |
| 8 | Change password: confirm password doesn't match | "Passwords don't match" error | Mismatched passwords saved |
| 9 | Worker profile: UPI ID with spaces | Trimmed or validated | Spaces saved in UPI ID |

---

### Test Route 23 — Empty State Testing

**Priority:** Medium
**User Role:** Admin
**Precondition:** Use a fresh database or filter to show 0 results

| Step | Action | Expected Result | Bug Watch |
|------|--------|----------------|-----------|
| 1 | `/requirements` with no requirements in DB | Empty state: "No requests yet" with icon | Blank page, spinner forever |
| 2 | `/workers` with no workers | Empty state with add button | Blank |
| 3 | `/clients` with no clients | Empty state with add button | Blank |
| 4 | `/attendance` for a date with no records | "No attendance records for this date" | Error thrown |
| 5 | `/complaints` with no complaints | Empty state | Crash |
| 6 | Client mobile: no requests yet | "Create your first request" prompt | Spinner forever |
| 7 | Worker mobile: no jobs assigned | "No jobs yet" message | Blank |
| 8 | Worker Attendance History: no records | "No attendance history" | Crash |

---

### Test Route 24 — Error State and API Failure Handling

**Priority:** Medium
**User Role:** Any

| Step | Action | Expected Result | Bug Watch |
|------|--------|----------------|-----------|
| 1 | Stop the backend, open `/dashboard` | "Could not load" error state with retry button | Infinite spinner, no error |
| 2 | Click Retry | Error state persists until server back | Crash on retry |
| 3 | Stop backend during form submit (Create Client) | Error toast: "Network error" or "Server error" | Spinner never stops, form locked |
| 4 | Restart backend, retry the form | Form submits successfully | Already locked, need refresh |
| 5 | Submit invalid payload directly via DevTools (e.g. workers = -1) | 422 Unprocessable Entity; error shown | 500 crash without user message |
| 6 | Simulate 401 Unauthorized (expired token) | Redirect to login | Blank page, 401 shown as text |
| 7 | Mobile: backend down → open app | Cached data shown with offline banner | App crashes |
| 8 | Attempt login with server down | "Cannot connect to server" message | App hangs |

---

### Test Route 25 — Settings: Change Password and Logout

**Priority:** High
**User Role:** Admin

| Step | Action | Expected Result | Bug Watch |
|------|--------|----------------|-----------|
| 1 | Go to `/settings` | Admin profile shown (name, email, role) | Blank, 404 |
| 2 | Change Password: enter wrong current password | Error: "Current password is incorrect" | Password changed with wrong current |
| 3 | Change Password: new = confirm (both valid), current correct | Password changed; success toast | Error even with correct data |
| 4 | Try to log in with old password | Rejected | Old password still works — security bug |
| 5 | Try to log in with new password | Success | New password rejected |
| 6 | Click "Sign Out" | Confirmation dialog or immediate logout | No logout button |
| 7 | After logout: go back in browser | Redirected to login | Dashboard still accessible |
| 8 | After logout: access token rejected | 401 on any authenticated API call | Old token still works |

---

### Test Route 26 — Admin Users and Permissions

**Priority:** High
**User Role:** Super Admin
**Precondition:** Logged in as Super Admin

| Step | Action | Expected Result | Bug Watch |
|------|--------|----------------|-----------|
| 1 | Go to `/admin-users` | Current admin users listed | Page only visible to Super Admin; Ops Admin gets 403 |
| 2 | Click "Create User" | Dialog opens with email, name, password, permission group fields | Dialog missing |
| 3 | Create an Ops Admin account | New user appears in list with Ops Admin badge | User not created, no email field validation |
| 4 | Log in as the new Ops Admin | Lands on dashboard | Login fails |
| 5 | As Ops Admin: navigate to Admin Users | 403 / redirect | Admin Users page accessible (permissions bug) |
| 6 | As Ops Admin: try to deactivate a worker | 403 error | Worker deactivated — permissions bug |
| 7 | As Super Admin: assign scoping to Ops Admin (specific clients only) | Scoping applied | No scoping option visible |
| 8 | Scoped Ops Admin: view requirements | Only requirements from scoped clients visible | All requirements visible |
| 9 | Delete (deactivate) the test Ops Admin account | Account deactivated | No delete option |

---

### Test Route 27 — Reports and Export

**Priority:** Medium
**User Role:** Admin

| Step | Action | Expected Result | Bug Watch |
|------|--------|----------------|-----------|
| 1 | Go to `/reports` | Three report cards: Requirements, Assignments, Complaints | Page 404 |
| 2 | Click "Requirements" | Requirements report page loads with table/list | 404 |
| 3 | Filter by date range or status | Filtered results shown | Filters missing |
| 4 | Click "Export CSV" or "Export" button | CSV downloaded | No export button |
| 5 | Open CSV — verify columns are correct | ID, category, city, status, start date | Empty CSV, wrong columns |
| 6 | Check Assignments report | Workers, requirements, salaries shown | Blank |
| 7 | Check Complaints report | Complaint type, severity, resolution status shown | Blank |

---

### Test Route 28 — Audit Log

**Priority:** Low
**User Role:** Admin

| Step | Action | Expected Result | Bug Watch |
|------|--------|----------------|-----------|
| 1 | Go to `/audit` | Audit events listed in reverse chronological order | Blank, or very old events |
| 2 | Perform an action (e.g. approve a requirement) | New audit event appears at top within seconds | Event not logged |
| 3 | Search the audit log by keyword | Matching events shown | Search does nothing |
| 4 | Check event categories: Auth, Write, Delete, System | Category badges colour-coded | All same colour |
| 5 | Click on an event | Full detail expanded inline | No expand, wrong data |

---

### Test Route 29 — SLA Policies

**Priority:** Low
**User Role:** Admin

| Step | Action | Expected Result | Bug Watch |
|------|--------|----------------|-----------|
| 1 | Go to `/sla` | SLA policies shown for Critical, High, Medium, Low severities | Blank, 404 |
| 2 | Each severity shows resolution time in hours | Numbers shown | Blank values |
| 3 | Edit "Critical" resolution time | Input field editable | Read-only, no edit |
| 4 | Save change | New SLA value saved; success toast | Error, value reverts |
| 5 | Raise a Critical complaint | SLA timer starts | No SLA tracking visible |

---

### Test Route 30 — Mobile: Worker Availability

**Priority:** Medium
**User Role:** Worker

| Step | Action | Expected Result | Bug Watch |
|------|--------|----------------|-----------|
| 1 | Worker: go to Profile tab → Availability | Availability screen opens | No availability option |
| 2 | Toggle off "Available" | Status set to unavailable; admin sees worker as unavailable | Toggle has no API effect |
| 3 | Toggle back on | Available again | |
| 4 | Change available days (remove Saturday) | Preference saved | Not saving to API |
| 5 | Change available shifts | Preference saved | |
| 6 | Admin: try to assign unavailable worker | Warning or block | Assigned silently |

---

### Test Route 31 — Refresh and Back Button Behaviour

**Priority:** Medium
**User Role:** Any

| Step | Action | Expected Result | Bug Watch |
|------|--------|----------------|-----------|
| 1 | Admin: navigate deep: `/requirements/[id]` | Page loads correctly | 404 on direct URL |
| 2 | Refresh the page | Page reloads with same data | Login redirect (token lost on refresh) |
| 3 | Press browser Back | Goes to `/requirements` list | Goes to `/dashboard` or blank |
| 4 | Admin: open dialog, press browser Back | Dialog closes; stays on current page | Navigates away from page |
| 5 | Mobile client: go deep into CreateRequest (step 5 of 6), press back | Goes to step 4 | Goes to Home |
| 6 | Mobile worker: check in, press back | Stays on Home (already checked in) | Check-in state lost |
| 7 | Mobile: kill app and reopen | User still logged in; lands on correct screen | Logged out every time |

---

### Test Route 32 — Notifications and Toast Messages

**Priority:** Medium
**User Role:** Any

| Step | Action | Expected Result | Bug Watch |
|------|--------|----------------|-----------|
| 1 | Admin performs approve action | Green success toast appears, disappears after ~3s | No toast, toast stays forever |
| 2 | Action fails | Red error toast with descriptive message | Generic "Error" with no detail |
| 3 | Admin: create client with duplicate phone | Error toast: "Phone already registered" | Generic error |
| 4 | Client accepts quote | Toast: "Quote accepted" | No feedback |
| 5 | Worker accepts job | Toast: "Job accepted" | No feedback |
| 6 | Push notification (physical device): admin approves a requirement | Client receives push notification | No notification received |
| 7 | Admin dashboard bell icon: notification count updates | Count matches unread notifications | Count stuck at 0 |

---

### Test Route 33 — Client Rating

**Priority:** Low
**User Role:** Client
**Precondition:** Job is COMPLETED

| Step | Action | Expected Result | Bug Watch |
|------|--------|----------------|-----------|
| 1 | Client: open COMPLETED requirement | "Rate this service" option visible | No rating option |
| 2 | Tap Rate Service | Star rating screen (1–5 stars) | Crash |
| 3 | Tap 0 stars, submit | Validation: "Please select a rating" | 0-star rating submitted |
| 4 | Tap 4 stars, add a comment | Comment field accepts text | |
| 5 | Submit | Rating saved; success message | 400 error |
| 6 | Try to rate again | "Already rated" message | Second rating allowed (bug) |
| 7 | Admin: check if rating is visible anywhere in admin UI | Should be somewhere on requirement detail | Not surfaced in admin UI |

---

## Part 4 — Master End-to-End Flow

# Master End-to-End Manual Testing Flow

This is the complete business journey. Follow every step in order. Start from an absolutely empty database.

**Total time:** ~60–90 minutes
**Accounts needed:** None pre-exist. All created during the flow.

---

### Phase 0: System Reset (Start Here)

1. Run all steps in **Part 0** of this guide (wipe DB → migrate → seed admin → start backend → start admin web).
2. Verify `http://localhost:8000/api/v1/health` returns `{ "status": "ok" }`.
3. Verify `http://localhost:3000` redirects to `/login`.
4. **Expected:** Login page shows. Backend terminal shows `Application startup complete.`
5. Log in at `http://localhost:3000` with `admin@annai-illam.test` / `Admin@12345`.
6. **Expected:** Redirected to `/dashboard`. All stat cards show **0**. Priority Actions are empty. This confirms the database is completely fresh.

---

### Phase 1: Worker Onboarding

1. Open mobile app (worker flow). Tap Welcome.
2. Enter a fresh phone number. Tap Send OTP.
3. Backend console shows OTP. Enter it on the Verify OTP screen.
4. Fill in Build Profile: name, city, state, 2+ skills, experience, available days and shifts.
5. Submit profile → lands on Consent screen.
6. Accept consent → lands on Verify Identity.
7. Upload a government ID image + selfie.
8. Submit → lands on "Profile Submitted" screen.
9. **Expected:** App shows "Under Review" if you log out and back in.

### Phase 2: Admin Reviews Worker

10. Open admin web. Login: `admin@annai-illam.test` / `Admin@12345`.
11. Go to `/workers`. Find the new pending worker.
12. Open worker detail. View uploaded ID documents.
13. Click Approve.
14. **Expected:** Worker status → verified.

### Phase 3: Worker Biometric Setup

15. Open worker app. Log in with same phone number.
16. **Expected:** Biometric Setup screen appears.
17. Tap "Enable Biometric Access". Complete device biometric auth.
18. **Expected:** Worker lands on Dashboard.

### Phase 4: Admin Creates a Client

19. In admin web → `/clients`. Click Add Client.
20. Fill in: phone, company name, contact name, city, state, type = company.
21. Save.
22. **Expected:** Client appears in list with correct details.

### Phase 5: Client Login

23. Open mobile app (client flow). Enter client's phone number.
24. Enter OTP. Complete profile setup (if first time): company name, contact name, city.
25. **Expected:** Client lands on Home screen with empty dashboard.

### Phase 6: Client Creates a Job Request

26. Tap "Create Request" on client Home.
27. Fill in all steps: category = "General Labour", location (Chennai), 2 workers, future start date, 30 days, General shift, food required.
28. Tap "Save as Draft" → verify DRAFT status in My Requests.
29. Re-open the draft. Edit workers to 3.
30. Tap "Submit Request". Confirm.
31. **Expected:** Status → SUBMITTED. Admin should see new request.

### Phase 7: Admin Reviews Request

32. In admin web, dashboard should show 1 pending request.
33. Go to `/requirements`. Find the SUBMITTED request.
34. Open it. Click "Mark as Under Review".
35. **Expected:** Status → UNDER_REVIEW.
36. Click "Send Quote": fill in quoted_amount = 45000, rate_per_worker = 5000, advance_amount = 10000, payment_model = platform_bills_client, valid_until = 7 days from now.
37. Submit quote.
38. **Expected:** Status → QUOTED. Client receives push notification.

### Phase 8: Client Accepts Quote

39. On client app, open the requirement. Find the Quote section.
40. Check: total = 45000, advance = 10000.
41. Tap "Accept Quote". Confirm.
42. **Expected:** Status → APPROVED.

### Phase 9: Admin Assigns Workers

43. In admin web, open the APPROVED requirement.
44. In the Assign Workers section, search for the new worker (by name or city).
45. Select the worker. Assign.
46. **Expected:** Status → WORKERS_ASSIGNED. Worker receives notification.

### Phase 10: Worker Accepts Job

47. On worker app, go to Jobs tab.
48. Find the new ASSIGNED job. Tap to open.
49. Review job details: location, shift, role.
50. Tap "Accept". Confirm.
51. **Expected:** Status → ACCEPTED. Job appears on Home screen.

### Phase 11: Worker Check-In

52. (Physical device or mock GPS to job site coordinates.)
53. On shift day, worker opens Home screen.
54. Tap "Check In".
55. Allow location permission if prompted.
56. If selfie required: take selfie.
57. Confirm check-in.
58. **Expected:** Attendance record created. Status → CHECKED_IN. Check Out button appears.

### Phase 12: Worker Check-Out

59. Worker taps "Check Out". Confirm.
60. **Expected:** Attendance → CHECKED_OUT. Home shows "Checked Out" state.

### Phase 13: Admin Verifies Attendance

61. In admin web → `/attendance`.
62. Select today's date. Find the attendance record for the worker.
63. Click "Verify".
64. **Expected:** Status → VERIFIED.

### Phase 14: Admin Completes Job

65. Go to the requirement detail. Click "Mark as Completed".
66. Confirm.
67. **Expected:** Status → COMPLETED. Client and worker both notified.

### Phase 15: Invoice and Payment

68. On requirement detail, create an invoice.
69. **Expected:** Invoice created with number INV-2026-XXXX.
70. Client app: open requirement → invoice section → tap invoice.
71. Choose "Pay via Bank Transfer". Enter UTR: UTR20260601TEST.
72. Submit.
73. **Expected:** Payment record created with PENDING status.
74. Admin → `/finance` → Incoming Payments. Find PENDING payment.
75. Click Confirm.
76. **Expected:** Status → PAID.

### Phase 16: Payroll

77. Admin → `/payroll`. Find the COMPLETED requirement.
78. Open payroll detail. Workers listed with verified attendance days.
79. Click "Lock and Run Payroll".
80. **Expected:** Payroll run created.
81. Admin → `/finance` → Payroll Queue. Find the run. Trigger disbursement.
82. **Expected:** Worker disbursements marked.
83. Worker app → Earnings tab.
84. **Expected:** New earning entry visible.

### Phase 17: Client Rates Service

85. Client app: open COMPLETED requirement.
86. Tap "Rate this service".
87. Give 4 stars with a comment.
88. Submit.
89. **Expected:** "Thank you for your feedback" message.

### Phase 18: Complaint Flow

90. Client app → Complaints tab → Raise Complaint.
91. Type a description. Select severity "Medium". Submit.
92. **Expected:** Complaint with OPEN status created.
93. Admin → `/complaints`. Find the complaint.
94. Open it → Mark as In Review → Resolve with notes.
95. **Expected:** Status → RESOLVED. Client sees resolution in app.

### Phase 19: Final Checks

96. Admin dashboard: verify all counters are updated.
97. Worker app: verify job shows as COMPLETED on Jobs tab.
98. Client app: requirement timeline shows all statuses in order.
99. Audit log: verify all key actions recorded.
100. **All phases complete. Job is fully closed.**

---

## Part 5 — Gaps, Missing Connections, and Risks

### Screens that look incomplete or use mock data

| Screen/Feature | Issue |
|----------------|-------|
| `BillingOverviewScreen` (client mobile) | Uses `MOCK_INVOICES` hardcoded data — not connected to real API at all |
| Worker interest expressions | Backend API exists (`GET /admin/requirements/{id}/interests`) but no admin UI to view or act on it |
| Blacklist management | Backend API (`/admin/people/workers/{id}/blacklist`) exists but no admin UI page — admin cannot blacklist a worker from the web |
| Quote "re-send" after rejection | Client rejects a quote → admin can re-quote, but the UI doesn't make this obvious (no visual prompt) |
| Worker earnings/payment history | Only works if payroll has been run and disbursements recorded — many apps show 0 by default |

---

### Flows that may break in production

| Risk | Detail |
|------|--------|
| **Razorpay webhook** | Payment confirmation via Razorpay requires a publicly accessible webhook URL. Works with ngrok in dev but will silently fail without it. |
| **GPS check-in** | Requires physical device. Emulator GPS mocking is unreliable. |
| **Push notifications** | Expo Push requires a physical device with a push token. Will silently fail in simulator. |
| **S3 document uploads** | Worker ID/selfie uploads use S3 in production. In dev, local filesystem is used. Failure silently results in missing documents. |
| **OTP SMS delivery** | Production OTP is sent via SMS gateway (not console). If SMS gateway is down, workers/clients cannot log in. |
| **Biometric** | `expo-local-authentication` depends on device hardware. Devices without biometric sensors skip setup — verify the fallback works. |
| **Google Places API** | `CreateRequestScreen` uses `react-native-google-places-autocomplete`. If `GOOGLE_PLACES_API_KEY` is not set, location search shows no results. |

---

### APIs that exist but are not connected to any UI

| API Endpoint | What it does | Missing UI |
|-------------|-------------|-----------|
| `GET /admin/requirements/{id}/interests` | List workers who expressed interest in a job | No admin UI panel |
| `POST /admin/people/workers/{id}/blacklist` | Blacklist a worker | No button in worker detail |
| `POST /admin/people/workers/bulk-import` | Bulk import workers via CSV | No import button in admin |
| `GET /admin/sla` / `PUT /admin/sla/{severity}` | SLA policies | Admin page exists at `/sla` but may not be wired |
| `GET /admin/maintenance` | Maintenance mode toggle | No settings page exposes this |
| `POST /auth/social` | Social login | Not exposed in any UI |
| `GET /worker/availability` | Worker sets availability days/shifts | UI screen exists but API connection uncertain |

---

### Business rules that may not be enforced in UI

| Rule | Risk |
|------|------|
| **Client cannot edit a submitted request** | Should be blocked after SUBMITTED status. Check that edit button is hidden/disabled. |
| **Quote expiry** | If `valid_until` passes, client should not be able to accept. Check expired quote handling on client mobile. |
| **Worker must be at job site** | Geofence check only applies when `require_geofence = true` on the requirement. If false, anyone can check in from anywhere. |
| **One check-in per day** | Duplicate check-in should be rejected. Verify the API rejects a second check-in on same date. |
| **Payroll lock** | After payroll is locked for a period, attendance cannot be modified. Verify this is enforced. |
| **Invoice uniqueness** | Only one non-cancelled invoice per requirement. Verify you cannot create a second invoice. |
| **Ops Admin cannot modify verified attendance** | Only Super Admin. Verify the 403 response. |

---

### Edge cases not handled (visible from code)

| Edge Case | Risk |
|-----------|------|
| Requirement without any workers assigned but forcefully moved to IN_PROGRESS | No check-in guard exists at the status transition level |
| Worker with no verified attendance gets a payroll item | Payroll will show 0 days which could still create a ₹0 disbursement |
| Client deletes profile mid-requirement | Requirement orphaned with no client — admin detail page may 500 |
| Admin assigns a worker then immediately deactivates them | Assignment remains active but worker cannot log in |
| Timezone issues | Attendance dates stored as UTC; local timezone display may show wrong date for Indian timezone (IST = UTC+5:30) |
| Simultaneous quote acceptance | If two clients share an account and both try to accept a quote simultaneously, no race condition protection visible |

---

## Part 6 — Priority Order for Testing

Test in this order to cover the most critical paths first:

| Priority | Test Route | Reason |
|----------|-----------|--------|
| 🔴 Critical | Route 1 — Admin Login | Nothing works without login |
| 🔴 Critical | Route 2 — Role Access Control | Security baseline |
| 🔴 Critical | Route 3 — Worker Onboarding | Worker supply chain starts here |
| 🔴 Critical | Route 4 — Admin Approves Worker | Blocks all worker flows |
| 🔴 Critical | Route 7 — Client Creates Request | Core business flow |
| 🔴 Critical | Route 8 — Admin Reviews Request | Admin side of core flow |
| 🔴 Critical | Route 9 — Client Accepts Quote | Money commitment point |
| 🔴 Critical | Route 10 — Admin Assigns Workers | Operational execution |
| 🔴 Critical | Route 11 — Worker Accept/Decline | Worker response |
| 🔴 Critical | Route 12 — Check-In / Check-Out | GPS + attendance |
| 🔴 Critical | Route 13 — Admin Verifies Attendance | Payroll dependency |
| 🔴 Critical | Route 14 — Admin Completes Job | End of service delivery |
| 🟠 High | Route 15 — Invoice and Payment | Revenue flow |
| 🟠 High | Route 16 — Payroll | Worker payment |
| 🟠 High | Route 17 — Complaints | Support flow |
| 🟠 High | Route 25 — Settings/Logout | Security |
| 🟠 High | Route 26 — Admin User Permissions | Multi-admin security |
| 🟠 High | Route 20 — Dashboard Stats | Operational visibility |
| 🟡 Medium | Routes 21–24 — Search/Filter/Validation/Errors | UX quality |
| 🟡 Medium | Route 18 — Disputes | Post-completion support |
| 🟡 Medium | Route 19 — Replacements | Operational fallback |
| 🟢 Low | Routes 27–33 — Reports/Audit/SLA/Rating | Analytics and tracking |

---

## Part 7 — Pre-Production Readiness Checklist

Before declaring the project ready for production:

**Authentication and Security**
- [ ] Admin login blocks wrong password (5-attempt lockout works)
- [ ] OTP expires after 5 minutes; reuse blocked
- [ ] JWT token rejected after logout
- [ ] Ops Admin cannot perform Super Admin actions (tested against live API)
- [ ] CORS headers set correctly (only allowed origins)

**Core Business Flow**
- [ ] Full flow completed end-to-end: Create → Quote → Assign → Check-in → Verify → Invoice → Pay
- [ ] Status transitions work in correct order (cannot skip from DRAFT to IN_PROGRESS)
- [ ] Invalid transitions return correct error messages

**Mobile App**
- [ ] Worker onboarding completes on a physical Android device
- [ ] Worker onboarding completes on a physical iOS device
- [ ] GPS check-in works at a real location
- [ ] Biometric login works on both Android (fingerprint) and iOS (Face ID)
- [ ] Offline mode shows cached data with stale banner
- [ ] Push notifications received on physical device

**Finance**
- [ ] Invoice created, client pays via UTR, admin confirms — end-to-end
- [ ] Razorpay webhook received and payment confirmed (requires ngrok or production URL)
- [ ] Payroll run created, locked, worker disbursements recorded

**Admin Dashboard**
- [ ] All pages load without console errors
- [ ] All filters work correctly
- [ ] All status transitions have correct buttons and produce correct status changes
- [ ] Audit log records all key actions
- [ ] Reports export CSV with correct columns

**Performance and Stability**
- [ ] Dashboard loads in < 3 seconds with 100+ requirements
- [ ] No N+1 query errors in logs on dashboard load
- [ ] No memory leaks during extended mobile session
- [ ] Backend stays up for 30+ minutes without restart

**Edge Cases**
- [ ] Empty states shown correctly (no data scenarios)
- [ ] Error states shown with retry button (server down scenario)
- [ ] Long names / long text don't break UI layout
- [ ] Special characters in names/descriptions handled correctly

---

*End of Manual UI Testing Guide.*
*Last updated: June 2026.*
*Covers: Admin Web (Next.js), Client Mobile (React Native/Expo), Worker Mobile (React Native/Expo), Backend (FastAPI)*
