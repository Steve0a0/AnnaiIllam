import os
from typing import List
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_VALID_APP_ENVS = {"local", "staging", "production"}


class Settings(BaseSettings):
    app_name: str = "Annai Illam API"
    # Default is "production" so that a missing APP_ENV on any server is safe.
    app_env: str = "production"
    # Default False — safe for production. Explicitly set DEBUG=true in local .env.
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    database_url: str
    redis_url: str

    # SQLAlchemy connection pool (QueuePool, applied for PostgreSQL only).
    # Increase pool_size in production to match expected concurrent request load.
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30        # seconds to wait before raising OperationalError
    db_pool_recycle: int = 1800      # recycle connections after 30 min to prevent stale sockets

    jwt_secret_key: str
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    otp_expire_minutes: int = 5
    otp_length: int = 6
    otp_max_attempts: int = 5

    google_client_id: str = ""
    apple_app_bundle_id: str = ""

    backend_cors_origins: str = ""
    payment_webhook_secret: str = ""
    payment_webhook_signature_header: str = "x-payment-signature"

    # Field-level encryption (AES-128 via Fernet).
    # Required in staging and production — omit only in local dev.
    # Generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    # Store in production via AWS Secrets Manager / Azure Key Vault — NOT only in .env
    field_encryption_key: str = ""

    # Selfie / Liveness validation — set to your storage bucket domain to enforce
    # that check-in selfies must come from your own bucket, e.g.:
    #   SELFIE_BUCKET_DOMAIN=your-bucket.s3.ap-south-1.amazonaws.com
    # Leave empty to disable selfie URL + token validation (local dev / tests).
    selfie_bucket_domain: str = ""

    # AWS S3 — document storage (India region: ap-south-1)
    # For local dev, point this at MinIO: http://localhost:9000
    # Leave empty in production to use real AWS S3
    s3_endpoint_url: str = ""
    # Public URL that *devices* can reach for presigned uploads.
    # In local dev this should be your LAN IP, e.g. http://192.168.0.166:9000
    # Leave empty in production (AWS presigned URLs are always public).
    s3_public_endpoint_url: str = ""
    s3_bucket: str = ""
    s3_region: str = "ap-south-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    # Local filesystem storage for free development document uploads.
    # Used only when S3 is not configured.
    local_upload_dir: str = "uploads"

    # SMS provider — set to "fast2sms" or "msg91" in staging/production.
    # Leave blank or "console" for local development (OTP returned in API response).
    sms_provider: str = "console"
    fast2sms_api_key: str = ""
    msg91_auth_key: str = ""
    msg91_template_id: str = ""

    # Razorpay payment gateway credentials.
    # Obtain from https://dashboard.razorpay.com/app/keys
    # Use rzp_test_* keys for staging, rzp_live_* for production.
    # PAYMENT_WEBHOOK_SECRET must match the secret set in Razorpay Dashboard → Webhooks.
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""

    # Unclosed check-in alerting — alert admins when a worker has been
    # checked in for this many hours without checking out. Default 10 hours.
    max_shift_hours: int = 10

    # Sentry error monitoring. Leave SENTRY_DSN empty to disable.
    sentry_dsn: str = ""
    sentry_environment: str = ""
    sentry_release: str = ""
    sentry_traces_sample_rate: float = 0.0
    sentry_profiles_sample_rate: float = 0.0

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def backend_cors_origins_list(self) -> List[str]:
        return [item.strip() for item in self.backend_cors_origins.split(",") if item.strip()]

    @property
    def is_local(self) -> bool:
        """True when APP_ENV is 'local'.

        Checks both the pydantic-parsed value and os.environ so that whichever
        source wins (shell export vs .env file) is honoured.
        """
        parsed_local = self.app_env == "local"
        env_local = os.environ.get("APP_ENV", "").strip().lower() == "local"
        # Either source saying "local" is sufficient — pydantic-settings loads
        # .env into self.app_env but does NOT write back to os.environ, so
        # requiring both simultaneously would wrongly treat .env-only configs
        # as non-local.
        return parsed_local or env_local

    @field_validator("app_env", mode="before")
    @classmethod
    def validate_app_env(cls, value: str) -> str:
        normalised = value.strip().lower()
        if normalised not in _VALID_APP_ENVS:
            raise ValueError(
                f"APP_ENV must be one of {sorted(_VALID_APP_ENVS)}, got {value!r}"
            )
        return normalised

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "prod", "production"}:
                return False
            if normalized in {"local", "dev", "development"}:
                return True
        return value

    @model_validator(mode="after")
    def validate_production_requirements(self) -> "Settings":
        """Fail fast at startup when required production settings are missing."""
        is_prod_like = self.app_env in {"staging", "production"}
        errors: list[str] = []

        if is_prod_like and not self.field_encryption_key:
            errors.append(
                "FIELD_ENCRYPTION_KEY must be set in staging/production. "
                "Generate with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )

        if is_prod_like and not self.payment_webhook_secret:
            errors.append("PAYMENT_WEBHOOK_SECRET must be set in staging/production.")

        if is_prod_like and self.payment_webhook_secret in {"change-me", "changeme", "secret", ""}:
            errors.append(
                "PAYMENT_WEBHOOK_SECRET is set to an insecure placeholder. "
                "Use a strong random value in staging/production."
            )

        if is_prod_like and not self.backend_cors_origins:
            errors.append("BACKEND_CORS_ORIGINS must be set in staging/production.")

        if is_prod_like and "*" in self.backend_cors_origins_list:
            errors.append(
                "BACKEND_CORS_ORIGINS must not contain '*' in staging/production. "
                "Use an explicit whitelist of allowed origins."
            )

        if is_prod_like and self.sms_provider == "console":
            errors.append(
                "SMS_PROVIDER=console is not allowed in staging/production. "
                "Set SMS_PROVIDER=fast2sms + FAST2SMS_API_KEY, "
                "or SMS_PROVIDER=msg91 + MSG91_AUTH_KEY / MSG91_TEMPLATE_ID."
            )

        if is_prod_like and not self.razorpay_key_id:
            errors.append(
                "RAZORPAY_KEY_ID must be set in staging/production. "
                "Obtain from https://dashboard.razorpay.com/app/keys"
            )

        if is_prod_like and not self.razorpay_key_secret:
            errors.append("RAZORPAY_KEY_SECRET must be set in staging/production.")

        # JWT secret must not be a weak placeholder and must be long enough to be secure.
        _weak_jwt = {"change-me", "changeme", "secret", "jwt-secret", "test-secret"}
        if is_prod_like and self.jwt_secret_key.lower() in _weak_jwt:
            errors.append(
                "JWT_SECRET_KEY is set to an insecure placeholder. "
                "Generate a strong secret: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        if is_prod_like and len(self.jwt_secret_key) < 32:
            errors.append(
                "JWT_SECRET_KEY must be at least 32 characters in staging/production. "
                "Generate: python -c \"import secrets; print(secrets.token_hex(32))\""
            )

        # S3 is required in staging/production for document storage.
        if is_prod_like and not self.s3_bucket:
            errors.append(
                "S3_BUCKET must be set in staging/production. "
                "Worker ID documents and selfies are stored in S3."
            )
        if is_prod_like and self.s3_bucket and not self.aws_access_key_id:
            errors.append("AWS_ACCESS_KEY_ID must be set when S3_BUCKET is configured.")
        if is_prod_like and self.s3_bucket and not self.aws_secret_access_key:
            errors.append("AWS_SECRET_ACCESS_KEY must be set when S3_BUCKET is configured.")
        if is_prod_like and self.s3_bucket and not self.field_encryption_key:
            # Already checked above; skip duplicate if already in errors.
            pass

        if errors:
            raise ValueError(
                "Production configuration errors:\n" + "\n".join(f"  - {e}" for e in errors)
            )

        return self


settings = Settings()
