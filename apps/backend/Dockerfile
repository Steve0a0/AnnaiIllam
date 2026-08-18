# ── Stage 1: builder ─────────────────────────────────────────────────────────
FROM python:3.14.7-slim AS builder

WORKDIR /app

# Install build tools for compiled wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM python:3.14.7-slim AS runtime

WORKDIR /app

# Runtime libs for psycopg / cryptography and pg_dump backups
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 postgresql-client && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY . .

# Non-root user for security
RUN addgroup --system app && adduser --system --ingroup app app
USER app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production

EXPOSE 8000

# API workers never start scheduled jobs; app.scheduler_runner is a separate
# one-replica process. WEB_CONCURRENCY can therefore be tuned independently.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${WEB_CONCURRENCY:-2} --no-access-log"]
