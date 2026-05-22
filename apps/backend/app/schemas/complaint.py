from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.complaint_constants import ComplaintSeverity, ComplaintStatus, ComplaintType, ReplacementStatus
from app.utils.validators import strip_optional_text, strip_text


class ComplaintCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_id: int
    assignment_id: int | None = None
    complaint_type: str
    severity: str = "medium"
    description: str = Field(min_length=5, max_length=5000)

    @field_validator("complaint_type")
    @classmethod
    def validate_complaint_type(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {item.value for item in ComplaintType}:
            raise ValueError("Invalid complaint type")
        return normalized

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {item.value for item in ComplaintSeverity}:
            raise ValueError("Invalid complaint severity")
        return normalized

    @field_validator("description")
    @classmethod
    def clean_description(cls, value: str) -> str:
        return strip_text(value)


class ComplaintStatusUpdateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    resolution_notes: str | None = Field(default=None, max_length=5000)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {item.value for item in ComplaintStatus}:
            raise ValueError("Invalid complaint status")
        return normalized

    @field_validator("resolution_notes")
    @classmethod
    def clean_resolution_notes(cls, value: str | None) -> str | None:
        return strip_optional_text(value)


class ReplacementCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    complaint_id: int
    old_assignment_id: int
    new_worker_profile_id: int
    reason: str | None = Field(default=None, max_length=1000)

    @field_validator("reason")
    @classmethod
    def clean_reason(cls, value: str | None) -> str | None:
        return strip_optional_text(value)


class ClientReplacementRequestSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assignment_id: int
    reason: str = Field(min_length=5, max_length=1000)

    @field_validator("reason")
    @classmethod
    def clean_reason(cls, value: str) -> str:
        return strip_text(value)


class ReplacementStatusUpdateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {item.value for item in ReplacementStatus}:
            raise ValueError("Invalid replacement status")
        return normalized
