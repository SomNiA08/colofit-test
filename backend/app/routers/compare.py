"""
A vs B 비교 API — GET /api/compare?ids=a,b (기획서 §4.5).

두 코디 ID를 받아 5축 점수를 비교하고 결정적 차이 요인과 결론을 반환한다.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.outfit import Outfit
from app.models.product import Product
from app.routers.feed import _outfit_to_dict, _build_outfit_response
from app.schemas.compare import CompareResponse
from app.services.comparator import compare
from app.services.feed_builder import compute_soft_scores

router = APIRouter()


async def _load_outfit_with_products(
    outfit_id: str,
    db: AsyncSession,
) -> tuple[Outfit, dict[str, Product]]:
    """코디 ORM + 연관 상품 dict를 반환한다."""
    outfit = (
        await db.execute(select(Outfit).where(Outfit.id == outfit_id))
    ).scalar_one_or_none()
    if outfit is None:
        raise HTTPException(status_code=404, detail=f"코디를 찾을 수 없어요: {outfit_id}")

    products: dict[str, Product] = {}
    if outfit.item_ids:
        rows = (
            await db.execute(
                select(Product).where(Product.id.in_(outfit.item_ids))
            )
        ).scalars().all()
        products = {p.id: p for p in rows}

    return outfit, products


@router.get("/api/compare", response_model=CompareResponse)
async def get_compare(
    ids: str,
    tone_id: str,
    gender: str,
    budget_min: int = 0,
    budget_max: int = 300000,
    tpo: str = "",
    db: AsyncSession = Depends(get_db),
) -> CompareResponse:
    """
    두 코디를 비교한다.

    Args:
        ids:        콤마 구분 코디 ID 2개 (e.g. "outfit_001,outfit_002")
        tone_id:    사용자 퍼스널컬러 tone_id
        gender:     "female" | "male"
        budget_min: 예산 하한
        budget_max: 예산 상한
        tpo:        TPO 콤마 구분 (e.g. "office,date")
    """
    # 1. IDs 파싱
    id_list = [i.strip() for i in ids.split(",") if i.strip()]
    if len(id_list) != 2:
        raise HTTPException(status_code=422, detail="ids에 코디 ID 2개를 콤마로 구분해서 보내주세요.")

    id_a, id_b = id_list
    if id_a == id_b:
        raise HTTPException(status_code=422, detail="서로 다른 코디 ID를 입력해주세요.")

    user_tpo_list = [t.strip() for t in tpo.split(",") if t.strip()] if tpo else []

    # 2. 두 코디 병렬 로드 (순차 실행, 각각 404 처리)
    outfit_a_orm, products_a = await _load_outfit_with_products(id_a, db)
    outfit_b_orm, products_b = await _load_outfit_with_products(id_b, db)

    # 3. ORM → dict 변환
    outfit_a = _outfit_to_dict(outfit_a_orm, products_a)
    outfit_b = _outfit_to_dict(outfit_b_orm, products_b)

    # 4. Soft Score 계산
    scores_a = compute_soft_scores(
        outfit_a,
        user_tone_id=tone_id,
        user_tpo_list=user_tpo_list,
        budget_min=float(budget_min),
        budget_max=float(budget_max),
    )
    scores_b = compute_soft_scores(
        outfit_b,
        user_tone_id=tone_id,
        user_tpo_list=user_tpo_list,
        budget_min=float(budget_min),
        budget_max=float(budget_max),
    )
    outfit_a["scores"] = scores_a
    outfit_b["scores"] = scores_b

    # 5. 비교
    result = compare(scores_a, scores_b)

    # 6. 응답 조합
    resp_a = _build_outfit_response(outfit_a, tone_id, user_tpo_list)
    resp_b = _build_outfit_response(outfit_b, tone_id, user_tpo_list)

    return CompareResponse(
        outfit_a=resp_a,
        outfit_b=resp_b,
        winner=result["winner"],
        decisive_axis=result["decisive_axis"],
        score_a=result["score_a"],
        score_b=result["score_b"],
        axis_diffs=result["axis_diffs"],
        conclusion=result["conclusion"],
    )
