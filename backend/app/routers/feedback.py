"""
피드백 API — POST /api/feedback (기획서 §6.8).

사용자 행동 이벤트(save/like/click/dislike)를 수신하여
PreferenceTracker로 개인화 학습 데이터를 누적한다.
"""

import uuid

import jwt as pyjwt
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services import preference_tracker
from app.services.jwt import verify_token

router = APIRouter()


# ── 요청/응답 스키마 ──────────────────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    outfit_id: str
    event_type: str  # save | like | click | dislike


class FeedbackResponse(BaseModel):
    ok: bool
    feedback_count: int
    has_overrides: bool  # True면 weight_overrides가 생성/갱신됨


# ── 내부 헬퍼 ─────────────────────────────────────────────────────────────────

def _extract_user_id(request: Request) -> uuid.UUID:
    """Authorization: Bearer <token> 헤더에서 user_id를 추출한다."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="인증 토큰이 필요해요.")

    token = auth_header[7:]
    try:
        payload = verify_token(token)
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="토큰이 만료됐어요. 다시 로그인해주세요.")
    except pyjwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰이에요.")

    try:
        return uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=401, detail="토큰 형식이 올바르지 않아요.")


# ── 엔드포인트 ────────────────────────────────────────────────────────────────

@router.post("/api/feedback", response_model=FeedbackResponse)
async def post_feedback(
    body: FeedbackRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> FeedbackResponse:
    """
    피드백 이벤트를 수신하여 사용자 선호도를 업데이트한다.

    event_type별 가중치:
      save(+2.0) | like(+1.0) | click(+0.3) | dislike(-1.5)

    10건 이상 축적 시 5축 weight_overrides가 자동 생성된다.
    """
    if body.event_type not in preference_tracker.EVENT_WEIGHTS:
        raise HTTPException(
            status_code=422,
            detail="올바른 event_type이 아니에요. (save/like/click/dislike 중 하나)",
        )

    user_id = _extract_user_id(request)

    pref = await preference_tracker.update_preference(
        user_id=user_id,
        outfit_id=body.outfit_id,
        event_type=body.event_type,
        db=db,
    )

    return FeedbackResponse(
        ok=True,
        feedback_count=pref.feedback_count or 0,
        has_overrides=bool(pref.weight_overrides),
    )
