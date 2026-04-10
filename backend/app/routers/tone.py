"""
Tone API — GET /api/tone/{id} (Task 3.6).
톤 메타데이터(정적) + 해당 톤에 어울리는 샘플 코디 3개(동적).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.outfit import Outfit
from app.models.product import Product
from app.schemas.tone import SampleOutfit, SwatchColor, ToneDetailResponse

router = APIRouter()

# ── 12톤 정적 메타데이터 ──────────────────────────────────────────────────────

_TONE_META: dict[str, dict] = {
    "spring_warm_light": {
        "name": "봄웜라이트",
        "gradient": "linear-gradient(135deg, #FF9E8A 0%, #FFC8A0 50%, #FFF5E4 100%)",
        "description": "밝고 투명한 복숭아·코랄 계열이 잘 어울려요. 선명하지 않은 부드러운 웜 컬러로 생기 있는 피부를 연출할 수 있어요.",
        "good_colors": [
            {"hex": "#FFCBA4", "name": "복숭아"},
            {"hex": "#FFF5E4", "name": "아이보리"},
            {"hex": "#FF7F5E", "name": "코랄"},
            {"hex": "#A8C44E", "name": "라임"},
            {"hex": "#E8B84B", "name": "골든"},
            {"hex": "#C8916A", "name": "카멜"},
        ],
        "avoid_colors": [
            {"hex": "#1A1A2E", "name": "블랙"},
            {"hex": "#1A2A4A", "name": "네이비"},
            {"hex": "#444444", "name": "차콜"},
            {"hex": "#722F37", "name": "와인"},
        ],
    },
    "spring_warm_bright": {
        "name": "봄웜브라이트",
        "gradient": "linear-gradient(135deg, #FF8066 0%, #FFA07A 50%, #FFD580 100%)",
        "description": "생동감 넘치는 코랄·오렌지·옐로우 계열로 활기찬 인상을 줘요. 선명한 웜 컬러가 화사한 피부톤을 더욱 빛나게 해줘요.",
        "good_colors": [
            {"hex": "#FF6B6B", "name": "코랄레드"},
            {"hex": "#FF8C42", "name": "오렌지"},
            {"hex": "#FFD166", "name": "옐로우"},
            {"hex": "#6BCB77", "name": "그린"},
            {"hex": "#4ECDC4", "name": "터콰이즈"},
            {"hex": "#A8E063", "name": "라임"},
        ],
        "avoid_colors": [
            {"hex": "#1A1A2E", "name": "블랙"},
            {"hex": "#6B2737", "name": "버건디"},
            {"hex": "#1A2A4A", "name": "네이비"},
            {"hex": "#444444", "name": "차콜"},
        ],
    },
    "spring_warm_mute": {
        "name": "봄웜뮤트",
        "gradient": "linear-gradient(135deg, #D4A574 0%, #C8916A 50%, #E8D5B7 100%)",
        "description": "카멜·올리브·피치 같은 내추럴한 어스톤이 잘 어울려요. 채도가 낮은 부드러운 웜 컬러로 편안하고 세련된 분위기를 낼 수 있어요.",
        "good_colors": [
            {"hex": "#C8916A", "name": "카멜"},
            {"hex": "#C1735A", "name": "테라코타"},
            {"hex": "#8B9E5E", "name": "올리브"},
            {"hex": "#F5C5A3", "name": "피치"},
            {"hex": "#D4A852", "name": "골든"},
            {"hex": "#F5ECD7", "name": "웜화이트"},
        ],
        "avoid_colors": [
            {"hex": "#1A1A2E", "name": "블랙"},
            {"hex": "#444444", "name": "차콜"},
            {"hex": "#F8F8F8", "name": "퓨어화이트"},
            {"hex": "#A89CC8", "name": "쿨라벤더"},
        ],
    },
    "summer_cool_light": {
        "name": "여름쿨라이트",
        "gradient": "linear-gradient(135deg, #C8B8E8 0%, #98D0E8 50%, #C0E8E0 100%)",
        "description": "라벤더·파우더블루·소프트핑크 등 밝고 파스텔한 쿨 컬러가 잘 어울려요. 차분하고 로맨틱한 분위기로 피부를 맑게 보이게 해줘요.",
        "good_colors": [
            {"hex": "#C8A8E8", "name": "라벤더"},
            {"hex": "#9BB8D4", "name": "파우더블루"},
            {"hex": "#F0A0B0", "name": "로즈"},
            {"hex": "#F5C5CC", "name": "소프트핑크"},
            {"hex": "#98DCC8", "name": "민트"},
            {"hex": "#C4A8D8", "name": "라일락"},
        ],
        "avoid_colors": [
            {"hex": "#FF8C42", "name": "오렌지"},
            {"hex": "#D4A852", "name": "머스타드"},
            {"hex": "#E8B84B", "name": "골든"},
            {"hex": "#C8916A", "name": "카멜"},
        ],
    },
    "summer_cool_soft": {
        "name": "여름쿨소프트",
        "gradient": "linear-gradient(135deg, #B0A6C6 0%, #98B8D4 50%, #C0D8E8 100%)",
        "description": "소프트핑크·라벤더·모브처럼 부드럽고 차분한 쿨 컬러가 잘 어울려요. 그레이시한 파스텔 계열로 우아하고 세련된 인상을 줘요.",
        "good_colors": [
            {"hex": "#F5C5CC", "name": "소프트핑크"},
            {"hex": "#C4A8D8", "name": "라벤더"},
            {"hex": "#A8C4DC", "name": "파스텔블루"},
            {"hex": "#E8A4B0", "name": "로즈"},
            {"hex": "#B8A8C4", "name": "모브"},
            {"hex": "#C8C8C8", "name": "그레이"},
        ],
        "avoid_colors": [
            {"hex": "#FF8C42", "name": "오렌지"},
            {"hex": "#D4A852", "name": "머스타드"},
            {"hex": "#8B9E5E", "name": "어스톤"},
            {"hex": "#8B7355", "name": "카키"},
        ],
    },
    "summer_cool_mute": {
        "name": "여름쿨뮤트",
        "gradient": "linear-gradient(135deg, #8B8B9E 0%, #8AAAB8 50%, #A8B8C0 100%)",
        "description": "스모키블루·로즈그레이·더스티핑크 같은 채도가 낮은 쿨 컬러가 잘 어울려요. 차분하고 성숙한 분위기로 세련된 스타일링에 적합해요.",
        "good_colors": [
            {"hex": "#7A9AB0", "name": "스모키블루"},
            {"hex": "#A890A8", "name": "모브"},
            {"hex": "#A89898", "name": "로즈그레이"},
            {"hex": "#D4A8B0", "name": "더스티핑크"},
            {"hex": "#9898B8", "name": "라벤더"},
            {"hex": "#B8B0A8", "name": "그레이지"},
        ],
        "avoid_colors": [
            {"hex": "#FF8C42", "name": "오렌지"},
            {"hex": "#FFD166", "name": "브라이트옐로"},
            {"hex": "#C8916A", "name": "카멜"},
            {"hex": "#8B9E5E", "name": "어스톤"},
        ],
    },
    "autumn_warm_bright": {
        "name": "가을웜브라이트",
        "gradient": "linear-gradient(135deg, #D4722A 0%, #C1735A 50%, #E8B84B 100%)",
        "description": "오렌지·테라코타·카키처럼 선명한 어스 계열이 잘 어울려요. 따뜻하고 강렬한 웜 컬러로 생동감 있는 가을 분위기를 연출할 수 있어요.",
        "good_colors": [
            {"hex": "#E0722A", "name": "오렌지"},
            {"hex": "#C1735A", "name": "테라코타"},
            {"hex": "#B85C28", "name": "버니"},
            {"hex": "#D4A852", "name": "골든"},
            {"hex": "#8B9E5E", "name": "카키"},
            {"hex": "#6B8A44", "name": "올리브"},
        ],
        "avoid_colors": [
            {"hex": "#FF69B4", "name": "핫핑크"},
            {"hex": "#F8F8F8", "name": "퓨어화이트"},
            {"hex": "#C4A8D8", "name": "라벤더"},
            {"hex": "#6BADB9", "name": "쿨블루"},
        ],
    },
    "autumn_warm_mute": {
        "name": "가을웜뮤트",
        "gradient": "linear-gradient(135deg, #A0856C 0%, #9C7A58 50%, #D4B896 100%)",
        "description": "카멜·어스톤·올리브처럼 차분하고 깊이 있는 자연 색상이 잘 어울려요. 내추럴하면서 성숙한 분위기로 편안한 스타일링을 완성해줘요.",
        "good_colors": [
            {"hex": "#C8916A", "name": "카멜"},
            {"hex": "#C1735A", "name": "테라코타"},
            {"hex": "#A08060", "name": "어스톤"},
            {"hex": "#C4943A", "name": "머스타드"},
            {"hex": "#8B9E5E", "name": "올리브"},
            {"hex": "#8B6040", "name": "브라운"},
        ],
        "avoid_colors": [
            {"hex": "#FF69B4", "name": "핫핑크"},
            {"hex": "#9B59B6", "name": "퍼플"},
            {"hex": "#00FF7F", "name": "네온"},
            {"hex": "#ADD8E6", "name": "아이시블루"},
        ],
    },
    "autumn_warm_deep": {
        "name": "가을웜딥",
        "gradient": "linear-gradient(135deg, #8B5A2B 0%, #722F37 50%, #9C4A2C 100%)",
        "description": "버건디·다크브라운·포레스트그린처럼 깊고 진한 어스 컬러가 잘 어울려요. 풍부하고 고급스러운 가을 감성을 담은 스타일링에 최적화되어 있어요.",
        "good_colors": [
            {"hex": "#722F37", "name": "버건디"},
            {"hex": "#5C3A1E", "name": "다크브라운"},
            {"hex": "#C1735A", "name": "테라코타"},
            {"hex": "#2D5A27", "name": "포레스트그린"},
            {"hex": "#C4943A", "name": "머스타드"},
            {"hex": "#A05A3A", "name": "카퍼"},
        ],
        "avoid_colors": [
            {"hex": "#F5DDE8", "name": "파스텔"},
            {"hex": "#C4A8D8", "name": "라벤더"},
            {"hex": "#FF69B4", "name": "핫핑크"},
            {"hex": "#F0F8FF", "name": "아이시화이트"},
        ],
    },
    "winter_cool_bright": {
        "name": "겨울쿨브라이트",
        "gradient": "linear-gradient(135deg, #1A2898 0%, #CC0066 50%, #E8B4C8 100%)",
        "description": "선명한 로열블루·마젠타·에메랄드처럼 대비가 강한 쿨 컬러가 잘 어울려요. 강렬하고 도시적인 인상으로 개성 있는 스타일을 완성해줘요.",
        "good_colors": [
            {"hex": "#FFFFFF", "name": "퓨어화이트"},
            {"hex": "#1A1A2E", "name": "블랙"},
            {"hex": "#1A2898", "name": "로열블루"},
            {"hex": "#CC0066", "name": "마젠타"},
            {"hex": "#008080", "name": "에메랄드"},
            {"hex": "#6B2780", "name": "퍼플"},
        ],
        "avoid_colors": [
            {"hex": "#FF8C42", "name": "오렌지"},
            {"hex": "#C8916A", "name": "카멜"},
            {"hex": "#E8B84B", "name": "골든"},
            {"hex": "#8B9E5E", "name": "어스톤"},
        ],
    },
    "winter_cool_deep": {
        "name": "겨울쿨딥",
        "gradient": "linear-gradient(135deg, #1E1E2E 0%, #2A2A5E 50%, #4A2060 100%)",
        "description": "블랙·네이비·버건디처럼 깊고 진한 쿨 컬러가 잘 어울려요. 강한 대비와 풍부한 색감으로 격조 있고 드라마틱한 분위기를 줘요.",
        "good_colors": [
            {"hex": "#1A1A2E", "name": "블랙"},
            {"hex": "#1A2A4A", "name": "네이비"},
            {"hex": "#722F37", "name": "버건디"},
            {"hex": "#3D1A5E", "name": "다크퍼플"},
            {"hex": "#006666", "name": "에메랄드"},
            {"hex": "#333333", "name": "차콜"},
        ],
        "avoid_colors": [
            {"hex": "#F5DDE8", "name": "파스텔"},
            {"hex": "#F5C5A3", "name": "피치"},
            {"hex": "#C8916A", "name": "카멜"},
            {"hex": "#E8B84B", "name": "골든"},
        ],
    },
    "winter_cool_light": {
        "name": "겨울쿨라이트",
        "gradient": "linear-gradient(135deg, #C8C8E8 0%, #A0B8E8 50%, #D4E8F4 100%)",
        "description": "아이시블루·실버·라벤더처럼 밝고 선명한 쿨 컬러가 잘 어울려요. 청명하고 우아한 분위기로 깔끔하고 시원한 이미지를 연출할 수 있어요.",
        "good_colors": [
            {"hex": "#FFFFFF", "name": "화이트"},
            {"hex": "#ADD8E6", "name": "아이시블루"},
            {"hex": "#C0C0C0", "name": "실버"},
            {"hex": "#C4A8D8", "name": "라벤더"},
            {"hex": "#FFB6C1", "name": "소프트핑크"},
            {"hex": "#AAAACC", "name": "페리윙클"},
        ],
        "avoid_colors": [
            {"hex": "#FF8C42", "name": "오렌지"},
            {"hex": "#D4A852", "name": "머스타드"},
            {"hex": "#C8916A", "name": "카멜"},
            {"hex": "#8B7355", "name": "카키"},
        ],
    },
}

_VALID_TONE_IDS = set(_TONE_META.keys())


# ── 엔드포인트 ────────────────────────────────────────────────────────────────

@router.get("/api/tone/{id}", response_model=ToneDetailResponse)
async def get_tone(
    id: str,
    db: AsyncSession = Depends(get_db),
) -> ToneDetailResponse:
    """
    톤 상세 정보 + 해당 톤에 어울리는 샘플 코디 최대 3개.

    샘플 코디: 해당 tone_id를 가진 상품이 포함된 코디를 우선 반환.
    해당 코디가 없으면 전체 코디 중 상위 3개를 반환.
    """
    if id not in _VALID_TONE_IDS:
        raise HTTPException(status_code=404, detail="존재하지 않는 톤 ID입니다.")

    meta = _TONE_META[id]

    # ── 샘플 코디 조회 ──
    # 1. 해당 tone_id 상품 ID 목록
    tone_product_rows = (
        await db.execute(
            select(Product.id).where(Product.tone_id == id)
        )
    ).scalars().all()
    tone_product_ids = set(tone_product_rows)

    sample_outfits: list[SampleOutfit] = []

    if tone_product_ids:
        # 2. 해당 상품을 포함한 코디 조회
        outfit_rows = (await db.execute(select(Outfit))).scalars().all()

        matched: list[Outfit] = []
        for o in outfit_rows:
            if o.item_ids and set(o.item_ids) & tone_product_ids:
                matched.append(o)
                if len(matched) >= 3:
                    break

        # 부족하면 나머지 코디로 채움
        if len(matched) < 3:
            for o in outfit_rows:
                if o not in matched:
                    matched.append(o)
                if len(matched) >= 3:
                    break

        # 3. 첫 아이템 이미지 조회
        all_ids: set[str] = set()
        for o in matched:
            if o.item_ids:
                all_ids.update(o.item_ids)

        product_map: dict[str, Product] = {}
        if all_ids:
            prod_rows = (
                await db.execute(
                    select(Product).where(Product.id.in_(all_ids))
                )
            ).scalars().all()
            product_map = {p.id: p for p in prod_rows}

        for o in matched:
            first_img: str | None = None
            for pid in (o.item_ids or []):
                p = product_map.get(pid)
                if p and p.image_url:
                    first_img = p.image_url
                    break
            sample_outfits.append(
                SampleOutfit(
                    outfit_id=o.id,
                    image_url=first_img,
                    total_price=o.total_price,
                    designed_tpo=o.designed_tpo,
                )
            )
    else:
        # tone_id 상품 없으면 전체에서 3개
        fallback_rows = (
            await db.execute(select(Outfit).limit(3))
        ).scalars().all()

        all_ids = set()
        for o in fallback_rows:
            if o.item_ids:
                all_ids.update(o.item_ids)

        product_map = {}
        if all_ids:
            prod_rows = (
                await db.execute(
                    select(Product).where(Product.id.in_(all_ids))
                )
            ).scalars().all()
            product_map = {p.id: p for p in prod_rows}

        for o in fallback_rows:
            first_img = None
            for pid in (o.item_ids or []):
                p = product_map.get(pid)
                if p and p.image_url:
                    first_img = p.image_url
                    break
            sample_outfits.append(
                SampleOutfit(
                    outfit_id=o.id,
                    image_url=first_img,
                    total_price=o.total_price,
                    designed_tpo=o.designed_tpo,
                )
            )

    return ToneDetailResponse(
        tone_id=id,
        name=meta["name"],
        gradient=meta["gradient"],
        description=meta["description"],
        good_colors=[SwatchColor(**c) for c in meta["good_colors"]],
        avoid_colors=[SwatchColor(**c) for c in meta["avoid_colors"]],
        sample_outfits=sample_outfits,
    )
