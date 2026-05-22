from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.roles import UserRole
from app.utils.validators import normalize_phone


def _validate_email(value: str) -> str:
    value = value.strip().lower()
    parts = value.split("@")
    if len(parts) != 2 or not parts[0] or "." not in parts[1]:
        raise ValueError("Enter a valid email address")
    return value


class OtpRequestSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone: str = Field(min_length=10, max_length=20)
    role: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return normalize_phone(value)

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {item.value for item in UserRole}:
            raise ValueError("Invalid role")
        return normalized


class PhoneOtpRequestSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone: str = Field(min_length=10, max_length=20)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return normalize_phone(value)


class OtpVerifySchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone: str = Field(min_length=10, max_length=20)
    code: str = Field(min_length=4, max_length=10)
    role: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return normalize_phone(value)

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized.isdigit():
            raise ValueError("OTP code must be numeric")
        return normalized

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {item.value for item in UserRole}:
            raise ValueError("Invalid role")
        return normalized


class PhoneOtpVerifySchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone: str = Field(min_length=10, max_length=20)
    code: str = Field(min_length=4, max_length=10)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return normalize_phone(value)

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized.isdigit():
            raise ValueError("OTP code must be numeric")
        return normalized


class RefreshTokenSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str


class AdminLoginSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _validate_email(value)


class AdminUserCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=5, max_length=255)
    name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _validate_email(value)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return value.strip()


class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict
