from datetime import date

from pydantic import BaseModel, Field, field_validator

from app.utils.validators import strip_optional_text


class RequirementCreateSchema(BaseModel):
    category: str = Field(min_length=2, max_length=100)
    subcategory: str | None = Field(default=None, max_length=100)
    number_of_workers: int = Field(ge=1, le=1000)
    work_location: str = Field(min_length=3, max_length=255)
    city: str = Field(min_length=2, max_length=100)
    state: str = Field(min_length=2, max_length=100)
    start_date: date
    duration_days: int = Field(ge=1, le=3650)
    shift_details: str | None = Field(default=None, max_length=255)
    food_required: bool = False
    accommodation_required: bool = False
    budget_amount: int | None = Field(default=None, ge=0)
    notes: str | None = None
    site_latitude: float | None = Field(default=None, ge=-90, le=90)
    site_longitude: float | None = Field(default=None, ge=-180, le=180)
    geofence_radius_meters: int | None = Field(default=2000, ge=0, le=50000)

    @field_validator("notes", "shift_details")
    @classmethod
    def clean_text_fields(cls, value: str | None) -> str | None:
        return strip_optional_text(value)


class RequirementResponseSchema(BaseModel):
    id: int
    category: str
    subcategory: str | None
    number_of_workers: int
    work_location: str
    city: str
    state: str
    start_date: date
    duration_days: int
    shift_details: str | None
    food_required: bool
    accommodation_required: bool
    budget_amount: int | None
    notes: str | None
    status: str
    site_latitude: float | None
    site_longitude: float | None
    geofence_radius_meters: int | None
