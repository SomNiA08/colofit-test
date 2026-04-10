"""
A vs B 코디 비교 서비스 (기획서 §4.5).

두 코디의 5축 점수를 비교하여 결정적 차이 요인과 한 줄 결론을 반환한다.
"""

# ── 축 메타 ────────────────────────────────────────────────────────────────────

_AXIS_LABEL: dict[str, str] = {
    "pcf": "퍼스널컬러 적합도",
    "of":  "TPO 적합도",
    "ch":  "색상 조화",
    "pe":  "가격 효율",
    "sf":  "스타일 완성도",
}

# 비교에 사용할 축 순서 (가중치 높은 순)
_AXES: list[str] = ["pcf", "sf", "of", "ch", "pe"]

# 동률 판정 임계값 (두 점수 차이 이 미만이면 해당 축은 무시)
_TIE_THRESHOLD = 3.0


def compare(
    scores_a: dict,
    scores_b: dict,
) -> dict:
    """
    두 코디의 5축 점수를 비교하여 비교 결과를 반환한다.

    Args:
        scores_a: 코디 A의 scores dict {pcf, of, ch, pe, sf, total}
        scores_b: 코디 B의 scores dict {pcf, of, ch, pe, sf, total}

    Returns:
        {
            winner:         "a" | "b" | "tie",
            decisive_axis:  "pcf" | "of" | "ch" | "pe" | "sf" | None,
            score_a:        float (total),
            score_b:        float (total),
            axis_diffs:     {축: diff(a-b), ...},  # 양수면 A가 높음
            conclusion:     str,  # 한 줄 한국어 결론
        }
    """
    total_a = scores_a.get("total", 0.0)
    total_b = scores_b.get("total", 0.0)
    total_diff = total_a - total_b

    # 축별 차이 (A - B, 양수 = A가 높음)
    axis_diffs = {
        axis: scores_a.get(axis, 0.0) - scores_b.get(axis, 0.0)
        for axis in _AXES
    }

    # 결정적 차이 축: 가중치 순서에서 임계값 초과하는 첫 번째 축
    decisive_axis: str | None = None
    for axis in _AXES:
        if abs(axis_diffs[axis]) >= _TIE_THRESHOLD:
            decisive_axis = axis
            break

    # 승자 판정
    if abs(total_diff) < _TIE_THRESHOLD:
        winner = "tie"
    elif total_diff > 0:
        winner = "a"
    else:
        winner = "b"

    # 한 줄 결론
    conclusion = _build_conclusion(winner, decisive_axis, axis_diffs)

    return {
        "winner": winner,
        "decisive_axis": decisive_axis,
        "score_a": round(total_a, 1),
        "score_b": round(total_b, 1),
        "axis_diffs": {k: round(v, 1) for k, v in axis_diffs.items()},
        "conclusion": conclusion,
    }


def _build_conclusion(
    winner: str,
    decisive_axis: str | None,
    axis_diffs: dict[str, float],
) -> str:
    """비교 결과를 한 줄 한국어 문장으로 표현한다."""
    if winner == "tie":
        return "두 코디가 비슷한 점수예요. 취향에 따라 골라보세요!"

    winner_label = "A" if winner == "a" else "B"

    if decisive_axis is None:
        return f"{winner_label}가 전반적으로 더 잘 맞는 코디예요."

    axis_name = _AXIS_LABEL[decisive_axis]
    diff = axis_diffs[decisive_axis]

    if decisive_axis == "pcf":
        return f"{winner_label}가 퍼스널컬러에 더 잘 맞아요. ({axis_name} +{abs(diff):.0f}점)"
    if decisive_axis == "of":
        return f"{winner_label}가 지금 상황(TPO)에 더 어울려요. ({axis_name} +{abs(diff):.0f}점)"
    if decisive_axis == "ch":
        return f"{winner_label}의 색상 조합이 더 세련됐어요. ({axis_name} +{abs(diff):.0f}점)"
    if decisive_axis == "pe":
        return f"{winner_label}가 예산 대비 더 효율적이에요. ({axis_name} +{abs(diff):.0f}점)"
    if decisive_axis == "sf":
        return f"{winner_label}의 스타일 완성도가 더 높아요. ({axis_name} +{abs(diff):.0f}점)"

    return f"{winner_label}가 {axis_name}에서 앞서요."
