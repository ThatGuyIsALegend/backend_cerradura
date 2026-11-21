from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserUpdate(BaseModel):

    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150
    )

    email: str | None = Field(
        default=None,
        max_length=150
    )

    active: bool | None = None


class UserResponse(BaseModel):

    id: UUID
    name: str
    email: str | None
    active: bool
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class FaceEmbeddingResponse(BaseModel):
    id: UUID
    user_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
