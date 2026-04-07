"""온보딩 API 스키마."""

import uuid
from typing import Annotated

from pydantic import BaseModel, Field


class OnboardingRequest(BaseModel):
    """POST /api/onboarding 요청 바디."""

    # 기존 사용자 갱신 시 전달. None이면 신규 생성.
    user_id: uuid.UUID | None = None

    # Step 1
    gender: Annotated[str, Field(pattern=r"^(female|male)$")]

    # Step 2
    tone_id: Annotated[str, Field(min_length=1, max_length=30)]

    # Step 3
    tpo: Annotated[list[str], Field(min_length=1, max_length=3)]
    moods: Annotated[list[str], Field(max_length=5)] = []

    # Step 4
    budget_min: Annotated[int, Field(ge=0)]
    budget_max: Annotated[int, Field(ge=0)]

    # Step 5 (패스한 라운드는 포함되지 않음 — 0~4개)
    visual_seeds: Annotated[list[str], Field(max_length=4)] = []

    model_config = {"json_schema_extra": {
        "example": {
            "gender": "female",
            "tone_id": "summer_cool_soft",
            "tpo": ["commute", "date"],
            "moods": ["minimal", "classic"],
            "budget_min": 30000,
            "budget_max": 100000,
            "visual_seeds": ["minimal", "casual", "minimal"],
        }
    }}


class OnboardingResponse(BaseModel):
    """POST /api/onboarding 응답."""

    user_id: uuid.UUID
