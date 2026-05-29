# Annai Illam — Business Rules

Source of truth for business logic. When code and this doc conflict, trust the code.
This doc reflects what is enforced in the codebase as of the last audit (2026-05-20).

---

## Roles

| Role | Login | Scope |
|---|---|---|
| Super Admin | Email + password (invite only) | Everything — including deactivations, overriding verified attendance, managing admin users |
| Ops Admin | Email + password (invite only) | Full operational access — cannot deactivate accounts or override verified records |
| Client | Phone OTP | Own company data only |
| Worker | Phone OTP + biometric gate | Own data only |

---

## Requirement Lifecycle

### Status Values (use exactly)

```
DRAFT            → Client saved but not yet submitted
SUBMITTED        → Client submitted; waiting for admin review
UNDER_REVIEW     → Admin opened and is reviewing (+ quote created during this phase)
APPROVED         → Admin approved; client approved the quote; payment advance confirmed
WORKERS_ASSIGNED → At least one worker has been assigned
IN_PROGRESS      → First worker has checked in
COMPLETED        → Admin marked the job complete
REJECTED         → Admin rejected the requirement (with reason)
CANCELLED        → Cancelled by admin or client
```

### Transitions

```
DRAFT         → SUBMITTED          (client submits)
SUBMITTED     → UNDER_REVIEW       (admin opens the requirement)
UNDER_REVIEW  → APPROVED           (admin creates quote → client approves → admin confirms payment)
UNDER_REVIEW  → REJECTED           (admin rejects with reason)
APPROVED      → WORKERS_ASSIGNED   (when first worker is assigned)
WORKERS_ASSIGNED → IN_PROGRESS     (when first worker checks in)
IN_PROGRESS   → COMPLETED          (admin marks complete)
Any           → CANCELLED          (client or admin cancels)
```

### Rules

- **Only admins can approve requirements.** Clients cannot approve their own requirements.
- **Only admins can reject requirements.** Rejection reason is mandatory.
- **Client can edit a requirement only while it is DRAFT.**
- **Once SUBMITTED, the client cannot edit the requirement.**
- **A quote must be created by admin and approved by the client** before the requirement moves to APPROVED.
- **Payment advance must be confirmed** before the requirement is considered fully approved and workers can be assigned.
- **CANCELLED and REJECTED requirements must not generate invoices or payroll items.**
- **A COMPLETED requirement cannot be re-opened** without admin intervention.

---

## Assignment Lifecycle

### Status Values (use exactly)

```
ASSIGNED    → Admin created the assignment; worker has not responded
ACCEPTED    → Worker accepted the job
DECLINED    → Worker declined the job (optional reason stored)
REPLACED    → Worker was replaced by another worker
COMPLETED   → Assignment completed
```

### Transitions

```
ASSIGNED → ACCEPTED   (worker accepts)
ASSIGNED → DECLINED   (worker declines)
ACCEPTED → COMPLETED  (job ends)
DECLINED → REPLACED   (admin assigns a replacement)
```

### Rules

- **Only admins can assign workers.** Clients cannot assign workers directly.
- **Only admins can replace a declined worker.** The original assignment is marked REPLACED.
- **A worker with an active ACCEPTED assignment on overlapping dates must not be assigned to another job.** The matching service (`app/services/worker_matching_service.py`) enforces this — the worker appears as "blocked" in the assignment modal.
- **A worker cannot be assigned to the same requirement twice simultaneously.** Duplicate active assignment is rejected with 400.
- **Assignment can only be created on a requirement in APPROVED or later status.**
- **Workers can only see their own assignments.** Cross-worker data access returns 403.
- **Clients can see assigned workers for their own requirements only** — name, skills, and check-in status. They cannot see phone numbers, bank details, or ID documents.

---

## Attendance Lifecycle

### Status Values (use exactly)

```
NOT_STARTED → Shift started; no check-in recorded
CHECKED_IN  → Worker has checked in
CHECKED_OUT → Worker has checked out
VERIFIED    → Admin has verified the record
ABSENT      → Admin marked worker as absent
LATE        → Worker checked in after shift start + grace period
```

### Transitions

```
NOT_STARTED → CHECKED_IN   (worker checks in)
CHECKED_IN  → CHECKED_OUT  (worker checks out)
CHECKED_OUT → VERIFIED     (admin verifies)
CHECKED_OUT → ABSENT       (admin marks absent)
Any         → ABSENT       (admin marks absent)
Any (admin) → LATE         (set via admin time correction resulting in late arrival)
```

### Rules

- **Worker must be within 500m of the job site to check in.** Distance calculated using Haversine formula in `app/utils/geofence.py`. Check-in fails with 400 if outside geofence.
- **Worker must have an ACCEPTED assignment for the current job to check in.** Cannot check in without an active accepted assignment.
- **GPS coordinates are mandatory for check-in.** Missing coordinates return 400.
- **A worker cannot check in twice without checking out.** Duplicate check-in is rejected.
- **A worker cannot check out without having checked in first.**
- **Worker cannot modify their own attendance records after any admin action.**
- **Admin cannot modify an attendance record that belongs to a locked payroll run.** This prevents retroactive changes to finalized payroll.
- **Only Super Admin can override a VERIFIED attendance record.** Ops Admin cannot.
- **Salary is calculated only from attendance records within a payroll run.** Unverified records can still be included but payroll lock prevents changes after locking.

---

## Complaint Lifecycle

### Status Values (use exactly)

```
OPEN        → Complaint submitted; not yet reviewed
IN_REVIEW   → Admin assigned and reviewing
RESOLVED    → Admin resolved with notes
REJECTED    → Admin rejected as invalid
```

### Transitions

```
OPEN → IN_REVIEW  (admin marks in review)
IN_REVIEW → RESOLVED  (admin resolves with notes — resolution notes are mandatory)
IN_REVIEW → REJECTED  (admin rejects with reason)
OPEN → REJECTED   (admin can reject directly if clearly invalid)
```

### Rules

- **Both clients and workers can raise complaints.** Worker complaints are called "issues" in the mobile UI but stored in the same backend model.
- **Clients can only see their own complaints.** Workers can only see their own issues.
- **Admins can see all complaints.**
- **Resolution notes are mandatory when resolving a complaint.**
- **SLA policies** define response and resolution hour targets per severity. Admin dashboard shows SLA breach status (`app/api/admin_sla.py`). Auto-escalation is not yet implemented (manual tracking only).

---

## Payroll Lifecycle

### Run Status Values

```
DRAFT      → Payroll run created; items generated; not yet reviewed
GENERATED  → Items confirmed/reviewed
LOCKED     → Run locked; no further edits to items or attendance records
PAID       → Run marked paid; worker payout records created
```

### Rules

- **Payroll is calculated from attendance records × worker daily rate.** Each worker assignment generates one payroll item.
- **Admin can add deductions to any payroll item before the run is locked.**
- **Once a run is LOCKED, no deductions or status changes can be made.** Attendance correction for records within a locked payroll period is also blocked.
- **Only admin can generate, lock, and pay payroll runs.** Workers have read-only access to their own earnings (worker payroll API).
- **A duplicate payroll run for the same date range is rejected.**
- **Payroll is only generated from active assignments** (ACCEPTED or COMPLETED status).

---

## Replacement Rules

- **When a worker declines an assignment, admin can assign a replacement worker.**
- **The original declined assignment is marked REPLACED.**
- **A replaced worker must not be double-counted in payroll.** Only the active assignment generates a payroll item.
- **Replacement tracking is stored in the `Replacement` model** and accessible via `/admin/replacements`.

---

## Data Isolation Rules

These are hard security rules enforced on the backend:

| Rule | Enforcement |
|---|---|
| Client A cannot access Client B's requirements | Ownership check in service layer: `requirement.client_id == current_user.client_id` |
| Client cannot see any worker's phone, bank details, or ID documents | These fields are excluded from client-facing schemas |
| Worker cannot see other workers' data | Ownership check: `assignment.worker_id == current_user.worker_id` |
| Worker cannot see client billing information | Client payment endpoints are admin-only |
| Admin token cannot access `/api/v1/client/*` or `/api/v1/worker/*` | `require_role()` dependency checks exact role |
| Client token cannot access `/api/v1/admin/*` or `/api/v1/worker/*` | Same dependency |
| Worker token cannot access `/api/v1/admin/*` or `/api/v1/client/*` | Same dependency |
| Unauthenticated requests to any protected endpoint | Returns 401 |
| Wrong role on protected endpoint | Returns 403 (not 404 — do not leak resource existence) |

---

## GPS Geofence Rules

- **Check-in radius:** 500 metres from the job site's `location_lat` / `location_lng`.
- **Distance calculation:** Haversine formula in `app/utils/geofence.py`.
- **Failure response:** HTTP 400 with message `"You are too far from the job site to check in."` (or equivalent).
- **Missing GPS:** HTTP 400 if latitude/longitude not provided.
- **Job site coordinates** are set on the Requirement model when the client creates the requirement.

---

## Business Rules Not Yet Fully Enforced in Code

The following are expected business rules that are partially or not yet enforced. They are listed
here so future developers know the intent and can implement them correctly.

| Rule | Current Status |
|---|---|
| Rate limiting on all business endpoints | Only auth endpoints are rate-limited. Business endpoints (requirement creation, complaint submission) are not yet rate-limited. |
| SLA auto-escalation | SLA policies exist and breach detection works, but no automatic escalation fires. Manual tracking only. |
| Push notifications for all key events | Push fires on assignment creation and some other events, but not consistently for all user-facing events (e.g., quote sent, payment confirmed, complaint resolved). |
| Social auth (Google/Apple) end-to-end | Backend API exists (`app/api/auth_social.py`) but mobile integration has not been confirmed working. |
| End-to-end automated test suite | Core API flows are tested (requirements, assignments, attendance, payroll, payments, complaints). Full E2E user journey tests do not exist. |
| Connection pool tuning | SQLAlchemy uses default pool settings; not tuned for production concurrent load. |

---

## Status Value Quick Reference

When writing backend or frontend code, use these exact string values:

```python
# Requirement status
"DRAFT", "SUBMITTED", "UNDER_REVIEW", "APPROVED", "WORKERS_ASSIGNED",
"IN_PROGRESS", "COMPLETED", "REJECTED", "CANCELLED"

# Assignment status
"ASSIGNED", "ACCEPTED", "DECLINED", "REPLACED", "COMPLETED"

# Attendance status
"NOT_STARTED", "CHECKED_IN", "CHECKED_OUT", "VERIFIED", "ABSENT", "LATE"

# Complaint status
"OPEN", "IN_REVIEW", "RESOLVED", "REJECTED"

# Payroll run status
"DRAFT", "GENERATED", "LOCKED", "PAID"
```
