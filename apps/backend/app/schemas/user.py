from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserDirectoryItem(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: int
    role: str
    is_active: bool
    created_at: datetime


class UserDirectoryPage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[UserDirectoryItem]
    page: int
    page_size: int
    total: int
    total_pages: int


class UserDirectoryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool = True
    message: str
    data: UserDirectoryPage
