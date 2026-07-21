# Production Deployment Runbook

This runbook describes a clean production deployment for the Annai Illam platform.

It assumes:

- Backend API runs as a Docker container from `apps/backend/Dockerfile`
- Admin dashboard runs as a Docker container from `apps/admin/Dockerfile`
- PostgreSQL, Redis, and S3-compatible object storage are managed services
- TLS is terminated by nginx or a cloud load balancer
- Secrets are stored in the hosting platform secret manager, not committed `.env` files

## 1. Production Architecture

Recommended production layout:

| Component | Production target | Notes |
|---|---|---|
| Backend API | Docker container on VM, ECS, Render, Fly, Railway, or equivalent | Exposes port `8000` internally |
| Scheduler | One backend-image container/process | Run `python -m app.scheduler_runner` with exactly one replica |
| Admin dashboard | Docker container or managed Next.js host | Exposes port `3000` internally |
| PostgreSQL | Managed PostgreSQL 16 | Required by backend |
| Redis | Managed Redis | Required for rate limiting/readiness |
| Object storage | AWS S3 or S3-compatible service | Worker documents and selfies |
| Reverse proxy | nginx or managed load balancer | Routes `api.*` and `admin.*` over HTTPS |
| Error monitoring | Sentry | Backend/admin SDKs are already wired |
| DNS | Public DNS provider | Points production domains to the proxy/load balancer |

Suggested domains:

| Domain | Target |
|---|---|
| `api.annaiillam.example` | Backend API |
| `admin.annaiillam.example` | Admin dashboard |

## 2. Pre-Deployment Checklist

Before deployment:

- CI is passing for backend and admin.
- A production PostgreSQL database exists.
- A production Redis instance exists.
- A private S3 bucket exists.
- DNS records are ready for API and admin domains.
- TLS certificates can be issued for both domains.
- Razorpay production keys and webhook secret are available.
- MSG91 production credentials are available.
- A Sentry project exists for backend/admin monitoring.
- A first admin email/password has been chosen.

## 3. Required Environment Variables

Do not commit production values. Store them in the platform secret manager.

### Backend

| Variable | Required | Example / Notes |
|---|---:|---|
| `APP_NAME` | No | `Annai Illam API` |
| `APP_ENV` | Yes | `production` |
| `DEBUG` | Yes | `false` |
| `API_V1_PREFIX` | Yes | `/api/v1` |
| `DATABASE_URL` | Yes | `postgresql+psycopg://USER:PASSWORD@HOST:5432/DB` |
| `REDIS_URL` | Yes | Managed Redis URL. Use `rediss://default:PASSWORD@HOST:PORT/0` when TLS is enabled |
| `JWT_SECRET_KEY` | Yes | Strong random secret, at least 32 chars |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `30` |
| `BACKEND_CORS_ORIGINS` | Yes | `https://admin.annaiillam.example` plus mobile origins if needed |
| `PAYMENT_WEBHOOK_SECRET` | Yes | Must match Razorpay webhook config |
| `PAYMENT_WEBHOOK_SIGNATURE_HEADER` | No | `x-payment-signature` |
| `FIELD_ENCRYPTION_KEY` | Yes | Fernet key for worker bank/UPI fields |
| `S3_BUCKET` | Yes | Private production bucket |
| `S3_REGION` | Yes | Example: `ap-south-1` |
| `S3_ENDPOINT_URL` | No | Empty for AWS S3; set for R2/MinIO-compatible storage |
| `S3_PUBLIC_ENDPOINT_URL` | No | Empty for AWS S3 |
| `AWS_ACCESS_KEY_ID` | Yes | Storage IAM user/key |
| `AWS_SECRET_ACCESS_KEY` | Yes | Storage IAM secret |
| `SMS_PROVIDER` | Yes | `msg91` |
| `MSG91_AUTH_KEY` | Yes | Production MSG91 auth key |
| `MSG91_TEMPLATE_ID` | Yes | Production OTP template ID |
| `RAZORPAY_KEY_ID` | Yes | `rzp_live_...` |
| `RAZORPAY_KEY_SECRET` | Yes | Razorpay live secret |
| `SENTRY_DSN` | Recommended | Backend Sentry DSN |
| `SENTRY_ENVIRONMENT` | Recommended | `production` |
| `SENTRY_RELEASE` | Recommended | Git SHA or release tag |
| `SENTRY_TRACES_SAMPLE_RATE` | No | Start with `0.05` |
| `SENTRY_PROFILES_SAMPLE_RATE` | No | Start with `0.0` |
| `WEB_CONCURRENCY` | No | Start with `2`, tune after load testing |
| `NO_SHOW_GRACE_PERIOD_MINUTES` | No | Default `60`; delay after parsed shift start before an absence is created |
| `BACKUP_S3_BUCKET` | Yes | Bucket for database dumps; may be separate from document bucket |
| `BACKUP_S3_PREFIX` | No | Default: `postgres` |
| `BACKUP_S3_REGION` | No | Defaults to `S3_REGION` or `ap-south-1` |
| `BACKUP_S3_ENDPOINT_URL` | No | Set only for S3-compatible storage |
| `BACKUP_RETENTION_DAYS` | No | Default: `30`; must be at least `1` |
| `BACKUP_S3_SSE` | No | Default: `AES256` |

Generate a Fernet encryption key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Generate a JWT secret:

```bash
openssl rand -hex 32
```

### Admin

| Variable | Required | Example / Notes |
|---|---:|---|
| `NODE_ENV` | Yes | `production` |
| `NEXT_PUBLIC_API_BASE_URL` | Yes | `https://api.annaiillam.example/api/v1` |
| `NEXT_PUBLIC_APP_ENV` | Yes | `production` |
| `SENTRY_DSN` | Recommended | Server-side/admin Sentry DSN |
| `SENTRY_ENVIRONMENT` | Recommended | `production` |
| `SENTRY_RELEASE` | Recommended | Git SHA or release tag |
| `SENTRY_TRACES_SAMPLE_RATE` | No | Start with `0.05` |
| `SENTRY_PROFILES_SAMPLE_RATE` | No | Start with `0.0` |
| `NEXT_PUBLIC_SENTRY_DSN` | Recommended | Browser/client Sentry DSN |
| `NEXT_PUBLIC_SENTRY_ENVIRONMENT` | Recommended | `production` |
| `NEXT_PUBLIC_SENTRY_RELEASE` | Recommended | Same release as backend/admin build |
| `NEXT_PUBLIC_SENTRY_TRACES_SAMPLE_RATE` | No | Start with `0.05` |
| `SENTRY_ORG` | Optional | Needed only for source map upload |
| `SENTRY_PROJECT` | Optional | Needed only for source map upload |
| `SENTRY_AUTH_TOKEN` | Optional | Needed only for source map upload |

### Mobile Build-Time Values

The mobile app is not deployed by this runbook, but production mobile builds must point to the production API:

| Variable | Example |
|---|---|
| `EXPO_PUBLIC_API_BASE_URL` | `https://api.annaiillam.example/api/v1` |
| `EXPO_PUBLIC_APP_VARIANT` | `client` or `worker` |

## 4. Provision Infrastructure

### PostgreSQL

Create a managed PostgreSQL 16 database.

Minimum starting size:

- 1 production database
- 20 GB storage with autoscaling if available
- automated daily backups
- point-in-time recovery if available
- private networking where supported

Create a least-privilege application user:

```sql
CREATE USER annai_app WITH PASSWORD '<strong-password>';
CREATE DATABASE annai_illam OWNER annai_app;
GRANT ALL PRIVILEGES ON DATABASE annai_illam TO annai_app;
```

Use the resulting connection string as `DATABASE_URL`.

### Redis

Create a managed Redis instance.

Minimum starting configuration:

- TLS enabled if the provider supports it
- private networking where supported
- password or ACL authentication enabled
- maxmemory policy that can evict volatile keys, such as `volatile-lru`, when supported
- at least one monitoring alert for memory usage and connection failures

Use the provider URL as `REDIS_URL`.

Recommended provider paths:

| Provider | Steps |
|---|---|
| AWS ElastiCache for Redis/Valkey | Create a replication group in the same VPC/subnets as the backend, enable in-transit encryption, enable auth token or user-group auth, restrict the security group to backend instances only, and use the primary endpoint in `REDIS_URL`. |
| Redis Cloud | Create a fixed-size production database in the nearest region, enable TLS, restrict source IPs or private connectivity where available, create an application user/password, and copy the TLS endpoint into `REDIS_URL`. |

Connection string examples:

```bash
REDIS_URL=rediss://default:<password>@annai-prod-redis.xxxxxx.apse1.cache.amazonaws.com:6379/0
REDIS_URL=rediss://default:<password>@redis-12345.c1.ap-south-1-1.ec2.cloud.redislabs.com:12345/0
```

Do not log or paste the real `REDIS_URL` into tickets. The backend rate limiter fails open if Redis is unavailable, so production must explicitly verify Redis before traffic is switched.

Verify Redis from the same runtime environment that will run the backend:

```bash
docker run --rm \
  --env-file /etc/annai/backend.env \
  registry.example.com/annai-backend:RELEASE_TAG \
  python -m scripts.check_redis
```

For a systemd/virtualenv deployment:

```bash
cd /opt/annai-illam-platform/apps/backend
set -a
. /etc/annai/backend.env
set +a
venv/bin/python -m scripts.check_redis
```

Expected output:

```text
Redis check passed for rediss://***@HOST:PORT/0 (ping + write/read/delete)
```

The command performs `PING`, writes one temporary key with a 60-second TTL, reads it back, and deletes it. If this fails, do not deploy; fix networking, TLS, authentication, or the secret value first.

### S3

Create a private bucket in the production region.

Recommended settings:

- block public access
- enable default server-side encryption
- enable versioning if supported
- restrict IAM credentials to the one bucket
- add a lifecycle policy for obsolete temporary uploads after business review

The backend serves documents through signed URLs; do not make the bucket public.

### Razorpay

Configure production webhook:

- URL: `https://api.annaiillam.example/api/v1/webhooks/payment`
- Secret: same value as `PAYMENT_WEBHOOK_SECRET`
- Events: payment/order events used by the Razorpay dashboard integration

### MSG91

Configure the production OTP template and set:

- `SMS_PROVIDER=msg91`
- `MSG91_AUTH_KEY`
- `MSG91_TEMPLATE_ID`

## 5. Build Images

From the repository root:

```bash
docker build -t annai-backend:$(git rev-parse --short HEAD) apps/backend
docker build -t annai-admin:$(git rev-parse --short HEAD) apps/admin
```

For a registry-backed deploy:

```bash
docker tag annai-backend:$(git rev-parse --short HEAD) registry.example.com/annai-backend:$(git rev-parse --short HEAD)
docker tag annai-admin:$(git rev-parse --short HEAD) registry.example.com/annai-admin:$(git rev-parse --short HEAD)
docker push registry.example.com/annai-backend:$(git rev-parse --short HEAD)
docker push registry.example.com/annai-admin:$(git rev-parse --short HEAD)
```

## 6. Run Database Migrations

Migrations must run before the new backend image receives traffic.

The migration runner now honors `DATABASE_URL` from the environment, so production deploys do not need to edit `alembic.ini`.

Docker example:

```bash
docker run --rm \
  --env-file /etc/annai/backend.env \
  registry.example.com/annai-backend:<release> \
  python -m alembic upgrade head
```

VM/venv example:

```bash
cd /opt/annai-illam-platform/apps/backend
DATABASE_URL='postgresql+psycopg://USER:PASSWORD@HOST:5432/annai_illam' \
APP_ENV=production \
python -m alembic upgrade head
```

Verify migration state:

```bash
docker run --rm \
  --env-file /etc/annai/backend.env \
  registry.example.com/annai-backend:<release> \
  python -m alembic current
```

## 7. Create the First Admin User

After migrations have run:

```bash
docker run --rm \
  --env-file /etc/annai/backend.env \
  registry.example.com/annai-backend:<release> \
  python -m scripts.seed_admin \
    --email "admin@example.com" \
    --password "replace-with-strong-temporary-password" \
    --name "Admin"
```

The seed command is idempotent for admin users. Rotate the password after first login.

## 8. Deploy With Docker Compose On A Single VM

This is the simplest production shape for an MVP VM. Managed PostgreSQL, Redis, and S3 are still recommended; do not run production database state inside this compose file unless there is a separate backup plan. API workers never run scheduled jobs, so deploy one separate scheduler service and do not scale it above one replica.

Example `/opt/annai/docker-compose.prod.yml`:

```yaml
services:
  backend:
    image: registry.example.com/annai-backend:<release>
    restart: unless-stopped
    env_file:
      - /etc/annai/backend.env
    ports:
      - "127.0.0.1:8000:8000"

  scheduler:
    image: registry.example.com/annai-backend:<release>
    restart: unless-stopped
    env_file:
      - /etc/annai/backend.env
    command: python -m app.scheduler_runner
    deploy:
      replicas: 1

  admin:
    image: registry.example.com/annai-admin:<release>
    restart: unless-stopped
    env_file:
      - /etc/annai/admin.env
    ports:
      - "127.0.0.1:3000:3000"
```

Deploy:

```bash
docker compose -f /opt/annai/docker-compose.prod.yml pull
docker compose -f /opt/annai/docker-compose.prod.yml up -d
docker compose -f /opt/annai/docker-compose.prod.yml ps
```

Review logs:

```bash
docker compose -f /opt/annai/docker-compose.prod.yml logs -f backend
docker compose -f /opt/annai/docker-compose.prod.yml logs -f scheduler
docker compose -f /opt/annai/docker-compose.prod.yml logs -f admin
```

## 9. Deploy With systemd Without Docker

Use this only if Docker is not available.

Backend service example: `/etc/systemd/system/annai-backend.service`

```ini
[Unit]
Description=Annai Illam Backend API
After=network-online.target
Wants=network-online.target

[Service]
WorkingDirectory=/opt/annai-illam-platform/apps/backend
EnvironmentFile=/etc/annai/backend.env
ExecStart=/opt/annai-illam-platform/apps/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2 --no-access-log
Restart=always
RestartSec=5
User=annai
Group=annai

[Install]
WantedBy=multi-user.target
```

Scheduler service example: `/etc/systemd/system/annai-scheduler.service`. Enable exactly one instance of this unit; never use a templated or multi-instance unit for the scheduler.

```ini
[Unit]
Description=Annai Illam Standalone Scheduler
After=network-online.target annai-backend.service
Wants=network-online.target

[Service]
WorkingDirectory=/opt/annai-illam-platform/apps/backend
EnvironmentFile=/etc/annai/backend.env
ExecStart=/opt/annai-illam-platform/apps/backend/venv/bin/python -m app.scheduler_runner
Restart=always
RestartSec=5
User=annai
Group=annai

[Install]
WantedBy=multi-user.target
```

Admin service example: `/etc/systemd/system/annai-admin.service`

```ini
[Unit]
Description=Annai Illam Admin Dashboard
After=network-online.target
Wants=network-online.target

[Service]
WorkingDirectory=/opt/annai-illam-platform/apps/admin
EnvironmentFile=/etc/annai/admin.env
ExecStart=/usr/bin/npm run start
Restart=always
RestartSec=5
User=annai
Group=annai

[Install]
WantedBy=multi-user.target
```

Enable services:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now annai-backend
sudo systemctl enable --now annai-scheduler
sudo systemctl enable --now annai-admin
sudo systemctl status annai-backend
sudo systemctl status annai-scheduler
sudo systemctl status annai-admin
```

## 10. DNS And TLS

Create DNS records:

| Record | Value |
|---|---|
| `api.annaiillam.example` | VM/load balancer IP |
| `admin.annaiillam.example` | VM/load balancer IP |

nginx example:

```nginx
server {
    listen 80;
    server_name api.annaiillam.example admin.annaiillam.example;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.annaiillam.example;

    ssl_certificate /etc/letsencrypt/live/api.annaiillam.example/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.annaiillam.example/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}

server {
    listen 443 ssl http2;
    server_name admin.annaiillam.example;

    ssl_certificate /etc/letsencrypt/live/admin.annaiillam.example/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/admin.annaiillam.example/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

Issue certificates:

```bash
sudo certbot --nginx -d api.annaiillam.example -d admin.annaiillam.example
sudo certbot renew --dry-run
```

If using a cloud load balancer, terminate TLS there and forward traffic to backend/admin over private networking.

## 11. Smoke Test Checklist

Run after every production deploy.

### API

```bash
curl -fsS https://api.annaiillam.example/api/v1/health
curl -fsS https://api.annaiillam.example/api/v1/ready
```

Expected:

- `/health` returns 200
- `/ready` returns 200 only when database and Redis are reachable
- Exactly one scheduler container/process is running and its logs contain `Standalone scheduler process starting`
- `python -m scripts.check_redis` passes from the backend runtime with the production `REDIS_URL`

### Admin

- Open `https://admin.annaiillam.example/login`
- Log in with the seeded admin account
- Open dashboard
- Open requirements, attendance, finance, complaints, and reports pages
- Confirm API calls use `https://api.annaiillam.example/api/v1`

### Core Flow

- Create or identify a client
- Create a test requirement
- Mark it under review
- Create a quote
- Approve the quote as client
- Confirm payment flow in staging before using live payment traffic
- Create an assignment
- Verify attendance and payroll pages load

### Sentry

- Confirm backend and admin releases are visible in Sentry.
- Trigger a controlled test exception only in a staging environment.
- Confirm sensitive headers and cookies are not visible in event payloads.

## 12. Rollback

Rollback is image-based.

1. Identify the previous known-good backend/admin image tags.
2. Stop traffic if the issue is data-corrupting.
3. Deploy the previous images:

```bash
docker compose -f /opt/annai/docker-compose.prod.yml up -d
```

4. Do not roll back database migrations manually unless a migration-specific rollback plan exists.
5. If a migration caused the issue, restore from the latest tested backup into a new database and point `DATABASE_URL` to the restored database after approval.

## 13. Automated Database Backups

The backend includes `scripts.backup_postgres`, a production backup command that:

- runs `pg_dump --format=custom --no-owner --no-acl`
- uploads the dump to S3
- uses server-side encryption by default
- deletes backup objects older than `BACKUP_RETENTION_DAYS`

Required runtime tools:

- `pg_dump` from `postgresql-client`
- Python dependencies from `apps/backend/requirements.txt`
- S3 credentials with put/list/delete access to the backup prefix

The backend Docker image includes `postgresql-client`, so the backup job can run from the same image as the API.

### Run A Backup Manually

Docker example:

```bash
docker run --rm \
  --env-file /etc/annai/backend.env \
  registry.example.com/annai-backend:<release> \
  python -m scripts.backup_postgres
```

VM/venv example:

```bash
cd /opt/annai-illam-platform/apps/backend
set -a
. /etc/annai/backend.env
set +a
python -m scripts.backup_postgres
```

Expected output:

```text
Uploaded database backup to s3://<bucket>/<prefix>/annai_illam_<timestamp>.dump
Deleted <n> expired backup object(s)
```

### Schedule Daily Backups With Cron

Create `/usr/local/bin/annai-db-backup`:

```bash
#!/usr/bin/env bash
set -euo pipefail

docker run --rm \
  --env-file /etc/annai/backend.env \
  registry.example.com/annai-backend:<release> \
  python -m scripts.backup_postgres
```

Install:

```bash
sudo chmod 750 /usr/local/bin/annai-db-backup
sudo crontab -e
```

Cron entry for 02:15 UTC daily:

```cron
15 2 * * * /usr/local/bin/annai-db-backup >> /var/log/annai-db-backup.log 2>&1
```

### Schedule Daily Backups With systemd

Service: `/etc/systemd/system/annai-db-backup.service`

```ini
[Unit]
Description=Annai Illam PostgreSQL backup to S3
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/annai-db-backup
User=root
Group=root
```

Timer: `/etc/systemd/system/annai-db-backup.timer`

```ini
[Unit]
Description=Run Annai Illam PostgreSQL backup daily

[Timer]
OnCalendar=*-*-* 02:15:00 UTC
Persistent=true
RandomizedDelaySec=10m

[Install]
WantedBy=timers.target
```

Enable:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now annai-db-backup.timer
sudo systemctl list-timers annai-db-backup.timer
```

### S3 Retention Policy

Use both application retention and bucket lifecycle retention:

- `BACKUP_RETENTION_DAYS=30` deletes old objects when the backup job runs.
- Configure S3 lifecycle expiration for the same prefix at 35-45 days as a second line of defense.
- Keep versioning enabled if the bucket supports it.
- Restrict delete permissions to the backup prefix only.

Suggested IAM permissions for the backup principal:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::annai-db-backups",
      "Condition": {
        "StringLike": {
          "s3:prefix": "postgres/*"
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::annai-db-backups/postgres/*"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:DeleteObject"],
      "Resource": "arn:aws:s3:::annai-db-backups/postgres/*"
    }
  ]
}
```

### Backup Monitoring

At minimum:

- alert if `/var/log/annai-db-backup.log` contains `Backup failed`
- alert if no new object appears under `s3://<bucket>/<prefix>/` within 26 hours
- alert if backup object size drops unexpectedly
- review backup job success during weekly operations checks

### Restore From A Backup

Download the selected dump:

```bash
aws s3 cp s3://annai-db-backups/postgres/annai_illam_<timestamp>.dump /tmp/annai_illam_restore.dump
```

Restore into a new database first:

```bash
createdb annai_illam_restore_test
pg_restore --dbname=annai_illam_restore_test --clean --if-exists /tmp/annai_illam_restore.dump
```

Validate:

```bash
DATABASE_URL='postgresql+psycopg://USER:PASSWORD@HOST:5432/annai_illam_restore_test' python -m alembic current
curl -fsS https://api-staging.annaiillam.example/api/v1/ready
```

Do not restore directly over production without an approved incident plan.

## 14. Backups And Restore Policy

Minimum backup policy:

- daily PostgreSQL backup
- 7 daily backups retained
- 4 weekly backups retained
- monthly restore drill before production launch and after major schema changes

Managed database backup is preferred and should remain enabled even when the S3 backup job is configured. If using `pg_dump` directly:

```bash
pg_dump "$DATABASE_URL" --format=custom --file="annai_illam_$(date +%Y%m%d_%H%M%S).dump"
```

Restore drill:

```bash
createdb annai_illam_restore_test
pg_restore --dbname=annai_illam_restore_test annai_illam_<timestamp>.dump
```

After restore:

```bash
python -m alembic current
curl -fsS https://api-staging.annaiillam.example/api/v1/ready
```

## 15. Operational Checks

Daily:

- `/api/v1/ready` is healthy
- Exactly one standalone scheduler process is healthy; investigate scheduler restarts or failed-cleanup logs
- Sentry has no unresolved production spikes
- Redis memory usage, evictions, and connection count are stable
- PostgreSQL storage and connections are below alert thresholds
- S3 upload errors are not increasing

Weekly:

- Review failed login/OTP spikes
- Review Razorpay webhook failures
- Confirm backup jobs completed
- Confirm TLS certificate expiry is more than 14 days away

Before every deploy:

```bash
cd apps/backend
python -m ruff check app tests scripts
python -m pytest -v

cd ../admin
npm run lint
npm run build
```

## 16. Go-Live Gate

Do not switch production traffic until all are true:

- Backend and admin images are built from a CI-passing commit.
- Production env vars are configured in the secret manager.
- `REDIS_URL` points to a managed Redis instance reachable only from backend infrastructure.
- `python -m scripts.check_redis` passes against the production `REDIS_URL`.
- Migrations have run successfully.
- First admin user exists.
- DNS resolves correctly.
- HTTPS works for API and admin.
- `/api/v1/health` and `/api/v1/ready` pass.
- Admin login works.
- Sentry receives a staging smoke-test event.
- PostgreSQL backup and restore process has been tested.
- Daily PostgreSQL backup job is enabled and a fresh dump exists in S3.
- Razorpay webhook endpoint is configured and signature verification is enabled.
- MSG91 OTP delivery is verified in production or final staging.
