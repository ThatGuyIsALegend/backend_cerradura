from uuid import UUID

from pydantic import BaseModel


class RecognitionResponse(BaseModel):
    matched: bool
    user_id: UUID | None = None
    user_name: str | None = None
    similarity: float | None = None


class AccessAttemptResponse(BaseModel):
    authorized: bool
    result: str
    reason: str
    similarity: float | None = None
    user_id: UUID | None = None
