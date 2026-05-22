# Smoke Test Checklist

Run this after staging deploy and production deploy.

## Core

- `GET /api/v1/health`
- `GET /api/v1/ready`
- OTP request
- OTP verify
- Refresh token
- Logout rejects revoked refresh token

## Business Flow

- Create client profile.
- Create worker profile.
- Create admin profile.
- Client creates requirement.
- Admin marks requirement under review.
- Admin creates quote.
- Client approves quote.
- Admin creates assignment.
- Worker views assignment.
- Worker checks in.
- Worker checks out.

## Finance Flow

- Admin generates payroll run.
- Admin adds deduction before lock.
- Admin locks payroll run.
- Adding deduction after lock fails.
- Attendance correction inside locked payroll period fails.
- Client creates payment order.
- Payment webhook marks payment paid with valid signature.
- Admin records manual client payment.
- Admin creates worker payout.
- Admin marks worker payout paid.

## Support Flow

- Client creates complaint.
- Admin marks complaint under review.
- Admin creates replacement.
- Old assignment becomes replaced.
- New assignment is created.
- Admin resolves complaint.

## Reporting

- Admin dashboard summary loads.
- Requirements report loads.
- Assignments report loads.
- Complaints report loads.
