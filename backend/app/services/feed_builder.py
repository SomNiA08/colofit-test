"""
Hard Filter 체인 + Soft Score + 리랭킹 (기획서 §5.4, §6.1).

적용 순서 (비용 낮은 순):
  H1 성별 → H2 예산 → H3 계절 → H4 TPO → H5 브랜드
  → H7 톤 → H8 StyleFilter → H6 LLM 품질
  → Soft Score (5축 가중합) → Re-ranking (가산/제외/다양성/개인화)
"""

import json
from collections import Counter
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from app.services.scoring import (
    _SEASON_GROUPS,
    _TONE_TO_SEASON,
    _expand_tpos,
    calculate_pcf,
    calculate_of,
    calculate_ch,
    calculate_pe,
    calculate_sf,
)
from app.services.style_filter import filter_outfit

_DATA_DIR = Path(__file__).parent.parent.parent / "data"

# ── 시즌 매핑 (기획서 §H3) ──────────────────────────────────────────────────
_MONTH_TO_SEASON: dict[int, str] = {
    3: "spring", 4: "spring", 5: "spring",
    6: "summer", 7: "summer", 8: "summer",
    9: "autumn", 10: "autumn", 11: "autumn",
    12: "winter", 1: "winter", 2: "winter",
}

# 인접 시즌 허용 (봄↔여름, 여름↔가을, 가을↔겨울, 겨울↔봄)
_ADJACENT_SEASONS: dict[str, set[str]] = {
    "spring": {"spring", "summer", "winter"},
    "summer": {"summer", "spring", "autumn"},
    "autumn": {"autumn", "summer", "winter"},
    "winter": {"winter", "autumn", "spring"},
}


@lru_cache(maxsize=1)
def _load_brand_whitelist() -> set[str]:
    """브랜드 화이트리스트를 로드한다."""
    path = _DATA_DIR / "brand_whitelist.json"
    with path.open(encoding="utf-8") as f:
        brands = json.load(f)
    return {b.strip().lower() for b in brands}


# ═══════════════════════════════════════════════════════════════════════════════
# 개별 Hard Filter 함수 (각각 독립, 순수 함수)
# ═══════════════════════════════════════════════════════════════════════════════


def h1_gender(outfit: dict, user_gender: str) -> bool:
    """
    H1 성별 불일치 필터.
    코디 내 모든 아이템의 gender가 유저 성별 또는 unisex이면 통과.
    """
    for item in outfit.get("items", []):
        item_gender = (item.get("gender") or "unisex").lower()
        if item_gender != "unisex" and item_gender != user_gender.lower():
            return False
    return True


def h2_budget(outfit: dict, budget_max: float) -> bool:
    """
    H2 예산 초과 필터.
    코디 총액 > 사용자 예산 상한 × 1.5 이면 제거.
    """
    if budget_max <= 0:
        return True
    total_price = outfit.get("total_price", 0)
    return total_price <= budget_max * 1.5


def h3_season(
    outfit: dict,
    current_month: int | None = None,
) -> bool:
    """
    H3 계절 완전 불일치 필터.
    현재 시즌과 인접 시즌 허용, 완전 반대 시즌만 제거.
    TPO에 "travel"이 포함되면 필터 비적용.
    """
    if current_month is None:
        current_month = datetime.now().month

    current_season = _MONTH_TO_SEASON.get(current_month, "spring")
    allowed = _ADJACENT_SEASONS.get(current_season, {current_season})

    # TPO에 travel이 있으면 시즌 필터 면제
    outfit_tags = outfit.get("tags", [])
    if "travel" in outfit_tags:
        return True

    # 코디 태그에서 시즌 정보 추출
    outfit_seasons = set()
    for tag in outfit_tags:
        tag_lower = tag.lower()
        if tag_lower in ("spring", "summer", "autumn", "winter"):
            outfit_seasons.add(tag_lower)
        # "spring_season" 같은 형식도 지원
        for season in ("spring", "summer", "autumn", "winter"):
            if season in tag_lower:
                outfit_seasons.add(season)

    # 시즌 태그 없으면 통과 (정보 부족 → 필터 비적용)
    if not outfit_seasons:
        return True

    # 코디의 시즌 중 하나라도 허용 범위면 통과
    return bool(outfit_seasons & allowed)


def h4_tpo(
    outfit: dict,
    user_tpo_list: list[str],
    is_all_tab: bool = False,
) -> bool:
    """
    H4 TPO 완전 불일치 필터.
    동의어 확장 후에도 매칭 0이면 제거.
    "전체" 탭이면 비적용.
    """
    if is_all_tab:
        return True

    if not user_tpo_list:
        return True

    outfit_tags = outfit.get("designed_tpo", [])
    if not outfit_tags:
        return True  # TPO 정보 없으면 통과

    expanded = _expand_tpos(user_tpo_list)
    match_count = sum(1 for tag in outfit_tags if tag in expanded)
    return match_count > 0


def h5_brand(outfit: dict) -> bool:
    """
    H5 브랜드 화이트리스트 필터.
    코디 내 아이템 중 1개 이상이 화이트리스트 브랜드면 통과.
    """
    whitelist = _load_brand_whitelist()
    for item in outfit.get("items", []):
        brand = (item.get("brand") or "").strip().lower()
        if brand in whitelist:
            return True
    return False


def h6_llm_quality(outfit: dict) -> bool:
    """
    H6 LLM 품질 필터.
    llm_quality_score < 3 이면 제거.
    점수 없으면 통과 (아직 평가 안 됨).
    """
    score = outfit.get("llm_quality_score")
    if score is None:
        return True
    return score >= 3.0


def h7_tone(outfit: dict, user_tone_id: str) -> bool:
    """
    H7 톤 호환성 필터 (P1 우선 원칙).
    사용자 톤 + 호환 톤(같은 시즌) 집합에 매칭되는 아이템이 0개이면 제거.
    """
    user_season = _TONE_TO_SEASON.get(user_tone_id)
    if not user_season:
        return True  # 알 수 없는 톤 → 통과

    compatible_tones = _SEASON_GROUPS.get(user_season, set())
    compatible_tones = compatible_tones | {user_tone_id}

    for item in outfit.get("items", []):
        item_tone = item.get("tone_id")
        if item_tone and item_tone in compatible_tones:
            return True

    # 톤 정보가 아예 없는 아이템만 있으면 통과
    has_any_tone = any(item.get("tone_id") for item in outfit.get("items", []))
    if not has_any_tone:
        return True

    return False


def h8_style_filter(outfit: dict) -> bool:
    """
    H8 StyleFilter 컷오프 필터.
    SF 3축 가중합 55점 미만 제거.
    """
    result = filter_outfit(outfit.get("items", []))
    return result["pass"]


# ═══════════════════════════════════════════════════════════════════════════════
# Hard Filter 체인
# ═══════════════════════════════════════════════════════════════════════════════


def apply_hard_filters(
    outfits: list[dict],
    user_gender: str,
    budget_max: float,
    user_tpo_list: list[str],
    user_tone_id: str,
    current_month: int | None = None,
    is_all_tab: bool = False,
) -> list[dict]:
    """
    Hard Filter 8단계를 순차 적용하여 부적합한 코디를 제거한다.

    적용 순서 (비용 낮은 순):
      H1 → H2 → H3 → H4 → H5 → H7 → H8 → H6

    Args:
        outfits: 후보 코디 리스트
        user_gender: 사용자 성별 ("female" / "male")
        budget_max: 사용자 예산 상한
        user_tpo_list: 사용자 TPO 리스트
        user_tone_id: 사용자 퍼스널컬러 tone_id
        current_month: 현재 월 (테스트용, None이면 자동)
        is_all_tab: "전체" 탭 여부 (True면 H4 비적용)

    Returns:
        Hard Filter를 통과한 코디 리스트
    """
    result = []
    for outfit in outfits:
        if not h1_gender(outfit, user_gender):
            continue
        if not h2_budget(outfit, budget_max):
            continue
        if not h3_season(outfit, current_month):
            continue
        if not h4_tpo(outfit, user_tpo_list, is_all_tab):
            continue
        if not h5_brand(outfit):
            continue
        if not h7_tone(outfit, user_tone_id):
            continue
        if not h8_style_filter(outfit):
            continue
        if not h6_llm_quality(outfit):
            continue
        result.append(outfit)
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Soft Score (5축 가중합) — 기획서 §6.1 4단계
# ═══════════════════════════════════════════════════════════════════════════════

# 기본 가중치 (기획서 §5.5)
DEFAULT_WEIGHTS: dict[str, float] = {
    "pcf": 0.25,
    "of":  0.20,
    "ch":  0.15,
    "pe":  0.15,
    "sf":  0.25,
}


def compute_soft_scores(
    outfit: dict,
    user_tone_id: str,
    user_tpo_list: list[str],
    budget_min: float,
    budget_max: float,
    weight_overrides: dict[str, float] | None = None,
) -> dict:
    """
    5축 Soft Score를 계산하여 outfit에 scores 필드를 추가한다.

    Args:
        outfit: 코디 dict (items 포함)
        user_tone_id: 사용자 퍼스널컬러 tone_id
        user_tpo_list: 사용자 TPO 리스트
        budget_min: 사용자 최소 예산
        budget_max: 사용자 최대 예산
        weight_overrides: 개인화 가중치 오버라이드 (합=1.0)

    Returns:
        scores dict: {pcf, of, ch, pe, sf, total}
    """
    items = outfit.get("items", [])
    cached = outfit.get("scores") or {}

    # PCF — 사용자 톤에 따라 달라지므로 항상 런타임 계산
    tone_ids = [item.get("tone_id") for item in items]
    hex_colors = [item.get("color_hex") for item in items]
    pcf = calculate_pcf(tone_ids, hex_colors, user_tone_id)

    # OF — 사용자 TPO에 따라 달라지므로 항상 런타임 계산
    outfit_tags = outfit.get("designed_tpo", [])
    of = calculate_of(outfit_tags, user_tpo_list)

    # CH — 사용자 무관, 프리컴퓨팅 캐시 우선 사용
    if "ch" in cached:
        ch = float(cached["ch"])
    else:
        valid_hex = [item.get("color_hex") for item in items if item.get("color_hex")]
        ch = calculate_ch(valid_hex)

    # PE — 사용자 예산에 따라 달라지므로 항상 런타임 계산
    total_price = outfit.get("total_price", 0)
    pe = calculate_pe(total_price, budget_min, budget_max)

    # SF — 사용자 무관, 프리컴퓨팅 캐시 우선 사용
    if "sf" in cached:
        sf = float(cached["sf"])
    else:
        sf = calculate_sf(items)

    # 가중합
    w = dict(DEFAULT_WEIGHTS)
    if weight_overrides:
        w.update(weight_overrides)
        # 합이 1.0이 되도록 정규화
        w_sum = sum(w.values())
        if w_sum > 0:
            w = {k: v / w_sum for k, v in w.items()}

    total = (
        pcf * w["pcf"]
        + of * w["of"]
        + ch * w["ch"]
        + pe * w["pe"]
        + sf * w["sf"]
    )

    return {
        "pcf": pcf,
        "of": of,
        "ch": ch,
        "pe": pe,
        "sf": sf,
        "total": total,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Re-ranking — 기획서 §6.1 5단계
# ═══════════════════════════════════════════════════════════════════════════════

def _is_complete_outfit(outfit: dict) -> bool:
    """상하의+아우터 포함 여부 → 완성 코디."""
    categories = {item.get("category", "") for item in outfit.get("items", [])}
    majors = set()
    top_cats = {"blouse", "shirt", "knit", "tshirt", "hoodie", "sweatshirt",
                "croptop", "cardigan", "turtleneck"}
    bottom_cats = {"slacks", "jeans", "wide_pants", "skirt", "mini_skirt",
                   "shorts", "jogger", "leggings", "chino"}
    outer_cats = {"blazer", "trench", "coat", "padding", "jacket", "jumper",
                  "suit_jacket"}
    for cat in categories:
        if cat in top_cats:
            majors.add("top")
        elif cat in bottom_cats:
            majors.add("bottom")
        elif cat in outer_cats:
            majors.add("outer")
    return {"top", "bottom", "outer"}.issubset(majors)


def _get_dominant_tone(outfit: dict) -> str | None:
    """코디의 지배적 톤(최다 톤) 반환."""
    tones = [item.get("tone_id") for item in outfit.get("items", []) if item.get("tone_id")]
    if not tones:
        return None
    counter = Counter(tones)
    return counter.most_common(1)[0][0]


def _get_main_item_id(outfit: dict) -> str | None:
    """코디의 메인 아이템(상의 or 원피스) product_id 반환."""
    top_cats = {"blouse", "shirt", "knit", "tshirt", "hoodie", "sweatshirt",
                "croptop", "cardigan", "turtleneck"}
    onepiece_cats = {"dress", "jumpsuit"}
    for item in outfit.get("items", []):
        cat = item.get("category", "")
        if cat in onepiece_cats or cat in top_cats:
            return item.get("product_id")
    return None


def _personalization_bonus(
    outfit: dict,
    preferred_tones: list[str] | None = None,
    preferred_categories: list[str] | None = None,
    preferred_brands: list[str] | None = None,
) -> float:
    """
    개인화 보정 점수 (-10 ~ +10).
    선호 톤/카테고리/브랜드 일치 여부에 따라 가감.
    """
    bonus = 0.0
    items = outfit.get("items", [])

    if preferred_tones:
        tone_matches = sum(
            1 for item in items
            if item.get("tone_id") in preferred_tones
        )
        bonus += min(4.0, tone_matches * 2.0)

    if preferred_categories:
        cat_matches = sum(
            1 for item in items
            if item.get("category") in preferred_categories
        )
        bonus += min(3.0, cat_matches * 1.5)

    if preferred_brands:
        brand_set = {b.lower() for b in preferred_brands}
        brand_matches = sum(
            1 for item in items
            if (item.get("brand") or "").lower() in brand_set
        )
        bonus += min(3.0, brand_matches * 1.5)

    return max(-10.0, min(10.0, bonus))


def rerank(
    scored_outfits: list[dict],
    disliked_ids: set[str] | None = None,
    preferred_tones: list[str] | None = None,
    preferred_categories: list[str] | None = None,
    preferred_brands: list[str] | None = None,
    max_results: int = 200,
) -> list[dict]:
    """
    리랭킹을 적용한다 (기획서 §6.1 5단계).

    1. 완성 코디 가산 (+3점)
    2. dislike 제외
    3. 톤 다양성 (동일 톤 3개 제한)
    4. 메인아이템 중복 제거 (1개 제한)
    5. 개인화 보정 (-10 ~ +10)
    6. 상위 max_results개 반환

    Args:
        scored_outfits: scores.total이 이미 계산된 코디 리스트
        disliked_ids: 사용자가 싫어요한 outfit_id 집합
        preferred_tones: 선호 톤 리스트 (피드백 학습)
        preferred_categories: 선호 카테고리 리스트
        preferred_brands: 선호 브랜드 리스트
        max_results: 최대 반환 수

    Returns:
        리랭킹된 코디 리스트 (상위 max_results개)
    """
    if disliked_ids is None:
        disliked_ids = set()

    candidates = []
    for outfit in scored_outfits:
        # 2. dislike 제외
        if outfit.get("outfit_id") in disliked_ids:
            continue

        total = outfit.get("scores", {}).get("total", 0.0)

        # 1. 완성 코디 가산 (+3점)
        if _is_complete_outfit(outfit):
            total += 3.0

        # 5. 개인화 보정
        p_bonus = _personalization_bonus(
            outfit, preferred_tones, preferred_categories, preferred_brands,
        )
        total += p_bonus

        candidates.append((total, outfit))

    # 점수 내림차순 정렬
    candidates.sort(key=lambda x: x[0], reverse=True)

    # 3. 톤 다양성 (동일 톤 3개 제한)
    # 4. 메인아이템 중복 제거 (1개 제한)
    result = []
    tone_counts: Counter = Counter()
    seen_main_items: set[str] = set()

    for total, outfit in candidates:
        # 톤 다양성
        dominant_tone = _get_dominant_tone(outfit)
        if dominant_tone and tone_counts[dominant_tone] >= 3:
            continue
        if dominant_tone:
            tone_counts[dominant_tone] += 1

        # 메인아이템 중복 제거
        main_id = _get_main_item_id(outfit)
        if main_id and main_id in seen_main_items:
            continue
        if main_id:
            seen_main_items.add(main_id)

        # 최종 점수 업데이트
        if "scores" not in outfit:
            outfit["scores"] = {}
        outfit["scores"]["total_reranked"] = total

        result.append(outfit)

        if len(result) >= max_results:
            break

    return result
