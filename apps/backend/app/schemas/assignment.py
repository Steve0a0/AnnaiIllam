from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.assignment_constants import AssignmentStatus
from app.utils.validators import strip_optional_text


class AssignmentCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_id: int
    worker_profile_id: int
    assigned_role: str | None = Field(default=None, max_length=100)
    assigned_shift: str | None = Field(default=None, max_length=255)
    salary_amount: int | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=1000)
    start_date: date | None = None
    end_date: date | None = None

    @field_validator("assigned_role", "assigned_shift", "notes")
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        return strip_optional_text(value)

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.end_date and not self.start_date:
            raise ValueError("start_date is required when end_date is set")
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class AssignmentStatusUpdateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {item.value for item in AssignmentStatus}:
            raise ValueError("Invalid assignment status")
        return normalized


class AssignmentResponseSchema(BaseModel):
    id: int
    requirement_id: int
    worker_profile_id: int
    status: str
    assigned_role: str | None
    assigned_shift: str | None
    salary_amount: int | None
    notes: str | None
