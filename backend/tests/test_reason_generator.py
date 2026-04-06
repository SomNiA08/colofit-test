"""
Task 2.10 — 추천 이유 생성 테스트.

실행: cd backend && venv/Scripts/activate && pytest tests/test_reason_generator.py -v
"""

import pytest

from app.services.reason_generator import (
    generate_reasons,
    TONE_NAMES,
    _resolve_tpo_name,
)


# ── 기본 동작 ────────────────────────────────────────────────────────────────

class TestGenerateReasons:
    def test_returns_two_reasons(self):
        scores = {"pcf": 95, "of": 80, "ch": 70, "pe": 60, "sf": 85}
        reasons = generate_reasons(scores)
        assert len(reasons) == 2

    def test_all_strings(self):
        scores = {"pcf": 90, "of": 80, "ch": 70, "pe": 60, "sf": 85}
        reasons = generate_reasons(scores)
        for r in reasons:
            assert isinstance(r, str)
            assert len(r) > 0

    # ── PCF 최고 기여 ────────────────────────────────────────────────────────

    def test_pcf_high_contribution_selected(self):
        # PCF 100 × 0.25 = 25 (최고), SF 100 × 0.25 = 25 (공동), OF 0 × 0.20 = 0
        scores = {"pcf": 100, "of": 0, "ch": 0, "pe": 0, "sf": 0}
        reasons = generate_reasons(
            scores, user_tone_id="spring_warm_light",
        )
        assert "봄웜라이트" in reasons[0]
        assert "피부톤" in reasons[0]

    def test_pcf_mid_template(self):
        # PCF 50 → mid 템플릿
        scores = {"pcf": 50, "of": 0, "ch": 0, "pe": 0, "sf": 0}
        reasons = generate_reasons(scores)
        assert "퍼스널컬러" in reasons[0]

    # ── OF 최고 기여 ─────────────────────────────────────────────────────────

    def test_of_high_contribution_selected(self):
        scores = {"pcf": 0, "of": 100, "ch": 0, "pe": 0, "sf": 0}
        reasons = generate_reasons(
            scores, user_tpo_list=["office"],
        )
        assert "출근" in reasons[0]
        assert "적합한" in reasons[0]

    def test_of_mid_template(self):
        scores = {"pcf": 0, "of": 50, "ch": 0, "pe": 0, "sf": 0}
        reasons = generate_reasons(scores)
        assert "다양한 상황" in reasons[0]

    # ── SF 최고 기여 ─────────────────────────────────────────────────────────

    def test_sf_high_contribution(self):
        scores = {"pcf": 0, "of": 0, "ch": 0, "pe": 0, "sf": 100}
        reasons = generate_reasons(scores)
        assert "스타일 조화" in reasons[0]

    # ── CH 기여 ──────────────────────────────────────────────────────────────

    def test_ch_high_template(self):
        scores = {"pcf": 0, "of": 0, "ch": 100, "pe": 0, "sf": 0}
        reasons = generate_reasons(scores)
        assert "컬러" in reasons[0]

    # ── PE 기여 ──────────────────────────────────────────────────────────────

    def test_pe_high_template(self):
        scores = {"pcf": 0, "of": 0, "ch": 0, "pe": 100, "sf": 0}
        reasons = generate_reasons(scores)
        assert "가성비" in reasons[0] or "예산" in reasons[0]

    # ── 동점 처리 ────────────────────────────────────────────────────────────

    def test_tie_returns_two_reasons(self):
        # PCF와 SF 가중치가 같고 점수도 같으면 둘 다 선택
        scores = {"pcf": 80, "of": 80, "ch": 80, "pe": 80, "sf": 80}
        reasons = generate_reasons(scores)
        assert len(reasons) == 2

    def test_all_zero_still_returns_two(self):
        scores = {"pcf": 0, "of": 0, "ch": 0, "pe": 0, "sf": 0}
        reasons = generate_reasons(scores)
        assert len(reasons) == 2

    # ── 톤 이름 매핑 ────────────────────────────────────────────────────────

    def test_tone_name_substitution(self):
        scores = {"pcf": 90, "of": 0, "ch": 0, "pe": 0, "sf": 0}
        reasons = generate_reasons(
            scores, user_tone_id="summer_cool_soft",
        )
        assert "여름쿨소프트" in reasons[0]

    def test_unknown_tone_fallback(self):
        scores = {"pcf": 90, "of": 0, "ch": 0, "pe": 0, "sf": 0}
        reasons = generate_reasons(
            scores, user_tone_id="unknown_tone",
        )
        assert "내 퍼스널컬러" in reasons[0]

    def test_all_12_tones_mapped(self):
        assert len(TONE_NAMES) == 12
        expected_tones = [
            "spring_warm_light", "spring_warm_bright", "spring_warm_mute",
            "summer_cool_light", "summer_cool_soft", "summer_cool_mute",
            "autumn_warm_bright", "autumn_warm_mute", "autumn_warm_deep",
            "winter_cool_bright", "winter_cool_deep", "winter_cool_light",
        ]
        for tone in expected_tones:
            assert tone in TONE_NAMES

    # ── TPO 이름 매핑 ───────────────────────────────────────────────────────

    def test_tpo_name_substitution(self):
        scores = {"pcf": 0, "of": 90, "ch": 0, "pe": 0, "sf": 0}
        reasons = generate_reasons(
            scores, user_tpo_list=["date"],
        )
        assert "데이트" in reasons[0]

    def test_empty_tpo_fallback(self):
        scores = {"pcf": 0, "of": 90, "ch": 0, "pe": 0, "sf": 0}
        reasons = generate_reasons(scores, user_tpo_list=[])
        assert "데일리" in reasons[0]

    # ── 가중치 오버라이드 ───────────────────────────────────────────────────

    def test_weight_override_changes_top_axes(self):
        # PE 가중치를 0.50으로 높이면 PE가 최고 기여
        scores = {"pcf": 80, "of": 80, "ch": 80, "pe": 80, "sf": 80}
        reasons = generate_reasons(
            scores,
            weight_overrides={"pe": 0.50, "pcf": 0.10, "of": 0.10, "ch": 0.10, "sf": 0.20},
        )
        # PE가 1위여야 함
        assert "예산" in reasons[0] or "가성비" in reasons[0]

    # ── 75점 분기 경계 ──────────────────────────────────────────────────────

    def test_exactly_75_is_high(self):
        scores = {"pcf": 75, "of": 0, "ch": 0, "pe": 0, "sf": 0}
        reasons = generate_reasons(
            scores, user_tone_id="autumn_warm_deep",
        )
        assert "가을웜딥" in reasons[0]
        assert "피부톤" in reasons[0]

    def test_74_is_mid(self):
        scores = {"pcf": 74, "of": 0, "ch": 0, "pe": 0, "sf": 0}
        reasons = generate_reasons(scores)
        assert "퍼스널컬러" in reasons[0]


# ── _resolve_tpo_name ────────────────────────────────────────────────────────

class TestResolveTpoName:
    def test_office(self):
        assert _resolve_tpo_name(["office"]) == "출근"

    def test_date(self):
        assert _resolve_tpo_name(["date"]) == "데이트"

    def test_empty_returns_daily(self):
        assert _resolve_tpo_name([]) == "데일리"

    def test_none_returns_daily(self):
        assert _resolve_tpo_name(None) == "데일리"

    def test_unknown_tpo_returns_raw(self):
        assert _resolve_tpo_name(["picnic"]) == "picnic"
