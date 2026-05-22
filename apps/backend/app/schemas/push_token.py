from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.validators import strip_text


class PushTokenRegisterSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=10, max_length=512)
    platform: str = Field(default="unknown", max_length=50)
    app_variant: str = Field(default="worker", max_length=50)

    @field_validator("token", "platform", "app_variant")
    @classmethod
    def clean_text(cls, value: str) -> str:
        return strip_text(value)
