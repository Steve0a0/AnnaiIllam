# MVP Scope

## MVP Objective

The MVP must prove the core manpower operations flow works end to end.

Version 1 is successful when:

```
Client creates a worker request
  → Admin approves the request
  → Admin assigns workers
  → Worker accepts the job
  → Worker checks in and checks out
  → Admin verifies attendance
  → Client sees the job and attendance status
  → Complaints can be raised and resolved
```

---

## MVP Principle

Build only what is required for the first working version.

Do not add future-version features unless explicitly requested.

The MVP should be stable, clear, and usable by real clients, workers, and admin staff.

---

## Must-Have Features for MVP

### 1. Authentication

| Feature | Details |
|---|---|
| Admin login | Email and password, invite-only account creation |
| Client login | Email and password |
| Worker login | Phone number and OTP |
| Worker onboarding | Full first-time profile, consent, ID upload, and biometric setup flow |
| Role-based routing | Each role lands on the correct dashboard |
| Protected routes | Wrong role cannot access wrong area |
| Token handling | JWT tokens, expiry handled correctly |

**Worker first-time flow:**

```
Phone number → OTP → Build Profile (name, city, skills, availability)
  → Consent (document retention + privacy)
  → Government ID upload + selfie
  → Submitted (pending admin approval)
  → Admin approves
  → Worker opens app → Biometric setup (one-time)
  → Dashboard
```

**Worker returning login flow:**

```
Phone number → OTP → Biometric check → Dashboard
```

**Rules:**
- Admin → Admin web dashboard
- Client → Client mobile dashboard
- Worker → Worker mobile dashboard
- No user can access screens or APIs that do not belong to their role

---

### 2. Admin Web App

Admin must be able to:

**Dashboard**
- View dashboard with simple stats
- See pending requests, workers on shift, open complaints

**Client Management**
- View list of all clients
- Create a new client
- Edit client details
- Deactivate a client

**Worker Management**
- View list of all workers
- Create a new worker
- Edit worker details
- Set worker availability status
- Add skill tags to workers
- Deactivate a worker

**Job Request Management**
- View all job requests
- Filter by status
- View request detail
- Approve a request
- Reject a request with a reason

**Worker Assignment**
- Assign workers to an approved job
- Assign workers to specific shifts
- Replace a worker who declined

**Attendance**
- View attendance records by job and date
- Verify attendance records
- Mark worker as absent
- Mark worker as late
- Override attendance with a reason

**Complaints**
- View all complaints
- View complaint detail
- Mark complaint as in review
- Resolve a complaint
- Reject a complaint

---

### 3. Client Mobile App

Client must be able to:

- Log in
- View dashboard (active jobs, recent activity)
- Create a worker request using step-by-step form
- Save a request as draft
- Submit a request
- View list of own requests
- View request detail and status timeline
- View workers assigned to own jobs
- View attendance status for own jobs (read-only)
- Raise a complaint
- View own complaints and status
- View and edit basic company profile

---

### 4. Worker Mobile App

Worker must be able to:

- Log in using phone number and OTP
- View dashboard with today's job
- View list of assigned jobs
- Accept a job
- Decline a job
- View full job detail (location, shift time, reporting info)
- Check in (GPS verified against job site)
- Check out
- View own attendance history
- Raise a complaint
- View own complaints and status
- View and edit basic profile

---

## MVP Screens

### Admin Web Screens

| Screen | Purpose |
|---|---|
| Login | Admin authentication |
| Dashboard | Stats, pending actions, recent activity |
| Clients List | View and search all clients |
| Client Detail | View client info, job history |
| Add / Edit Client | Create or update client |
| Workers List | View and filter all workers |
| Worker Detail | View worker profile, assignment history |
| Add / Edit Worker | Create or update worker |
| Job Requests List | View all requests, filter by status |
| Job Request Detail | View request, approve or reject |
| Assign Workers | Assign workers to job and shifts |
| Attendance List | View attendance by job and date |
| Attendance Verification | Verify, mark absent, mark late |
| Complaints List | View all complaints |
| Complaint Detail | Review and resolve or reject |
| Settings / Profile | Admin account settings |

### Client Mobile Screens

| Screen | Purpose |
|---|---|
| Login | Client authentication |
| Dashboard | Active jobs, recent activity |
| Requests List | View own job requests |
| Create Request | Step-by-step request form |
| Request Detail | Status, assigned workers, timeline |
| Assigned Workers | Workers on the job |
| Attendance Status | Read-only check-in view |
| Complaints List | Own complaints |
| Raise Complaint | Submit a new complaint |
| Complaint Detail | View status and updates |
| Profile | Company details |

### Worker Mobile Screens

| Screen | Purpose |
|---|---|
| Welcome | App entry point, phone number entry |
| Verify OTP | 6-digit code entry and verification |
| Build Profile | Name, city, skills, availability, payment details |
| Consent | Document retention and privacy consent |
| Identity Upload | Government ID photo + selfie capture |
| Profile Submitted | Confirmation screen, pending admin review |
| Under Review | Waiting state shown after profile submission |
| Biometric Setup | One-time biometric enrolment after first approval |
| Biometric Check | Per-session biometric gate for returning workers |
| Dashboard | Today's job, check-in button |
| My Jobs | All assigned jobs |
| Job Detail | Location, shift, reporting info |
| Accept / Decline | Respond to assignment |
| Check In | GPS-verified check-in |
| Check Out | GPS-verified check-out |
| Attendance History | Calendar of own attendance |
| Raise Complaint | Submit a new complaint |
| Complaint Detail | View status and updates |
| Profile | Personal details |

---

## MVP Database Models

Only these models are required for MVP:

| Model | Purpose |
|---|---|
| User | All login accounts (Admin, Client, Worker) |
| ClientCompany | Client company profile |
| WorkerProfile | Worker personal and skill profile |
| JobRequest | A client's request for workers |
| Shift | Shift details within a job |
| WorkerAssignment | A worker assigned to a job/shift |
| AttendanceRecord | Check-in, check-out, and verification |
| Complaint | Complaint raised by client or worker |
| Notification | In-app notifications |

Do not add finance, salary, or invoice models in MVP.

---

## MVP Status Values

### Job Request Status

```
DRAFT           → Saved but not submitted
SUBMITTED       → Client has submitted, waiting for admin
UNDER_REVIEW    → Admin has opened and is reviewing
APPROVED        → Admin has approved
REJECTED        → Admin has rejected with reason
WORKERS_ASSIGNED → At least one worker has been assigned
IN_PROGRESS     → First worker has checked in
COMPLETED       → Job marked complete by admin
CANCELLED       → Cancelled by client or admin
```

### Worker Assignment Status

```
ASSIGNED    → Admin has assigned the worker
ACCEPTED    → Worker has accepted the job
DECLINED    → Worker has declined the job
REPLACED    → Worker was replaced by another worker
COMPLETED   → Assignment completed
```

### Attendance Status

```
NOT_STARTED → Shift started, no check-in recorded
CHECKED_IN  → Worker has checked in
CHECKED_OUT → Worker has checked out
VERIFIED    → Admin has verified the record
ABSENT      → Admin marked worker as absent
LATE        → Worker checked in after grace period
```

### Complaint Status

```
OPEN        → Complaint submitted, not yet reviewed
IN_REVIEW   → Admin has assigned and is reviewing
RESOLVED    → Admin has resolved with notes
REJECTED    → Admin has rejected as invalid
```

---

## Not Included in MVP

The following features are **intentionally out of scope** for Version 1.

Do not build these unless explicitly requested:

| Feature | Reason |
|---|---|
| Invoice generation | Version 2 |
| Salary automation | Version 2 |
| Payment tracking | Version 2 |
| Payment gateway | Version 2 |
| Food and accommodation billing | Version 2 |
| PDF report export | Version 2 |
| Advanced analytics and reports | Version 2 |
| Worker document re-upload portal | Version 2 |
| AI worker matching | Future |
| In-app chat | Future |
| Offline sync | Future |
| Multi-branch support | Future |
| Multi-language support | Future |
| Client invoice dispute | Version 2 |
| Worker rating system | Version 2 |
| Native biometric API (expo-local-authentication) | Version 1.1 |
| Automated payroll disbursement | Future |
| Third-party HR integrations | Future |

---

## MVP Success Criteria

The MVP is complete only when all of the following are true:

- [ ] Admin, Client, and Worker can log in successfully
- [ ] Each role lands on the correct dashboard
- [ ] Client can create and submit a worker request
- [ ] Admin can approve or reject the request
- [ ] Admin can assign workers to an approved request
- [ ] Worker can accept or decline assigned job
- [ ] Worker can check in and check out
- [ ] Admin can verify attendance
- [ ] Client can view request and attendance status
- [ ] Client or worker can raise a complaint
- [ ] Admin can resolve or reject a complaint
- [ ] Role-based permissions are enforced on all API endpoints
- [ ] No user can access data they should not see
- [ ] Main flow works end to end without broken states
- [ ] All screens have proper loading, empty, and error states