from datetime import date

from pydantic import BaseModel, Field


class QuoteCreateSchema(BaseModel):
    requirement_id: int
    quoted_amount: int = Field(ge=1)
    rate_per_worker: int | None = Field(default=None, ge=1)
    worker_daily_rate: int | None = Field(default=None, ge=1)
    total_worker_days: int | None = Field(default=None, ge=1)
    advance_amount: int | None = Field(default=None, ge=0)
    payment_model: str = Field(min_length=2, max_length=50)
    valid_until: date | None = None
    terms_notes: str | None = None
    internal_notes: str | None = None


class QuoteDecisionSchema(BaseModel):
    action: str = Field(pattern="^(approve|reject)$")


class QuoteResponseSchema(BaseModel):
    id: int
    requirement_id: int
    quoted_amount: int
    rate_per_worker: int | None
    worker_daily_rate: int | None
    total_worker_days: int | None
    advance_amount: int | None
    payment_model: str
    valid_until: date | None
    terms_notes: str | None
    status: str
