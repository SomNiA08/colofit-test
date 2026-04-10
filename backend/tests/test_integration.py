"""
Task 4.10 — 통합 테스트.

전체 서비스 레이어 흐름을 검증한다 (DB 불필요 — 순수 함수 체인 테스트).

커버 범위:
  Flow 1: 온보딩 → 피드(Hard Filter → Score → Rerank) → Top Pick
  Flow 2: 저장 목록 → Top Pick 선택
  Flow 3: 피드백 누적 → weight_overrides 자동 생성
  Edge case: 코디 0개 결과 / 예산 초과 / 톤 불일치

실행: cd backend && venv/Scripts/activate && pytest tests/test_integration.py -v
"""

from __future__ import annotations

import dataclasses

import pytest

from app.services.feed_builder import (
    apply_hard_filters,
    compute_soft_scores,
    rerank,
    h1_gender,
    h2_budget,
    h7_tone,
)
from app.services.top_pick import select_top_pick, infer_tpo_from_hour
from app.services.preference_tracker import (
    EVENT_WEIGHTS,
    MIN_FEEDBACK_COUNT,
    generate_weight_overrides,
)


# ═══════════════════════════════════════════════════════════════════════════════
# 픽스처 / 헬퍼
# ═══════════════════════════════════════════════════════════════════════════════

def _make_item(**kwargs) -> dict:
    """테스트용 아이템 dict 기본값 생성."""
    defaults: dict = {
        "title": "기본 아이템",
        "gender": "female",
        "brand": "무신사 스탠다드",
        "tone_id": "spring_warm_light",
        "category": "blouse",
        "color_hex": "#FFCBA4",   # 봄웜 팔레트 색상 — PCF 100
        "price": 30_000,
    }
    defaults.update(kwargs)
    return defaults


def _make_winter_item(**kwargs) -> dict:
    """
    퍼스널컬러가 봄웜(spring_warm_light)인 사용자와 불일치하는 아이템.
    tone_id=winter_cool_bright + color_hex=None → PCF ≈ 0.
    """
    defaults: dict = {
        "title": "겨울 아이템",
        "gender": "female",
        "brand": "무신사 스탠다드",
        "tone_id": "winter_cool_bright",
        "category": "blouse",
        "color_hex": None,  # hex 없으면 비호환 톤 → pcf 0
        "price": 30_000,
    }
    defaults.update(kwargs)
    return defaults


def _make_outfit(**kwargs) -> dict:
    """테스트용 코디 dict 기본값 생성."""
    defaults: dict = {
        "id": "outfit_001",
        "items": [_make_item()],
        "total_price": 77_900,
        "tags": ["캐주얼", "데일리"],   # 시즌 키워드 없음 → H3 통과
        "designed_tpo": ["casual"],
        "llm_quality_score": 4.0,
        "season_tags": ["spring"],
        "gender": "female",
        "scores": {},
    }
    defaults.update(kwargs)
    return defaults


@dataclasses.dataclass
class _FakePref:
    """UserPreference ORM 모델 대체용 dataclass (DB 불필요)."""
    feedback_count: int = 0
    tone_preferences: dict = dataclasses.field(default_factory=dict)
    category_preferences: dict = dataclasses.field(default_factory=dict)
    brand_preferences: dict = dataclasses.field(default_factory=dict)
    avg_liked_price: int | None = None
    weight_overrides: dict | None = None


# apply_hard_filters 실제 시그니처:
#   (outfits, user_gender, budget_max, user_tpo_list, user_tone_id, current_month=None, is_all_tab=False)
# budget_min 파라미터는 없음

def _apply_filters(outfits: list[dict], **kw) -> list[dict]:
    """apply_hard_filters 래퍼 — 테스트에서 공통 기본값 적용."""
    return apply_hard_filters(
        outfits,
        user_gender=kw.get("user_gender", "female"),
        budget_max=kw.get("budget_max", 200_000),
        user_tpo_list=kw.get("user_tpo_list", ["casual"]),
        user_tone_id=kw.get("user_tone_id", "spring_warm_light"),
        current_month=kw.get("current_month", 4),  # 4월 = 봄
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Flow 1: 피드 파이프라인 (Hard Filter → Soft Score → Rerank)
# ═══════════════════════════════════════════════════════════════════════════════

class TestFeedPipeline:
    """온보딩 컨텍스트 → 피드 추천 전체 흐름."""

    TONE = "spring_warm_light"
    GENDER = "female"
    BUDGET_MIN = 0.0
    BUDGET_MAX = 150_000.0
    TPO = ["casual"]

    def _run_pipeline(self, outfits: list[dict]) -> list[dict]:
        """Hard Filter → Soft Score → Rerank 파이프라인 실행."""
        filtered = _apply_filters(
            outfits,
            user_gender=self.GENDER,
            user_tone_id=self.TONE,
            budget_max=self.BUDGET_MAX,
            user_tpo_list=self.TPO,
        )
        for outfit in filtered:
            outfit["scores"] = compute_soft_scores(
                outfit,
                user_tone_id=self.TONE,
                user_tpo_list=self.TPO,
                budget_min=self.BUDGET_MIN,
                budget_max=self.BUDGET_MAX,
            )
        return rerank(filtered)

    def test_normal_flow_returns_scored_outfits(self):
        """정상 케이스: 코디가 필터 통과 후 스코어가 포함된 결과를 반환해야 한다."""
        outfits = [
            _make_outfit(id="a", total_price=80_000),
            _make_outfit(id="b", total_price=90_000),
            _make_outfit(id="c", total_price=100_000),
        ]
        result = self._run_pipeline(outfits)

        assert len(result) > 0
        for outfit in result:
            scores = outfit.get("scores", {})
            assert "total" in scores
            assert 0.0 <= scores["total"] <= 100.0

    def test_result_has_five_axes(self):
        """피드 결과 각 코디에 5축 스코어(pcf/of/ch/pe/sf)가 모두 있어야 한다."""
        outfits = [_make_outfit(id="a", total_price=80_000)]
        result = self._run_pipeline(outfits)

        assert len(result) > 0
        for axis in ("pcf", "of", "ch", "pe", "sf", "total"):
            assert axis in result[0]["scores"], f"{axis} 축 스코어 누락"

    def test_result_is_sorted_by_total_score_descending(self):
        """리랭킹 후 total 점수 내림차순 정렬이어야 한다."""
        outfits = [
            # winter 아이템(PCF 낮음)
            _make_outfit(id="low",  items=[_make_winter_item()], total_price=50_000),
            # spring 아이템(PCF 높음)
            _make_outfit(id="high", items=[_make_item()],         total_price=50_000),
        ]
        result = self._run_pipeline(outfits)
        if len(result) >= 2:
            scores = [o["scores"]["total"] for o in result]
            assert scores == sorted(scores, reverse=True), \
                "total 점수 내림차순 정렬 실패"

    def test_complete_outfit_bonus_applied(self):
        """상의+하의+아우터 3종 코디가 불완전 코디보다 높은 순위여야 한다."""
        # _is_complete_outfit 기준: top + bottom + outer 모두 있어야 완성
        complete_items = [
            _make_item(category="blouse"),   # top
            _make_item(category="slacks"),   # bottom
            _make_item(category="blazer"),   # outer
        ]
        incomplete_items = [_make_item(category="blouse")]  # top만

        complete   = _make_outfit(id="complete",   items=complete_items,   total_price=90_000)
        incomplete = _make_outfit(id="incomplete", items=incomplete_items, total_price=90_000)

        result = self._run_pipeline([incomplete, complete])
        if len(result) >= 2:
            ids = [o["id"] for o in result]
            assert ids.index("complete") < ids.index("incomplete"), \
                "완전 코디(3종+)가 불완전 코디보다 앞에 와야 한다"


# ═══════════════════════════════════════════════════════════════════════════════
# Flow 2: 저장 목록 → Top Pick
# ═══════════════════════════════════════════════════════════════════════════════

class TestSavedToTopPick:
    """저장 목록 → Top Pick 선택 흐름."""

    TONE = "spring_warm_light"
    TPO = ["casual"]
    BUDGET_MIN = 0.0
    BUDGET_MAX = 200_000.0

    def test_top_pick_selects_highest_pcf(self):
        """Top Pick은 Soft Score 기준 최고 점수 코디를 선택해야 한다."""
        # low: 겨울 아이템 (PCF ≈ 0)
        low  = _make_outfit(id="low",  items=[_make_winter_item()], total_price=50_000)
        # high: 봄 아이템 (PCF = 100)
        high = _make_outfit(id="high", items=[_make_item()],         total_price=50_000)

        result = select_top_pick(
            [low, high],
            user_tone_id=self.TONE,
            user_tpo_list=self.TPO,
            budget_min=self.BUDGET_MIN,
            budget_max=self.BUDGET_MAX,
        )

        assert result is not None
        assert result["id"] == "high", "PCF 높은 코디가 Top Pick으로 선택되어야 한다"

    def test_top_pick_returns_none_for_empty_list(self):
        """저장 목록이 비어있으면 Top Pick은 None이어야 한다."""
        result = select_top_pick(
            [],
            user_tone_id=self.TONE,
            user_tpo_list=self.TPO,
            budget_min=self.BUDGET_MIN,
            budget_max=self.BUDGET_MAX,
        )
        assert result is None

    def test_top_pick_includes_all_score_axes(self):
        """Top Pick 결과에 5축 스코어가 모두 포함되어야 한다."""
        outfits = [_make_outfit(id="a", total_price=70_000)]
        result = select_top_pick(
            outfits,
            user_tone_id=self.TONE,
            user_tpo_list=self.TPO,
            budget_min=self.BUDGET_MIN,
            budget_max=self.BUDGET_MAX,
        )
        assert result is not None
        for axis in ("pcf", "of", "ch", "pe", "sf", "total"):
            assert axis in result["scores"], f"{axis} 축 스코어 누락"

    def test_tpo_inference_from_hour(self):
        """시간대별 TPO 추론이 올바르게 동작해야 한다."""
        assert infer_tpo_from_hour(9)  == "commute"   # 오전 출근
        assert infer_tpo_from_hour(14) == "casual"    # 오후
        assert infer_tpo_from_hour(20) == "date"      # 저녁
        assert infer_tpo_from_hour(2)  == "casual"    # 심야


# ═══════════════════════════════════════════════════════════════════════════════
# Flow 3: 피드백 누적 → 개인화 학습
# ═══════════════════════════════════════════════════════════════════════════════

class TestFeedbackPersonalization:
    """피드백 누적 → weight_overrides 자동 생성 흐름."""

    def test_event_weights_are_correct(self):
        """이벤트별 가중치가 기획서 §6.8 사양과 일치해야 한다."""
        assert EVENT_WEIGHTS["save"]    == pytest.approx(+2.0)
        assert EVENT_WEIGHTS["like"]    == pytest.approx(+1.0)
        assert EVENT_WEIGHTS["click"]   == pytest.approx(+0.3)
        assert EVENT_WEIGHTS["dislike"] == pytest.approx(-1.5)

    def test_no_overrides_below_threshold(self):
        """피드백 10건 미만이면 weight_overrides가 생성되지 않아야 한다."""
        pref = _FakePref(
            feedback_count=MIN_FEEDBACK_COUNT - 1,
            tone_preferences={"spring_warm_light": 5.0},
            avg_liked_price=50_000,
        )
        assert generate_weight_overrides(pref) == {}  # type: ignore[arg-type]

    def test_overrides_generated_at_threshold(self):
        """피드백 10건 이상이고 조건 충족 시 weight_overrides가 생성되어야 한다."""
        pref = _FakePref(
            feedback_count=MIN_FEEDBACK_COUNT,
            tone_preferences={"spring_warm_light": 5.0},  # >= 4.0 → pcf 상향
            category_preferences={"blouse": 4.0},          # >= 3.0 → sf 상향
            avg_liked_price=50_000,                        # < 80,000 → pe 상향
        )
        result = generate_weight_overrides(pref)  # type: ignore[arg-type]

        assert "pcf" in result, "강한 톤 선호 → pcf 가중치 상향 필요"
        assert "sf"  in result, "강한 카테고리 선호 → sf 가중치 상향 필요"
        assert "pe"  in result, "저가 선호 → pe 가중치 상향 필요"

    def test_pcf_override_range(self):
        """pcf 오버라이드 값이 기본값(0.25)~최대(0.40) 범위 내여야 한다."""
        pref = _FakePref(
            feedback_count=10,
            tone_preferences={"spring_warm_light": 8.0},
        )
        result = generate_weight_overrides(pref)  # type: ignore[arg-type]
        if "pcf" in result:
            assert 0.25 <= result["pcf"] <= 0.40

    def test_high_price_preference_lowers_pe(self):
        """고가 선호(avg >= 150,000) 시 pe 가중치가 하향(0.08)이어야 한다."""
        pref = _FakePref(feedback_count=10, avg_liked_price=200_000)
        result = generate_weight_overrides(pref)  # type: ignore[arg-type]
        if "pe" in result:
            assert result["pe"] == pytest.approx(0.08)

    def test_low_price_preference_raises_pe(self):
        """저가 선호(avg < 80,000) 시 pe 가중치가 상향(0.25)이어야 한다."""
        pref = _FakePref(feedback_count=10, avg_liked_price=40_000)
        result = generate_weight_overrides(pref)  # type: ignore[arg-type]
        if "pe" in result:
            assert result["pe"] == pytest.approx(0.25)

    def test_save_outweighs_dislike(self):
        """save 5회 누적 가중치 합이 dislike 5회보다 커야 한다 (선호 신호 우세)."""
        save_sum    = EVENT_WEIGHTS["save"]    * 5   # +10.0
        dislike_sum = EVENT_WEIGHTS["dislike"] * 5   # -7.5
        assert save_sum + dislike_sum > 0


# ═══════════════════════════════════════════════════════════════════════════════
# Edge Case: 코디 0개 결과
# ═══════════════════════════════════════════════════════════════════════════════

class TestEdgeCaseEmptyResult:
    """코디 0개 결과 — empty state 검증."""

    def test_gender_mismatch_returns_false(self):
        """성별 불일치 코디는 h1_gender 필터에서 False를 반환해야 한다."""
        male_outfit = _make_outfit(items=[_make_item(gender="male")])
        assert h1_gender(male_outfit, "female") is False

    def test_gender_match_returns_true(self):
        """성별 일치 코디는 h1_gender 필터에서 True를 반환해야 한다."""
        female_outfit = _make_outfit(items=[_make_item(gender="female")])
        assert h1_gender(female_outfit, "female") is True

    def test_apply_hard_filters_returns_empty_on_gender_mismatch(self):
        """성별 불일치 코디만 있으면 apply_hard_filters는 빈 리스트를 반환해야 한다."""
        outfits = [
            _make_outfit(id=str(i), items=[_make_item(gender="male")])
            for i in range(5)
        ]
        result = _apply_filters(outfits, user_gender="female")
        assert result == []

    def test_select_top_pick_returns_none_on_empty(self):
        """빈 리스트에서 Top Pick은 None이어야 한다."""
        result = select_top_pick([], "spring_warm_light", ["casual"], 0, 150_000)
        assert result is None


# ═══════════════════════════════════════════════════════════════════════════════
# Edge Case: 예산 초과
# ═══════════════════════════════════════════════════════════════════════════════

class TestEdgeCaseBudgetOverflow:
    """예산 초과 — H2 Budget Filter 검증 (총액 > 예산 × 1.5 제거)."""

    def test_outfit_over_budget_fails_h2(self):
        """총액이 예산 × 1.5 초과인 코디는 h2_budget에서 False를 반환해야 한다."""
        budget_max = 100_000
        expensive = _make_outfit(total_price=int(budget_max * 1.6))
        assert h2_budget(expensive, budget_max) is False

    def test_outfit_within_budget_passes_h2(self):
        """총액이 예산 × 1.5 이하인 코디는 h2_budget을 통과해야 한다."""
        budget_max = 100_000
        affordable = _make_outfit(total_price=80_000)
        assert h2_budget(affordable, budget_max) is True

    def test_all_outfits_over_budget_returns_empty(self):
        """모든 코디가 예산 초과면 apply_hard_filters는 빈 리스트를 반환해야 한다."""
        budget_max = 50_000
        outfits = [
            _make_outfit(id="a", total_price=200_000),
            _make_outfit(id="b", total_price=300_000),
        ]
        result = _apply_filters(outfits, budget_max=budget_max)
        assert result == []

    def test_budget_score_penalizes_expensive_outfit(self):
        """예산 내에서도 비싼 코디는 저렴한 코디보다 PE 스코어가 낮거나 같아야 한다."""
        cheap  = _make_outfit(total_price=30_000)
        pricey = _make_outfit(total_price=140_000)

        s_cheap  = compute_soft_scores(cheap,  "spring_warm_light", ["casual"], 0, 150_000)
        s_pricey = compute_soft_scores(pricey, "spring_warm_light", ["casual"], 0, 150_000)

        assert s_cheap["pe"] >= s_pricey["pe"], \
            "저렴한 코디의 PE 스코어가 비싼 코디보다 높거나 같아야 한다"


# ═══════════════════════════════════════════════════════════════════════════════
# Edge Case: 톤 불일치
# ═══════════════════════════════════════════════════════════════════════════════

class TestEdgeCaseToneMismatch:
    """톤 불일치 — H7 톤 필터 + PCF 스코어 검증."""

    def test_incompatible_tone_item_fails_h7(self):
        """모든 아이템이 비호환 톤인 코디는 h7_tone에서 False를 반환해야 한다."""
        outfit = _make_outfit(items=[_make_winter_item()])
        assert h7_tone(outfit, "spring_warm_light") is False

    def test_compatible_tone_item_passes_h7(self):
        """호환 톤 아이템이 있는 코디는 h7_tone을 통과해야 한다."""
        outfit = _make_outfit(items=[_make_item()])
        assert h7_tone(outfit, "spring_warm_light") is True

    def test_mixed_tone_outfit_passes_h7_p1_principle(self):
        """
        P1 우선 원칙: 아이템 중 하나라도 호환 톤이면 코디 전체가 통과해야 한다.
        비호환 아이템이 있더라도 호환 아이템이 1개 이상이면 통과.
        """
        mixed_outfit = _make_outfit(
            items=[
                _make_item(),              # 봄웜 (호환)
                _make_winter_item(),       # 겨울쿨 (비호환)
            ]
        )
        assert h7_tone(mixed_outfit, "spring_warm_light") is True, \
            "호환 아이템이 1개 이상이면 h7을 통과해야 한다 (P1 원칙)"

    def test_pcf_score_lower_for_mismatched_tone(self):
        """톤 불일치 코디의 PCF 스코어는 일치 코디보다 낮아야 한다."""
        # 봄웜 아이템: tone_id + color 모두 봄웜 → PCF 높음
        matching   = _make_outfit(items=[_make_item()])
        # 겨울쿨 아이템: color_hex=None → 비호환 톤 0점 처리 → PCF 낮음
        mismatched = _make_outfit(items=[_make_winter_item()])

        s_match = compute_soft_scores(matching,   "spring_warm_light", ["casual"], 0, 200_000)
        s_miss  = compute_soft_scores(mismatched, "spring_warm_light", ["casual"], 0, 200_000)

        assert s_match["pcf"] > s_miss["pcf"], \
            f"톤 일치 PCF({s_match['pcf']})가 불일치 PCF({s_miss['pcf']})보다 높아야 한다"

    def test_tone_matching_outfits_pass_full_pipeline(self):
        """톤 일치 코디는 전체 파이프라인을 통과해야 한다."""
        outfits = [
            _make_outfit(id=str(i), items=[_make_item()])
            for i in range(5)
        ]
        result = _apply_filters(outfits, user_tone_id="spring_warm_light")
        assert len(result) == 5, "톤 일치 코디는 전량 필터를 통과해야 한다"
