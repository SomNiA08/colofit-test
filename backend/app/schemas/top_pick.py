"""Top Pick API 스키마."""

from app.schemas.outfit import OutfitResponse


class TopPickResponse(OutfitResponse):
    """GET /api/top-pick 응답. OutfitResponse에 메타 정보 추가."""

    source: str          # "saved" | "global"
    inferred_tpo: str    # 시간대 추론 TPO (tpo 파라미터가 없을 때 적용된 값)
