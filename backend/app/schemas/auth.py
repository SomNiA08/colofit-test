"""Auth API 스키마."""

import uuid
from pydantic import BaseModel


class TokenResponse(BaseModel):
    """로그인 성공 시 반환하는 토큰 정보."""
    access_token: str
    token_type: str = "bearer"
    user_id: uuid.UUID
    email: str | None = None
    is_new_user: bool = False   # True면 온보딩 미완료 → 프론트에서 온보딩으로 안내


class UserMeResponse(BaseModel):
    """GET /api/auth/me 응답."""
    user_id: uuid.UUID
    email: str | None = None
    provider: str | None = None
    has_onboarding: bool       # tone_id가 있으면 온보딩 완료로 판단
