from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.payroll_constants import DeductionType, PayrollRunStatus
from app.utils.validators import strip_optional_text


class PayrollRunCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    period_start: date
    period_end: date
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("notes")
    @classmethod
    def clean_notes(cls, value: str | None) -> str | None:
        return strip_optional_text(value)

    @model_validator(mode="after")
    def validate_period(self):
        if self.period_end < self.period_start:
            raise ValueError("period_end must be on or after period_start")
        return self


class PayrollDeductionAddSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    payroll_item_id: int
    deduction_type: str
    amount: int = Field(ge=0)
    reason: str | None = Field(default=None, max_length=1000)

    @field_validator("deduction_type")
    @classmethod
    def validate_deduction_type(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {item.value for item in DeductionType}:
            raise ValueError("Invalid deduction type")
        return normalized

    @field_validator("reason")
    @classmethod
    def clean_reason(cls, value: str | None) -> str | None:
        return strip_optional_text(value)


class PayrollRunStatusUpdateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {item.value for item in PayrollRunStatus}:
            raise ValueError("Invalid payroll status")
        return normalized


class PayrollItemResponseSchema(BaseModel):
    id: int
    payroll_run_id: int
    assignment_id: int
    worker_profile_id: int
    gross_amount: int
    total_deduction_amount: int
    net_amount: int
    attendance_days: int
    half_days: int
    absent_days: int
    payment_status: str
