"""Reaction API 스키마."""

import uuid

from pydantic import BaseModel, Field


class ReactionRequest(BaseModel):
    """POST /api/reaction 요청 바디."""

    user_id: uuid.UUID | None = None
    outfit_id: str = Field(min_length=1)
    reaction_type: str = Field(pattern=r"^(save|dislike)$")

    model_config = {"json_schema_extra": {
        "example": {
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "outfit_id": "outfit_001",
            "reaction_type": "save",
        }
    }}


class ReactionResponse(BaseModel):
    """POST /api/reaction 응답."""

    id: int
    reaction_type: str
    outfit_id: str
