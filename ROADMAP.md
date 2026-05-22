# MVP Roadmap

## Roadmap Principle

This project already has code.

The first step is not to rebuild. The first step is to understand what already exists, then continue from the correct phase.

Always use:

- `apps/backend` for FastAPI backend
- `apps/admin` for admin web dashboard
- `apps/mobile-ui-lab` for mobile app (Client + Worker)

Do not recreate the deleted `apps/mobile` folder unless explicitly requested.

---

## Phase 1: Understand and Stabilise Existing Project

### Goal

Review the current backend, admin app, and mobile app. Understand what has already been built. Do not rewrite working code.

### Tasks

**Backend inspection:**
- [ ] Inspect all FastAPI routes in `apps/backend/app/api/`
- [ ] Inspect all SQLAlchemy models in `apps/backend/app/models/`
- [ ] Inspect all Pydantic schemas in `apps/backend/app/schemas/`
- [ ] Inspect all services in `apps/backend/app/services/`
- [ ] Inspect repositories if they exist
- [ ] Inspect existing tests in `apps/backend/tests/`
- [ ] Review `alembic.ini` and existing migrations

**Admin app inspection:**
- [ ] Inspect routing in `apps/admin/src/app/`
- [ ] Inspect existing components in `apps/admin/src/components/`
- [ ] Inspect existing services in `apps/admin/src/services/`
- [ ] Identify what screens have been built

**Mobile app inspection:**
- [ ] Inspect `apps/mobile-ui-lab/App.tsx`
- [ ] Inspect `apps/mobile-ui-lab/src/screens/`
- [ ] Inspect navigation structure
- [ ] Inspect `tamagui.config.ts`
- [ ] Identify what screens have been built

### Output

- Document what is complete
- Document what is broken or incomplete
- Confirm actual tech stack matches `TECH_STACK.md`
- Identify which roadmap phase to continue from

### Done When

- Project structure is fully understood
- Completed features are documented
- Gaps are identified
- Next phase is clear

---

## Phase 2: Authentication and Role Routing

### Goal

All three roles can log in and land on the correct dashboard. Wrong roles are blocked from wrong areas.

### Features

- Admin login (email + password)
- Client login (email + password)
- Worker login (phone number + OTP)
- JWT token issuance and refresh
- Role-based routing on all three apps
- Protected FastAPI endpoints
- Protected admin page routes
- Protected mobile screen routes

### Backend Work

- [ ] Confirm User model has role field (ADMIN / CLIENT / WORKER)
- [ ] Confirm login endpoint returns role in token payload
- [ ] Confirm JWT token validation middleware
- [ ] Add or fix role-based permission decorators
- [ ] OTP generation and verification endpoint for workers
- [ ] Add tests for role access control

### Admin Work

- [ ] Admin login page
- [ ] Redirect to dashboard on successful login
- [ ] Protect all admin routes (redirect to login if no valid token)
- [ ] Redirect wrong role away from admin

### Mobile Work

- [ ] Client login screen (email + password)
- [ ] Worker login screen (phone number entry)
- [ ] Worker OTP entry screen
- [ ] Role-based navigation after login
- [ ] Store JWT token securely
- [ ] Handle token expiry gracefully

**Worker first-time onboarding flow (new workers):**

- [ ] Build Profile screen (name, city, skills, availability, payment details)
- [ ] Consent screen (document retention and privacy consent)
- [ ] Identity Upload screen (government ID photo + selfie)
- [ ] Profile Submitted / Under Review screen (pending admin approval)

**Worker returning login flow:**

- [ ] Biometric Setup screen — one-time enrolment shown after admin first approves the worker
- [ ] Biometric Check screen — per-session gate for approved workers who have completed setup
- [ ] `biometricSetupDone` persisted in secure storage to distinguish first approval from subsequent logins

**Onboarding step routing (RootNavigator logic):**

```
No token              → AuthNavigator (phone entry)
profile_submitted     → Under Review screen
approved + no biometric setup  → Biometric Setup (one-time)
approved + setup done + not verified  → Biometric Check (per session)
approved + biometric passed  → App (Dashboard)
```

### Testing Checklist

- [ ] Admin can log in with correct credentials
- [ ] Client can log in with correct credentials
- [ ] Worker can log in with phone + OTP
- [ ] Incorrect password shows proper error message
- [ ] Expired OTP is rejected
- [ ] Admin token cannot access client or worker-only APIs
- [ ] Client token cannot access admin APIs
- [ ] Worker token cannot access client data
- [ ] Expired token is handled (redirect to login)
- [ ] New worker completes full onboarding flow (profile → consent → ID upload → submitted)
- [ ] Returning worker sees biometric check on login (not onboarding flow again)
- [ ] Biometric Setup shown exactly once (first login after admin approval)
- [ ] Worker under review cannot reach dashboard

### Done When

Each role reaches the correct dashboard after login. Wrong roles are blocked. Auth works across backend, admin app, and mobile app. New workers complete the full onboarding flow and approved returning workers reach the dashboard via biometric check.

---

## Phase 3: Client and Worker Management

### Goal

Admin can create and manage clients and workers through the admin dashboard.

### Features

**Client Management:**
- View list of all clients
- View client detail
- Create a new client
- Edit client details
- Deactivate a client

**Worker Management:**
- View list of all workers
- View worker detail
- Create a new worker
- Edit worker details
- Set worker availability status
- Add skill tags to worker
- Deactivate a worker

### Backend Work

- [ ] Confirm ClientCompany model and schema
- [ ] Confirm WorkerProfile model and schema
- [ ] CRUD endpoints for clients (`GET`, `POST`, `PATCH`, `DELETE`)
- [ ] CRUD endpoints for workers (`GET`, `POST`, `PATCH`, `DELETE`)
- [ ] Worker availability status field and update endpoint
- [ ] Worker skill tags field
- [ ] Permission checks (admin only for management)
- [ ] Worker can view and update own profile
- [ ] Client can view own company profile
- [ ] Tests for all endpoints

### Admin Work

- [ ] Clients list page (table with search and filter)
- [ ] Client detail page
- [ ] Add client form
- [ ] Edit client form
- [ ] Deactivate client action with confirmation modal
- [ ] Workers list page (table with skill/status filters)
- [ ] Worker detail page
- [ ] Add worker form
- [ ] Edit worker form
- [ ] Deactivate worker action with confirmation modal

### Mobile Work

- [ ] Worker profile screen
- [ ] Worker edit profile screen
- [ ] Client company profile screen
- [ ] Client edit profile screen

### Testing Checklist

- [ ] Admin can create a client
- [ ] Admin can edit a client
- [ ] Admin can deactivate a client
- [ ] Admin can create a worker
- [ ] Admin can edit a worker
- [ ] Admin can deactivate a worker
- [ ] Deactivated user cannot log in
- [ ] Client can view own profile only
- [ ] Worker can view and edit own profile only
- [ ] Client cannot access another client's profile

### Done When

Admin can fully manage clients and workers. Role-based profile access is enforced.

---

## Phase 4: Job Request Flow

### Goal

Client can create and submit a worker request. Admin can approve or reject it.

### Features

**Client:**
- Create worker request (step-by-step form)
- Save as draft
- Submit request
- View list of own requests
- View request detail with status timeline

**Admin:**
- View all job requests
- Filter by status
- View request detail
- Approve request
- Reject request with a reason

### Backend Work

- [ ] JobRequest model with all required fields
- [ ] Shift model linked to JobRequest
- [ ] `POST /api/jobs/` — create job request
- [ ] `GET /api/jobs/` — list all requests (admin) / own requests (client)
- [ ] `GET /api/jobs/:id/` — request detail
- [ ] `PATCH /api/jobs/:id/` — edit draft
- [ ] `POST /api/jobs/:id/submit/` — submit draft
- [ ] `POST /api/jobs/:id/approve/` — admin approve
- [ ] `POST /api/jobs/:id/reject/` — admin reject with reason
- [ ] `POST /api/jobs/:id/cancel/` — cancel by admin or client
- [ ] Status transition rules enforced in service layer
- [ ] Ownership check (client can only access own requests)
- [ ] Tests for all status transitions

### Admin Work

- [ ] Job requests list page with status filter
- [ ] Job request detail page
- [ ] Approve modal with confirmation
- [ ] Reject modal with reason text field
- [ ] Status badge on every request row

### Mobile Work

- [ ] Client request list screen
- [ ] Create request — Step 1: Job type and location
- [ ] Create request — Step 2: Headcount and skills
- [ ] Create request — Step 3: Shift type and dates
- [ ] Create request — Step 4: Review and submit
- [ ] Request detail screen with status timeline
- [ ] Draft save and resume

### Testing Checklist

- [ ] Client can create and save a draft
- [ ] Client can resume a draft
- [ ] Client can submit a draft
- [ ] Required fields are validated before submission
- [ ] Admin receives notification on new submission
- [ ] Admin can approve the request
- [ ] Admin can reject with a reason
- [ ] Client sees the updated status and rejection reason
- [ ] Client cannot edit a submitted request
- [ ] Worker cannot see job requests before assignment

### Done When

Client request → admin approval or rejection flow works end to end. Status is visible to both parties in real time.

---

## Phase 5: Worker Assignment

### Goal

Admin can assign workers to approved jobs. Workers can accept or decline. Client can see who is assigned.

### Features

**Admin:**
- View available workers (filterable by skill and availability)
- Assign workers to a job
- Assign workers to specific shifts
- Replace a worker who declined

**Worker:**
- View assigned jobs
- View full job detail
- Accept a job
- Decline a job

**Client:**
- View workers assigned to own job

### Backend Work

- [ ] WorkerAssignment model
- [ ] `POST /api/jobs/:id/assign/` — assign workers to job
- [ ] `GET /api/jobs/:id/assignments/` — list assignments for job
- [ ] `DELETE /api/assignments/:id/` — remove assignment
- [ ] `POST /api/assignments/:id/accept/` — worker accepts
- [ ] `POST /api/assignments/:id/decline/` — worker declines
- [ ] `POST /api/assignments/:id/replace/` — admin replaces worker
- [ ] Assignment status transition rules
- [ ] Worker availability status updates on assignment
- [ ] Tests for assignment flow

### Admin Work

- [ ] Assign workers screen (filter panel + worker list)
- [ ] Shift assignment (assign worker to specific shift)
- [ ] Assignment summary view
- [ ] Replacement flow for declined workers

### Mobile Work

- [ ] Worker: My Jobs list screen
- [ ] Worker: Job Detail screen (location, shift, reporting info)
- [ ] Worker: Accept job action with confirmation
- [ ] Worker: Decline job action with reason (optional)
- [ ] Client: Assigned workers view on request detail

### Testing Checklist

- [ ] Admin can assign a worker to a job
- [ ] Worker receives notification of assignment
- [ ] Worker can view job detail
- [ ] Worker can accept the job
- [ ] Worker can decline the job
- [ ] Admin is notified when worker declines
- [ ] Admin can assign a replacement worker
- [ ] Client can see assigned workers for own job only
- [ ] Worker cannot see jobs assigned to another worker

### Done When

Full assignment flow works from admin assignment to worker response to client visibility.

---

## Phase 6: Attendance

### Goal

Workers check in and out. Admin verifies attendance. Client can see attendance status.

### Features

**Worker:**
- Check in (GPS verified against job site location)
- Check out
- View own attendance history

**Admin:**
- View attendance records by job and date
- Verify attendance records
- Mark worker as absent
- Mark worker as late
- Override attendance with a mandatory reason

**Client:**
- View attendance status for own jobs (read-only)

### Backend Work

- [ ] AttendanceRecord model
- [ ] `POST /api/attendance/checkin/` — worker check-in with GPS coordinates
- [ ] `POST /api/attendance/checkout/` — worker check-out
- [ ] `GET /api/attendance/` — list all records (admin)
- [ ] `GET /api/attendance/my/` — worker's own history
- [ ] `GET /api/jobs/:id/attendance/` — all attendance for a job
- [ ] `PATCH /api/attendance/:id/verify/` — admin verify
- [ ] `POST /api/attendance/bulk-verify/` — admin bulk verify
- [ ] `PATCH /api/attendance/:id/override/` — admin override with reason
- [ ] GPS distance check (worker must be within 500m of job site)
- [ ] Late detection logic (check-in after shift start + grace period)
- [ ] Tests for all attendance operations

### Admin Work

- [ ] Attendance list with job and date filters
- [ ] Colour-coded rows (on time / late / absent)
- [ ] Verify individual attendance record
- [ ] Bulk verify selected records
- [ ] Mark absent action
- [ ] Mark late action
- [ ] Override modal with mandatory reason field

### Mobile Work

- [ ] Worker: Check In screen (GPS confirmation + shift info)
- [ ] Worker: Check Out screen
- [ ] Worker: Attendance History (calendar view)
- [ ] Client: Read-only attendance status on job detail

### Testing Checklist

- [ ] Worker can check in when within 500m of site
- [ ] Check-in is rejected when worker is too far from site
- [ ] Timestamp is recorded accurately
- [ ] Late flag applies when check-in is after grace period
- [ ] Worker can check out after checking in
- [ ] Admin can verify a single attendance record
- [ ] Admin can bulk verify multiple records
- [ ] Admin can mark worker as absent
- [ ] Admin can override time with a reason
- [ ] Client sees check-in status for own job only
- [ ] Worker cannot modify verified attendance

### Done When

Workers check in and out. Admin verifies attendance. Client has read-only visibility. Late and absent flags work correctly.

---

## Phase 7: Complaints

### Goal

Clients and workers can raise complaints. Admin can review and resolve them.

### Features

**Client:**
- Raise a complaint (type, job, worker, description)
- View own complaints
- View complaint status

**Worker:**
- Raise a complaint
- View own complaints
- View complaint status

**Admin:**
- View all complaints
- View complaint detail
- Mark complaint as in review
- Resolve complaint with notes
- Reject complaint with reason

### Backend Work

- [ ] Complaint model
- [ ] `POST /api/complaints/` — raise complaint
- [ ] `GET /api/complaints/` — list all (admin)
- [ ] `GET /api/complaints/my/` — own complaints (client / worker)
- [ ] `GET /api/complaints/:id/` — complaint detail
- [ ] `PATCH /api/complaints/:id/assign/` — assign to admin
- [ ] `PATCH /api/complaints/:id/resolve/` — resolve with notes
- [ ] `PATCH /api/complaints/:id/reject/` — reject with reason
- [ ] Status transition rules
- [ ] Ownership check (client/worker can only see own complaints)
- [ ] Tests for complaint lifecycle

### Admin Work

- [ ] Complaints list with status filter
- [ ] Complaint detail page
- [ ] Mark in review action
- [ ] Resolve modal with notes field
- [ ] Reject modal with reason field

### Mobile Work

- [ ] Complaints list screen (client and worker)
- [ ] Raise complaint form (type selector, job selector, description)
- [ ] Complaint detail screen
- [ ] Status badge and update visibility

### Testing Checklist

- [ ] Client can raise a complaint
- [ ] Worker can raise a complaint
- [ ] Admin sees new complaint with OPEN status
- [ ] Admin can mark complaint as IN_REVIEW
- [ ] Admin can resolve with resolution notes
- [ ] Admin can reject with reason
- [ ] Client/worker sees updated status
- [ ] Client cannot see another client's complaints
- [ ] Worker cannot see another worker's complaints

### Done When

Full complaint lifecycle works for both client and worker complaints.

---

## Phase 8: Notifications

### Goal

In-app notifications are created and delivered for all key events.

### Notification Events

| Event | Recipient |
|---|---|
| New job request submitted | Admin |
| Request approved | Client |
| Request rejected | Client |
| Worker assigned to job | Worker |
| Worker accepted job | Admin |
| Worker declined job | Admin |
| Worker checked in | Admin |
| Worker did not check in (30 min after shift start) | Admin |
| Attendance verified | Worker |
| New complaint raised | Admin |
| Complaint resolved | Client / Worker |
| Complaint rejected | Client / Worker |

### Backend Work

- [ ] Notification model
- [ ] Create notification from each key event in service layer
- [ ] `GET /api/notifications/` — list own notifications
- [ ] `PATCH /api/notifications/:id/read/` — mark as read
- [ ] `POST /api/notifications/mark-all-read/` — mark all read
- [ ] FCM push notification delivery via Firebase
- [ ] Tests for notification creation

### Admin Work

- [ ] Notification indicator in top bar
- [ ] Notification list panel or page

### Mobile Work

- [ ] Notification list screen
- [ ] Unread indicator on tab bar
- [ ] Tap notification → navigate to relevant screen

### Testing Checklist

- [ ] Notification is created for every key event
- [ ] User can only see own notifications
- [ ] User can mark a notification as read
- [ ] User can mark all notifications as read
- [ ] Push notification arrives on device for key events

### Done When

In-app notifications work for all key events. Users cannot see each other's notifications.

---

## Phase 9: Polish and Final Testing

### Goal

Make the MVP stable, complete, and usable by real people.

### Work Items

**Backend:**
- [ ] Add missing tests to reach acceptable coverage
- [ ] Fix any remaining permission gaps
- [ ] Improve validation error messages
- [ ] Clean up API error responses (no stack traces in production)
- [ ] Confirm all migrations are in order
- [ ] Rate limit sensitive endpoints (login, OTP)

**Admin:**
- [ ] Polish dashboard layout and stats
- [ ] Polish all table layouts and filters
- [ ] Polish all modals and confirmation dialogs
- [ ] Add proper empty states to all list views
- [ ] Add proper error states to all data views
- [ ] Add loading skeletons to all data-fetching screens

**Mobile:**
- [ ] Polish client dashboard
- [ ] Polish worker dashboard and check-in flow
- [ ] Polish all forms with inline validation
- [ ] Add proper empty states to all screens
- [ ] Add proper error states with retry actions
- [ ] Add loading indicators throughout

### Final MVP Test Flow

Test this complete flow from start to finish:

```
1.  Admin logs in to web dashboard
2.  Admin creates a new client company
3.  Admin creates three new workers with skill tags
4.  Client logs in to mobile app
5.  Client creates a worker request (saves as draft, then submits)
6.  Admin receives notification, reviews the request
7.  Admin approves the request
8.  Admin assigns workers to the job and shifts
9.  Workers receive assignment notifications
10. Worker logs in, views the assigned job, accepts it
11. On shift day, worker checks in (GPS verified)
12. After shift, worker checks out
13. Admin views attendance dashboard, verifies the record
14. Client opens app, views the job, sees attendance status
15. Client raises a complaint about a worker
16. Admin receives complaint notification, marks it IN_REVIEW
17. Admin resolves the complaint with notes
18. Client sees complaint status updated to RESOLVED
19. Admin marks the job as COMPLETED
```

### Done When

- [ ] Full test flow above passes without errors
- [ ] No role can access data they should not see
- [ ] No screen has a broken or empty state without a proper UI
- [ ] All backend tests pass
- [ ] All API errors return user-friendly messages
- [ ] App is ready for real MVP testing with actual users

---

## Roadmap Summary

| Phase | Focus | Status |
|---|---|---|
| 1 | Understand and stabilise existing code | — |
| 2 | Authentication and role routing | — |
| 3 | Client and worker management | — |
| 4 | Job request flow | — |
| 5 | Worker assignment | — |
| 6 | Attendance | — |
| 7 | Complaints | — |
| 8 | Notifications | — |
| 9 | Polish and final testing | — |