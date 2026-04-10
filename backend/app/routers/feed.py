"""
Feed API — GET /api/feed (기획서 §14.3).

파이프라인:
  DB 로드 → Hard Filter → Soft Score → Rerank → Reason → 페이지네이션
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.outfit import Outfit
from app.models.product import Product
from app.schemas.outfit import (
    FeedResponse,
    OutfitResponse,
    OutfitScores,
    ProductResponse,
)
from app.services.feed_builder import apply_hard_filters, compute_soft_scores, rerank
from app.services.reason_generator import generate_reasons

router = APIRouter()

_PAGE_SIZE = 20


# ── 변환 헬퍼 ────────────────────────────────────────────────────────────────

def _product_to_dict(p: Product) -> dict:
    return {
        "product_id": p.id,
        "name": p.name,
        "brand": p.brand,
        "category": p.category,
        "color_hex": p.color_hex,
        "tone_id": p.tone_id,
        "price": p.price,
        "gender": p.gender,
        "silhouette": p.silhouette,
        "formality": p.formality,
        "image_url": p.image_url,
        "mall_url": p.mall_url,
    }


def _outfit_to_dict(o: Outfit, products: dict[str, Product]) -> dict:
    """ORM Outfit 객체를 파이프라인용 dict로 변환한다."""
    items = [
        _product_to_dict(products[pid])
        for pid in (o.item_ids or [])
        if pid in products
    ]
    return {
        "outfit_id": o.id,
        "items": items,
        "gender": o.gender,
        # DB에는 단일 문자열, 파이프라인은 리스트를 기대함
        "designed_tpo": [o.designed_tpo] if o.designed_tpo else [],
        "designed_moods": o.designed_moods or [],
        "total_price": o.total_price,
        "lowest_total_price": o.lowest_total_price,
        "is_complete_outfit": o.is_complete_outfit,
        "tags": o.tags or [],
        "scores": o.scores or {},
        "llm_quality_score": o.llm_quality_score,
    }


def _build_outfit_response(
    outfit_dict: dict,
    user_tone_id: str,
    user_tpo_list: list[str],
) -> OutfitResponse:
    """파이프라인 결과 dict를 OutfitResponse Pydantic 모델로 변환한다."""
    scores = outfit_dict.get("scores") or {}
    reasons = generate_reasons(
        scores,
        user_tone_id=user_tone_id,
        user_tpo_list=user_tpo_list,
    )
    items = [
        ProductResponse(
            product_id=item["product_id"],
            name=item.get("name"),
            brand=item.get("brand"),
            category=item.get("category"),
            color_hex=item.get("color_hex"),
            tone_id=item.get("tone_id"),
            price=item.get("price"),
            gender=item.get("gender"),
            image_url=item.get("image_url"),
            mall_url=item.get("mall_url"),
        )
        for item in outfit_dict.get("items", [])
    ]
    designed_tpo_list = outfit_dict.get("designed_tpo") or []
    return OutfitResponse(
        outfit_id=outfit_dict["outfit_id"],
        items=items,
        total_price=outfit_dict.get("total_price"),
        lowest_total_price=outfit_dict.get("lowest_total_price"),
        scores=OutfitScores(
            pcf=scores.get("pcf", 0.0),
            of=scores.get("of", 0.0),
            ch=scores.get("ch", 0.0),
            pe=scores.get("pe", 0.0),
            sf=scores.get("sf", 0.0),
            total=scores.get("total", 0.0),
            total_reranked=scores.get("total_reranked"),
        ),
        reasons=reasons,
        is_complete_outfit=outfit_dict.get("is_complete_outfit"),
        designed_tpo=designed_tpo_list[0] if designed_tpo_list else None,
    )


# ── 엔드포인트 ───────────────────────────────────────────────────────────────

@router.get("/api/feed", response_model=FeedResponse)
async def get_feed(
    tone_id: str,
    gender: str,
    budget_min: int = 0,
    budget_max: int = 300000,
    tpo: str = "",
    page: int = 1,
    db: AsyncSession = Depends(get_db),
) -> FeedResponse:
    """
    코디 피드를 반환한다.

    파이프라인: Hard Filter → Soft Score → Rerank → Reason → 페이지네이션

    Args:
        tone_id: 사용자 퍼스널컬러 (e.g. "summer_cool_soft")
        gender: 사용자 성별 ("female" / "male")
        budget_min: 예산 최솟값
        budget_max: 예산 최댓값
        tpo: TPO 콤마 구분 문자열 (e.g. "office,date")
        page: 페이지 번호 (1부터 시작)
    """
    user_tpo_list = [t.strip() for t in tpo.split(",") if t.strip()] if tpo else []
    page = max(1, page)

    # 1. DB에서 코디 로드 — gender 프리필터 + 상한 500개 (H1은 이미 DB에서 처리)
    outfit_rows = (
        await db.execute(
            select(Outfit)
            .where(Outfit.gender == gender)
            .limit(500)
        )
    ).scalars().all()

    # 2. 참조된 상품 일괄 로드
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

    # 3. ORM → dict 변환
    outfit_dicts = [_outfit_to_dict(o, products) for o in outfit_rows]

    # 4. Hard Filter
    is_all_tab = len(user_tpo_list) == 0  # "전체" 탭 여부
    filtered = apply_hard_filters(
        outfit_dicts,
        user_gender=gender,
        budget_max=float(budget_max),
        user_tpo_list=user_tpo_list,
        user_tone_id=tone_id,
        is_all_tab=is_all_tab,
    )

    # 5. Soft Score
    for outfit in filtered:
        outfit["scores"] = compute_soft_scores(
            outfit,
            user_tone_id=tone_id,
            user_tpo_list=user_tpo_list,
            budget_min=float(budget_min),
            budget_max=float(budget_max),
        )

    # 6. Rerank (최대 200개)
    reranked = rerank(filtered)

    # 7. 페이지네이션
    total_count = len(reranked)
    offset = (page - 1) * _PAGE_SIZE
    page_items = reranked[offset: offset + _PAGE_SIZE]
    has_next = offset + _PAGE_SIZE < total_count

    # 8. 응답 조합
    outfit_responses = [
        _build_outfit_response(o, tone_id, user_tpo_list)
        for o in page_items
    ]

    return FeedResponse(
        outfits=outfit_responses,
        total_count=total_count,
        has_next=has_next,
    )
