from pydantic import BaseModel, Field, field_validator

from app.utils.validators import strip_optional_text


class CheckInSchema(BaseModel):
    assignment_id: int
    notes: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    selfie_url: str | None = Field(default=None, max_length=2048)
    qr_code: str | None = Field(default=None, max_length=255)

    @field_validator("notes")
    @classmethod
    def clean_notes(cls, value: str | None) -> str | None:
        return strip_optional_text(value)


class CheckOutSchema(BaseModel):
    assignment_id: int
    notes: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    selfie_url: str | None = Field(default=None, max_length=2048)

    @field_validator("notes")
    @classmethod
    def clean_notes(cls, value: str | None) -> str | None:
        return strip_optional_text(value)


class AttendanceCorrectionSchema(BaseModel):
    status: str
    notes: str | None = None

    @field_validator("notes")
    @classmethod
    def clean_notes(cls, value: str | None) -> str | None:
        return strip_optional_text(value)


class AttendanceResponseSchema(BaseModel):
    id: int
    assignment_id: int
    worker_profile_id: int
    attendance_date: str
    status: str
    check_in_time: str | None
    check_out_time: str | None
    notes: str | None
