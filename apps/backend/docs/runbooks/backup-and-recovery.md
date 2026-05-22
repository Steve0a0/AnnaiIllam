# Backup And Recovery Runbook

## Scope

This runbook covers recovery for the Annai Illam backend production data:

- PostgreSQL database
- Worker document storage metadata and object storage
- Audit and security logs
- Payment and payout records

## Backup Policy

- PostgreSQL backups must run at least daily in production.
- Point-in-time recovery should be enabled when the hosting provider supports it.
- Object storage must have versioning or provider-level backup enabled.
- Audit logs must be retained in centralized storage with restricted access.
- Backup access must be limited to approved production operators.

## Restore Process

1. Identify the incident, affected environment, and target restore time.
2. Stop write traffic if data corruption is ongoing.
3. Restore the database backup into a staging database first.
4. Run `alembic current` and confirm the schema is at the expected revision.
5. Run health checks and a basic login flow against staging.
6. Verify critical tables: users, requirements, assignments, attendance, payroll, payments, complaints, replacements.
7. Restore or reconnect private document storage references.
8. Get approval from the production owner before restoring production.
9. Restore production and run the smoke test checklist.
10. Record the restore time, operator, reason, and validation results.

## Restore Ownership

- Production owner approves restore.
- Backend maintainer performs database validation.
- Finance/admin owner validates payroll and payment records after restore.

## Verification Checklist

- Database is reachable.
- `alembic current` matches the expected migration head.
- `/api/v1/health` returns success.
- OTP login works.
- Dashboard summary loads for admin.
- Recent requirement, assignment, payroll, payment, and complaint records are present.
- Document links resolve through the intended private storage mechanism.

## Recovery Notes

- Never restore production directly without staging validation unless the production owner approves emergency recovery.
- Never overwrite production with a backup whose migration state is unknown.
- Never expose backup files or database dumps in source control, chat, or public storage.
