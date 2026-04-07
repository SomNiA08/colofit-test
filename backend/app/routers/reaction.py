"""
Reaction API — POST /api/reaction

save/dislike 반응을 저장한다.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.reaction import Reaction
from app.schemas.reaction import ReactionRequest, ReactionResponse

router = APIRouter()


@router.post("/api/reaction", response_model=ReactionResponse)
async def post_reaction(
    body: ReactionRequest,
    db: AsyncSession = Depends(get_db),
) -> ReactionResponse:
    """
    코디에 대한 반응을 저장한다.

    - save: 이미 save 상태이면 삭제(토글)
    - dislike: 무조건 추가 (중복 시 무시)
    """
    # 기존 동일 반응 조회
    existing = None
    if body.user_id:
        stmt = select(Reaction).where(
            Reaction.user_id == body.user_id,
            Reaction.outfit_id == body.outfit_id,
            Reaction.reaction_type == body.reaction_type,
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()

    # save 토글: 이미 있으면 삭제
    if existing and body.reaction_type == "save":
        await db.execute(
            delete(Reaction).where(Reaction.id == existing.id)
        )
        await db.commit()
        return ReactionResponse(
            id=existing.id,
            reaction_type="unsave",
            outfit_id=body.outfit_id,
        )

    # dislike 중복 방지
    if existing and body.reaction_type == "dislike":
        return ReactionResponse(
            id=existing.id,
            reaction_type="dislike",
            outfit_id=body.outfit_id,
        )

    # 새 반응 생성
    reaction = Reaction(
        user_id=body.user_id,
        outfit_id=body.outfit_id,
        reaction_type=body.reaction_type,
    )
    db.add(reaction)
    await db.commit()
    await db.refresh(reaction)

    return ReactionResponse(
        id=reaction.id,
        reaction_type=reaction.reaction_type or body.reaction_type,
        outfit_id=body.outfit_id,
    )
