from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.validators import strip_optional_text


VALID_AVAILABILITY_STATUSES = {"available", "unavailable", "leave"}


class WorkerAvailabilityUpsertSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    availability_date: date
    status: str = Field(min_length=1, max_length=50)
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in VALID_AVAILABILITY_STATUSES:
            raise ValueError(
                f"status must be one of: {', '.join(sorted(VALID_AVAILABILITY_STATUSES))}"
            )
        return normalized

    @field_validator("notes")
    @classmethod
    def clean_notes(cls, value: str | None) -> str | None:
        return strip_optional_text(value)


class WorkerAvailabilityResponseSchema(BaseModel):
    id: int
    availability_date: str
    status: str
    notes: str | None
