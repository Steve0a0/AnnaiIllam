# Annai Illam Backend

## Run Locally

1. Create virtualenv
2. Install requirements
3. Start Postgres
4. Copy `.env.example` to `.env`
5. Run migrations
6. Start server

## Commands

- `uvicorn app.main:app --reload`
- `alembic revision --autogenerate -m "message"`
- `alembic upgrade head`
- `make seed-admin EMAIL=admin@example.com PASSWORD=SomePass123! NAME="Admin"`
- `make backup-db`
- `make check-redis`
- `pytest`

## First Admin User

Create or reset the first admin account after migrations have run:

```bash
make seed-admin EMAIL=admin@example.com PASSWORD=SomePass123! NAME="Admin"
```

The command is idempotent for admin users: running it again with the same email updates the admin name/password, ensures the account is active, and does not create a duplicate user. If the email belongs to a non-admin user, the command exits with an error.

## Security Notes

- Keep real secrets in `.env`; commit only safe example values in `.env.example`.
- Restrict CORS to the origins needed by the frontend clients.
- Set `DEBUG=false` in production.
- Use FastAPI and Pydantic validation for request inputs, and add stricter schemas as endpoints grow.
- Do not return raw Python exceptions to clients.
- Use Alembic migrations for schema changes instead of manual database edits.

## Production Security Checklist

- Set `APP_ENV=production` and `DEBUG=false`.
- Replace `JWT_SECRET_KEY` and `PAYMENT_WEBHOOK_SECRET` with strong secret values from a secret manager.
- Run Redis and keep `REDIS_URL` private; auth, webhook, and complaint rate limits depend on it.
- Verify managed production Redis from the backend runtime with `python -m scripts.check_redis`.
- Use explicit `BACKEND_CORS_ORIGINS`; never use wildcard origins in production.
- Verify payment gateway webhook signatures using the configured signature header.
- Store worker documents in private object storage and serve them through short-lived signed URLs.
- Validate document MIME type and size before upload; only PDF, JPG, JPEG, and PNG should be accepted.
- Keep database backups enabled and test restore into a staging database before go-live.
- Keep audit/security logs retained centrally with restricted access.
- Run `alembic upgrade head` during deploys and never edit schema manually in production.

## Backup And Restore Check

- Backup: use managed PostgreSQL automated backups and run `python -m scripts.backup_postgres` on a schedule for S3-retained logical dumps.
- Restore test: restore the latest backup into staging and run `alembic current`, health checks, and a basic login flow.
- Recovery rule: document the restore owner, database target, and rollback decision process before launch.

Detailed production runbooks:

- Production deployment, backups, and smoke tests: `../../docs/DEPLOYMENT.md`
