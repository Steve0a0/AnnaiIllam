# Annai Illam — Testing Guide

Practical testing reference. For full manual test scripts see `docs/MANUAL_QA_CHECKLIST.md`.

---

## 1. Running Tests

### Backend (pytest)

```bash
cd apps/backend

# Full test suite
python -m pytest -v

# Specific test file
python -m pytest tests/test_requirements.py -v

# With lint
python -m ruff check app tests scripts
python -m pytest -v
```

Tests use an **SQLite in-memory database** — no PostgreSQL or Redis needed.
The CI runs this on every pull request (`.github/workflows/backend.yml`).

### Admin (ESLint + build)

```bash
cd apps/admin
npm run lint
npm run build
```

The CI runs this on every pull request (`.github/workflows/admin.yml`).

### Mobile (TypeScript check)

```bash
cd apps/mobile-ui-lab
npx expo start          # checks for runtime errors
npx tsc --noEmit        # TypeScript type check
```

---

## 2. Existing Automated Test Coverage

| Test file | What it covers |
|---|---|
| `tests/test_auth.py` | Admin login, OTP flow, token refresh, logout + blocklist, inactive accounts |
| `tests/test_security.py` | Pure security functions (hashing, token generation) |
| `tests/test_requirements.py` | Client creates requirement, admin reviews, admin creates quote, client approves/rejects quote, ownership, role checks, duplicate quote, invalid transitions |
| `tests/test_assignments.py` | Admin create/list/filter/read, all status updates, worker accept/decline, role checks, ownership, payment gate, availability gate, duplicate active assignment rejection |
| `tests/test_attendance.py` | GPS check-in/out, geofence rejection, missing GPS, duplicate check-in, no-open-checkout, admin list/correction, locked payroll blocking, ownership, role checks |
| `tests/test_payroll.py` | Payroll run generation, zero-attendance items, duplicate generation rejection, deductions, net recalculation, all statuses, paid transition, locked run blocking, role checks |
| `tests/test_finance_payments.py` | Razorpay order creation, webhook signature verification (valid/invalid/duplicate), manual payment recording, status updates, requirement auto-transition, worker payouts |
| `tests/test_complaints.py` | Complaint creation, replacement requests, admin listing, all status transitions, SLA policy CRUD, SLA breach detection |
| `tests/test_worker_onboarding.py` | Full onboarding step machine: consent → identity → profile → approved/rejected; admin approve/reject; re-profile flow |
| `tests/test_seed_admin.py` | Admin seed script — idempotent, duplicate prevention |
| `tests/test_backup_postgres.py` | Backup key helpers and retention logic |
| `tests/test_check_redis.py` | Redis URL redaction and connectivity check |

---

## 3. What Is NOT Covered by Automated Tests

| Area | Gap |
|---|---|
| Worker profile update, availability toggle | No automated test |
| Client profile create and update | No automated test |
| Worker issues (create, list, view) | No automated test |
| Admin dashboard stat accuracy | No automated test |
| Audit log event recording | No automated test |
| End-to-end user journeys (login → full flow) | No E2E suite exists |
| Admin and mobile UI | No frontend unit or E2E tests |

---

## 4. Critical Business Logic Tests

When writing new tests or verifying existing behavior, always cover these cases:

### Role and Permission Tests

```python
# Every protected endpoint must return:
# - 401 with no token
# - 403 with wrong role token
# - 403 when accessing another user's resource
# - 200/201 with correct role + ownership
```

### Status Transition Tests

```python
# Test that invalid transitions return 400:
# - Approve a CANCELLED requirement
# - Assign workers to a REJECTED requirement
# - Check in on a DECLINED assignment
# - Check in when already CHECKED_IN
# - Add deduction to a LOCKED payroll run
```

### Geofence Test

```python
# Check-in within 500m → 201
# Check-in outside 500m → 400 with geofence error
# Check-in with no GPS coordinates → 400
```

### Ownership Isolation Tests

```python
# Client A cannot GET Client B's requirement → 403
# Worker A cannot GET Worker B's attendance → 403
# Worker cannot call /api/v1/admin/* → 403
# Client cannot call /api/v1/worker/* → 403
```

### Payroll Lock Tests

```python
# Attendance correction within locked payroll period → 400
# Deduction on locked payroll run → 400
# Status change on locked run → 400
```

---

## 5. Key Manual Test Flows

Use `docs/MANUAL_QA_CHECKLIST.md` for full step-by-step instructions. The five most critical
flows to verify before any release:

### 1. Core E2E Flow (E2E-001)
Client creates request → Admin approves → Admin assigns worker → Worker accepts → Worker GPS check-in → Worker GPS check-out → Admin verifies attendance

### 2. Complaint Flow (E2E-002)
Client raises complaint → Admin marks in review → Admin resolves with notes → Client sees RESOLVED status

### 3. Worker Onboarding (E2E-003)
New worker: Phone → OTP → Build Profile → Consent → Upload ID + Selfie → Under Review → Admin approves → Biometric setup → Check-in

### 4. Role Access Restrictions (TC-NEG-003 / TC-NEG-004 / TC-PERM-001)
Using Postman or curl, verify client token returns 403 on admin endpoints, worker token returns 403 on client endpoints, and Ops Admin cannot deactivate accounts.

### 5. GPS Geofence (TC-NEG-001)
With spoofed location far from job site, verify check-in fails with the correct error message.

---

## 6. Retesting After Code Changes

After any code change, run the smallest useful check:

| Change area | Command |
|---|---|
| Any backend code | `cd apps/backend && python -m pytest -v` |
| Auth or security | Focus on `test_auth.py` and `test_security.py` |
| Requirements/quotes | Focus on `test_requirements.py` |
| Assignments | Focus on `test_assignments.py` |
| Attendance or geofence | Focus on `test_attendance.py` |
| Payroll or finance | Focus on `test_payroll.py` and `test_finance_payments.py` |
| Complaints | Focus on `test_complaints.py` |
| Any Alembic migration | `alembic upgrade head` on a clean DB |
| Admin frontend | `cd apps/admin && npm run lint && npm run build` |
| Mobile | `cd apps/mobile-ui-lab && npx tsc --noEmit` |

---

## 7. Creating Admin Test Account

```bash
cd apps/backend
make seed-admin EMAIL=admin@test.com PASSWORD=Admin@123 NAME="Test Admin"
```

This command is idempotent — safe to run multiple times.

---

## 8. Full Manual QA Reference

All page-by-page test cases, edge cases, role permission tests, and the pre-production
sign-off checklist are in:

**[docs/MANUAL_QA_CHECKLIST.md](MANUAL_QA_CHECKLIST.md)**

That document covers all 3 apps, 40+ test cases, and a final L-section sign-off checklist
grouped by: Authentication, Admin Web, Client Mobile, Worker Mobile, Security/Permissions,
UX/Design, and Connectivity.
