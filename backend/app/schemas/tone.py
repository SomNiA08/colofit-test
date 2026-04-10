"""
Tone API Pydantic 스키마 (Task 3.6).
"""

from pydantic import BaseModel


class SwatchColor(BaseModel):
    hex: str
    name: str


class SampleOutfit(BaseModel):
    """코디 캐러셀용 경량 응답."""
    outfit_id: str
    image_url: str | None = None   # 첫 번째 아이템 이미지
    total_price: int | None = None
    designed_tpo: str | None = None


class ToneDetailResponse(BaseModel):
    """GET /api/tone/{id} 응답."""
    tone_id: str
    name: str
    gradient: str                   # CSS linear-gradient 문자열
    description: str                # 시즌 설명 1~2문장
    good_colors: list[SwatchColor]
    avoid_colors: list[SwatchColor]
    sample_outfits: list[SampleOutfit]  # 최대 3개
