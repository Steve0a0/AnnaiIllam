from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin_assignments import router as admin_assignments_router
from app.api.admin_audit import router as admin_audit_router
from app.api.admin_attendance import router as admin_attendance_router
from app.api.admin_complaints import router as admin_complaints_router
from app.api.admin_dashboard import router as admin_dashboard_router
from app.api.admin_maintenance import router as admin_maintenance_router
from app.api.admin_payroll import router as admin_payroll_router
from app.api.admin_people import router as admin_people_router
from app.api.admin_finance import router as admin_finance_router
from app.api.admin_profile import router as admin_profile_router
from app.api.admin_replacements import router as admin_replacements_router
from app.api.admin_reports import router as admin_reports_router
from app.api.admin_requirements import router as admin_requirements_router
from app.api.admin_sla import router as admin_sla_router
from app.api.auth import router as auth_router
from app.api.auth_social import router as auth_social_router
from app.api.client_phone import router as client_phone_router
from app.api.client_profile import router as client_profile_router
from app.api.client_complaints import router as client_complaints_router
from app.api.client_requirements import router as client_requirements_router
from app.api.client_payments import router as client_payments_router
from app.api.client_ratings import router as client_ratings_router
from app.api.health import router as health_router
from app.api.me import router as me_router
from app.api.payment_webhooks import router as payment_webhooks_router
from app.api.push_tokens import router as push_tokens_router
from app.api.users import router as users_router
from app.api.worker_assignments import router as worker_assignments_router
from app.api.worker_attendance import router as worker_attendance_router
from app.api.worker_availability import router as worker_availability_router
from app.api.worker_jobs import router as worker_jobs_router
from app.api.worker_onboarding import router as worker_onboarding_router
from app.api.worker_issues import router as worker_issues_router
from app.api.worker_payroll import router as worker_payroll_router
from app.api.worker_profile import router as worker_profile_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import log_requests
from app.core.monitoring import init_sentry
from app.core.scheduler import start_scheduler, stop_scheduler
from app.core.security_headers import security_headers_middleware

init_sentry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    docs_url="/docs" if settings.is_local else None,
    redoc_url="/redoc" if settings.is_local else None,
    openapi_url="/openapi.json" if settings.is_local else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.middleware("http")(security_headers_middleware)
app.middleware("http")(log_requests)

register_exception_handlers(app)

app.include_router(health_router, prefix=settings.api_v1_prefix)
app.include_router(users_router, prefix=settings.api_v1_prefix)
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(auth_social_router, prefix=settings.api_v1_prefix)
app.include_router(me_router, prefix=settings.api_v1_prefix)
app.include_router(push_tokens_router, prefix=settings.api_v1_prefix)
app.include_router(client_profile_router, prefix=settings.api_v1_prefix)
app.include_router(client_phone_router, prefix=settings.api_v1_prefix)
app.include_router(worker_profile_router, prefix=settings.api_v1_prefix)
app.include_router(worker_onboarding_router, prefix=settings.api_v1_prefix)
app.include_router(admin_profile_router, prefix=settings.api_v1_prefix)
app.include_router(admin_people_router, prefix=settings.api_v1_prefix)
app.include_router(client_requirements_router, prefix=settings.api_v1_prefix)
app.include_router(admin_requirements_router, prefix=settings.api_v1_prefix)
app.include_router(admin_assignments_router, prefix=settings.api_v1_prefix)
app.include_router(worker_assignments_router, prefix=settings.api_v1_prefix)
app.include_router(worker_attendance_router, prefix=settings.api_v1_prefix)
app.include_router(worker_availability_router, prefix=settings.api_v1_prefix)
app.include_router(worker_jobs_router, prefix=settings.api_v1_prefix)
app.include_router(worker_payroll_router, prefix=settings.api_v1_prefix)
app.include_router(worker_issues_router, prefix=settings.api_v1_prefix)
app.include_router(admin_attendance_router, prefix=settings.api_v1_prefix)
app.include_router(admin_payroll_router, prefix=settings.api_v1_prefix)
app.include_router(client_payments_router, prefix=settings.api_v1_prefix)
app.include_router(client_ratings_router, prefix=settings.api_v1_prefix)
app.include_router(payment_webhooks_router, prefix=settings.api_v1_prefix)
app.include_router(admin_finance_router, prefix=settings.api_v1_prefix)
app.include_router(client_complaints_router, prefix=settings.api_v1_prefix)
app.include_router(admin_complaints_router, prefix=settings.api_v1_prefix)
app.include_router(admin_replacements_router, prefix=settings.api_v1_prefix)
app.include_router(admin_dashboard_router, prefix=settings.api_v1_prefix)
app.include_router(admin_reports_router, prefix=settings.api_v1_prefix)
app.include_router(admin_audit_router, prefix=settings.api_v1_prefix)
app.include_router(admin_sla_router, prefix=settings.api_v1_prefix)
app.include_router(admin_maintenance_router, prefix=settings.api_v1_prefix)
