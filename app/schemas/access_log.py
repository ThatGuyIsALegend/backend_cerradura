from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AccessLogResponse(BaseModel):
    id: UUID
    user_id: UUID | None
    result: str
    reason: str | None
    similarity: float | None
    attempted_at: datetime

    model_config = ConfigDict(from_attributes=True)
