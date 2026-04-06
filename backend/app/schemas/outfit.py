"""
Outfit / Feed API Pydantic 스키마 (기획서 §14.3).
"""

from pydantic import BaseModel


class ProductResponse(BaseModel):
    product_id: str
    name: str | None = None
    brand: str | None = None
    category: str | None = None
    color_hex: str | None = None
    tone_id: str | None = None
    price: int | None = None
    gender: str | None = None
    image_url: str | None = None
    mall_url: str | None = None


class OutfitScores(BaseModel):
    pcf: float
    of: float
    ch: float
    pe: float
    sf: float
    total: float
    total_reranked: float | None = None


class OutfitResponse(BaseModel):
    outfit_id: str
    items: list[ProductResponse]
    total_price: int | None = None
    lowest_total_price: int | None = None
    scores: OutfitScores
    reasons: list[str]
    is_complete_outfit: bool | None = None
    designed_tpo: str | None = None


class FeedResponse(BaseModel):
    outfits: list[OutfitResponse]
    total_count: int
    has_next: bool
