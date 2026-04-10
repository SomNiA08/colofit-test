"""
피드백 개인화 학습 서비스.

사용자 피드백 이벤트를 UserPreference에 누적하고,
10건 이상 축적 시 5축 weight_overrides를 자동 생성한다.
"""

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.outfit import Outfit
from app.models.product import Product
from app.models.user_preference import UserPreference

# ── 행동별 가중치 ─────────────────────────────────────────────────────────────

EVENT_WEIGHTS: dict[str, float] = {
    "save":    +2.0,
    "like":    +1.0,
    "click":   +0.3,
    "dislike": -1.5,
}

MIN_FEEDBACK_COUNT = 10  # weight_overrides 생성 임계값


# ═══════════════════════════════════════════════════════════════════════════════
# 순수 함수
# ═══════════════════════════════════════════════════════════════════════════════

def generate_weight_overrides(pref: UserPreference) -> dict[str, float]:
    """
    UserPreference 데이터로부터 5축 weight_overrides를 생성한다.

    - 강한 톤 일관성 (최고 톤 점수 >= 4.0): pcf 가중치 상향
    - 강한 카테고리 일관성 (최고 카테고리 점수 >= 3.0): sf 가중치 상향
    - 저가 선호 (avg_liked_price < 80,000): pe 가중치 상향
    - 고가 선호 (avg_liked_price >= 150,000): pe 가중치 하향

    feed_builder.DEFAULT_WEIGHTS = {pcf:0.25, of:0.20, ch:0.15, pe:0.15, sf:0.25}
    오버라이드 값은 정규화 후 적용되므로 상대 비중이 중요.

    Returns:
        weight_overrides dict — 비어있으면 아직 데이터 부족.
    """
    if (pref.feedback_count or 0) < MIN_FEEDBACK_COUNT:
        return {}

    overrides: dict[str, float] = {}

    # PCF: 특정 톤을 반복적으로 선호 → 퍼스널컬러 가중치 상향
    tones: dict[str, float] = pref.tone_preferences or {}
    if tones:
        max_tone_score = max(tones.values())
        if max_tone_score >= 4.0:
            # 0.25 → 최대 0.40 (선형 스케일)
            overrides["pcf"] = round(min(0.40, 0.25 + max_tone_score / 50.0), 3)

    # SF: 특정 카테고리(스타일)를 반복적으로 선호 → 스타일 가중치 상향
    cats: dict[str, float] = pref.category_preferences or {}
    if cats:
        max_cat_score = max(cats.values())
        if max_cat_score >= 3.0:
            overrides["sf"] = round(min(0.38, 0.25 + max_cat_score / 40.0), 3)

    # PE: 평균 좋아요 가격대 기반 → 가격효율 가중치 조정
    avg_price = pref.avg_liked_price or 0
    if avg_price > 0:
        if avg_price < 80_000:
            overrides["pe"] = 0.25  # 저가 선호 → pe 상향 (0.15 → 0.25)
        elif avg_price >= 150_000:
            overrides["pe"] = 0.08  # 고가 선호 → pe 하향 (0.15 → 0.08)

    return overrides


# ═══════════════════════════════════════════════════════════════════════════════
# 비동기 DB 함수
# ═══════════════════════════════════════════════════════════════════════════════

async def update_preference(
    user_id: uuid.UUID,
    outfit_id: str,
    event_type: str,
    db: AsyncSession,
) -> UserPreference:
    """
    피드백 이벤트 1건을 UserPreference에 반영한다.

    1. UserPreference 로드 (없으면 생성)
    2. Outfit의 아이템(Product) 로드
    3. 선호도 누적 (tone/category/brand/price)
    4. feedback_count 증가
    5. 10건+ 시 weight_overrides 재생성
    6. DB 저장 후 반환
    """
    delta = EVENT_WEIGHTS.get(event_type, 0.0)

    pref = await _get_or_create_pref(user_id, db)

    if delta == 0.0:
        # 알 수 없는 이벤트 → 선호도 변화 없음
        return pref

    # ── Outfit + Products 로드 ─────────────────────────────────────────
    outfit = (await db.execute(
        select(Outfit).where(Outfit.id == outfit_id)
    )).scalar_one_or_none()

    products: list[Product] = []
    if outfit and outfit.item_ids:
        products = (await db.execute(
            select(Product).where(Product.id.in_(outfit.item_ids))
        )).scalars().all()

    # ── 선호도 누적 ───────────────────────────────────────────────────
    tone_prefs: dict[str, float] = dict(pref.tone_preferences or {})
    cat_prefs: dict[str, float] = dict(pref.category_preferences or {})
    brand_prefs: dict[str, float] = dict(pref.brand_preferences or {})

    for product in products:
        if product.tone_id:
            tone_prefs[product.tone_id] = tone_prefs.get(product.tone_id, 0.0) + delta
        if product.category:
            cat_prefs[product.category] = cat_prefs.get(product.category, 0.0) + delta
        if product.brand:
            brand_prefs[product.brand] = brand_prefs.get(product.brand, 0.0) + delta

    # 평균 가격 갱신 (save/like만, 지수이동평균 α=0.35)
    if event_type in ("save", "like") and outfit and outfit.total_price:
        old_avg = pref.avg_liked_price or outfit.total_price
        pref.avg_liked_price = int(0.35 * outfit.total_price + 0.65 * old_avg)

    # 필드 갱신 (새 dict 할당으로 JSONB 변경 감지 보장)
    pref.tone_preferences = tone_prefs
    pref.category_preferences = cat_prefs
    pref.brand_preferences = brand_prefs
    pref.feedback_count = (pref.feedback_count or 0) + 1

    # weight_overrides 재생성 (10건+ 시)
    new_overrides = generate_weight_overrides(pref)
    if new_overrides:
        pref.weight_overrides = new_overrides

    await db.commit()
    await db.refresh(pref)
    return pref


async def get_preference(
    user_id: uuid.UUID,
    db: AsyncSession,
) -> UserPreference | None:
    """사용자의 현재 선호도 프로파일을 반환한다."""
    return (await db.execute(
        select(UserPreference).where(UserPreference.user_id == user_id)
    )).scalar_one_or_none()


# ── 내부 헬퍼 ─────────────────────────────────────────────────────────────────

async def _get_or_create_pref(
    user_id: uuid.UUID,
    db: AsyncSession,
) -> UserPreference:
    """UserPreference 행을 가져오거나 새로 생성한다."""
    pref = (await db.execute(
        select(UserPreference).where(UserPreference.user_id == user_id)
    )).scalar_one_or_none()

    if pref is None:
        pref = UserPreference(
            user_id=user_id,
            tone_preferences={},
            category_preferences={},
            brand_preferences={},
            feedback_count=0,
        )
        db.add(pref)
        await db.flush()  # autoincrement id 생성

    return pref
