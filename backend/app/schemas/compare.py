"""A vs B 비교 API 스키마."""

from pydantic import BaseModel

from app.schemas.outfit import OutfitResponse


class CompareResponse(BaseModel):
    """GET /api/compare 응답."""

    outfit_a: OutfitResponse
    outfit_b: OutfitResponse
    winner: str                     # "a" | "b" | "tie"
    decisive_axis: str | None       # "pcf" | "of" | "ch" | "pe" | "sf" | None
    score_a: float
    score_b: float
    axis_diffs: dict[str, float]    # {축: diff(a-b), 양수=A가 높음}
    conclusion: str                 # 한 줄 한국어 결론
