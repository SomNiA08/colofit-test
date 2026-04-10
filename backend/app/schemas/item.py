"""
Item API Pydantic 스키마 (Task 3.2).
"""

from pydantic import BaseModel


class PriceEntry(BaseModel):
    """가격 비교 테이블 1행 — 판매처 + 가격 + 유형."""
    product_id: str
    mall_name: str | None = None
    mall_url: str | None = None
    price: int | None = None
    match_type: str  # "base" | "exact"


class ItemDetailResponse(BaseModel):
    """GET /api/item/{id} 응답."""
    product_id: str
    name: str | None = None
    brand: str | None = None
    category: str | None = None
    color_hex: str | None = None
    tone_id: str | None = None
    price: int | None = None
    mall_name: str | None = None
    mall_url: str | None = None
    image_url: str | None = None
    gender: str | None = None
    price_comparison: list[PriceEntry]   # 자신 포함, 가격 오름차순


class SimilarProductResponse(BaseModel):
    """유사 상품 1건."""
    product_id: str
    name: str | None = None
    brand: str | None = None
    category: str | None = None
    color_hex: str | None = None
    price: int | None = None
    image_url: str | None = None
    mall_url: str | None = None
    mall_name: str | None = None
    similarity: float           # 0.0 ~ 1.0
    similarity_pct: int         # round(similarity × 100)
    match_type: str             # "exact" | "similar"


class SimilarResponse(BaseModel):
    """GET /api/item/{id}/similar 응답."""
    base_product_id: str
    items: list[SimilarProductResponse]
