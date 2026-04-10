"""
저장 목록 API — GET /api/saved (기획서 §4.3).

save 반응이 있는 코디를 정렬하여 반환한다.
sort 파라미터: recent(최신순) | score(점수순) | price(가격순)
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.outfit import Outfit
from app.models.product import Product
from app.models.reaction import Reaction
from app.routers.feed import _outfit_to_dict, _build_outfit_response
from app.schemas.outfit import OutfitResponse
from app.services.feed_builder import compute_soft_scores
from pydantic import BaseModel


class SavedResponse(BaseModel):
    outfits: list[OutfitResponse]
    total_count: int


router = APIRouter()


@router.get("/api/saved", response_model=SavedResponse)
async def get_saved(
    user_id: str,
    tone_id: str,
    gender: str,
    budget_min: int = 0,
    budget_max: int = 300000,
    tpo: str = "",
    sort: str = "recent",
    db: AsyncSession = Depends(get_db),
) -> SavedResponse:
    """
    사용자가 저장한 코디 목록을 반환한다.

    Args:
        user_id:    사용자 UUID
        tone_id:    퍼스널컬러 tone_id
        gender:     "female" | "male"
        budget_min: 예산 하한
        budget_max: 예산 상한
        tpo:        TPO 콤마 구분
        sort:       recent | score | price
    """
    # 1. UUID 검증
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="올바른 user_id가 아니에요.")

    user_tpo_list = [t.strip() for t in tpo.split(",") if t.strip()] if tpo else []

    # 2. 저장 반응 조회 (최신순으로 가져옴, created_at 포함)
    reaction_rows = (
        await db.execute(
            select(Reaction)
            .where(
                Reaction.user_id == uid,
                Reaction.reaction_type == "save",
                Reaction.outfit_id.isnot(None),
            )
            .order_by(Reaction.created_at.desc())
        )
    ).scalars().all()

    if not reaction_rows:
        return SavedResponse(outfits=[], total_count=0)

    saved_outfit_ids = [r.outfit_id for r in reaction_rows]

    # 3. 코디 일괄 로드
    outfit_rows = (
        await db.execute(
            select(Outfit).where(Outfit.id.in_(saved_outfit_ids))
        )
    ).scalars().all()

    # 4. 상품 일괄 로드
    all_item_ids: set[str] = set()
    for o in outfit_rows:
        if o.item_ids:
            all_item_ids.update(o.item_ids)

    products: dict[str, Product] = {}
    if all_item_ids:
        prod_rows = (
            await db.execute(select(Product).where(Product.id.in_(all_item_ids)))
        ).scalars().all()
        products = {p.id: p for p in prod_rows}

    # 5. ORM → dict 변환 + Soft Score 계산
    outfit_map: dict[str, dict] = {}
    for o in outfit_rows:
        d = _outfit_to_dict(o, products)
        d["scores"] = compute_soft_scores(
            d,
            user_tone_id=tone_id,
            user_tpo_list=user_tpo_list,
            budget_min=float(budget_min),
            budget_max=float(budget_max),
        )
        outfit_map[o.id] = d

    # 6. 정렬
    # recent: saved_outfit_ids 순서 유지 (이미 created_at DESC)
    ordered: list[dict] = []
    if sort == "recent":
        for oid in saved_outfit_ids:
            if oid in outfit_map:
                ordered.append(outfit_map[oid])
    elif sort == "score":
        ordered = sorted(
            outfit_map.values(),
            key=lambda o: o["scores"].get("total", 0.0),
            reverse=True,
        )
    elif sort == "price":
        ordered = sorted(
            outfit_map.values(),
            key=lambda o: o.get("total_price") or 0,
        )
    else:
        for oid in saved_outfit_ids:
            if oid in outfit_map:
                ordered.append(outfit_map[oid])

    # 7. 응답 조합
    outfit_responses = [
        _build_outfit_response(o, tone_id, user_tpo_list)
        for o in ordered
    ]

    return SavedResponse(outfits=outfit_responses, total_count=len(outfit_responses))
