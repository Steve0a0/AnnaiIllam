from datetime import date
from pathlib import PurePosixPath
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.file_upload_constants import ALLOWED_DOCUMENT_EXTENSIONS
from app.core.profile_constants import WorkerDocumentType
from app.utils.validators import strip_optional_text, strip_text


class ClientProfileCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_type: str | None = Field(default="company", max_length=20)  # 'individual' | 'company'
    company_name: str | None = Field(default=None, min_length=2, max_length=255)
    contact_name: str = Field(min_length=2, max_length=255)
    city: str = Field(min_length=2, max_length=100)
    state: str = Field(min_length=2, max_length=100)
    address: str | None = Field(default=None, max_length=1000)
    gst_number: str | None = Field(default=None, max_length=50)


class ClientProfileUpdateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_type: str | None = Field(default=None, max_length=20)
    company_name: str | None = Field(default=None, min_length=2, max_length=255)
    contact_name: str | None = Field(default=None, min_length=2, max_length=255)
    city: str | None = Field(default=None, min_length=2, max_length=100)
    state: str | None = Field(default=None, min_length=2, max_length=100)
    address: str | None = Field(default=None, max_length=1000)
    gst_number: str | None = Field(default=None, max_length=50)
    industry: str | None = Field(default=None, max_length=100)
    email: str | None = Field(default=None, max_length=255)
    default_job_category: str | None = Field(default=None, max_length=100)
    food_preference: bool | None = None
    accommodation_preference: bool | None = None
    standing_notes: str | None = Field(default=None, max_length=5000)


class WorkerProfileCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str = Field(min_length=2, max_length=255)
    category: str = Field(min_length=2, max_length=100)
    subcategory: str | None = Field(default=None, max_length=100)
    city: str = Field(min_length=2, max_length=100)
    state: str = Field(min_length=2, max_length=100)
    address: str | None = Field(default=None, max_length=1000)
    date_of_birth: date | None = None
    skills: list[str] | None = Field(default=None, max_length=20)
    experience_notes: str | None = Field(default=None, max_length=5000)


class WorkerBulkImportItemSchema(WorkerProfileCreateSchema):
    phone: str = Field(min_length=5, max_length=20)
    email: str | None = Field(default=None, max_length=255)

    @field_validator("phone")
    @classmethod
    def clean_phone(cls, value: str) -> str:
        return strip_text(value)


class WorkerBulkImportSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workers: list[WorkerBulkImportItemSchema] = Field(min_length=1, max_length=500)


class WorkerRejectSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=10, max_length=1000)

    @field_validator("reason")
    @classmethod
    def clean_reason(cls, value: str) -> str:
        return strip_text(value)


class WorkerProfileUpdateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    category: str | None = Field(default=None, min_length=2, max_length=100)
    subcategory: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, min_length=2, max_length=100)
    state: str | None = Field(default=None, min_length=2, max_length=100)
    address: str | None = Field(default=None, max_length=1000)
    date_of_birth: date | None = None
    skills: list[str] | None = Field(default=None, max_length=20)
    experience_notes: str | None = Field(default=None, max_length=5000)
    is_available: bool | None = None
    available_days: list[str] | None = None
    available_shifts: list[str] | None = None


class WorkerDocumentCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_type: str
    file_url: str = Field(min_length=1, max_length=2048)
    expiry_date: date | None = None
    remarks: str | None = Field(default=None, max_length=1000)

    @field_validator("document_type")
    @classmethod
    def validate_document_type(cls, value: str) -> str:
        allowed_values = {item.value for item in WorkerDocumentType}
        normalized = value.strip().lower()
        if normalized not in allowed_values:
            raise ValueError(f"document_type must be one of: {', '.join(sorted(allowed_values))}")
        return normalized

    @field_validator("file_url")
    @classmethod
    def validate_file_url(cls, value: str) -> str:
        normalized = strip_text(value)
        parsed = urlparse(normalized)
        extension = PurePosixPath(parsed.path).suffix.lower()
        if extension not in ALLOWED_DOCUMENT_EXTENSIONS:
            allowed = ", ".join(sorted(ALLOWED_DOCUMENT_EXTENSIONS))
            raise ValueError(f"document file type must be one of: {allowed}")
        return normalized

    @field_validator("remarks")
    @classmethod
    def clean_remarks(cls, value: str | None) -> str | None:
        return strip_optional_text(value)


_ALLOWED_PERMISSION_GROUPS = {"super_admin", "ops_admin", "finance_admin", "viewer"}


class AdminProfileCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str = Field(min_length=2, max_length=255)
    department: str | None = Field(default=None, max_length=100)
    permission_group: str = Field(default="ops_admin", max_length=50)

    @field_validator("permission_group")
    @classmethod
    def validate_permission_group(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in _ALLOWED_PERMISSION_GROUPS:
            raise ValueError(
                f"permission_group must be one of: {', '.join(sorted(_ALLOWED_PERMISSION_GROUPS))}"
            )
        return normalized


class AdminProfileUpdateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    department: str | None = Field(default=None, max_length=100)
    permission_group: str | None = Field(default=None, max_length=50)

    @field_validator("permission_group")
    @classmethod
    def validate_permission_group(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if normalized not in _ALLOWED_PERMISSION_GROUPS:
            raise ValueError(
                f"permission_group must be one of: {', '.join(sorted(_ALLOWED_PERMISSION_GROUPS))}"
            )
        return normalized
