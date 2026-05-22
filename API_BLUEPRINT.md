# API Blueprint

## Base URL

```
/api/v1/
```

## Authentication

All protected endpoints require:

```
Authorization: Bearer <jwt_token>
```

Role is encoded in the JWT payload. The backend validates the role on every request.

---

## Auth Endpoints

| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| POST | `/auth/login/` | Email + password login (Admin, Client) | Public |
| POST | `/auth/worker/send-otp/` | Send OTP to worker phone number | Public |
| POST | `/auth/worker/verify-otp/` | Verify OTP, return JWT token | Public |
| POST | `/auth/admin/invite/` | Create admin invite link | Super Admin |
| POST | `/auth/admin/accept-invite/` | Accept invite and set password | Invited Admin |
| POST | `/auth/logout/` | Invalidate refresh token | All |
| POST | `/auth/token/refresh/` | Refresh JWT access token | All |
| POST | `/auth/change-password/` | Change own password | All |
| PATCH | `/auth/fcm-token/` | Register or update FCM device token | All |

---

## Client Endpoints

| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| GET | `/clients/` | List all clients (paginated, searchable) | Admin |
| POST | `/clients/` | Create new client | Admin |
| GET | `/clients/:id/` | Get client detail | Admin |
| PATCH | `/clients/:id/` | Update client details | Admin |
| POST | `/clients/:id/deactivate/` | Deactivate client account | Super Admin |
| GET | `/clients/:id/jobs/` | Client's job request history | Admin |
| GET | `/clients/me/` | Get own company profile | Client |
| PATCH | `/clients/me/` | Update own company profile | Client |

---

## Worker Endpoints

| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| GET | `/workers/` | List all workers (filterable by skill, status) | Admin |
| POST | `/workers/` | Create new worker | Admin |
| GET | `/workers/:id/` | Worker detail | Admin |
| PATCH | `/workers/:id/` | Update worker | Admin |
| POST | `/workers/:id/deactivate/` | Deactivate worker | Super Admin |
| GET | `/workers/:id/assignments/` | Worker's assignment history | Admin |
| GET | `/workers/available/` | Available workers with filters | Admin |
| GET | `/workers/me/` | Worker's own profile | Worker |
| PATCH | `/workers/me/` | Update own profile | Worker |

---

## Job Request Endpoints

| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| GET | `/jobs/` | List all requests (admin) or own requests (client) | Admin, Client |
| POST | `/jobs/` | Create job request (starts as DRAFT) | Client |
| GET | `/jobs/:id/` | Job request detail | Admin, Client (own) |
| PATCH | `/jobs/:id/` | Edit draft request | Client (own, DRAFT only) |
| POST | `/jobs/:id/submit/` | Submit draft for review | Client (own, DRAFT only) |
| POST | `/jobs/:id/approve/` | Approve submitted request | Admin |
| POST | `/jobs/:id/reject/` | Reject with reason | Admin |
| POST | `/jobs/:id/cancel/` | Cancel request | Admin, Client (own) |
| POST | `/jobs/:id/complete/` | Mark job as complete | Admin |
| GET | `/jobs/:id/shifts/` | List shifts for a job | Admin, Client (own) |
| POST | `/jobs/:id/shifts/` | Create shift for a job | Admin |
| PATCH | `/jobs/:id/shifts/:shift_id/` | Edit shift | Admin |

**Status Transition Rules:**

```
DRAFT       → SUBMITTED         (by Client, via /submit/)
SUBMITTED   → UNDER_REVIEW      (by Admin, opening the request)
UNDER_REVIEW → APPROVED         (by Admin, via /approve/)
UNDER_REVIEW → REJECTED         (by Admin, via /reject/)
APPROVED    → WORKERS_ASSIGNED  (automatic, when first worker assigned)
WORKERS_ASSIGNED → IN_PROGRESS  (automatic, when first worker checks in)
IN_PROGRESS → COMPLETED         (by Admin, via /complete/)
Any status  → CANCELLED         (by Admin or Client, via /cancel/)
```

---

## Assignment Endpoints

| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| GET | `/jobs/:id/assignments/` | List all assignments for a job | Admin, Client (own job) |
| POST | `/jobs/:id/assign/` | Assign one or more workers to job | Admin |
| DELETE | `/assignments/:id/` | Remove an assignment | Admin |
| POST | `/assignments/:id/accept/` | Worker accepts the assignment | Worker (own) |
| POST | `/assignments/:id/decline/` | Worker declines with optional reason | Worker (own) |
| POST | `/assignments/:id/replace/` | Replace a worker with another | Admin |
| GET | `/workers/me/assignments/` | Worker's own assignments | Worker |

**Request body for `/jobs/:id/assign/`:**

```json
{
  "assignments": [
    {
      "worker_id": "uuid",
      "shift_id": "uuid",
      "daily_rate_override": null
    }
  ]
}
```

---

## Attendance Endpoints

| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| POST | `/attendance/checkin/` | Worker check-in with GPS | Worker |
| POST | `/attendance/checkout/` | Worker check-out | Worker |
| GET | `/attendance/` | List all records (filterable) | Admin |
| GET | `/attendance/me/` | Worker's own attendance history | Worker |
| GET | `/jobs/:id/attendance/` | All attendance records for a job | Admin, Client (own) |
| PATCH | `/attendance/:id/verify/` | Admin verifies a single record | Admin |
| POST | `/attendance/bulk-verify/` | Admin bulk verifies multiple records | Admin |
| PATCH | `/attendance/:id/override/` | Admin overrides time with reason | Admin |
| PATCH | `/attendance/:id/mark-absent/` | Admin marks worker as absent | Admin |

**Request body for `/attendance/checkin/`:**

```json
{
  "job_request_id": "uuid",
  "latitude": 13.0827,
  "longitude": 80.2707
}
```

**GPS validation rule:**
Worker must be within 500 metres of the job site's `location_lat` / `location_lng`.
If outside 500m, return `400` with message: `"You are too far from the job site to check in."`

---

## Complaint Endpoints

| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| GET | `/complaints/` | List all complaints | Admin |
| GET | `/complaints/me/` | Own complaints | Client, Worker |
| POST | `/complaints/` | Raise a new complaint | Client, Worker |
| GET | `/complaints/:id/` | Complaint detail | Admin, Raiser (own) |
| PATCH | `/complaints/:id/assign/` | Assign to an admin user | Admin |
| PATCH | `/complaints/:id/in-review/` | Mark as in review | Admin |
| PATCH | `/complaints/:id/resolve/` | Resolve with notes | Admin |
| PATCH | `/complaints/:id/reject/` | Reject with reason | Admin |

**Status Transition Rules:**

```
OPEN → IN_REVIEW   (by Admin)
IN_REVIEW → RESOLVED  (by Admin)
IN_REVIEW → REJECTED  (by Admin)
OPEN → REJECTED    (by Admin, if obviously invalid)
```

---

## Notification Endpoints

| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| GET | `/notifications/` | List own notifications | All |
| GET | `/notifications/unread-count/` | Count of unread notifications | All |
| PATCH | `/notifications/:id/read/` | Mark one notification as read | All |
| POST | `/notifications/mark-all-read/` | Mark all as read | All |

---

## Reports Endpoints (MVP — basic only)

| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| GET | `/reports/attendance/` | Attendance summary (filterable by job, date range) | Admin |
| GET | `/reports/jobs/` | Job request summary (status breakdown) | Admin |
| GET | `/reports/workers/` | Worker activity summary | Admin |

---

## Error Response Format

All error responses use this format:

```json
{
  "detail": "Human-readable error message",
  "code": "ERROR_CODE",
  "field_errors": {
    "field_name": ["Validation error message"]
  }
}
```

`field_errors` is only present for validation errors (422).

---

## Standard Response Codes

| Code | Meaning |
|---|---|
| 200 | Success |
| 201 | Created |
| 204 | Deleted / No content |
| 400 | Bad request (business rule violation) |
| 401 | Unauthorised (no valid token) |
| 403 | Forbidden (wrong role or wrong ownership) |
| 404 | Not found |
| 422 | Validation error (invalid input) |
| 429 | Rate limit exceeded |
| 500 | Server error |

---

## Pagination

List endpoints use offset pagination:

```
GET /workers/?limit=20&offset=0
```

Response format:

```json
{
  "count": 124,
  "next": "/api/v1/workers/?limit=20&offset=20",
  "previous": null,
  "results": [...]
}
```

---

## Filtering

Common filter parameters used across list endpoints:

| Parameter | Type | Example |
|---|---|---|
| `status` | String | `?status=APPROVED` |
| `search` | String | `?search=Chennai` |
| `date_from` | Date | `?date_from=2026-05-01` |
| `date_to` | Date | `?date_to=2026-05-31` |
| `client_id` | UUID | `?client_id=...` |
| `worker_id` | UUID | `?worker_id=...` |
| `skills` | String (comma-separated) | `?skills=electrical,welding` |
| `availability_status` | String | `?availability_status=AVAILABLE` |