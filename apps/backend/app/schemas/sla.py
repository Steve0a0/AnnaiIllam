from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.complaint_constants import ComplaintSeverity


class ComplaintSlaPolicyUpdateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    severity: str
    response_hours: int = Field(ge=1, le=720)
    resolution_hours: int = Field(ge=1, le=1440)

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {item.value for item in ComplaintSeverity}:
            raise ValueError("Invalid complaint severity")
        return normalized
