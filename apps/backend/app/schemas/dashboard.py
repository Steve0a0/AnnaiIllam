from pydantic import BaseModel


class DashboardSummarySchema(BaseModel):
    total_requirements: int
    total_open_requirements: int
    total_assignments: int
    total_active_assignments: int
    total_workers: int
    total_available_workers: int
    total_open_complaints: int
    total_payroll_runs: int
    total_client_payments: int
    total_worker_payouts: int
