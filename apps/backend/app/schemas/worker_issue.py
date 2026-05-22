from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.validators import strip_text


class WorkerIssueCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    assignment_id: int | None = None
    issue_type: str = Field(min_length=2, max_length=50)
    description: str = Field(min_length=5, max_length=5000)

    @field_validator("issue_type", "description")
    @classmethod
    def clean_text(cls, value: str) -> str:
        return strip_text(value)
