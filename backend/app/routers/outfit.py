"""
Outfit 상세 API — GET /api/outfit/{outfit_id} (기획서 §14.3).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.outfit import Outfit
from app.models.product import Product
from app.routers.feed import _build_outfit_response, _outfit_to_dict
from app.schemas.outfit import OutfitResponse
from app.services.feed_builder import compute_soft_scores

router = APIRouter()


@router.get("/api/outfit/{outfit_id}", response_model=OutfitResponse)
async def get_outfit(
    outfit_id: str,
    tone_id: str,
    gender: str = "female",
    budget_min: int = 0,
    budget_max: int = 300000,
    tpo: str = "",
    db: AsyncSession = Depends(get_db),
) -> OutfitResponse:
    """
    코디 상세 정보를 반환한다.

    Args:
        outfit_id: 코디 ID
        tone_id: 사용자 퍼스널컬러 (e.g. "summer_cool_soft")
        gender: 사용자 성별 ("female" / "male")
        budget_min: 예산 최솟값
        budget_max: 예산 최댓값
        tpo: TPO 콤마 구분 문자열 (e.g. "office,date")
    """
    result = await db.execute(select(Outfit).where(Outfit.id == outfit_id))
    outfit = result.scalar_one_or_none()
    if outfit is None:
        raise HTTPException(status_code=404, detail="Outfit not found")

    # 아이템 일괄 로드
    item_ids = outfit.item_ids or []
    products: dict[str, Product] = {}
    if item_ids:
        prod_rows = (
            await db.execute(select(Product).where(Product.id.in_(item_ids)))
        ).scalars().all()
        products = {p.id: p for p in prod_rows}

    user_tpo_list = [t.strip() for t in tpo.split(",") if t.strip()] if tpo else []
    outfit_dict = _outfit_to_dict(outfit, products)

    # 프리컴퓨팅 스코어가 없으면 런타임 계산
    scores = outfit_dict.get("scores") or {}
    if not scores.get("total"):
        scores = compute_soft_scores(
            outfit_dict,
            user_tone_id=tone_id,
            user_tpo_list=user_tpo_list,
            budget_min=float(budget_min),
            budget_max=float(budget_max),
        )
        outfit_dict["scores"] = scores

    return _build_outfit_response(outfit_dict, tone_id, user_tpo_list)
