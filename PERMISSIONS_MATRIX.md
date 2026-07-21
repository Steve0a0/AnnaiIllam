# Permissions Matrix

## Overview

All permissions are enforced on the **backend API**. Frontend role-routing is for UX only — the backend never trusts the frontend to enforce access control.

Every protected endpoint checks:
1. Is the request authenticated? (valid JWT token)
2. Does the user's role allow this action?
3. Does the user own the resource they are accessing?

---

## Role Summary

| Role | Login Method | Primary Surface |
|---|---|---|
| Super Admin | Email + password (invite only) | Next.js web dashboard |
| Ops Admin | Email + password (invite only) | Next.js web dashboard |
| Client | Email + password | React Native mobile app |
| Worker | Phone number + OTP | React Native mobile app |

---

## Full Permissions Matrix

| Feature | Super Admin | Ops Admin | Client | Worker |
|---|:---:|:---:|:---:|:---:|
| **Authentication** | | | | |
| Login | ✓ | ✓ | ✓ | ✓ |
| Invite new admin | ✓ | ✗ | ✗ | ✗ |
| Deactivate admin account | ✓ | ✗ | ✗ | ✗ |
| Change own password | ✓ | ✓ | ✓ | ✓ |
| **Client Management** | | | | |
| View all clients | ✓ | ✓ | ✗ | ✗ |
| Create client | ✓ | ✓ | ✗ | ✗ |
| Edit any client | ✓ | ✓ | ✗ | ✗ |
| Deactivate client | ✓ | ✗ | ✗ | ✗ |
| View own company profile | ✓ | ✓ | ✓ | ✗ |
| Edit own company profile | ✗ | ✗ | ✓ | ✗ |
| **Worker Management** | | | | |
| View all workers | ✓ | ✓ | ✗ | ✗ |
| View workers assigned to own job | ✓ | ✓ | Limited* | ✗ |
| Create worker | ✓ | ✓ | ✗ | ✗ |
| Edit any worker | ✓ | ✓ | ✗ | ✗ |
| Deactivate worker | ✓ | ✗ | ✗ | ✗ |
| View own profile | ✓ | ✓ | ✗ | ✓ |
| Edit own profile | ✗ | ✗ | ✗ | ✓ |
| **Job Requests** | | | | |
| View all job requests | ✓ | ✓ | ✗ | ✗ |
| View own job requests | ✓ | ✓ | ✓ | ✗ |
| Create job request | ✗ | ✗ | ✓ | ✗ |
| Edit draft request | ✗ | ✗ | ✓ (own only) | ✗ |
| Submit draft request | ✗ | ✗ | ✓ (own only) | ✗ |
| Approve request | ✓ | ✓ | ✗ | ✗ |
| Reject request | ✓ | ✓ | ✗ | ✗ |
| Cancel request | ✓ | ✓ | ✓ (own only) | ✗ |
| Complete job | ✓ | ✓ | ✗ | ✗ |
| **Worker Assignment** | | | | |
| Assign workers to job | ✓ | ✓ | ✗ | ✗ |
| Remove assignment | ✓ | ✓ | ✗ | ✗ |
| Replace declined worker | ✓ | ✓ | ✗ | ✗ |
| Accept assignment | ✗ | ✗ | ✗ | ✓ (own only) |
| Decline assignment | ✗ | ✗ | ✗ | ✓ (own only) |
| View assignments for own job | ✓ | ✓ | ✓ (own job) | ✗ |
| View own assignments | ✗ | ✗ | ✗ | ✓ |
| **Attendance** | | | | |
| Check in | ✗ | ✗ | ✗ | ✓ (own only) |
| Check out | ✗ | ✗ | ✗ | ✓ (own only) |
| View all attendance records | ✓ | ✓ | ✗ | ✗ |
| View attendance for own job | ✓ | ✓ | ✓ (read-only) | ✗ |
| View own attendance history | ✗ | ✗ | ✗ | ✓ |
| Verify attendance | ✓ | ✓ | ✗ | ✗ |
| Bulk verify attendance | ✓ | ✓ | ✗ | ✗ |
| Override attendance | ✓ | ✓ | ✗ | ✗ |
| Mark absent | ✓ | ✓ | ✗ | ✗ |
| Mark late | ✓ | ✓ | ✗ | ✗ |
| Modify verified attendance | ✓ | ✗ | ✗ | ✗ |
| **Complaints** | | | | |
| View all complaints | ✓ | ✓ | ✗ | ✗ |
| View own complaints | ✗ | ✗ | ✓ | ✓ |
| Raise complaint | ✓ | ✓ | ✓ | ✓ |
| Assign complaint to admin | ✓ | ✓ | ✗ | ✗ |
| Mark complaint in review | ✓ | ✓ | ✗ | ✗ |
| Resolve complaint | ✓ | ✓ | ✗ | ✗ |
| Reject complaint | ✓ | ✓ | ✗ | ✗ |
| **Notifications** | | | | |
| View own notifications | ✓ | ✓ | ✓ | ✓ |
| Mark notification as read | ✓ | ✓ | ✓ | ✓ |
| **Reports** | | | | |
| View attendance report | ✓ | ✓ | ✗ | ✗ |
| View job summary report | ✓ | ✓ | ✗ | ✗ |
| View worker activity report | ✓ | ✓ | ✗ | ✗ |
| Export any report | ✓ | ✓ | ✗ | ✗ |
| **Privacy Requests** | | | | |
| Request own data export | ✗ | ✗ | ✓ (own only) | ✓ (own only) |
| Download approved own data export | ✗ | ✗ | ✓ (own only) | ✓ (own only) |
| Request own account deletion | ✗ | ✗ | ✓ (own only) | ✓ (own only) |
| View and resolve privacy queue | ✓ | ✗ | ✗ | ✗ |
| Complete anonymization | ✓ | ✗ | ✗ | ✗ |
| View published legal documents | ✓ | ✓ | ✓ | ✓ |
| View own legal acceptance status | ✗ | ✗ | ✓ (own only) | ✓ (own only) |
| Record own current legal acceptance | ✗ | ✗ | ✓ (own only) | ✓ (own only) |
| **Settings** | | | | |
| Manage admin users | ✓ | ✗ | ✗ | ✗ |
| Change app settings | ✓ | ✗ | ✗ | ✗ |
| View settings | ✓ | ✓ | ✗ | ✗ |

---

## Notes

**Client — Limited worker visibility (*)**

Clients can see the following details for workers assigned to their own jobs only:
- Full name
- Skill tags
- Today's check-in status

Clients **cannot** see:
- Worker phone number or personal contact
- Bank details
- ID documents
- Other clients' worker assignments
- Worker salary or payment information

**Super Admin vs Ops Admin**

Super Admin can do everything Ops Admin can do, plus:
- Invite new admin accounts
- Deactivate admin accounts
- Deactivate client and worker accounts
- Override verified attendance
- Manage app settings

**Ownership checks**

Every "own only" permission means the backend verifies that the requesting user's ID matches the resource owner's ID. This check happens in the service layer before any data is returned or modified.

---

## API Permission Enforcement

Every protected API endpoint uses a dependency injection pattern that checks:

```
1. Request has valid Bearer token → 401 if missing or invalid
2. Token contains expected role → 403 if wrong role
3. If ownership required: resource.owner_id == current_user.id → 403 if mismatch
4. Business rule check → 400 if invalid state transition
```

**Never return 404 when the real reason is 403.** This can inadvertently reveal that a resource exists. If a user cannot access a resource, return 403.
