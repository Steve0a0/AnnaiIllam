# Pre-Deploy Security Checklist

## Application

- `APP_ENV=production`.
- `DEBUG=false`.
- `JWT_SECRET_KEY` is strong and environment-specific.
- `PAYMENT_WEBHOOK_SECRET` is strong and environment-specific.
- `DATABASE_URL` and `REDIS_URL` are set only in the deployment environment.
- CORS origins are explicit and production-only.
- HTTPS is enabled at the platform/load balancer.
- Security headers middleware is enabled.
- API docs are reviewed for production exposure policy.

## Database

- `alembic current` matches the expected migration head.
- `alembic upgrade head` has been tested in staging.
- No manual schema edits are pending.
- Backup and restore have been validated recently.

## Payments

- Webhook signature verification is configured.
- Payment gateway test keys are not present in production.
- Duplicate gateway order/payment constraints are in place.

## Storage

- Document storage bucket is private.
- Upload validation allows only PDF, JPG, JPEG, and PNG.
- Signed URL strategy is confirmed before exposing documents to users.

## Operations

- Redis is running and rate limits are active.
- Audit/security logs are retained centrally.
- Payroll lock behavior has been tested.
- Admin, finance, payroll, support, and operations route groups are documented for future sub-role enforcement.
