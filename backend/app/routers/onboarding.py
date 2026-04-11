"""
온보딩 API — POST /api/onboarding (기획서 §온보딩 플로우).

5 Step 결과를 한 번에 받아:
  1. users 테이블 — gender, tone_id, tpo_list, style_moods, budget_min, budget_max 저장
  2. style_seeds 테이블 — 비주얼 취향 분석 결과 저장
"""

import uuid
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.style_seed import StyleSeed
from app.models.user import User
from app.schemas.onboarding import OnboardingRequest, OnboardingResponse

router = APIRouter()


# ── 헬퍼: visual_seeds → style_seed 행 생성 ──────────────────────────────────

def _derive_seed_fields(visual_seeds: list[str]) -> dict:
    """
    visual_seeds(선택된 스타일 태그 리스트)에서 mood_seed를 추출한다.
    가장 많이 선택된 태그를 mood_seed로 사용.
    """
    if not visual_seeds:
        return {
            "mood_seed": None,
            "silhouette_seed": None,
            "color_seed": None,
            "price_seed": None,
            "seed_confidence": 0,
        }

    counts = Counter(visual_seeds)
    top_mood = counts.most_common(1)[0][0]

    return {
        "mood_seed": top_mood,
        "silhouette_seed": None,   # Step 5 확장 시 추가
        "color_seed": None,        # Step 5 확장 시 추가
        "price_seed": None,        # budget 범위로 자동 추론 가능 (추후 적용)
        "seed_confidence": len(visual_seeds),  # 참여한 라운드 수 (0~4)
    }


# ── POST /api/onboarding ─────────────────────────────────────────────────────

@router.post(
    "/api/onboarding",
    response_model=OnboardingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="온보딩 5 Step 결과 저장",
)
async def submit_onboarding(
    body: OnboardingRequest,
    db: AsyncSession = Depends(get_db),
) -> OnboardingResponse:
    """
    프론트에서 5 Step 결과를 모아 전송.
    user_id가 없으면 anonymous 사용자를 새로 생성한다.
    """
    # ── 1. 사용자 조회 or 생성 ────────────────────────────────────────────────
    user: User | None = None

    if body.user_id:
        result = await db.execute(select(User).where(User.id == body.user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"user_id {body.user_id} 를 찾을 수 없습니다.",
            )

    if user is None:
        user = User(id=uuid.uuid4())
        db.add(user)

    # ── 2. users 테이블 업데이트 ──────────────────────────────────────────────
    tpo = body.tpo or []
    user.gender      = body.gender
    user.tone_id     = body.tone_id
    user.tpo_list    = tpo
    user.tpo_primary = tpo[0] if len(tpo) > 0 else None
    user.tpo_secondary = tpo[1] if len(tpo) > 1 else None
    user.style_moods = body.moods or []
    user.budget_min  = body.budget_min
    user.budget_max  = body.budget_max
    await db.flush()
    # ── 3. style_seeds 테이블 저장 (기존 행 교체) ──────────────────────────────
    existing = await db.execute(
        select(StyleSeed).where(StyleSeed.user_id == user.id)
    )
    old_seed = existing.scalar_one_or_none()
    if old_seed:
        await db.delete(old_seed)

    seed_fields = _derive_seed_fields(body.visual_seeds or [])
    style_seed = StyleSeed(user_id=user.id, **seed_fields)
    db.add(style_seed)

    await db.commit()
    await db.refresh(user)

    return OnboardingResponse(user_id=user.id)
