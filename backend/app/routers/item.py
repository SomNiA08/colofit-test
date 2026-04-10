"""
Item API — GET /api/item/{id}, GET /api/item/{id}/similar (Task 3.2).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.product import Product
from app.schemas.item import (
    ItemDetailResponse,
    PriceEntry,
    SimilarProductResponse,
    SimilarResponse,
)
from app.services.similar_finder import ProductInfo, find_similar, _is_exact

router = APIRouter()


# ── 헬퍼 ─────────────────────────────────────────────────────────────────────

def _to_product_info(p: Product) -> ProductInfo:
    return ProductInfo(
        id=p.id,
        name=p.name,
        brand=p.brand,
        category=p.category,
        color_hex=p.color_hex,
        price=p.price,
        mall_name=p.mall_name,
        mall_url=p.mall_url,
        image_url=p.image_url,
    )


# ── GET /api/item/{id} ───────────────────────────────────────────────────────

@router.get("/api/item/{id}", response_model=ItemDetailResponse)
async def get_item(
    id: str,
    db: AsyncSession = Depends(get_db),
) -> ItemDetailResponse:
    """
    아이템 상세 + 판매처별 가격 비교.

    price_comparison:
      - 기준 상품 자신 (match_type="base")
      - 동일 상품명+브랜드의 다른 판매처 (match_type="exact"), 가격 오름차순
    """
    # 기준 상품 조회
    row = (
        await db.execute(select(Product).where(Product.id == id))
    ).scalar_one_or_none()

    if row is None:
        raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다.")

    base = _to_product_info(row)

    # 동일 브랜드·카테고리 상품을 후보로 로드 후 Exact 필터링
    price_rows: list[PriceEntry] = [
        PriceEntry(
            product_id=row.id,
            mall_name=row.mall_name,
            mall_url=row.mall_url,
            price=row.price,
            match_type="base",
        )
    ]

    if row.brand and row.category:
        candidates_q = await db.execute(
            select(Product).where(
                Product.brand == row.brand,
                Product.category == row.category,
                Product.id != row.id,
            )
        )
        for p in candidates_q.scalars().all():
            if _is_exact(base, _to_product_info(p)):
                price_rows.append(
                    PriceEntry(
                        product_id=p.id,
                        mall_name=p.mall_name,
                        mall_url=p.mall_url,
                        price=p.price,
                        match_type="exact",
                    )
                )

    # 가격 오름차순 정렬 (None 가격은 마지막)
    price_rows.sort(key=lambda e: (e.price is None, e.price or 0))

    return ItemDetailResponse(
        product_id=row.id,
        name=row.name,
        brand=row.brand,
        category=row.category,
        color_hex=row.color_hex,
        tone_id=row.tone_id,
        price=row.price,
        mall_name=row.mall_name,
        mall_url=row.mall_url,
        image_url=row.image_url,
        gender=row.gender,
        price_comparison=price_rows,
    )


# ── GET /api/item/{id}/similar ───────────────────────────────────────────────

@router.get("/api/item/{id}/similar", response_model=SimilarResponse)
async def get_similar_items(
    id: str,
    top_n: int = 5,
    db: AsyncSession = Depends(get_db),
) -> SimilarResponse:
    """
    유사 상품 리스트 (색상 유사도 0.6 + 가격 유사도 0.4, 상위 top_n개).

    동일 카테고리 상품을 후보 풀로 사용한다.
    """
    # 기준 상품 조회
    row = (
        await db.execute(select(Product).where(Product.id == id))
    ).scalar_one_or_none()

    if row is None:
        raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다.")

    base = _to_product_info(row)

    # 동일 카테고리 후보 로드
    candidates: list[ProductInfo] = []
    if row.category:
        cand_rows = (
            await db.execute(
                select(Product).where(Product.category == row.category)
            )
        ).scalars().all()
        candidates = [_to_product_info(p) for p in cand_rows]

    results = find_similar(base, candidates, top_n=top_n)

    items = [
        SimilarProductResponse(
            product_id=r.product.id,
            name=r.product.name,
            brand=r.product.brand,
            category=r.product.category,
            color_hex=r.product.color_hex,
            price=r.product.price,
            image_url=r.product.image_url,
            mall_url=r.product.mall_url,
            mall_name=r.product.mall_name,
            similarity=r.similarity,
            similarity_pct=round(r.similarity * 100),
            match_type=r.match_type,
        )
        for r in results
    ]

    return SimilarResponse(base_product_id=id, items=items)
