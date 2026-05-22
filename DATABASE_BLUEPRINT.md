# Database Blueprint

## Overview

PostgreSQL relational database.

All models below are required for MVP. Do not add invoice, salary, or payment models until explicitly requested.

---

## Model: User

**Purpose:** Single auth table for all three roles. Every login account in the system is a User record.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| email | String (nullable) | Unique. Used by Admin and Client |
| phone | String (nullable) | Unique. Used by Worker |
| password_hash | String (nullable) | Hashed with bcrypt. Null for OTP-only workers |
| role | Enum | ADMIN / CLIENT / WORKER |
| is_active | Boolean | Default true. False = deactivated, cannot log in |
| is_verified | Boolean | Phone or email verified |
| fcm_token | String (nullable) | Firebase push notification token |
| created_at | DateTime | Auto-set on creation |
| updated_at | DateTime | Auto-updated |
| last_login | DateTime (nullable) | Updated on each login |

**Relationships:**
- One-to-one with `ClientCompany` (if role = CLIENT)
- One-to-one with `WorkerProfile` (if role = WORKER)

---

## Model: ClientCompany

**Purpose:** Profile and details for each client company that requests workers.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | FK → User | The login account for this client |
| company_name | String | |
| industry | String (nullable) | e.g. Manufacturing, Warehousing |
| address | Text (nullable) | |
| city | String (nullable) | |
| state | String (nullable) | |
| contact_person_name | String | |
| contact_phone | String | |
| gst_number | String (nullable) | For future invoicing |
| payment_terms_days | Integer | Default 30 |
| is_active | Boolean | Default true |
| created_at | DateTime | |
| updated_at | DateTime | |

**Relationships:**
- Belongs to `User`
- Has many `JobRequest`
- Has many `Complaint`

---

## Model: WorkerProfile

**Purpose:** Full profile for each worker who can be deployed to a job site.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | FK → User | The login account for this worker |
| full_name | String | |
| date_of_birth | Date (nullable) | |
| gender | Enum (nullable) | MALE / FEMALE / OTHER |
| address | Text (nullable) | |
| city | String (nullable) | |
| skills | JSON Array | e.g. ["electrical", "welding", "forklift"] |
| experience_years | Integer | Default 0 |
| profile_photo_url | String (nullable) | S3 URL |
| daily_rate | Decimal | Default rate used in salary calculation |
| availability_status | Enum | AVAILABLE / ON_ASSIGNMENT / ON_LEAVE / INACTIVE |
| bank_account_number | String (nullable) | For future salary. Store encrypted. |
| bank_ifsc | String (nullable) | |
| bank_name | String (nullable) | |
| emergency_contact_name | String (nullable) | |
| emergency_contact_phone | String (nullable) | |
| created_at | DateTime | |
| updated_at | DateTime | |

**Relationships:**
- Belongs to `User`
- Has many `WorkerAssignment`
- Has many `AttendanceRecord`
- Has many `Complaint`

---

## Model: JobRequest

**Purpose:** A client's request for workers. The central entity of the platform. Every assignment, attendance record, and job-related complaint links back to a JobRequest.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| client_id | FK → ClientCompany | |
| title | String | e.g. "Technical Trainees — Sriperumbudur" |
| job_type | String | e.g. "Technical Trainee", "General Labour" |
| location_address | Text | Full site address |
| location_city | String | |
| location_lat | Decimal (nullable) | For GPS check-in verification |
| location_lng | Decimal (nullable) | For GPS check-in verification |
| total_headcount | Integer | Total workers needed across all shifts |
| shift_type | Enum | SINGLE / DOUBLE / TRIPLE |
| start_date | Date | |
| end_date | Date | |
| food_required | Boolean | Default false |
| accommodation_required | Boolean | Default false |
| special_requirements | Text (nullable) | Any extra notes from client |
| status | Enum | DRAFT / SUBMITTED / UNDER_REVIEW / APPROVED / REJECTED / WORKERS_ASSIGNED / IN_PROGRESS / COMPLETED / CANCELLED |
| rejection_reason | Text (nullable) | Set when admin rejects |
| approved_by | FK → User (nullable) | Admin who approved |
| approved_at | DateTime (nullable) | |
| completed_at | DateTime (nullable) | |
| created_at | DateTime | |
| updated_at | DateTime | |

**Relationships:**
- Belongs to `ClientCompany`
- Has many `Shift`
- Has many `WorkerAssignment`
- Has many `AttendanceRecord`
- Has many `Complaint`

---

## Model: Shift

**Purpose:** Represents a specific shift within a job request (e.g. Morning, Evening, Night).

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| job_request_id | FK → JobRequest | |
| shift_name | String | e.g. "Morning", "Evening", "Night" |
| start_time | Time | e.g. 06:00 |
| end_time | Time | e.g. 14:00 |
| headcount_required | Integer | Workers needed for this shift |
| created_at | DateTime | |

**Relationships:**
- Belongs to `JobRequest`
- Has many `WorkerAssignment`

---

## Model: WorkerAssignment

**Purpose:** Links a specific worker to a specific job and shift. Tracks whether the worker accepted, declined, or was replaced.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| worker_id | FK → WorkerProfile | |
| job_request_id | FK → JobRequest | |
| shift_id | FK → Shift (nullable) | Which shift the worker is assigned to |
| assigned_by | FK → User | Admin who created the assignment |
| assigned_at | DateTime | |
| status | Enum | ASSIGNED / ACCEPTED / DECLINED / REPLACED / COMPLETED |
| decline_reason | Text (nullable) | Optional reason if worker declines |
| replaced_by_id | FK → WorkerAssignment (nullable) | Self-reference to replacement assignment |
| daily_rate_override | Decimal (nullable) | Override if different from worker default |
| created_at | DateTime | |
| updated_at | DateTime | |

**Relationships:**
- Belongs to `WorkerProfile`
- Belongs to `JobRequest`
- Belongs to `Shift`
- Has many `AttendanceRecord`

---

## Model: AttendanceRecord

**Purpose:** One record per worker per day. Stores check-in time, check-out time, GPS coordinates, and verification status.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| assignment_id | FK → WorkerAssignment | |
| worker_id | FK → WorkerProfile | Denormalised for easier querying |
| job_request_id | FK → JobRequest | Denormalised for easier querying |
| date | Date | The date of this attendance record |
| check_in_time | DateTime (nullable) | Full timestamp |
| check_in_lat | Decimal (nullable) | GPS latitude at check-in |
| check_in_lng | Decimal (nullable) | GPS longitude at check-in |
| check_out_time | DateTime (nullable) | |
| check_out_lat | Decimal (nullable) | |
| check_out_lng | Decimal (nullable) | |
| status | Enum | NOT_STARTED / CHECKED_IN / CHECKED_OUT / VERIFIED / ABSENT / LATE |
| is_late | Boolean | True if check-in was after shift start + grace period |
| verified_by | FK → User (nullable) | Admin who verified |
| verified_at | DateTime (nullable) | |
| override_reason | Text (nullable) | Required if admin overrides time |
| created_at | DateTime | |
| updated_at | DateTime | |

**Relationships:**
- Belongs to `WorkerAssignment`
- Belongs to `WorkerProfile`
- Belongs to `JobRequest`

---

## Model: Complaint

**Purpose:** Formal complaint raised by a client or worker. Tracked from open to resolved.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| raised_by_id | FK → User | The user who raised the complaint |
| raised_by_role | Enum | CLIENT / WORKER |
| job_request_id | FK → JobRequest (nullable) | Related job if applicable |
| worker_id | FK → WorkerProfile (nullable) | Specific worker the complaint is about |
| complaint_type | Enum | WORKER_BEHAVIOUR / ATTENDANCE / QUALITY / PAYMENT / OTHER |
| description | Text | |
| attachment_url | String (nullable) | S3 URL for photo evidence |
| status | Enum | OPEN / IN_REVIEW / RESOLVED / REJECTED |
| assigned_to | FK → User (nullable) | Admin handling this complaint |
| resolution_notes | Text (nullable) | What was done to resolve it |
| rejection_reason | Text (nullable) | Why it was rejected |
| resolved_at | DateTime (nullable) | |
| created_at | DateTime | |
| updated_at | DateTime | |

**Relationships:**
- Belongs to `User` (raised_by)
- Belongs to `JobRequest`
- Belongs to `WorkerProfile`

---

## Model: Notification

**Purpose:** Persists all in-app notifications. Used for the notification centre in all three apps.

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| recipient_id | FK → User | Who this notification is for |
| title | String | Short notification title |
| body | String | Notification body text |
| type | Enum | JOB_REQUEST_SUBMITTED / REQUEST_APPROVED / REQUEST_REJECTED / JOB_ASSIGNED / JOB_ACCEPTED / JOB_DECLINED / CHECKED_IN / ATTENDANCE_VERIFIED / COMPLAINT_RAISED / COMPLAINT_RESOLVED / COMPLAINT_REJECTED |
| reference_id | UUID (nullable) | ID of the related object |
| reference_type | String (nullable) | e.g. "job_request" / "complaint" / "assignment" |
| is_read | Boolean | Default false |
| created_at | DateTime | |

**Relationships:**
- Belongs to `User`

---

## Relationships Summary

```
User ─────────────── ClientCompany (1:1)
User ─────────────── WorkerProfile (1:1)

ClientCompany ─────── JobRequest (1:many)
JobRequest ────────── Shift (1:many)
JobRequest ────────── WorkerAssignment (1:many)
JobRequest ────────── AttendanceRecord (1:many)
JobRequest ────────── Complaint (1:many)

WorkerProfile ─────── WorkerAssignment (1:many)
WorkerProfile ─────── AttendanceRecord (1:many)
WorkerProfile ─────── Complaint (1:many)

WorkerAssignment ──── AttendanceRecord (1:many)
Shift ─────────────── WorkerAssignment (1:many)

User ──────────────── Notification (1:many)
User ──────────────── Complaint (1:many, as raised_by)
```

---

## Notes

- All primary keys use UUID (not integer) for security and portability
- All timestamps use UTC
- Soft delete is used where possible (is_active flag) rather than hard delete
- GPS coordinates stored as Decimal with sufficient precision (6 decimal places)
- Sensitive fields (bank account number) should be encrypted at rest
- JSON Array fields (skills) use PostgreSQL native JSON column