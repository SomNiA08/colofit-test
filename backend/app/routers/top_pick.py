"""
Top Pick API — GET /api/top-pick (기획서 §4.4).

우선순위:
  1. user_id + save 반응 있음 → 저장 코디 중 최고 점수
  2. user_id 없음 or save 0건 → 전체 DB 중 최고 점수 (콜드스타트)

시간대 TPO:
  tpo 파라미터가 비어 있으면 현재 서버 시각으로 자동 추론.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.outfit import Outfit
from app.models.product import Product
from app.models.reaction import Reaction
from app.routers.feed import _outfit_to_dict, _build_outfit_response
from app.schemas.top_pick import TopPickResponse
from app.services.feed_builder import apply_hard_filters
from app.services.top_pick import infer_tpo_from_hour, select_top_pick

router = APIRouter()


async def _load_products(db: AsyncSession, item_ids: set[str]) -> dict[str, Product]:
    if not item_ids:
        return {}
    rows = (
        await db.execute(select(Product).where(Product.id.in_(item_ids)))
    ).scalars().all()
    return {p.id: p for p in rows}


@router.get("/api/top-pick", response_model=TopPickResponse)
async def get_top_pick(
    tone_id: str,
    gender: str,
    budget_min: int = 0,
    budget_max: int = 300000,
    tpo: str = "",
    user_id: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> TopPickResponse:
    """
    사용자에게 가장 잘 맞는 코디 1개를 반환한다.

    Args:
        tone_id:    퍼스널컬러 tone_id
        gender:     "female" | "male"
        budget_min: 예산 하한
        budget_max: 예산 상한
        tpo:        TPO 콤마 구분 (비면 시간대 자동 추론)
        user_id:    사용자 UUID (있으면 저장 코디 우선)
    """
    # 1. TPO 결정 (명시 > 시간대 추론)
    now_hour = datetime.now(tz=timezone.utc).hour
    inferred_tpo = infer_tpo_from_hour(now_hour)
    if tpo:
        user_tpo_list = [t.strip() for t in tpo.split(",") if t.strip()]
        applied_tpo = tpo
    else:
        user_tpo_list = [inferred_tpo]
        applied_tpo = inferred_tpo

    # 2. 저장 코디 ID 조회 (user_id 있을 때)
    saved_outfit_ids: set[str] = set()
    if user_id:
        try:
            uid = uuid.UUID(user_id)
            rows = (
                await db.execute(
                    select(Reaction.outfit_id).where(
                        Reaction.user_id == uid,
                        Reaction.reaction_type == "save",
                        Reaction.outfit_id.isnot(None),
                    )
                )
            ).scalars().all()
            saved_outfit_ids = {r for r in rows if r}
        except ValueError:
            pass  # 잘못된 UUID → 콜드스타트로 진행

    # 3. 후보 코디 로드
    source = "global"
    outfit_rows: list[Outfit] = []

    if saved_outfit_ids:
        outfit_rows = (
            await db.execute(
                select(Outfit).where(Outfit.id.in_(saved_outfit_ids))
            )
        ).scalars().all()
        source = "saved"

    # 저장 코디가 없으면 전체 DB
    if not outfit_rows:
        outfit_rows = (await db.execute(select(Outfit))).scalars().all()
        source = "global"

    # 4. 상품 일괄 로드
    all_item_ids: set[str] = set()
    for o in outfit_rows:
        if o.item_ids:
            all_item_ids.update(o.item_ids)
    products = await _load_products(db, all_item_ids)

    # 5. ORM → dict 변환
    outfit_dicts = [_outfit_to_dict(o, products) for o in outfit_rows]

    # 6. Hard Filter
    filtered = apply_hard_filters(
        outfit_dicts,
        user_gender=gender,
        budget_max=float(budget_max),
        user_tpo_list=user_tpo_list,
        user_tone_id=tone_id,
    )

    # Hard Filter 후 후보가 없으면 필터 없이 재시도 (저장 코디 전용)
    if not filtered and source == "saved":
        filtered = outfit_dicts

    # 7. Top Pick 선택
    top = select_top_pick(
        filtered,
        user_tone_id=tone_id,
        user_tpo_list=user_tpo_list,
        budget_min=float(budget_min),
        budget_max=float(budget_max),
    )

    # 8. 전체 DB에서도 없으면 404
    if top is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="추천할 코디가 없어요.")

    # 9. 응답 조합
    outfit_resp = _build_outfit_response(top, tone_id, user_tpo_list)
    return TopPickResponse(
        **outfit_resp.model_dump(),
        source=source,
        inferred_tpo=applied_tpo,
    )
