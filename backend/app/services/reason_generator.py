"""
추천 이유 생성기 — 기획서 §6.4.

5축 가중 기여도 상위 2개 축 → high/mid 템플릿 → 자연어 2줄.
"""

from app.services.feed_builder import DEFAULT_WEIGHTS

# ── 톤 한글 이름 매핑 ────────────────────────────────────────────────────────
TONE_NAMES: dict[str, str] = {
    "spring_warm_light":  "봄웜라이트",
    "spring_warm_bright": "봄웜브라이트",
    "spring_warm_mute":   "봄웜뮤트",
    "summer_cool_light":  "여름쿨라이트",
    "summer_cool_soft":   "여름쿨소프트",
    "summer_cool_mute":   "여름쿨뮤트",
    "autumn_warm_bright": "가을웜브라이트",
    "autumn_warm_mute":   "가을웜뮤트",
    "autumn_warm_deep":   "가을웜딥",
    "winter_cool_bright": "겨울쿨브라이트",
    "winter_cool_deep":   "겨울쿨딥",
    "winter_cool_light":  "겨울쿨라이트",
}

# ── 축별 템플릿 (high: 75+, mid: <75) ───────────────────────────────────────
_TEMPLATES: dict[str, dict[str, str]] = {
    "pcf": {
        "high": "{tone_name} 핵심 컬러와 잘 어울려서 피부톤이 한층 밝아 보여요",
        "mid":  "퍼스널컬러와 비교적 잘 어울리는 색상 구성이에요",
    },
    "of": {
        "high": "{tpo_name} 룩에 적합한 스타일링이에요",
        "mid":  "다양한 상황에 무난하게 활용할 수 있는 스타일이에요",
    },
    "ch": {
        "high": "메인-서브-포인트 컬러가 균형 있게 조화를 이뤄요",
        "mid":  "전체적으로 안정감 있는 색상 배합이에요",
    },
    "pe": {
        "high": "예산 범위 내에서 가성비 좋은 조합이에요",
        "mid":  "가격 대비 만족스러운 구성이에요",
    },
    "sf": {
        "high": "스타일 조화가 뛰어난 코디예요",
        "mid":  "전체적으로 무난한 스타일 구성이에요",
    },
}

# ── TPO 한글 이름 매핑 ───────────────────────────────────────────────────────
_TPO_NAMES: dict[str, str] = {
    "office":    "출근",
    "commute":   "출퇴근",
    "interview": "면접",
    "date":      "데이트",
    "weekend":   "주말",
    "casual":    "캐주얼",
    "daily":     "데일리",
    "campus":    "캠퍼스",
    "event":     "행사",
    "party":     "파티",
    "wedding":   "하객",
    "workout":   "운동",
    "travel":    "여행",
}

# 75점 분기 기준 (기획서 §6.4)
_HIGH_THRESHOLD = 75.0


def generate_reasons(
    scores: dict,
    user_tone_id: str | None = None,
    user_tpo_list: list[str] | None = None,
    weight_overrides: dict[str, float] | None = None,
) -> list[str]:
    """
    5축 가중 기여도 상위 2개 축의 추천 이유를 생성한다.

    Args:
        scores: {pcf, of, ch, pe, sf} 점수 dict
        user_tone_id: 사용자 톤 ID (PCF 템플릿 변수)
        user_tpo_list: 사용자 TPO 리스트 (OF 템플릿 변수)
        weight_overrides: 개인화 가중치 오버라이드

    Returns:
        2줄의 추천 이유 문자열 리스트
    """
    w = dict(DEFAULT_WEIGHTS)
    if weight_overrides:
        w.update(weight_overrides)
        w_sum = sum(w.values())
        if w_sum > 0:
            w = {k: v / w_sum for k, v in w.items()}

    # 1. 가중 기여도 계산
    axes = ["pcf", "of", "ch", "pe", "sf"]
    contributions = [
        (axis, scores.get(axis, 0.0) * w.get(axis, 0.0), scores.get(axis, 0.0))
        for axis in axes
    ]

    # 2. 기여도 내림차순 정렬 → 상위 2개
    contributions.sort(key=lambda x: x[1], reverse=True)
    top_2 = contributions[:2]

    # 3. 템플릿 분기 및 렌더링
    reasons: list[str] = []
    for axis, _contribution, raw_score in top_2:
        level = "high" if raw_score >= _HIGH_THRESHOLD else "mid"
        template = _TEMPLATES[axis][level]

        # 변수 치환
        text = template
        if "{tone_name}" in text:
            tone_name = TONE_NAMES.get(user_tone_id or "", "내 퍼스널컬러")
            text = text.replace("{tone_name}", tone_name)
        if "{tpo_name}" in text:
            tpo_name = _resolve_tpo_name(user_tpo_list)
            text = text.replace("{tpo_name}", tpo_name)

        reasons.append(text)

    return reasons


def _resolve_tpo_name(user_tpo_list: list[str] | None) -> str:
    """사용자 TPO 리스트에서 대표 한글 TPO명을 반환한다."""
    if not user_tpo_list:
        return "데일리"
    first = user_tpo_list[0]
    return _TPO_NAMES.get(first, first)
