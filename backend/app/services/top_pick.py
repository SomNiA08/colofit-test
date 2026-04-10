"""
Top Pick 서비스 (기획서 §4.4).

선택 우선순위:
  1. user_id가 있고 save된 코디가 있으면 → 저장 목록 중 최고 점수 1개
  2. 저장 없음(콜드스타트) → 전체 DB 코디 중 최고 점수 1개

시간대 기반 TPO 자동 추론:
  06~11시 → commute  (출근)
  12~18시 → casual   (오후)
  19~23시 → date     (저녁)
  00~05시 → casual   (심야)
"""

from app.services.feed_builder import compute_soft_scores

# ── 시간대 → TPO 매핑 ────────────────────────────────────────────────────────

_HOUR_TPO: dict[range, str] = {
    range(6, 12):  "commute",
    range(12, 19): "casual",
    range(19, 24): "date",
    range(0, 6):   "casual",
}


def infer_tpo_from_hour(hour: int) -> str:
    """
    현재 시각(0~23)으로 TPO를 추론한다.

    Args:
        hour: 0~23 정수

    Returns:
        "commute" | "casual" | "date"
    """
    for r, tpo in _HOUR_TPO.items():
        if hour in r:
            return tpo
    return "casual"


# ── 최고 점수 코디 선택 ──────────────────────────────────────────────────────

def select_top_pick(
    outfit_dicts: list[dict],
    user_tone_id: str,
    user_tpo_list: list[str],
    budget_min: float,
    budget_max: float,
) -> dict | None:
    """
    주어진 코디 목록에서 Soft Score 기준 최고 점수 코디를 반환한다.

    Args:
        outfit_dicts: Hard Filter를 통과한 코디 dict 목록
        user_tone_id: 사용자 퍼스널컬러 tone_id
        user_tpo_list: 사용자 TPO 리스트
        budget_min: 예산 하한
        budget_max: 예산 상한

    Returns:
        scores가 포함된 최고 점수 코디 dict, 목록이 비면 None.
    """
    if not outfit_dicts:
        return None

    scored: list[dict] = []
    for outfit in outfit_dicts:
        outfit_copy = dict(outfit)
        outfit_copy["scores"] = compute_soft_scores(
            outfit_copy,
            user_tone_id=user_tone_id,
            user_tpo_list=user_tpo_list,
            budget_min=budget_min,
            budget_max=budget_max,
        )
        scored.append(outfit_copy)

    return max(scored, key=lambda o: o["scores"].get("total", 0.0))
