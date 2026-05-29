# Annai Illam Staffing Platform — Manual QA Testing Checklist

**Version:** 1.0  
**Date:** 2026-05-23  
**Platform:** Admin Web (Next.js) · Client Mobile (React Native/Expo) · Worker Mobile (React Native/Expo)  
**Scope:** Full MVP manual test plan — use this document for regression testing before every production release.

---

## A. Manual Testing Overview

### What the Application Does

Annai Illam is an industrial staffing operations platform. It connects three types of users:

- **Admin (web):** Operations team who manage clients, workers, job requests, attendance, and complaints from a Next.js dashboard.
- **Client (mobile):** Companies that hire temporary workers. They create job requests, view assigned workers, and raise complaints.
- **Worker (mobile):** Contract workers who receive job assignments, check in and out using GPS, and raise issues.

### Core Business Flow

```
Client creates request → Admin approves → Admin assigns workers → Worker accepts job
→ Worker GPS check-in → Worker GPS check-out → Admin verifies attendance
→ Client views status → Complaints can be raised and resolved at any point
```

### Apps and URLs

| Surface | Technology | Dev URL |
|---|---|---|
| Admin Dashboard | Next.js 16 App Router | `http://localhost:3000` |
| Backend API | FastAPI | `http://localhost:8000` (docs at `/docs` in local mode only) |
| Client Mobile | Expo React Native | `npm run clients` from `apps/mobile-ui-lab` |
| Worker Mobile | Expo React Native | `npm run worker` from `apps/mobile-ui-lab` |

### API Base URL

All API calls are prefixed with `/api/v1/`.

---

## B. Test User Roles and Test Data Needed

### Roles

| Role | Login Method | Surface | Note |
|---|---|---|---|
| Super Admin | Email + Password | Admin web at `/login` | Can do everything |
| Ops Admin | Email + Password | Admin web at `/login` | Cannot deactivate, cannot modify verified attendance |
| Client | Phone + OTP | Client mobile app | Can only see own data |
| Worker | Phone + OTP + Biometric | Worker mobile app | Full onboarding required first |

### Step 1: Create Test Accounts Before Testing

**Admin accounts (run once before testing):**
```bash
cd apps/backend
make seed-admin EMAIL=superadmin@test.com PASSWORD=Admin@123 NAME="Super Admin"
make seed-admin EMAIL=opsadmin@test.com PASSWORD=Admin@123 NAME="Ops Admin"
```

**Client account:**
- Open the client mobile app
- Enter a test phone number (e.g. `9876543210`)
- Enter the OTP from server logs or SMS
- Complete profile setup

OR create via admin dashboard:
- Go to `/clients` → click "Add Client"
- Fill in: Company Name, Contact Name, Phone, GST (optional), Email, Address, City

**Worker account:**
- Open the worker mobile app
- Complete full onboarding: Phone → OTP → Build Profile → Consent → Upload ID + Selfie → Submitted
- Admin must approve the worker: go to `/workers`, find the pending worker, approve

**Test Data to Create Before Running Tests:**

| Item | How to Create | Notes |
|---|---|---|
| Super Admin | `make seed-admin` command | First user only |
| Ops Admin | Admin web → Admin Users → Invite | Requires Super Admin |
| Client Company | Admin web → Clients → Add Client | Get login phone from record |
| Worker Profile | Worker mobile onboarding | Must be approved by admin |
| Job Request (DRAFT) | Client mobile → Jobs → + Create | Save as draft |
| Job Request (SUBMITTED) | Client mobile → Jobs → + Create → Submit | Needs client login |
| Job Request (APPROVED) | Admin → Requirements → Approve | Needs submitted request |
| Assignment | Admin → Requirements → [id] → Assign Workers | Needs approved request |
| Attendance Record | Worker mobile → Check In | Needs accepted assignment |

---

## C. Page-by-Page Manual Test Cases

---

### ADMIN WEB APP

---

#### TC-A-001 — Admin Login Page

| Field | Value |
|---|---|
| **Feature** | Authentication |
| **Role** | Admin (any) |
| **URL** | `/login` |
| **Priority** | Critical |
| **Pass/Fail** | |

**Preconditions:** Admin account exists (seeded). Browser cleared of cookies.

**Test Steps:**
1. Open `http://localhost:3000/login`
2. Verify the page title reads "Sign in"
3. Verify the subtitle reads "Login with your email address and password."
4. Verify the eyebrow text reads "ADMIN ACCESS"
5. Locate the Email field and Password field
6. Enter email: `superadmin@test.com`
7. Enter password: `Admin@123`
8. Click the **Sign in** button (or press Enter)
9. Observe the loading spinner on the button during login
10. Verify redirect to `/dashboard`
11. Verify admin name and role appear in the sidebar footer
12. Verify the sidebar shows sections: Operations, Finance, Management

**Expected Result:** Successful redirect to `/dashboard`. Sidebar shows logged-in admin's name and role (SUPER_ADMIN or OPS_ADMIN).

**Negative Cases:**
- Enter wrong password → Verify error message appears (not a stack trace)
- Enter non-existent email → Verify error message
- Leave both fields empty and click Sign In → Verify fields highlight as required
- Enter email without @ → Verify inline validation
- Rapidly submit 6+ times → Verify rate limit response (HTTP 429)

---

#### TC-A-002 — Admin Session Expiry and Auto-Refresh

| Field | Value |
|---|---|
| **Feature** | Token Management |
| **Role** | Admin |
| **Priority** | High |
| **Pass/Fail** | |

**Test Steps:**
1. Log in as admin
2. Open browser DevTools → Application → Local Storage
3. Verify `admin_access_token`, `admin_refresh_token`, and `admin_user` keys exist
4. Manually delete `admin_access_token` from localStorage (leave refresh token)
5. Navigate to `/requirements`
6. Verify the page loads successfully (auto-refresh should have fired)
7. Verify new `admin_access_token` now appears in localStorage

**Negative Case:**
- Delete both `admin_access_token` AND `admin_refresh_token` from localStorage
- Navigate to any protected page
- Verify redirect to `/login`

---

#### TC-A-003 — Admin Dashboard Page

| Field | Value |
|---|---|
| **Feature** | Dashboard / KPI Stats |
| **Role** | Admin |
| **URL** | `/dashboard` |
| **Priority** | Critical |
| **Pass/Fail** | |

**Preconditions:** Some test data must exist (at least one requirement, client, worker).

**Test Steps:**
1. Log in as admin
2. Navigate to `/dashboard` (should land here after login)
3. Verify page header shows "Dashboard"
4. Verify 5 KPI stat cards are displayed in a row: they should include counts for Active Requests, Workers, Clients, Attendance, Complaints (or similar categories)
5. Verify each stat card shows: an icon, a number, a label, and a trend indicator
6. Verify "Priority Actions" section appears below KPI cards
7. Verify "Recent Activity" section appears (right side)
8. Verify sidebar navigation is fully expanded with Operations, Finance, Management groups
9. Verify clicking "Requests" in sidebar navigates to `/requirements`
10. Click each sidebar item and verify navigation works (Dashboard, Requests, Workers, Clients, Attendance, Payroll, Finance, Complaints, Reports, Audit Log, SLA Policies, Admin Users, Settings)

**Expected Result:** Dashboard loads with real data counts. All sidebar items navigate correctly.

**Negative Case:**
- Navigate to `/dashboard` without being logged in → should redirect to `/login`

---

#### TC-A-004 — Clients List Page

| Field | Value |
|---|---|
| **Feature** | Client Management |
| **Role** | Admin |
| **URL** | `/clients` |
| **Priority** | High |
| **Pass/Fail** | |

**Test Steps:**
1. Log in as admin, click "Clients" in sidebar
2. Verify table shows columns: Company Name, Contact, Phone, City, Status, Actions
3. Verify each row shows: company avatar initials, company name, contact name, phone number, active/inactive badge
4. Verify search box is visible at the top
5. Type a partial company name in the search box
6. Verify table filters to matching clients only
7. Clear search → verify all clients return
8. Hover over a table row → verify Edit and Deactivate action buttons appear
9. Click anywhere on a row → verify navigation to `/clients/[id]`

**Expected Result:** Client list loads, search works, row hover shows actions.

**Negative Case:**
- Search for a non-existent company name → verify empty state with "No clients found" message (not a blank page)

---

#### TC-A-005 — Create Client Dialog

| Field | Value |
|---|---|
| **Feature** | Client Management — Create |
| **Role** | Admin |
| **URL** | `/clients` |
| **Priority** | High |
| **Pass/Fail** | |

**Test Steps:**
1. Navigate to `/clients`
2. Click the "Add Client" button (top right)
3. Verify a dialog/modal opens with title "Add Client"
4. Verify the form contains: Company Name*, Contact Name*, Phone*, Email, GST Number (optional), Address*, City*, State*
5. Leave required fields blank and click Submit → verify inline validation errors per field
6. Fill all required fields:
   - Company Name: `Test Industries Pvt Ltd`
   - Contact Name: `Rajesh Kumar`
   - Phone: `9876543210`
   - Email: `rajesh@testind.com`
   - Address: `No. 12 Industrial Area`
   - City: `Chennai`
   - State: `Tamil Nadu`
7. Click "Save" (or "Create Client")
8. Verify dialog closes and the new client appears in the list
9. Verify a success toast appears at the top right

**Expected Result:** Client created successfully. Appears in list immediately.

**Negative Cases:**
- Enter duplicate phone number → verify error message from backend
- Enter invalid email format → verify inline error

---

#### TC-A-006 — Edit Client Dialog

| Field | Value |
|---|---|
| **Feature** | Client Management — Edit |
| **Role** | Admin |
| **Priority** | High |
| **Pass/Fail** | |

**Test Steps:**
1. Navigate to `/clients`
2. Hover over the test client row → click the Edit (pencil) icon
3. Verify the edit dialog opens pre-filled with existing client data
4. Change the City field to `Bengaluru`
5. Click "Save"
6. Verify the dialog closes and the updated city appears in the table row

**Expected Result:** Edit saves and reflects immediately.

---

#### TC-A-007 — Deactivate Client (Super Admin Only)

| Field | Value |
|---|---|
| **Feature** | Client Management — Deactivate |
| **Role** | Super Admin |
| **Priority** | High |
| **Pass/Fail** | |

**Preconditions:** Logged in as Super Admin (not Ops Admin).

**Test Steps:**
1. Navigate to `/clients`, hover a client row → click the Deactivate button
2. Verify a confirmation modal opens with a warning message explaining the consequence
3. Click "Cancel" → verify nothing happens, modal closes
4. Click Deactivate again → confirm in the modal
5. Verify the client row now shows an "Inactive" badge
6. Log out, log in as the client's phone number → verify they can still log in (deactivate sets `is_active=False` in DB but does not delete)

**Negative Case — Ops Admin cannot deactivate:**
1. Log out, log in as Ops Admin
2. Navigate to `/clients`, hover a row
3. Verify NO Deactivate button is visible for Ops Admin role

---

#### TC-A-008 — Client Detail Page

| Field | Value |
|---|---|
| **Feature** | Client Management — Detail |
| **Role** | Admin |
| **URL** | `/clients/[id]` |
| **Priority** | Medium |
| **Pass/Fail** | |

**Test Steps:**
1. Navigate to `/clients`, click a client row
2. Verify breadcrumb shows `Clients / [Company Name]`
3. Verify profile card shows: company name, contact name, phone, email, GST, address, city, active status badge
4. Verify a stats sidebar shows summary numbers (requirements count, etc.)
5. Verify a "Requirements" table at the bottom shows the client's job requests
6. Click a requirement row → verify navigation to `/requirements/[id]`

---

#### TC-A-009 — Workers List Page

| Field | Value |
|---|---|
| **Feature** | Worker Management |
| **Role** | Admin |
| **URL** | `/workers` |
| **Priority** | High |
| **Pass/Fail** | |

**Test Steps:**
1. Click "Workers" in the sidebar
2. Verify table shows workers with: Name, Skills, City, Status badge, Available/Unavailable indicator
3. Verify search works by partial name
4. Verify filter dropdown exists for availability status (Available, Unavailable, Under Review, Inactive)
5. Filter by "Under Review" → verify only pending onboarding workers appear
6. Click a worker row → navigate to `/workers/[id]`
7. Hover a row → verify Edit and Deactivate action buttons

---

#### TC-A-010 — Worker Detail Page (and Admin Approval)

| Field | Value |
|---|---|
| **Feature** | Worker Management — Detail + Approval |
| **Role** | Admin |
| **URL** | `/workers/[id]` |
| **Priority** | Critical |
| **Pass/Fail** | |

**Preconditions:** A worker has completed onboarding and is in "Under Review" state.

**Test Steps:**
1. Navigate to `/workers`, filter by "Under Review"
2. Click the pending worker row
3. Verify the worker detail page shows: full name, phone, city, skills (as chips), experience, shift preferences, availability days, status badge
4. Verify uploaded documents (ID + selfie) are viewable or linked
5. Find the "Approve" button and click it
6. Verify a confirmation dialog appears
7. Confirm approval
8. Verify worker status badge changes to "Active" or "Available"
9. On the worker mobile app, log in as that worker — verify they now reach the Biometric Setup screen (not Under Review screen)

---

#### TC-A-011 — Job Requests List Page

| Field | Value |
|---|---|
| **Feature** | Job Request Management |
| **Role** | Admin |
| **URL** | `/requirements` |
| **Priority** | Critical |
| **Pass/Fail** | |

**Test Steps:**
1. Click "Requests" → "All Requests" in sidebar
2. Verify list shows requirements with columns: Title/Category, Client, Status badge, Date, Workers count
3. Verify status badge colors are correct:
   - DRAFT → grey
   - SUBMITTED → blue
   - UNDER_REVIEW → purple
   - APPROVED → green
   - WORKERS_ASSIGNED → dark green
   - IN_PROGRESS → teal (with pulsing dot)
   - COMPLETED → green
   - REJECTED → red
   - CANCELLED → red
4. Filter by status "SUBMITTED" → verify only submitted requests appear
5. Clear filter → all return
6. Click a requirement row → navigate to `/requirements/[id]`

---

#### TC-A-012 — Job Request Detail: Review and Approve

| Field | Value |
|---|---|
| **Feature** | Job Request — Admin Approval |
| **Role** | Admin |
| **URL** | `/requirements/[id]` |
| **Priority** | Critical |
| **Pass/Fail** | |

**Preconditions:** A SUBMITTED job request exists.

**Test Steps:**
1. Navigate to `/requirements`, click a SUBMITTED request
2. Verify status badge shows "SUBMITTED" (blue)
3. Verify detail shows: category, subcategory, work location, city, number of workers, shift details, start date, duration, skills required, notes, food/accommodation flags
4. Verify breadcrumb: "Requests / [Request ID]"
5. Verify the status automatically changes to "UNDER_REVIEW" when admin opens the detail (or there is an explicit "Start Review" action)
6. Locate the "Approve" button (top right area)
7. Click "Approve"
8. Verify a confirmation dialog opens
9. Confirm approval
10. Verify status badge changes to "APPROVED" (green)
11. Verify a "Assign Workers" button now appears
12. Verify the status timeline on the right side shows SUBMITTED → UNDER_REVIEW → APPROVED with timestamps

**Expected Result:** Status transitions correctly, timeline updates.

---

#### TC-A-013 — Job Request Detail: Reject

| Field | Value |
|---|---|
| **Feature** | Job Request — Admin Rejection |
| **Role** | Admin |
| **URL** | `/requirements/[id]` |
| **Priority** | Critical |
| **Pass/Fail** | |

**Preconditions:** A SUBMITTED or UNDER_REVIEW job request exists.

**Test Steps:**
1. Open a SUBMITTED requirement's detail page
2. Click "Reject"
3. Verify a dialog opens asking for a rejection reason
4. Leave the reason blank and try to submit → verify validation error (reason is required)
5. Enter reason: "Budget does not meet our minimum threshold"
6. Click "Reject Request"
7. Verify status badge changes to "REJECTED" (red)
8. Verify the rejection reason is visible on the page

---

#### TC-A-014 — Assign Workers to a Job

| Field | Value |
|---|---|
| **Feature** | Worker Assignment |
| **Role** | Admin |
| **URL** | `/requirements/[id]` |
| **Priority** | Critical |
| **Pass/Fail** | |

**Preconditions:** Job request is APPROVED. At least one worker is AVAILABLE and has matching skills.

**Test Steps:**
1. Open an APPROVED requirement detail
2. Click "Assign Workers" button
3. Verify the assignment modal opens (wide dialog, ~640px)
4. Verify it shows: "Ready to assign" count, "Blocked" count, matched workers list
5. Verify each worker shows: name, skills, availability status
6. Select one or more workers by checking their checkboxes
7. Click "Assign" (or "Confirm Assignment")
8. Verify the dialog closes
9. Verify the requirement status changes to "WORKERS_ASSIGNED"
10. Verify the Assigned Workers section in the detail page shows the assigned workers

**Negative Cases:**
- Try to assign when no workers are available → verify message explains blocked workers
- Try to assign a worker already on another active job → verify they appear blocked, not selectable

---

#### TC-A-015 — Attendance Page: Lookup and Verify

| Field | Value |
|---|---|
| **Feature** | Attendance Management |
| **Role** | Admin |
| **URL** | `/attendance` |
| **Priority** | Critical |
| **Pass/Fail** | |

**Preconditions:** At least one worker has checked in/out.

**Test Steps:**
1. Click "Attendance" in the sidebar
2. Verify the page shows a lookup form (search by Requirement ID or Assignment ID)
3. Enter a valid Requirement ID
4. Verify the attendance table loads with columns: Worker Name, Date, Check-in Time, Check-out Time, Status, Assignment ID
5. Verify summary stat cards: Total, Verified, Pending, Absent
6. Find a record with status "CHECKED_OUT"
7. Click the "Verify" button on that row
8. Verify the status badge changes to "VERIFIED" (green)
9. Find a record and click "Correct" (correction button)
10. Verify a dialog opens for time correction with a reason field
11. Enter new check-in and check-out times, enter a reason, confirm
12. Verify the record updates with the corrected times

**Negative Cases:**
- Try to correct a VERIFIED record as Ops Admin → verify the action is blocked (Super Admin only for verified corrections)
- Enter an invalid Requirement ID → verify "No records found" empty state

---

#### TC-A-016 — Complaints List Page

| Field | Value |
|---|---|
| **Feature** | Complaint Management |
| **Role** | Admin |
| **URL** | `/complaints` |
| **Priority** | High |
| **Pass/Fail** | |

**Test Steps:**
1. Click "Complaints" → "All Complaints" in sidebar
2. Verify list shows: Complainant name, type (client/worker), status badge, severity, date, requirement/job link
3. Verify status badge colors: OPEN=blue, IN_REVIEW=purple, RESOLVED=green, REJECTED=red
4. Filter by status "OPEN" → verify only open complaints appear
5. Click a complaint row → navigate to `/complaints/[id]`

---

#### TC-A-017 — Complaint Detail: Review and Resolve

| Field | Value |
|---|---|
| **Feature** | Complaint Management — Resolution |
| **Role** | Admin |
| **URL** | `/complaints/[id]` |
| **Priority** | High |
| **Pass/Fail** | |

**Preconditions:** A complaint in OPEN status exists.

**Test Steps:**
1. Open a complaint detail page
2. Verify it shows: complaint type, severity, description, raised by (client or worker name), related requirement/assignment, current status, timestamps
3. Click "Mark In Review"
4. Verify status changes to "IN_REVIEW" (purple)
5. Click "Resolve"
6. Verify a dialog opens with a "Resolution Notes" text area
7. Leave it blank → verify validation error
8. Enter resolution notes: "Discussed with site supervisor. Issue addressed and confirmed resolved."
9. Click "Resolve Complaint"
10. Verify status changes to "RESOLVED" (green)
11. Verify resolution notes appear on the detail page

**Negative Case:**
- Try to Resolve without first setting to IN_REVIEW (if business rule requires it) → verify error
- Try to Reject an OPEN complaint → verify if direct OPEN→REJECTED is allowed

---

#### TC-A-018 — Payroll Pages

| Field | Value |
|---|---|
| **Feature** | Payroll (Finance) |
| **Role** | Admin |
| **URL** | `/payroll` |
| **Priority** | Medium |
| **Pass/Fail** | |

**Test Steps:**
1. Click "Payroll" in the Finance section of the sidebar
2. Verify the payroll list page loads (may show empty state if no payroll runs exist)
3. If a "Generate Payroll Run" button exists, click it
4. Verify form fields for generating a run (date range, requirement/assignment filter)
5. Generate a run and verify it appears in the list with status: PENDING
6. Click on the payroll run → navigate to `/payroll/[id]`
7. Verify the detail shows per-worker pay breakdown, deductions, net amounts
8. Verify amounts use monospace font (Geist Mono)

---

#### TC-A-019 — Finance Page

| Field | Value |
|---|---|
| **Feature** | Finance |
| **Role** | Admin |
| **URL** | `/finance` |
| **Priority** | Low |
| **Pass/Fail** | |

**Test Steps:**
1. Click "Finance" in the sidebar
2. Verify the page loads without error
3. Verify it shows client payment or financial summary data
4. If empty, verify an empty state is shown (not a blank page or error)

---

#### TC-A-020 — Reports Pages

| Field | Value |
|---|---|
| **Feature** | Reports |
| **Role** | Admin |
| **URL** | `/reports`, `/reports/requirements`, `/reports/assignments`, `/reports/complaints` |
| **Priority** | Medium |
| **Pass/Fail** | |

**Test Steps:**
1. Click "Reports" in the sidebar → verify landing on `/reports`
2. Navigate to `/reports/requirements`
3. Verify filter controls are visible: date range (from/to), status filter
4. Set a date range covering today → verify results table loads
5. Verify row count is shown (e.g. "12 results")
6. Navigate to `/reports/assignments`
7. Verify similar filter/table functionality
8. Navigate to `/reports/complaints`
9. Verify complaints report loads with date + status filters

---

#### TC-A-021 — Audit Log Page

| Field | Value |
|---|---|
| **Feature** | Audit Log |
| **Role** | Admin |
| **URL** | `/audit` |
| **Priority** | Low |
| **Pass/Fail** | |

**Test Steps:**
1. Click "Audit Log" in the sidebar
2. Verify the page loads
3. Verify a timestamped log of admin actions is shown
4. Verify empty state if no actions logged yet

---

#### TC-A-022 — SLA Policies Page

| Field | Value |
|---|---|
| **Feature** | SLA Policies |
| **Role** | Admin |
| **URL** | `/sla` |
| **Priority** | Low |
| **Pass/Fail** | |

**Test Steps:**
1. Click "SLA Policies" in the sidebar
2. Verify the page loads without error
3. Verify SLA policy entries are displayed (or empty state)

---

#### TC-A-023 — Admin Users Page

| Field | Value |
|---|---|
| **Feature** | Admin User Management |
| **Role** | Super Admin only |
| **URL** | `/admin-users` |
| **Priority** | Medium |
| **Pass/Fail** | |

**Test Steps:**
1. Log in as Super Admin
2. Click "Admin Users" in sidebar
3. Verify the page lists all admin accounts
4. Verify an "Invite Admin" button exists
5. Click "Invite Admin" → verify a dialog appears with email field
6. Enter an email for a new admin → submit
7. Verify the new admin appears in the list with "Invited" status

**Negative Case (Ops Admin cannot access):**
1. Log in as Ops Admin
2. Navigate to `/admin-users`
3. Verify redirect to `/dashboard` or a 403 error page (Ops Admin cannot manage admin users)

---

#### TC-A-024 — Settings Page

| Field | Value |
|---|---|
| **Feature** | Settings |
| **Role** | Admin |
| **URL** | `/settings` |
| **Priority** | Low |
| **Pass/Fail** | |

**Test Steps:**
1. Click "Settings" in the sidebar
2. Verify the page loads
3. Verify admin profile information is visible (name, email, role)
4. If "Change Password" is available, click it and verify the form works

---

#### TC-A-025 — Replacements Page

| Field | Value |
|---|---|
| **Feature** | Worker Replacements |
| **Role** | Admin |
| **URL** | `/replacements` |
| **Priority** | Medium |
| **Pass/Fail** | |

**Test Steps:**
1. Click "Complaints" → "Replacements" in sidebar
2. Verify the page lists replacement records (or empty state)
3. Verify replacement records show: original worker, replacement worker, reason, date

---

#### TC-A-026 — Assignments List and Detail Pages

| Field | Value |
|---|---|
| **Feature** | Assignment Management |
| **Role** | Admin |
| **URL** | `/assignments`, `/assignments/[id]` |
| **Priority** | High |
| **Pass/Fail** | |

**Test Steps:**
1. Click "Requests" → "Assignments" in the sidebar
2. Verify the assignments list shows: worker name, requirement/job link, shift, status badge, date
3. Filter by status "ASSIGNED" → verify results
4. Click an assignment row → navigate to `/assignments/[id]`
5. Verify detail shows: worker info, job requirement, shift details, current status, accept/decline/replace controls
6. Click "Replace Worker" → verify a dialog appears to select a replacement worker

---

### CLIENT MOBILE APP

---

#### TC-C-001 — Client Welcome and Login Screen

| Field | Value |
|---|---|
| **Feature** | Client Authentication |
| **Role** | Client |
| **Screen** | WelcomeScreen → LoginScreen |
| **Priority** | Critical |
| **Pass/Fail** | |

**Preconditions:** Client mobile app started with `npm run clients` from `apps/mobile-ui-lab`.

**Test Steps:**
1. Open the client app
2. Verify the Welcome screen appears with a "Get Started" or "Login" button
3. Tap the button → verify navigation to LoginScreen
4. Verify the phone number input field is visible with a label
5. Enter a valid phone number: `9876543210`
6. Tap "Send OTP" (or "Continue")
7. Verify a loading state appears briefly
8. Verify navigation to the VerifyOTP screen
9. Verify a 6-digit OTP input is shown

**Expected Result:** OTP request sent. Navigation to OTP screen.

**Negative Cases:**
- Enter a phone number with fewer than 10 digits → verify error
- Leave the field empty and tap Continue → verify validation error
- Enter a completely invalid number (letters) → verify input rejects or shows error

---

#### TC-C-002 — Client OTP Verification

| Field | Value |
|---|---|
| **Feature** | Client Authentication — OTP |
| **Role** | Client |
| **Screen** | VerifyOtpScreen |
| **Priority** | Critical |
| **Pass/Fail** | |

**Test Steps:**
1. After entering phone number and tapping Send OTP
2. Retrieve OTP from server logs or SMS
3. Enter the 6-digit OTP in the input field
4. Tap "Verify"
5. Verify loading state during verification
6. If first-time user: verify navigation to ProfileSetupScreen
7. If returning user: verify navigation to HomeScreen (Home tab)

**Negative Cases:**
- Enter a wrong 6-digit OTP → verify error "Invalid OTP" or similar
- Enter expired OTP (wait >5 minutes) → verify error about expiry
- Tap "Resend OTP" → verify a new OTP is sent and old one is invalidated

---

#### TC-C-003 — Client Home Screen

| Field | Value |
|---|---|
| **Feature** | Client Dashboard |
| **Role** | Client |
| **Screen** | HomeScreen (Home tab) |
| **Priority** | Critical |
| **Pass/Fail** | |

**Test Steps:**
1. Log in as a client who has active job requests
2. Verify the Home tab is selected by default
3. Verify a greeting: "Good morning, [First Name]" and today's date
4. Verify "ACTIVE JOBS" section shows horizontally scrollable job request cards
5. Each job card shows: job title/category, status badge, location, date range, worker count chip
6. Verify "Quick Stats" row shows 3 cards: "Workers on site today", "Open requests", "Pending complaints"
7. Verify "RECENT ACTIVITY" section shows a chronological list of activity items
8. Tap one of the active job cards → verify navigation to RequestDetailScreen
9. Pull down to refresh → verify data reloads

**Negative Case:**
- New client with no requests: verify empty state shown instead of blank scroll area

---

#### TC-C-004 — Client Jobs Tab (Requests List)

| Field | Value |
|---|---|
| **Feature** | Job Requests List |
| **Role** | Client |
| **Screen** | RequestsScreen (Jobs tab) |
| **Priority** | High |
| **Pass/Fail** | |

**Test Steps:**
1. Tap the "Jobs" bottom tab (briefcase icon)
2. Verify the Requests list screen loads
3. Verify all own job requests are listed with status badges
4. Verify you can see different statuses: DRAFT, SUBMITTED, APPROVED, etc.
5. Tap a request row → navigate to RequestDetailScreen
6. Tap the "+" or "New Request" button → navigate to CreateRequestScreen
7. Pull down to refresh → verify list reloads

---

#### TC-C-005 — Create Job Request (4-Step Form)

| Field | Value |
|---|---|
| **Feature** | Job Request Creation |
| **Role** | Client |
| **Screen** | CreateRequestScreen |
| **Priority** | Critical |
| **Pass/Fail** | |

**Test Steps:**

**Step 1 — Job Type:**
1. From Jobs tab or Home, tap "Create Request" / "+"
2. Verify progress bar shows "STEP 1 OF 4" (or similar)
3. Verify a list of job categories is shown (General Labour, Security, Housekeeping, Packing, etc.)
4. Tap "Security" to select it
5. Optionally enter a sub-category / custom type
6. Tap "Next" or "Continue"

**Step 2 — Location and Workers:**
7. Verify Step 2 shows location and worker count inputs
8. Verify work_location field (Google Places Autocomplete or manual entry)
9. Enter or select: `Chennai, Tamil Nadu`
10. Verify City and State auto-fill from selection (or fill manually)
11. Increase number of workers using the "+" button → verify count increments
12. Decrease using "−" button → verify count decrements (minimum 1)
13. Tap "Next"

**Step 3 — Schedule and Shift:**
14. Verify date picker for Start Date
15. Select a start date (at least tomorrow)
16. Select duration from the duration selector (e.g. "7" days)
17. Select a shift type: "General: 09:00-18:00"
18. If "Custom" is selected → verify a custom shift text input appears
19. Tap "Next"

**Step 4 — Requirements and Review:**
20. Verify skills multi-select chips (Packing, Loading, Electrical, etc.)
21. Select 1-2 skills
22. Toggle "Food Required" switch → verify it highlights
23. Toggle "Accommodation Required" switch
24. Enter a budget amount
25. Enter notes (optional)
26. Tap "Save Draft" → verify request saved as DRAFT, navigation to Requests list
27. Open the draft again, verify all data is preserved
28. Tap "Submit" → verify confirmation prompt or direct submission
29. Verify status changes to SUBMITTED
30. Verify request appears in list with SUBMITTED badge

**Negative Cases:**
- Try to submit with no job category selected → verify validation error on step 1
- Try to navigate to Step 2 without completing required Step 1 fields → verify cannot advance
- Enter 0 workers → verify minimum validation
- Enter a past start date → verify validation error

---

#### TC-C-006 — Request Detail Screen

| Field | Value |
|---|---|
| **Feature** | Job Request Detail — Client View |
| **Role** | Client |
| **Screen** | RequestDetailScreen |
| **Priority** | High |
| **Pass/Fail** | |

**Test Steps:**
1. Tap any request from the Jobs tab
2. Verify the screen shows: Job category, location, start date, duration, number of workers, shift, skills, food/accommodation flags, status badge
3. Verify status timeline section shows the chronological progression (DRAFT → SUBMITTED → UNDER_REVIEW → APPROVED, etc.)
4. For an APPROVED request: verify a "View Workers" or "Assigned Workers" button/chip appears
5. Tap "View Workers" → verify navigation to AssignedWorkersScreen
6. For a request with a quote (if quote feature is used): verify the quote details (daily rate, total amount) and "Accept Quote" / "Reject Quote" buttons appear
7. Tap "Accept Quote" → verify status updates

---

#### TC-C-007 — Assigned Workers Screen

| Field | Value |
|---|---|
| **Feature** | Assigned Workers View |
| **Role** | Client |
| **Screen** | AssignedWorkersScreen |
| **Priority** | High |
| **Pass/Fail** | |

**Preconditions:** A job request has workers assigned to it.

**Test Steps:**
1. Open a WORKERS_ASSIGNED or IN_PROGRESS request
2. Tap "View all workers" or the workers chip
3. Verify the AssignedWorkersScreen loads
4. Verify summary strip shows: Assigned count, Checked In count, Absent count
5. Verify each worker card shows: name, attendance status pill (CHECKED_IN, CHECKED_OUT, NOT_STARTED, ABSENT), check-in time, check-out time
6. Verify multi-day attendance streak dots (up to 14 days) are visible per worker
7. Tap "Raise complaint" shortcut on a worker card → verify navigation to Complaints tab → RaiseComplaintScreen with requirement pre-filled

**Negative Case:**
- View assigned workers for a request with no workers yet → verify empty state

---

#### TC-C-008 — Complaints Tab: View All Complaints

| Field | Value |
|---|---|
| **Feature** | Client Complaints |
| **Role** | Client |
| **Screen** | ComplaintsScreen (Complaints tab) |
| **Priority** | High |
| **Pass/Fail** | |

**Test Steps:**
1. Tap the "Complaints" bottom tab (warning icon)
2. Verify the complaints list loads
3. Verify each complaint card shows: type, severity badge, status badge, date, brief description
4. Verify status badge colors match: OPEN=blue, IN_REVIEW=purple, RESOLVED=green, REJECTED=red
5. Tap a complaint row → navigate to ComplaintDetailScreen
6. Tap "Raise Complaint" button → navigate to RaiseComplaintScreen

---

#### TC-C-009 — Raise a Complaint (Client)

| Field | Value |
|---|---|
| **Feature** | Client Complaint Submission |
| **Role** | Client |
| **Screen** | RaiseComplaintScreen |
| **Priority** | High |
| **Pass/Fail** | |

**Test Steps:**
1. Tap "Raise Complaint" from the Complaints tab
2. Verify the form shows: Requirement selector (pick which job the complaint is about), Complaint Type selector, Severity selector, Description text area
3. Select a requirement from the dropdown/picker
4. Select complaint type (e.g. "Worker Behaviour", "Attendance Issue")
5. Select severity (e.g. "High")
6. Enter description: "Two workers consistently arrived 30 minutes late on Monday and Tuesday."
7. Tap "Submit"
8. Verify success message or navigation back to complaints list
9. Verify the new complaint appears with status "OPEN"

**Negative Cases:**
- Submit with no description → verify validation error
- Submit without selecting a requirement → verify validation error

---

#### TC-C-010 — Complaint Detail Screen (Client)

| Field | Value |
|---|---|
| **Feature** | Client Complaint Detail |
| **Role** | Client |
| **Screen** | ComplaintDetailScreen |
| **Priority** | Medium |
| **Pass/Fail** | |

**Test Steps:**
1. Tap an existing complaint from the Complaints list
2. Verify the detail shows: complaint type, severity, full description, status badge, raised date, related requirement
3. If the complaint is RESOLVED: verify resolution notes are visible
4. If the complaint is IN_REVIEW: verify a message like "Under Review" is shown
5. Verify the client CANNOT see any admin-only fields (admin notes, assignment details)

---

#### TC-C-011 — Client Profile Screen

| Field | Value |
|---|---|
| **Feature** | Client Profile |
| **Role** | Client |
| **Screen** | ClientProfileScreen (Profile tab) |
| **Priority** | Medium |
| **Pass/Fail** | |

**Test Steps:**
1. Tap the "Profile" bottom tab (user icon)
2. Verify the profile screen shows 3 sections: Company Info, Preferences, Account
3. Verify Company Info shows: company name, contact name, email, phone, industry
4. Tap the Edit button (pencil icon or "Edit Profile" button)
5. Verify a slide-up modal/sheet opens with editable fields: industry, email, default_job_category, food_preference toggle, accommodation_preference toggle, standing_notes
6. Edit the email field to `updated@test.com`
7. Tap "Save"
8. Verify the modal closes and the profile screen shows the updated email
9. Verify a success toast or confirmation appears

---

### WORKER MOBILE APP

---

#### TC-W-001 — Worker Welcome and Login

| Field | Value |
|---|---|
| **Feature** | Worker Authentication |
| **Role** | Worker |
| **Screen** | WelcomeScreen → LoginScreen |
| **Priority** | Critical |
| **Pass/Fail** | |

**Preconditions:** Worker mobile app started with `npm run worker`.

**Test Steps:**
1. Open the worker app
2. Verify the Welcome screen is shown (Annai Illam branding)
3. Tap "Get Started" or "Log In"
4. Verify phone number input screen
5. Enter phone: `9876543211`
6. Tap "Send OTP"
7. Verify navigation to VerifyOtpScreen

---

#### TC-W-002 — Worker First-Time Onboarding: OTP to Profile Submission

| Field | Value |
|---|---|
| **Feature** | Worker Onboarding |
| **Role** | Worker (new) |
| **Screens** | VerifyOtpScreen → BuildProfileScreen → ConsentScreen → VerifyIdentityScreen → ProfileSubmittedScreen |
| **Priority** | Critical |
| **Pass/Fail** | |

**Test Steps:**
1. Enter OTP received on phone `9876543211`
2. Tap "Verify"
3. If new user, verify navigation to BuildProfileScreen

**BuildProfileScreen:**
4. Enter Full Name: `Murugan S`
5. Enter City: `Chennai`
6. Enter State: `Tamil Nadu`
7. Tap skill chips to select at least one: `Cleaning`
8. Select experience: `1–2 years`
9. Select available days: `Mon`, `Tue`, `Wed`, `Thu`, `Fri`
10. Select available shifts: `Morning`
11. Optionally fill UPI ID or tap "Add Bank Details" to fill Account No + IFSC
12. Verify the "Continue" or "Next" button activates only when required fields are filled
13. Tap "Continue"

**ConsentScreen:**
14. Verify a consent/privacy policy screen appears
15. Read the consent text
16. Tap "I Agree" or similar consent button
17. Verify navigation to VerifyIdentityScreen

**VerifyIdentityScreen:**
18. Verify the screen prompts for Government ID photo and a selfie
19. Tap "Upload ID" → verify camera or gallery picker opens (or simulated on emulator)
20. Select/capture a photo for the ID
21. Tap "Take Selfie" → verify camera opens
22. Capture or select selfie
23. Tap "Submit"

**ProfileSubmittedScreen:**
24. Verify a confirmation screen appears: "Profile Submitted"
25. Verify message: "Your profile is under review. We'll notify you once approved."
26. Verify a "Under Review" or waiting state screen appears

---

#### TC-W-003 — Worker Under Review State

| Field | Value |
|---|---|
| **Feature** | Worker Onboarding — Under Review |
| **Role** | Worker |
| **Screen** | UnderReviewScreen |
| **Priority** | High |
| **Pass/Fail** | |

**Test Steps:**
1. After profile submission, verify the UnderReviewScreen shows
2. Verify descriptive text explaining the review process
3. Verify a "Contact Us" or support link is visible
4. Verify a "Logout" option is available
5. Tap Logout → verify navigation back to WelcomeScreen
6. Log back in with same phone → verify UnderReviewScreen appears again (not the dashboard)

---

#### TC-W-004 — Worker Biometric Setup (After Admin Approval)

| Field | Value |
|---|---|
| **Feature** | Biometric Enrollment |
| **Role** | Worker (just approved) |
| **Screen** | BiometricSetupScreen |
| **Priority** | High |
| **Pass/Fail** | |

**Preconditions:** Admin has approved the worker's profile.

**Test Steps:**
1. Worker opens the app after admin approval
2. Verify they are directed to BiometricSetupScreen (NOT the UnderReviewScreen)
3. Verify a prompt to enable Face ID / Touch ID / Fingerprint
4. Tap "Enable Biometrics" → verify the system biometric prompt appears
5. Authenticate with biometric
6. Verify navigation to the main HomeScreen (worker dashboard)

**Negative Case:**
- Tap "Skip" or "Do it later" (if option exists) → verify behavior (allowed or forced)

---

#### TC-W-005 — Worker Returning Login with Biometric Check

| Field | Value |
|---|---|
| **Feature** | Worker Authentication — Biometric |
| **Role** | Worker (returning) |
| **Screen** | BiometricCheckScreen |
| **Priority** | High |
| **Pass/Fail** | |

**Preconditions:** Worker has completed onboarding + biometric setup.

**Test Steps:**
1. Open worker app (already approved and set up biometrics)
2. Enter phone number → enter OTP
3. Verify BiometricCheckScreen appears (not the dashboard directly)
4. Verify biometric authentication prompt shows
5. Authenticate → verify navigation to HomeScreen

**Negative Case:**
- Fail biometric 3 times → verify fallback to PIN or OTP re-entry (check behavior)

---

#### TC-W-006 — Worker Home Screen (Dashboard)

| Field | Value |
|---|---|
| **Feature** | Worker Dashboard |
| **Role** | Worker |
| **Screen** | HomeScreen (Home tab) |
| **Priority** | Critical |
| **Pass/Fail** | |

**Preconditions:** Worker has an ACCEPTED assignment for today.

**Test Steps:**
1. Verify the Home screen shows the dark green hero card (brand-900 background)
2. Verify the hero card shows: "TODAY'S SHIFT" label, Company Name, Location (with pin icon), Shift time (e.g. "09:00–18:00")
3. Verify the "Check In" button is visible inside the hero card (green button)
4. Verify the "This Week" strip below shows the current 5 days with attendance color coding
5. Verify the top bar shows: today's date on left, bell icon on right
6. Verify availability toggle is visible (AVAILABLE / UNAVAILABLE)
7. Verify a "Browse Jobs" button or link is visible

**No-job state:**
8. Log in as a worker with no active assignment today
9. Verify the hero card shows "No shift today" empty state (not an error)

---

#### TC-W-007 — Worker GPS Check-In

| Field | Value |
|---|---|
| **Feature** | GPS Check-In |
| **Role** | Worker |
| **Screen** | HomeScreen (hero card) |
| **Priority** | Critical |
| **Pass/Fail** | |

**Preconditions:**
- Worker has an ACCEPTED assignment for today
- Device location is enabled
- Worker is physically within 500m of the job site (or test data has the job site set to match the device location)

**Test Steps:**
1. Open worker HomeScreen with an active assignment
2. Verify the "Check In" button is shown in the hero card
3. Tap "Check In"
4. Verify the app requests location permission (first time)
5. Grant location permission
6. Verify a brief loading indicator while GPS coordinates are fetched and verified
7. Verify successful check-in: the button area changes to show:
   - Green pulsing dot + "Checked in at [time]"
   - A "Check Out" button appears
8. Verify the "This Week" strip updates today's tile to green (Present)
9. Verify the attendance status is now "CHECKED_IN" in the admin dashboard

**Negative Cases:**
- Worker is more than 500m from the job site → verify error message: "You are too far from the job site to check in." (or equivalent)
- Location permission denied → verify error asking to enable location
- GPS signal unavailable → verify graceful error message

---

#### TC-W-008 — Worker GPS Check-Out

| Field | Value |
|---|---|
| **Feature** | GPS Check-Out |
| **Role** | Worker |
| **Screen** | HomeScreen (hero card) |
| **Priority** | Critical |
| **Pass/Fail** | |

**Preconditions:** Worker is CHECKED_IN.

**Test Steps:**
1. After checking in, verify the "Check Out" button is visible
2. Tap "Check Out"
3. Verify loading state
4. Verify the check-in indicator changes to show check-in time and check-out time
5. Verify the hero card shows the assignment as completed for today
6. Verify in admin dashboard: attendance record status = "CHECKED_OUT"

---

#### TC-W-009 — Worker Accept / Decline Assignment

| Field | Value |
|---|---|
| **Feature** | Assignment Accept / Decline |
| **Role** | Worker |
| **Screen** | HomeScreen or JobDetailScreen |
| **Priority** | Critical |
| **Pass/Fail** | |

**Preconditions:** Admin has assigned the worker (status = ASSIGNED).

**Test Steps:**
1. Worker opens the app and sees an ASSIGNED job in the hero card or a notification
2. Verify "Accept" and "Decline" buttons are visible
3. Tap "Accept"
4. Verify a confirmation prompt (if any)
5. Verify status changes to "ACCEPTED"
6. Verify the hero card updates to show the accepted job with Check In button

**Decline flow:**
7. Start with a different ASSIGNED job
8. Tap "Decline"
9. Verify a reason input appears (optional decline reason)
10. Enter reason or leave blank, confirm decline
11. Verify status changes to "DECLINED"
12. Verify the admin dashboard shows the assignment as DECLINED
13. Verify admin can then replace the declined worker

---

#### TC-W-010 — Worker Jobs Board

| Field | Value |
|---|---|
| **Feature** | Jobs Browse |
| **Role** | Worker |
| **Screen** | JobsBoardScreen (Jobs tab) |
| **Priority** | Medium |
| **Pass/Fail** | |

**Test Steps:**
1. Tap the "Jobs" bottom tab
2. Verify the JobsBoardScreen shows sections: "Best Match", "Nearby", "Other"
3. Verify job cards show: company, location, shift, skills required
4. Tap a job card → verify navigation to JobDetailScreen
5. On JobDetailScreen, verify full job details
6. Tap an "Express Interest" or "Toggle Interest" button → verify interest registered

---

#### TC-W-011 — Worker Attendance History

| Field | Value |
|---|---|
| **Feature** | Attendance History |
| **Role** | Worker |
| **Screen** | AttendanceHistoryScreen (Attendance tab) |
| **Priority** | Medium |
| **Pass/Fail** | |

**Test Steps:**
1. Tap the "Attendance" bottom tab (clipboard icon)
2. Verify the screen shows a calendar or list of past attendance records
3. Verify each record shows: date, assignment/job name, check-in time, check-out time, status badge
4. Status colors: CHECKED_IN=teal, CHECKED_OUT=blue, VERIFIED=green, ABSENT=red, LATE=amber
5. Verify pull-to-refresh works

---

#### TC-W-012 — Worker Raise an Issue

| Field | Value |
|---|---|
| **Feature** | Worker Issue Submission |
| **Role** | Worker |
| **Screen** | RaiseIssueScreen |
| **Priority** | High |
| **Pass/Fail** | |

**Test Steps:**
1. From the Home screen, navigate to Issues (via link or Home stack → Issues)
2. Or navigate from Profile or Home to Issues list
3. Tap "Raise Issue" or "+"
4. Verify RaiseIssueScreen shows: Assignment picker (optional), Issue Type selector, Description text area
5. Optionally select an assignment
6. Select issue type (e.g. "Payment Delay", "Safety Concern", "Harassment")
7. Enter description: "The work site does not have proper safety equipment as promised."
8. Tap "Submit"
9. Verify navigation to Issues list
10. Verify the new issue appears with status "OPEN"

---

#### TC-W-013 — Worker Issue Detail Screen

| Field | Value |
|---|---|
| **Feature** | Worker Issue Detail |
| **Role** | Worker |
| **Screen** | IssueDetailScreen |
| **Priority** | Medium |
| **Pass/Fail** | |

**Test Steps:**
1. Tap an issue from the IssuesScreen list
2. Verify the detail shows: issue type, description, status badge, date raised, related assignment (if any)
3. If RESOLVED: verify resolution notes are visible
4. Verify the worker cannot edit or delete the issue after submission

---

#### TC-W-014 — Worker Earnings Screen

| Field | Value |
|---|---|
| **Feature** | Worker Earnings (Non-MVP stub) |
| **Role** | Worker |
| **Screen** | EarningsScreen (Earnings tab) |
| **Priority** | Low |
| **Pass/Fail** | |

**Test Steps:**
1. Tap the "Earnings" bottom tab (dollar sign icon)
2. Verify the screen loads without crashing
3. Verify either real earnings data is shown OR a meaningful empty/coming-soon state
4. Verify no raw error or undefined values are shown to the user

---

#### TC-W-015 — Worker Profile and Availability

| Field | Value |
|---|---|
| **Feature** | Worker Profile |
| **Role** | Worker |
| **Screen** | ProfileScreen (Profile tab) |
| **Priority** | Medium |
| **Pass/Fail** | |

**Test Steps:**
1. Tap the "Profile" bottom tab
2. Verify the screen shows: full name, city, state, skills, experience, availability days and shifts, payment method (UPI/Bank)
3. Verify bank details are NOT shown in plain text (they are encrypted on backend — UI should show masked or confirmed icon)
4. Tap "Edit Profile" or the edit icon
5. Update a skill (add or remove one)
6. Save changes → verify the profile updates

**Availability Screen:**
7. Tap "Manage Availability" or "Availability"
8. Verify AvailabilityScreen shows a weekly calendar
9. Tap a day to toggle available/unavailable
10. Save → verify changes persist

---

## D. Feature-by-Feature Manual Test Cases

---

### D1 — Admin Logout

| Field | Value |
|---|---|
| **Feature** | Admin Logout |
| **Role** | Admin |
| **Priority** | High |
| **Pass/Fail** | |

**Test Steps:**
1. Log in as admin
2. Click the user avatar or profile block in the sidebar footer
3. Find and click "Logout" (or it may be in a dropdown from the avatar)
4. Verify redirect to `/login`
5. Verify `admin_access_token`, `admin_refresh_token`, `admin_user` are cleared from localStorage
6. Try to navigate to `/dashboard` directly → verify redirect back to `/login`

---

### D2 — OTP Flow Rate Limiting

| Field | Value |
|---|---|
| **Feature** | Auth Rate Limiting |
| **Role** | Client or Worker |
| **Priority** | High |
| **Pass/Fail** | |

**Test Steps:**
1. Open the client or worker app
2. Enter a phone number and tap Send OTP 6+ times rapidly
3. Verify the backend returns a rate limit error (HTTP 429)
4. Verify a user-friendly message appears (not a raw HTTP code)
5. Verify the Send OTP button is temporarily disabled after the error

---

### D3 — Search, Filter, and Pagination (Admin)

| Field | Value |
|---|---|
| **Feature** | Data Filtering |
| **Role** | Admin |
| **Priority** | Medium |
| **Pass/Fail** | |

**Test Steps:**
1. Go to `/requirements` with at least 5+ requests in different statuses
2. Filter by status "APPROVED" → verify only APPROVED entries appear
3. Change filter to "IN_PROGRESS" → verify table refreshes
4. Clear all filters → verify full list returns
5. Go to `/workers` with 20+ workers
6. Verify pagination controls appear at the bottom of the table
7. Verify "Showing 1–20 of X" count is displayed
8. Click page 2 → verify next set of workers loads
9. Search for a partial worker name → verify results narrow
10. Combine search + filter (e.g. search "Murugan" + filter AVAILABLE) → verify combined results

---

### D4 — Status Badge Visual Verification

| Field | Value |
|---|---|
| **Feature** | Status Badges |
| **Role** | Admin |
| **Priority** | Medium |
| **Pass/Fail** | |

**Test Steps for each status:**

Requirements:
| Status | Expected Badge Color | Check |
|---|---|---|
| DRAFT | Grey background, grey text | |
| SUBMITTED | Blue background, blue text | |
| UNDER_REVIEW | Purple background, purple text | |
| APPROVED | Green background, green text | |
| WORKERS_ASSIGNED | Dark green background, dark green text | |
| IN_PROGRESS | Teal background, teal text, pulsing dot | |
| COMPLETED | Green background, green text | |
| CANCELLED | Red background, red text | |
| REJECTED | Red background, red text | |

Attendance:
| Status | Expected Badge Color | Check |
|---|---|---|
| NOT_STARTED | Grey | |
| CHECKED_IN | Teal (pulsing) | |
| CHECKED_OUT | Blue | |
| VERIFIED | Green | |
| ABSENT | Red | |
| LATE | Amber | |

---

### D5 — Empty States

| Field | Value |
|---|---|
| **Feature** | Empty State Design |
| **Role** | Admin |
| **Priority** | Medium |
| **Pass/Fail** | |

**Test Steps:**
1. Go to `/complaints` with no complaints → verify an icon, a title ("All clear"), and a body message appear (NOT a blank white page)
2. Search for a non-existent worker name → verify "No workers match" with an icon and "Clear filters" button
3. Go to `/requirements` with status filter that returns nothing → verify empty state
4. New client mobile home screen with no requests → verify empty state for Active Jobs section
5. Worker attendance history with no records → verify empty state

---

### D6 — Loading States

| Field | Value |
|---|---|
| **Feature** | Skeleton Loaders |
| **Role** | All |
| **Priority** | Medium |
| **Pass/Fail** | |

**Test Steps:**
1. Throttle network to "Slow 3G" in DevTools (admin) or airplane mode briefly (mobile)
2. Navigate to `/requirements` — verify skeleton loader rows appear before data loads
3. Open a requirement detail — verify skeleton placeholder appears for the detail sections
4. On mobile client, navigate to Jobs tab — verify loading skeleton or spinner appears before list loads
5. Verify no blank white screens are shown at any point during loading

---

### D7 — Form Validation (Admin)

| Field | Value |
|---|---|
| **Feature** | Form Validation |
| **Role** | Admin |
| **Priority** | High |
| **Pass/Fail** | |

**Test Steps:**
1. Open the "Add Client" dialog
2. Immediately tab through all fields without entering any data
3. Verify each required field shows an error indicator (red border + error message below the field)
4. Verify required fields are marked with `*`
5. Enter an invalid email (no "@") in the Email field
6. Tab to the next field → verify inline error "Invalid email format" appears
7. Fix the email, verify error clears
8. Verify form cannot be submitted with validation errors (Submit button remains disabled or shows errors on click)

---

### D8 — Toast Notifications (Admin)

| Field | Value |
|---|---|
| **Feature** | Toast Feedback |
| **Role** | Admin |
| **Priority** | Medium |
| **Pass/Fail** | |

**Test Steps:**
1. Create a new client → verify a success toast appears in the top-right corner
2. Verify toast has: green left border, check icon, message text
3. Verify toast auto-dismisses after ~4 seconds
4. Trigger an error (e.g. try to deactivate a client as Ops Admin) → verify an error toast with red border appears
5. Verify toast auto-dismisses after ~7 seconds (error toasts stay longer)
6. Verify clicking the X button on a toast closes it immediately

---

## E. End-to-End Business Workflow Tests

---

### E2E-001 — Full Core Flow: Client Request to Attendance Verification

| Field | Value |
|---|---|
| **Scenario** | Client creates request → Admin approves → Admin assigns → Worker accepts → Worker checks in/out → Admin verifies |
| **Roles Involved** | Client, Admin, Worker |
| **Priority** | Critical |
| **Pass/Fail** | |

**Preconditions:**
- Admin account active
- Client account active with ClientProfile
- Worker account active (approved and past biometric setup)
- All three apps running

**Steps:**

**PHASE 1 — Client Creates and Submits Request (Client Mobile):**
1. Log in as client on mobile app
2. Tap "+" or "Create Request" from Jobs tab
3. Complete all 4 steps of the form:
   - Category: "General Labour"
   - Location: "Sriperumbudur, Tamil Nadu" (use a location close to a GPS point you can simulate)
   - Workers: 2
   - Start Date: tomorrow
   - Duration: 7 days
   - Shift: "General: 09:00-18:00"
   - Skills: "Loading"
4. Tap "Submit"
5. Note the Requirement ID shown or remember you can find it in the list
6. Verify status is SUBMITTED on the client's Jobs tab

**PHASE 2 — Admin Reviews and Approves (Admin Web):**
7. Log in as admin on web
8. Navigate to `/requirements` — find the SUBMITTED request
9. Click the request → verify it auto-transitions to UNDER_REVIEW
10. Click "Approve"
11. Confirm in dialog
12. Verify status = APPROVED

**PHASE 3 — Admin Assigns Worker (Admin Web):**
13. On the requirement detail page, click "Assign Workers"
14. In the assignment modal, select the test worker
15. Click "Assign"
16. Verify status = WORKERS_ASSIGNED
17. Verify the worker appears in the assigned workers section

**PHASE 4 — Worker Accepts Assignment (Worker Mobile):**
18. On worker mobile, refresh or wait for the new assignment to appear
19. Verify the HomeScreen hero card shows the new ASSIGNED job
20. Tap "Accept"
21. Verify status changes to ACCEPTED in the hero card
22. Verify the "Check In" button appears (but check-in is only valid during shift time or in test mode)

**PHASE 5 — Worker Checks In (Worker Mobile):**
23. Enable GPS on the device (or use a test location matching the job site coordinates)
24. Tap "Check In"
25. Verify location permission dialog (approve it)
26. Verify successful check-in confirmation (pulsing green dot + "Checked in at [time]")
27. In admin web → `/attendance` → verify a new attendance record appears with status CHECKED_IN

**PHASE 6 — Worker Checks Out (Worker Mobile):**
28. Tap "Check Out"
29. Verify the hero card shows both check-in and check-out times
30. In admin web, verify the attendance record now shows CHECKED_OUT

**PHASE 7 — Admin Verifies Attendance (Admin Web):**
31. Navigate to `/attendance`
32. Enter the Requirement ID from phase 1
33. Find the worker's attendance record with status CHECKED_OUT
34. Click "Verify"
35. Verify the record status changes to VERIFIED (green badge)

**PHASE 8 — Client Sees Updated Status (Client Mobile):**
36. Open the client app
37. Navigate to the job request
38. Tap "View Workers"
39. Verify the worker's attendance shows as CHECKED_OUT or VERIFIED
40. Verify check-in and check-out times are displayed

**Expected Result:** The full flow completes without errors or broken states. All status transitions occur correctly.

---

### E2E-002 — Complaint Raise and Resolution Flow

| Field | Value |
|---|---|
| **Scenario** | Client raises complaint → Admin reviews → Admin resolves → Client sees resolution |
| **Roles Involved** | Client, Admin |
| **Priority** | High |
| **Pass/Fail** | |

**Steps:**
1. On client mobile: tap Complaints tab → tap "Raise Complaint"
2. Select an active requirement
3. Select type: "Worker Behaviour"
4. Select severity: "High"
5. Enter: "Workers are not following site safety protocols."
6. Tap Submit → verify complaint created with status OPEN

7. On admin web: navigate to `/complaints`
8. Find the new complaint with status OPEN (blue badge)
9. Click it → verify detail page shows client's description

10. Click "Mark In Review"
11. Verify status changes to IN_REVIEW (purple)

12. Click "Resolve"
13. In the resolution dialog, enter: "Safety briefing conducted on-site. Workers confirmed compliance."
14. Click "Resolve Complaint"
15. Verify status changes to RESOLVED (green)

16. On client mobile: navigate to Complaints tab
17. Find the complaint → verify status badge now shows RESOLVED
18. Tap the complaint → verify ComplaintDetailScreen shows resolution notes

**Expected Result:** Client sees the resolution note. Status reflects correctly on both sides.

---

### E2E-003 — Worker Onboarding to First Check-In

| Field | Value |
|---|---|
| **Scenario** | New worker completes full onboarding → Admin approves → Worker sets up biometrics → Worker gets a job → First check-in |
| **Roles Involved** | Worker (new), Admin |
| **Priority** | Critical |
| **Pass/Fail** | |

**Steps:**
1. Open worker app with a fresh, never-registered phone number (e.g. `9000000001`)
2. Enter phone → receive OTP → enter OTP
3. Complete BuildProfileScreen (name, city, state, skills, experience, availability)
4. Agree to ConsentScreen
5. Upload ID photo and selfie on VerifyIdentityScreen
6. Verify ProfileSubmittedScreen appears
7. Verify subsequent app opens show the UnderReviewScreen

8. On admin web: navigate to `/workers`, filter by "Under Review"
9. Click the worker's row
10. Click "Approve"
11. Confirm approval

12. Worker opens app again → verify BiometricSetupScreen appears (not Under Review)
13. Enable biometrics → verify HomeScreen appears
14. Admin assigns this worker to a job (see E2E-001 Phase 3)
15. Worker accepts → checks in → verify full flow

**Expected Result:** Complete new worker journey works end-to-end.

---

### E2E-004 — Worker Raises an Issue During a Job

| Field | Value |
|---|---|
| **Scenario** | Worker raises issue about a job → Admin reviews it as a complaint |
| **Roles Involved** | Worker, Admin |
| **Priority** | High |
| **Pass/Fail** | |

**Steps:**
1. Worker is on an active assignment
2. On worker HomeScreen, navigate to Issues (via Home stack)
3. Tap "Raise Issue"
4. Select the active assignment from the dropdown
5. Select type: "Safety Concern"
6. Enter: "The machine is not properly guarded. Risk of injury."
7. Tap Submit → verify success

8. On admin web: navigate to `/complaints` (worker issues are shown here)
9. Find the issue → click it
10. Verify type shows as Worker issue
11. Admin marks IN_REVIEW, then RESOLVED with notes
12. Worker opens IssueDetailScreen → verify RESOLVED status and resolution note visible

---

## F. Negative and Edge Case Tests

---

### TC-NEG-001 — GPS Geofence Rejection

| Field | Value |
|---|---|
| **Feature** | GPS Check-In Validation |
| **Role** | Worker |
| **Priority** | High |
| **Pass/Fail** | |

**Test Steps:**
1. Set up a job with location: Chennai (lat 13.0827, lng 80.2707)
2. Use a device or emulator with a spoofed location far away (e.g. Bengaluru: lat 12.9716, lng 77.5946 — about 290 km away)
3. Worker attempts to check in
4. Verify API returns 400
5. Verify the app shows: "You are too far from the job site to check in." (exact or equivalent message)
6. Verify the "Check In" button does NOT change to a confirmed state

---

### TC-NEG-002 — Submit Job Request Without Required Fields (Client Mobile)

| Field | Value |
|---|---|
| **Feature** | Form Validation — Client |
| **Role** | Client |
| **Priority** | High |
| **Pass/Fail** | |

**Test Steps:**
1. Open CreateRequestScreen
2. On Step 1: do NOT select any job category
3. Tap "Next" or "Continue"
4. Verify an error message appears and navigation is blocked
5. On Step 2: clear the location field
6. Tap "Next" → verify location is required
7. On Step 3: clear start date
8. Tap "Next" → verify error
9. Try to submit a form with number_of_workers = 0 → verify minimum validation

---

### TC-NEG-003 — Client Cannot Access Admin Pages

| Field | Value |
|---|---|
| **Feature** | Role-Based Access |
| **Role** | Client (attempting admin access) |
| **Priority** | Critical |
| **Pass/Fail** | |

**Test Steps:**
1. On client mobile, capture the client's JWT token from SecureStore or network logs
2. In a REST client (Postman / Insomnia), make a request to `GET /api/v1/admin/people/clients` with the client's Bearer token
3. Verify the API returns HTTP 403 Forbidden
4. Try `GET /api/v1/admin/dashboard/summary` with client token → verify 403
5. Try `POST /api/v1/admin/requirements/{id}/approve` with client token → verify 403

---

### TC-NEG-004 — Worker Cannot Access Client Data

| Field | Value |
|---|---|
| **Feature** | Role-Based Access |
| **Role** | Worker |
| **Priority** | Critical |
| **Pass/Fail** | |

**Test Steps:**
1. Get worker's JWT token
2. In Postman: `GET /api/v1/client/requirements` with worker token → verify 403
3. `GET /api/v1/admin/people/workers` with worker token → verify 403
4. `POST /api/v1/client/requirements` with worker token → verify 403

---

### TC-NEG-005 — Ownership Check: Client Cannot See Another Client's Data

| Field | Value |
|---|---|
| **Feature** | Data Ownership |
| **Role** | Client |
| **Priority** | Critical |
| **Pass/Fail** | |

**Preconditions:** Two client accounts exist — Client A and Client B. Client B has a requirement with ID `REQ_B_ID`.

**Test Steps:**
1. Log in as Client A, get Client A's token
2. In Postman: `GET /api/v1/client/requirements/{REQ_B_ID}` with Client A's token
3. Verify: HTTP 403 (not 200, and not 404 — should be 403 because the resource exists but is not owned by Client A)
4. Verify the response body does NOT contain Client B's data

---

### TC-NEG-006 — Invalid State Transitions

| Field | Value |
|---|---|
| **Feature** | Business Rule Enforcement |
| **Role** | Admin (via Postman) |
| **Priority** | High |
| **Pass/Fail** | |

**Test Steps:**
1. Create a COMPLETED requirement
2. Try to approve it via Postman: `POST /api/v1/admin/requirements/{id}/approve` → verify 400 (invalid transition)
3. Create a REJECTED requirement
4. Try to assign workers to it → verify 400
5. Try to check in a worker with a DECLINED assignment → verify 400
6. Try to check in a worker who is already CHECKED_IN → verify 400

---

### TC-NEG-007 — Duplicate Assignment Prevention

| Field | Value |
|---|---|
| **Feature** | Assignment Business Rules |
| **Role** | Admin |
| **Priority** | High |
| **Pass/Fail** | |

**Test Steps:**
1. Assign Worker A to Job X
2. Try to assign Worker A to the same Job X again → verify backend returns 400
3. Verify error message explains the worker is already assigned
4. In admin UI: if the worker appears in the assignment modal, verify they are shown as "blocked" not selectable for the same job

---

### TC-NEG-008 — Token Expiry (Mobile)

| Field | Value |
|---|---|
| **Feature** | Token Management — Mobile |
| **Role** | Client or Worker |
| **Priority** | High |
| **Pass/Fail** | |

**Test Steps:**
1. Log in on mobile app
2. In the backend, force the access token to expire (or wait 30 minutes)
3. Make an API call in the app (e.g. navigate to Jobs tab)
4. Verify the app silently refreshes the token using the refresh token
5. Verify the app continues to work without showing a login screen

**If refresh token also expires (30 days):**
6. Expire both tokens
7. Verify the app redirects to the Login screen with a message

---

### TC-NEG-009 — Deactivated Client Login Attempt

| Field | Value |
|---|---|
| **Feature** | Account Status Check |
| **Role** | Client (deactivated) |
| **Priority** | Medium |
| **Pass/Fail** | |

**Preconditions:** A client has been deactivated by a Super Admin.

**Test Steps:**
1. Try to log in as the deactivated client (phone OTP)
2. Verify the OTP is sent but on verification, login is rejected
3. Verify an appropriate error message (e.g. "Your account has been deactivated. Please contact admin.")
4. Verify the deactivated client cannot access any API endpoints even with a previously valid token

---

### TC-NEG-010 — Invalid OTP Expiry

| Field | Value |
|---|---|
| **Feature** | OTP Validation |
| **Role** | Client or Worker |
| **Priority** | Medium |
| **Pass/Fail** | |

**Test Steps:**
1. Request an OTP for a phone number
2. Wait for the OTP to expire (check backend config for OTP TTL — typically 5 minutes)
3. Enter the expired OTP
4. Verify error message: "OTP has expired. Please request a new one." or equivalent
5. Tap "Resend OTP" → verify new OTP is sent

---

## G. Role and Permission Testing

---

### TC-PERM-001 — Super Admin vs Ops Admin: Deactivate Permissions

| Test | Super Admin | Ops Admin | Expected |
|---|---|---|---|
| Deactivate a client | Yes | No | Ops Admin sees no deactivate button |
| Deactivate a worker | Yes | No | Ops Admin sees no deactivate button |
| Invite a new admin | Yes | No | Ops Admin cannot access /admin-users |
| Override verified attendance | Yes | No | Ops Admin correction is blocked |
| Approve a job request | Yes | Yes | Both can approve |
| Assign workers | Yes | Yes | Both can assign |
| Resolve a complaint | Yes | Yes | Both can resolve |

**Test Steps for each row:**
1. Log in as Ops Admin
2. Navigate to the relevant page
3. Verify the restricted actions are hidden from the UI
4. Verify that directly calling the API with the Ops Admin token also returns 403 for restricted actions

---

### TC-PERM-002 — Client Cannot See Other Clients' Workers

| Field | Value |
|---|---|
| **Feature** | Worker Data Privacy |
| **Role** | Client |
| **Priority** | Critical |
| **Pass/Fail** | |

**Test Steps:**
1. Log in as Client A who has workers assigned
2. Navigate to AssignedWorkersScreen for their own job
3. Verify they can see: worker full name, skills, check-in status
4. Verify they CANNOT see: worker's phone number, bank details, ID documents, salary/rate
5. Via Postman with Client A's token: `GET /api/v1/workers/{worker_id}` → verify 403 (workers endpoint is admin-only)

---

### TC-PERM-003 — Worker Cannot See Other Workers' Data

| Field | Value |
|---|---|
| **Feature** | Worker Data Privacy |
| **Role** | Worker |
| **Priority** | Critical |
| **Pass/Fail** | |

**Test Steps:**
1. Log in as Worker A, get their token
2. Via Postman: `GET /api/v1/worker/profile` → verify returns only Worker A's profile
3. `GET /api/v1/admin/people/workers` with Worker A's token → verify 403
4. Try to access Worker B's attendance: `GET /api/v1/worker/attendance` → verify returns only Worker A's records

---

### TC-PERM-004 — Protected Admin Routes Redirect Unauthenticated Users

| Field | Value |
|---|---|
| **Feature** | Route Protection |
| **Role** | Unauthenticated |
| **Priority** | Critical |
| **Pass/Fail** | |

**Test Steps:**
1. In a fresh browser (no cookies, no localStorage), navigate directly to:
   - `http://localhost:3000/dashboard` → verify redirect to `/login`
   - `http://localhost:3000/requirements` → verify redirect to `/login`
   - `http://localhost:3000/workers` → verify redirect to `/login`
   - `http://localhost:3000/clients` → verify redirect to `/login`
2. Verify that the browser does NOT briefly flash the protected page content before redirecting

---

### TC-PERM-005 — Admin Cannot Access Client or Worker API Paths

| Field | Value |
|---|---|
| **Feature** | Role Segregation |
| **Role** | Admin |
| **Priority** | High |
| **Pass/Fail** | |

**Test Steps:**
1. Get admin JWT token
2. Via Postman: `POST /api/v1/client/requirements` with admin token → verify 403
3. `POST /api/v1/worker/attendance/checkin` with admin token → verify 403
4. `GET /api/v1/worker/assignments` with admin token → verify 403

---

## H. Mobile and Responsive Testing

---

### TC-MOB-001 — Client App Responsive Layout

| Field | Value |
|---|---|
| **Feature** | Mobile Responsive Layout |
| **Role** | Client |
| **Priority** | Medium |
| **Pass/Fail** | |

**Test on devices:** iPhone SE (375px), iPhone 14 Pro Max (430px), Android medium (360px), Android large (412px)

**Test Steps:**
1. Open client app on the smallest test device (375px width)
2. Verify the Job Request card on HomeScreen is fully readable without horizontal scroll within the card
3. Verify the 4-step Create Request form fields stack correctly and are not cut off
4. Verify bottom tab bar labels are readable at small screen size
5. Verify modals (complaint form) appear as bottom sheets and do not overflow the screen
6. Open on the largest device (430px)
7. Verify no excessive padding or overly large elements

---

### TC-MOB-002 — Worker App Hero Card

| Field | Value |
|---|---|
| **Feature** | Worker Dashboard Hero Card |
| **Role** | Worker |
| **Priority** | High |
| **Pass/Fail** | |

**Test Steps:**
1. On various device sizes, verify the dark green hero card (brand-900 background) fills the screen correctly
2. Verify "Check In" button (56px height) is fully visible and tappable
3. Verify the "This Week" strip fits all 5 day tiles without overflow
4. Verify the greeting text does not truncate the admin name on small screens

---

### TC-MOB-003 — Safe Area Insets

| Field | Value |
|---|---|
| **Feature** | Safe Area / Notch / Home Bar |
| **Role** | Client and Worker |
| **Priority** | Medium |
| **Pass/Fail** | |

**Test Steps (iOS with notch / Dynamic Island):**
1. Open both apps on iPhone with notch or Dynamic Island
2. Verify the top status bar area is not obscured by content
3. Verify the bottom tab bar correctly adds safeAreaInsets.bottom padding
4. Verify the fixed "Check In" button on worker app does not overlap the home indicator bar

**Test Steps (Android with gesture navigation):**
1. Verify the bottom tab bar has adequate padding above gesture navigation zone
2. Verify no content is obscured by system gesture zones

---

### TC-MOB-004 — Keyboard Handling

| Field | Value |
|---|---|
| **Feature** | Keyboard + Form Interaction |
| **Role** | Client |
| **Priority** | Medium |
| **Pass/Fail** | |

**Test Steps:**
1. Open CreateRequestScreen, tap a text input field
2. Verify the keyboard appears and the focused input scrolls into view (not hidden behind keyboard)
3. On the notes/description field at the bottom of the form, verify the keyboard does not cover the input
4. Verify tapping outside the keyboard or tapping a "Done" button dismisses the keyboard

---

### TC-MOB-005 — Pull to Refresh

| Field | Value |
|---|---|
| **Feature** | Pull-to-Refresh |
| **Role** | Client and Worker |
| **Priority** | Low |
| **Pass/Fail** | |

**Test Steps:**
1. Open the client Jobs tab (RequestsScreen)
2. Pull down from the top of the list
3. Verify a loading indicator appears
4. Release → verify the list reloads
5. Repeat on worker AttendanceHistoryScreen and HomeScreen

---

## I. Browser Compatibility Testing

---

### TC-BROWSER-001 — Admin Dashboard Cross-Browser

| Field | Value |
|---|---|
| **Feature** | Browser Compatibility |
| **Role** | Admin |
| **Priority** | Medium |
| **Pass/Fail** | |

**Test the admin web app in:**
| Browser | Version | Login Works | Dashboard Loads | Tables Render | Forms Submit | Pass/Fail |
|---|---|---|---|---|---|---|
| Chrome | Latest | | | | | |
| Firefox | Latest | | | | | |
| Safari | Latest (macOS) | | | | | |
| Edge | Latest | | | | | |
| Chrome (mobile) | Latest | | | | | |
| Safari (iOS) | Latest | | | | | |

**For each browser, test:**
1. Navigate to the admin login page
2. Log in with email and password
3. Navigate through the sidebar
4. Open a requirements detail page
5. Open the assignment modal
6. Submit a form (e.g. add a client)
7. Verify status badges render with correct colors
8. Verify the sidebar collapses and expands correctly

---

### TC-BROWSER-002 — Sidebar Collapse

| Field | Value |
|---|---|
| **Feature** | Sidebar Collapse (Admin) |
| **Role** | Admin |
| **Priority** | Low |
| **Pass/Fail** | |

**Test Steps:**
1. On admin web, find the sidebar toggle (rail/collapse control)
2. Click to collapse the sidebar
3. Verify sidebar collapses to icon-only mode (shows only icons, no text labels)
4. Verify the main content area expands to fill the space
5. Verify tooltips appear on sidebar icon hover in collapsed mode
6. Click to expand → verify sidebar returns to full width

---

## J. Missing UI Features Found

The following screens or features have partial or placeholder implementations that are **not fully MVP-complete** and should be verified before production:

| # | Screen / Feature | Status | Notes |
|---|---|---|---|
| J1 | `InvoiceDetailScreen` (client mobile) | Present but not MVP | Out of MVP scope. Verify it does not crash if navigated to. Confirm it shows a "Coming soon" or is unreachable from normal navigation. |
| J2 | `PaymentConfirmScreen` (client mobile) | Present but not MVP | Out of MVP scope. Same as above. |
| J3 | `RateRequirementScreen` (client mobile) | Present but not MVP | Worker rating system is post-MVP. |
| J4 | `BillingOverviewScreen` (client mobile) | Present but not MVP | Finance screens are V2. |
| J5 | `EarningsScreen` (worker mobile) | Present but not MVP | Worker earnings display is V2. Verify it shows a meaningful empty/stub state. |
| J6 | `BillingOverviewScreen` (client mobile) | Present but not MVP | Finance billing V2. |
| J7 | Worker Notification Bell | UI present | Bell icon in worker HomeScreen. Verify it either shows notifications or shows an empty state. Does NOT crash. |
| J8 | Push Notifications (FCM) | Backend model present | FCM push token endpoint exists (`PATCH /auth/fcm-token/`). Mobile FCM integration status not fully confirmed. Manual test: verify that receiving a push notification while app is backgrounded actually works. |
| J9 | Admin Notifications | Bell icon in TopBar | Verify unread count badge appears or disappears correctly. Verify clicking opens notification list or is gracefully handled. |

---

## K. Backend Features Without Full UI

The following backend capabilities exist and are enforced but may not have a complete UI surface:

| # | Backend Feature | API Endpoint | UI Status | What to Test |
|---|---|---|---|---|
| K1 | Bulk attendance verify | `POST /api/v1/admin/attendance/bulk-verify` | No bulk verify UI found in admin | Test via API directly. Add to admin attendance page backlog. |
| K2 | Mark attendance as ABSENT | `PATCH /api/v1/admin/attendance/{id}/mark-absent` | Not confirmed in admin UI | Look for an "Absent" button in the attendance table. Test it. |
| K3 | Mark attendance as LATE | Not an explicit endpoint; set via correction | Admin can correct time and system derives LATE | Verify the status correctly shows LATE after a time correction resulting in late arrival |
| K4 | Worker interest toggle | `POST /api/v1/worker/interest` | Worker JobsBoardScreen has interest button | Test that tapping interest button registers. Verify admin can see worker interest. |
| K5 | Social auth | `apps/backend/app/api/auth_social.py` | No social login UI in mobile | Backend stub exists. Not in MVP scope. Verify it is unreachable from current UI. |
| K6 | Client payments webhook | `apps/backend/app/api/payment_webhooks.py` | No payment flow in mobile MVP | V2 feature. Backend endpoint exists. No UI surface needed now. |
| K7 | Client ratings | `apps/backend/app/api/client_ratings.py` | `RateRequirementScreen` is a stub | Test the screen loads. Verify no crash. V2 feature. |
| K8 | Admin invite new admin | `POST /api/v1/auth/admin/invite/` | Admin Users page should cover this | Verify the invite flow works end to end. |
| K9 | Accept admin invite | `POST /api/v1/auth/admin/accept-invite/` | No admin invite accept UI found | Test via API directly. Invited admin needs a UI to set password. Verify or flag as a gap. |
| K10 | Admin maintenance mode | `apps/backend/app/api/admin_maintenance.py` | No UI | Admin-only endpoint. Test via API. |
| K11 | Change own password | `POST /api/v1/auth/change-password/` | Settings page or profile page should have this | Verify the "Change Password" form exists and works. |
| K12 | Worker availability toggle (home) | `PATCH /api/v1/worker/availability` | Worker HomeScreen has availability toggle | Verify the toggle saves to backend and admin can see the updated availability status. |

---

## L. Final Manual QA Checklist Before Production

Use this checklist as the final sign-off gate before going live.

### Authentication

- [ ] Admin email + password login works
- [ ] Admin redirect to `/dashboard` after login
- [ ] Admin redirect to `/login` if not authenticated
- [ ] Client phone + OTP login works
- [ ] Client new user creates profile (ProfileSetupScreen if applicable)
- [ ] Worker phone + OTP login works
- [ ] Worker onboarding full flow: Phone → OTP → Build Profile → Consent → ID Upload → Under Review
- [ ] Admin approval changes worker status from Under Review to Active
- [ ] Worker biometric setup appears after first approval
- [ ] Worker biometric check on returning login
- [ ] Token auto-refresh works on admin web (axios interceptor)
- [ ] Token auto-refresh works on client mobile
- [ ] Token auto-refresh works on worker mobile
- [ ] Expired session redirects to login

### Admin Web

- [ ] Sidebar shows all navigation groups: Operations, Finance, Management
- [ ] All sidebar links navigate to correct pages
- [ ] Dashboard KPI stat cards load real data
- [ ] Clients list: search, hover actions, row click → detail
- [ ] Create client dialog: validation, success, error
- [ ] Edit client dialog: pre-filled, saves correctly
- [ ] Deactivate client (Super Admin only)
- [ ] Client detail: shows requirements history
- [ ] Workers list: search, availability filter
- [ ] Worker detail: profile, skills, status
- [ ] Worker approval from worker detail page
- [ ] Requirements list: status filter, correct badge colors
- [ ] Requirement detail: shows all fields, timeline, quote section
- [ ] Approve requirement: status transitions, confirmation dialog
- [ ] Reject requirement: requires reason, status transitions
- [ ] Assign workers modal: ready/blocked counts, selectable workers
- [ ] Assignments list page loads
- [ ] Assignment detail: shows worker info, status, replace option
- [ ] Attendance lookup by Requirement ID
- [ ] Attendance lookup by Assignment ID
- [ ] Attendance stat summary cards
- [ ] Verify single attendance record
- [ ] Correct attendance (Super Admin can correct verified records)
- [ ] Complaints list: status filter, badge colors
- [ ] Complaint detail: full context shown
- [ ] Mark complaint IN_REVIEW
- [ ] Resolve complaint with notes
- [ ] Reject complaint with reason
- [ ] Payroll list page loads (or empty state)
- [ ] Finance page loads (or empty state)
- [ ] Reports sub-pages: requirements, assignments, complaints
- [ ] Report filters (date range, status) work
- [ ] Audit log page loads
- [ ] SLA page loads
- [ ] Admin Users page (Super Admin): shows list, invite works
- [ ] Settings page loads, profile info visible
- [ ] Replacements page loads

### Client Mobile

- [ ] Welcome → Login → OTP → Home flow
- [ ] Home shows active jobs, stats, recent activity
- [ ] Jobs tab shows all client requirements
- [ ] Create Request 4-step form all steps complete
- [ ] Save as DRAFT preserves data
- [ ] Submit changes status to SUBMITTED
- [ ] Request Detail shows full info and timeline
- [ ] View Assigned Workers from Request Detail
- [ ] AssignedWorkers shows per-worker attendance
- [ ] "Raise complaint" shortcut from AssignedWorkers navigates to correct screen
- [ ] Complaints tab shows client's complaints
- [ ] Raise Complaint form submits successfully
- [ ] Complaint Detail shows resolution notes when RESOLVED
- [ ] Profile screen shows company info in 3 sections
- [ ] Edit Profile slide-up modal saves changes

### Worker Mobile

- [ ] Welcome → Login → OTP → Onboarding flow (new user)
- [ ] Welcome → Login → OTP → Biometric check → Home (returning user)
- [ ] Under Review screen shown for unapproved workers
- [ ] Biometric setup one-time on first approval
- [ ] Home hero card shows today's assignment
- [ ] Home hero card shows "No shift today" when no assignment
- [ ] Accept assignment changes status to ACCEPTED
- [ ] Decline assignment changes status to DECLINED
- [ ] Check In: GPS validated, changes status to CHECKED_IN
- [ ] Check In: blocked when outside geofence
- [ ] Check Out: records time, changes status to CHECKED_OUT
- [ ] This Week strip shows attendance color coding
- [ ] Jobs tab (JobsBoardScreen) shows available/nearby jobs
- [ ] JobDetailScreen shows full job info
- [ ] Attendance tab shows attendance history
- [ ] Earnings tab loads without crash
- [ ] Issues list accessible from Home
- [ ] Raise Issue form submits correctly
- [ ] Issue detail shows resolution notes
- [ ] Profile tab shows worker info
- [ ] Profile edit saves correctly
- [ ] Availability screen allows day/shift toggle

### Security and Permissions

- [ ] Client cannot call admin API endpoints (403)
- [ ] Worker cannot call client or admin API endpoints (403)
- [ ] Admin cannot call client or worker API endpoints (403)
- [ ] Ops Admin cannot deactivate accounts (403)
- [ ] Ops Admin cannot modify verified attendance (403)
- [ ] Client A cannot access Client B's requirements (403)
- [ ] Worker A cannot access Worker B's attendance (403)
- [ ] Unauthenticated requests to all protected endpoints return 401
- [ ] OTP rate limiting works (6+ requests → 429)
- [ ] Admin password login rate limiting works

### UX / Design

- [ ] All required form fields marked with *
- [ ] Inline form errors appear on blur (not only on submit)
- [ ] Error messages are human-readable (no stack traces or "undefined")
- [ ] All empty states have an icon, title, and body message
- [ ] All loading states show skeleton loaders (not blank pages)
- [ ] Success/error toast notifications appear for all critical actions
- [ ] Confirmation modals appear before all destructive or irreversible actions
- [ ] Status badges use correct colors consistently
- [ ] IN_PROGRESS and CHECKED_IN status badges have pulsing dot animation
- [ ] All modal/dialog close buttons work
- [ ] All back navigation works correctly
- [ ] No "undefined", "null", or "[object Object]" visible to end users

### Connectivity and Edge Cases

- [ ] API errors (500) show a user-friendly error message, not a crash
- [ ] Network offline: mobile apps show a meaningful offline message
- [ ] Slow network: loading states appear correctly
- [ ] GPS unavailable on worker check-in: shows error, does not crash
- [ ] Large data sets: pagination controls appear and work

---

## M. Physical Device Testing Requirements

> **Important:** The following tests **require a real physical device** (iOS or Android). They cannot be verified on simulators/emulators, as simulators lack GPS hardware, push notification support, and realistic network conditions.

### M1 — Push Notifications (physical device required)

| Event | Notification Title | Deep-link Tab |
|---|---|---|
| Worker profile approved | "Profile Approved!" | HomeTab |
| Worker assigned to job | "New job assigned" | HomeTab |
| Worker assignment replaced | (old worker) | JobsTab |
| New assignment after replacement | "New Job" | HomeTab |
| Attendance marked no-show | "Attendance marked as no-show" | HomeTab |
| Attendance rejected | "Attendance Not Approved" | AttendanceTab |
| Assignment extended | "Assignment extended" | JobsTab |
| Disbursement paid | "Payment Processed" | EarningsTab |
| Disbursement failed | "Payment Issue" | EarningsTab |
| Invoice issued to client | "Invoice Issued" | JobsTab |
| Dispute resolved | "Dispute Resolved" | ComplaintsTab |
| Dispute closed | "Dispute Closed" | ComplaintsTab |

**Verification steps for each row:**
1. Ensure the push token is registered (first login on a physical device registers it automatically).
2. Trigger the backend action (via admin web or API call).
3. Confirm the notification appears in the device notification tray.
4. Tap the notification — the app must open and navigate to the correct tab listed above.
5. Verify the notification appears even when the app is in the background or closed.

**Setup:**
```bash
# Expo Go or a dev build is required — push does not work in simulator
cd apps/mobile-ui-lab
# Worker variant:
EXPO_PUBLIC_APP_VARIANT=worker npx expo start
# Client variant:
EXPO_PUBLIC_APP_VARIANT=client npx expo start
```

**Known limitation:** Expo Push only works on physical devices. `expo-notifications` will skip token registration on emulators (the `use-push-token.ts` hook detects this and exits early).

---

### M2 — GPS Check-in / Geofence (physical device required)

- [ ] Worker can check in when within the 200 m geofence radius — confirmed CHECKED_IN status
- [ ] Worker is blocked and sees an error when outside the geofence
- [ ] Check-in shows GPS accuracy (move indoors to test low-accuracy warning: > 100 m triggers "GPS accuracy is low" alert)
- [ ] Denying location permission shows "Enable location permission in Settings" alert with "Open Settings" button
- [ ] "Open Settings" button opens the correct OS settings screen (iOS: App Settings → Location; Android: App Settings → Permissions → Location)
- [ ] GPS times out gracefully (10 s) if location fix cannot be obtained — shows human-readable message, does not freeze UI
- [ ] GPS check-out flow mirrors check-in (same permission / accuracy / timeout handling)

---

### M3 — Offline / Network Resilience (physical device or Airplane Mode test)

- [ ] Enable Airplane Mode → open worker app → home screen shows cached assignment and attendance data (stale banner shown in amber/yellow)
- [ ] Enable Airplane Mode → open worker app → no cached data yet → "Could not load jobs" alert appears (no crash)
- [ ] Enable Airplane Mode → amber "No internet connection — showing cached data" banner is visible
- [ ] Restore network connection → pull-to-refresh clears stale banner and loads fresh data
- [ ] Enable Airplane Mode → attempt check-in → axios request times out in ≤ 15 s → error toast shown (not an infinite spinner)
- [ ] Same tests repeated for client app (stale banner, refresh clears it)

---

*End of QA Checklist — Annai Illam Staffing Platform*

