from pydantic import BaseModel, Field


class ClientRatingCreateSchema(BaseModel):
    assignment_id: int | None = None
    rating: int = Field(ge=1, le=5)
    comments: str | None = Field(default=None, max_length=1000)
