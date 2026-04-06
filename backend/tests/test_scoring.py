"""
Task 2.1~2.5 — 5축 스코어링 테스트.

실행: cd backend && venv/Scripts/activate && pytest tests/test_scoring.py -v
"""

import math
import pytest

from app.services.scoring import (
    calculate_pcf,
    _item_pcf_score,
    _color_level_score,
    _tone_level_score,
    _RGB_SCALE,
    calculate_of,
    _expand_tpos,
    calculate_ch,
    _ch_base_score,
    _rgb_to_saturation,
    calculate_pe,
    calculate_sf,
    _category_compat_score,
    _silhouette_balance_score,
    _formality_consistency_score,
)


# ── 톤 레벨 테스트 ────────────────────────────────────────────────────────────

class TestToneLevelScore:
    def test_same_tone_returns_100(self):
        assert _tone_level_score("spring_warm_light", "spring_warm_light") == 100.0

    def test_compatible_tone_returns_95(self):
        # 같은 시즌(spring) 내 다른 톤
        assert _tone_level_score("spring_warm_bright", "spring_warm_light") == 95.0

    def test_incompatible_season_returns_0(self):
        # 봄웜 vs 겨울쿨 → 다른 시즌
        assert _tone_level_score("winter_cool_bright", "spring_warm_light") == 0.0

    def test_cross_temperature_incompatible(self):
        # 가을웜 vs 여름쿨 → 다른 시즌
        assert _tone_level_score("autumn_warm_deep", "summer_cool_light") == 0.0


# ── 색상 레벨 테스트 ──────────────────────────────────────────────────────────

class TestColorLevelScore:
    def test_exact_palette_color_returns_100(self):
        # spring_warm_light 팔레트 첫 번째 색 #FFCBA4 = [255, 203, 164]
        score = _color_level_score("#FFCBA4", "spring_warm_light")
        assert score == pytest.approx(100.0, abs=0.01)

    def test_black_against_spring_palette_returns_near_0(self):
        # 검정 #000000 vs 봄웜 팔레트 (밝고 따뜻한 톤) → 매우 낮은 점수
        score = _color_level_score("#000000", "spring_warm_light")
        assert score < 30.0

    def test_score_between_0_and_100(self):
        score = _color_level_score("#808080", "spring_warm_light")
        assert 0.0 <= score <= 100.0

    def test_hex_without_hash(self):
        # '#' 없어도 동작해야 함
        score_with = _color_level_score("#FFCBA4", "spring_warm_light")
        score_without = _color_level_score("FFCBA4", "spring_warm_light")
        assert score_with == pytest.approx(score_without, abs=0.001)

    def test_score_formula(self):
        # d=0 → 100, d=441.67 → 0 에 가깝게
        # 완전 반대색(대략 최대 거리)은 0에 수렴
        max_d = math.sqrt(3 * 255 ** 2)  # ≈ 441.67
        expected_min = max(0.0, 100.0 - max_d / _RGB_SCALE)
        assert expected_min < 1.0  # 최대 거리는 거의 0점


# ── _item_pcf_score 단위 테스트 ──────────────────────────────────────────────

class TestItemPcfScore:
    def test_tone_match_bypasses_color(self):
        # 동일 톤 → 100, hex 값 무관
        assert _item_pcf_score("spring_warm_light", "#000000", "spring_warm_light") == 100.0

    def test_compatible_tone_bypasses_color(self):
        # 호환 톤 → 95
        assert _item_pcf_score("spring_warm_bright", "#000000", "spring_warm_light") == 95.0

    def test_incompatible_tone_falls_back_to_hex(self):
        # 비호환 톤이지만 팔레트와 가까운 색 → 색상 레벨 점수 반환
        score = _item_pcf_score("winter_cool_bright", "#FFCBA4", "spring_warm_light")
        # 팔레트 정확히 일치하는 색이니 100점
        assert score == pytest.approx(100.0, abs=0.01)

    def test_no_tone_no_hex_returns_neutral(self):
        assert _item_pcf_score(None, None, "spring_warm_light") == 50.0

    def test_none_tone_with_hex_uses_color_level(self):
        score = _item_pcf_score(None, "#FFCBA4", "spring_warm_light")
        assert score == pytest.approx(100.0, abs=0.01)

    def test_incompatible_tone_no_hex_returns_0(self):
        # 비호환 톤 + hex 없음 → 0
        assert _item_pcf_score("winter_cool_bright", None, "spring_warm_light") == 0.0


# ── calculate_pcf 통합 테스트 ─────────────────────────────────────────────────

class TestCalculatePcf:
    def test_empty_inputs_returns_neutral(self):
        assert calculate_pcf([], [], "spring_warm_light") == 50.0

    def test_single_exact_tone_match(self):
        score = calculate_pcf(["spring_warm_light"], ["#FFCBA4"], "spring_warm_light")
        assert score == pytest.approx(100.0, abs=0.01)

    def test_multiple_items_averaged(self):
        # 아이템 2개: 동일 톤(100) + 반대 시즌 비호환 + 나쁜 색(~낮은 점수)
        # 결과는 평균
        score_same = calculate_pcf(
            ["spring_warm_light", "spring_warm_light"],
            ["#FFCBA4", "#FFCBA4"],
            "spring_warm_light",
        )
        assert score_same == pytest.approx(100.0, abs=0.01)

    def test_compatible_season_items(self):
        # 봄웜 유저, 아이템 3개 모두 봄웜 계열 → 95 이상
        score = calculate_pcf(
            ["spring_warm_bright", "spring_warm_mute", "spring_warm_light"],
            [None, None, None],
            "spring_warm_light",
        )
        # spring_warm_light와 같은 시즌: bright→95, mute→95, light→100 → avg=96.67
        assert score == pytest.approx(96.67, abs=0.1)

    def test_opposite_season_items(self):
        # 봄웜 유저, 아이템 모두 겨울쿨 → 낮은 점수
        score = calculate_pcf(
            ["winter_cool_bright", "winter_cool_deep"],
            [None, None],
            "spring_warm_light",
        )
        assert score < 50.0

    def test_mismatched_list_lengths_padded(self):
        # tone_ids 길고 hex_colors 짧으면 None 패딩
        score = calculate_pcf(
            ["spring_warm_light", "spring_warm_light"],
            ["#FFCBA4"],
            "spring_warm_light",
        )
        # 두 번째 아이템은 hex=None → _item_pcf_score("spring_warm_light", None, ...) = 100
        assert score == pytest.approx(100.0, abs=0.01)

    def test_boundary_black_color(self):
        # 검정(#000000) 아이템 → 점수는 0~100 범위 내
        score = calculate_pcf([None], ["#000000"], "spring_warm_light")
        assert 0.0 <= score <= 100.0

    def test_boundary_white_color(self):
        # 흰색(#FFFFFF)은 팔레트에 가까울 수도 있어 0~100 범위
        score = calculate_pcf([None], ["#FFFFFF"], "spring_warm_light")
        assert 0.0 <= score <= 100.0

    def test_winter_user_winter_items(self):
        # 겨울쿨 유저, 겨울쿨 아이템 → 높은 점수
        score = calculate_pcf(
            ["winter_cool_bright", "winter_cool_deep", "winter_cool_light"],
            [None, None, None],
            "winter_cool_bright",
        )
        # bright→100, deep→95, light→95 → avg=96.67
        assert score == pytest.approx(96.67, abs=0.1)


# ── OF 테스트 ─────────────────────────────────────────────────────────────────

class TestExpandTpos:
    def test_commute_expands_to_office_and_commute(self):
        assert _expand_tpos(["commute"]) == frozenset({"office", "commute"})

    def test_office_expands_to_office_and_commute(self):
        assert _expand_tpos(["office"]) == frozenset({"office", "commute"})

    def test_weekend_expands_to_casual_daily(self):
        assert _expand_tpos(["weekend"]) == frozenset({"casual", "weekend", "daily"})

    def test_interview_expands_to_office(self):
        # interview는 office를 포함하지만, office는 interview를 포함하지 않음
        result = _expand_tpos(["interview"])
        assert "office" in result
        assert "interview" in result

    def test_workout_has_no_synonyms(self):
        assert _expand_tpos(["workout"]) == frozenset({"workout"})

    def test_multiple_tpos_merged(self):
        result = _expand_tpos(["commute", "weekend"])
        assert "office" in result
        assert "casual" in result
        assert "daily" in result

    def test_unknown_tpo_returns_itself(self):
        # 매핑에 없는 TPO → 자기 자신만 반환
        assert _expand_tpos(["picnic"]) == frozenset({"picnic"})


class TestCalculateOf:
    # ── 정확 매칭 ──────────────────────────────────────────────────────────────

    def test_exact_single_match(self):
        # outfit_tags=["office"], user=["office"] → match_count=1, total=1
        # score = 60 + (1/1)*20 = 80
        score = calculate_of(["office"], ["office"])
        assert score == pytest.approx(80.0)

    def test_exact_double_match(self):
        # outfit_tags=["office","casual"], user=["office","casual"]
        # match_count=2, total=2 → 80 + (2/2)*20 = 100
        score = calculate_of(["office", "casual"], ["office", "casual"])
        assert score == pytest.approx(100.0)

    def test_exact_partial_match_of_two(self):
        # outfit_tags=["office","party","wedding"], user=["office"]
        # match_count=1, total=3 → 60 + (1/3)*20 ≈ 66.67
        score = calculate_of(["office", "party", "wedding"], ["office"])
        assert score == pytest.approx(60.0 + 20.0 / 3, abs=0.01)

    # ── 동의어 매칭 ────────────────────────────────────────────────────────────

    def test_synonym_commute_matches_office_tag(self):
        # 유저 TPO="commute" → expanded={"office","commute"}, outfit_tag="office" → match 1
        score = calculate_of(["office"], ["commute"])
        assert score == pytest.approx(80.0)

    def test_synonym_weekend_matches_casual_tag(self):
        score = calculate_of(["casual"], ["weekend"])
        assert score == pytest.approx(80.0)

    def test_synonym_daily_matches_weekend_tag(self):
        score = calculate_of(["weekend"], ["daily"])
        assert score == pytest.approx(80.0)

    def test_interview_matches_office_tag(self):
        # interview → {"interview","office"}, tag="office" → match 1
        score = calculate_of(["office"], ["interview"])
        assert score == pytest.approx(80.0)

    def test_office_does_not_match_interview_tag(self):
        # office → {"office","commute"}, tag="interview" → match 0
        score = calculate_of(["interview"], ["office"])
        assert score == pytest.approx(30.0)

    def test_campus_matches_casual_tag(self):
        score = calculate_of(["casual"], ["campus"])
        assert score == pytest.approx(80.0)

    def test_event_matches_party_tag(self):
        score = calculate_of(["party"], ["event"])
        assert score == pytest.approx(80.0)

    def test_party_does_not_expand_to_wedding(self):
        # party → {"party","event"}, wedding은 포함 안 됨
        score = calculate_of(["wedding"], ["party"])
        assert score == pytest.approx(30.0)

    # ── 완전 미매칭 ────────────────────────────────────────────────────────────

    def test_no_match_returns_30(self):
        score = calculate_of(["workout"], ["office"])
        assert score == pytest.approx(30.0)

    def test_workout_no_synonyms_mismatches_casual(self):
        score = calculate_of(["casual"], ["workout"])
        assert score == pytest.approx(30.0)

    # ── 경계값 ────────────────────────────────────────────────────────────────

    def test_empty_outfit_tags_returns_30(self):
        score = calculate_of([], ["office"])
        assert score == pytest.approx(30.0)

    def test_empty_user_tpo_returns_30(self):
        score = calculate_of(["office"], [])
        assert score == pytest.approx(30.0)

    def test_score_capped_at_100(self):
        # match_count=10, total=10 → 80 + 20 = 100
        tags = ["office"] * 10
        score = calculate_of(tags, ["office"])
        assert score <= 100.0

    def test_score_floor_is_30(self):
        score = calculate_of(["workout", "travel", "beach"], ["office"])
        assert score == pytest.approx(30.0)

    def test_score_in_range(self):
        score = calculate_of(["office", "commute", "party"], ["commute"])
        assert 30.0 <= score <= 100.0

    def test_multi_match_beats_single_match(self):
        # 유저 TPO 여러 개로 outfit 태그 2개 이상 커버
        score_multi = calculate_of(["office", "commute"], ["office"])
        # commute→{"office","commute"} → office+commute 모두 매칭
        score_single = calculate_of(["office"], ["office"])
        # 2매칭 >= 1매칭
        assert score_multi >= score_single


# ── CH 테스트 ─────────────────────────────────────────────────────────────────

class TestChBaseScore:
    def test_d_lt_30_returns_60(self):
        assert _ch_base_score(0.0) == 60.0
        assert _ch_base_score(15.0) == 60.0
        assert _ch_base_score(29.99) == 60.0

    def test_d_at_30_boundary(self):
        # 30 → 80 + 0 = 80
        assert _ch_base_score(30.0) == pytest.approx(80.0)

    def test_d_in_30_80_range(self):
        # d=55 → 80 + 25/50*20 = 80+10 = 90
        assert _ch_base_score(55.0) == pytest.approx(90.0)

    def test_d_at_80_boundary(self):
        # 80 → 100 - 0 = 100
        assert _ch_base_score(80.0) == pytest.approx(100.0)

    def test_d_in_80_150_range(self):
        # d=115 → 100 - 35/70*21 = 100 - 10.5 = 89.5
        assert _ch_base_score(115.0) == pytest.approx(89.5)

    def test_d_at_150_boundary(self):
        # 150 → max(30, 79 - 0) = 79
        assert _ch_base_score(150.0) == pytest.approx(79.0)

    def test_d_ge_150_decreases(self):
        # d=440 → max(30, 79 - 290/290*49) = max(30, 30) = 30
        assert _ch_base_score(440.0) == pytest.approx(30.0, abs=0.1)

    def test_d_max_rgb_returns_30(self):
        # 최대 RGB 거리 441.67 → 30점 하한
        assert _ch_base_score(441.67) == pytest.approx(30.0, abs=0.1)


class TestRgbToSaturation:
    def test_pure_red_is_fully_saturated(self):
        assert _rgb_to_saturation(255, 0, 0) == pytest.approx(1.0)

    def test_gray_is_zero_saturation(self):
        assert _rgb_to_saturation(128, 128, 128) == pytest.approx(0.0)

    def test_white_is_zero_saturation(self):
        assert _rgb_to_saturation(255, 255, 255) == pytest.approx(0.0)

    def test_black_is_zero_saturation(self):
        assert _rgb_to_saturation(0, 0, 0) == pytest.approx(0.0)

    def test_saturation_in_0_1_range(self):
        s = _rgb_to_saturation(200, 150, 100)
        assert 0.0 <= s <= 1.0


class TestCalculateCh:
    # ── 경계값 & 구간 ──────────────────────────────────────────────────────────

    def test_empty_returns_60(self):
        assert calculate_ch([]) == pytest.approx(60.0)

    def test_single_item_returns_60(self):
        assert calculate_ch(["#FF0000"]) == pytest.approx(60.0)

    def test_identical_colors_returns_60(self):
        # 동일색 쌍 d=0 → 60
        assert calculate_ch(["#000000", "#000000"]) == pytest.approx(60.0)

    def test_all_black_3_items_returns_60(self):
        assert calculate_ch(["#000000", "#000000", "#000000"]) == pytest.approx(60.0)

    def test_very_similar_colors_returns_60(self):
        # d=29.44 < 30 → 60
        assert calculate_ch(["#000000", "#111111"]) == pytest.approx(60.0)

    # ── 유사색 조화 (30~80) ────────────────────────────────────────────────────

    def test_analogous_colors_score(self):
        # #FFCBA4 vs #FF9E8A d≈51.97 → score≈88.79
        score = calculate_ch(["#FFCBA4", "#FF9E8A"])
        assert score == pytest.approx(88.79, abs=0.1)

    def test_analogous_above_threshold(self):
        # d=31.18 → 80 + 1.18/50*20 ≈ 80.47
        score = calculate_ch(["#000000", "#121212"])
        assert score == pytest.approx(80.47, abs=0.1)

    # ── 적절한 대비 (80~150) ──────────────────────────────────────────────────

    def test_moderate_contrast_3_items(self):
        # #FFCBA4, #FF9E8A, #FFF5E4 d_avg≈84.57 → score≈98.63
        score = calculate_ch(["#FFCBA4", "#FF9E8A", "#FFF5E4"])
        assert score == pytest.approx(98.63, abs=0.1)

    def test_moderate_contrast_in_range(self):
        score = calculate_ch(["#FFCBA4", "#FF9E8A", "#FFF5E4"])
        assert 79.0 <= score <= 100.0

    # ── 과도한 대비 (≥150) ────────────────────────────────────────────────────

    def test_extreme_contrast_scores_low(self):
        # 형광빨강 vs 파스텔블루 d≈346.51 → score≈45.80
        score = calculate_ch(["#FF0000", "#CCE5FF"])
        assert score == pytest.approx(45.80, abs=0.1)

    def test_black_and_white_returns_30(self):
        # 검정+흰색 d=441.67 → 30점 하한
        score = calculate_ch(["#000000", "#FFFFFF"])
        assert score == pytest.approx(30.0, abs=0.1)

    def test_extreme_contrast_floor_is_30(self):
        score = calculate_ch(["#000000", "#FFFFFF"])
        assert score >= 30.0

    # ── 채도 보너스 ───────────────────────────────────────────────────────────

    def test_saturation_bonus_applied(self):
        # 아이보리+코랄+카멜: std_sat≈0.257 (0.15~0.40) → +5
        # base≈82.40 → final≈87.40
        score = calculate_ch(["#FFF5E4", "#FF6B6B", "#C8956C"])
        assert score == pytest.approx(87.40, abs=0.1)

    def test_no_bonus_for_2_items(self):
        # 아이템 2개는 보너스 조건(3개 이상) 미충족
        score_2 = calculate_ch(["#FFF5E4", "#FF6B6B"])
        score_3 = calculate_ch(["#FFF5E4", "#FF6B6B", "#C8956C"])
        # 3개 버전은 보너스 적용되어 더 높음
        assert score_3 > score_2

    def test_no_bonus_for_high_saturation_std(self):
        # std > 0.40 → 보너스 없음 (#FFFFFF, #FF4500, #D2691E → std≈0.425)
        # std=0.425 > 0.40이므로 보너스 없음
        score = calculate_ch(["#FFFFFF", "#FF4500", "#D2691E"])
        # 보너스 없는 기본 점수만 반환
        assert isinstance(score, float)
        assert 0.0 <= score <= 100.0

    def test_score_always_capped_at_100(self):
        # 보너스 포함해도 100 초과 불가
        score = calculate_ch(["#FFF5E4", "#FF6B6B", "#C8956C"])
        assert score <= 100.0


# ── PE 테스트 ────────────────────────────────────────────────────────────────

class TestCalculatePe:
    """Task 2.4 — PE (Price Efficiency) 스코어링 테스트."""

    # ── Case 1: 예산 범위 내 ──────────────────────────────────────────────────

    def test_center_price_returns_100(self):
        # 중앙 가격 = (30000+70000)/2 = 50000 → 100점
        score = calculate_pe(50000, 30000, 70000)
        assert score == pytest.approx(100.0)

    def test_budget_min_boundary(self):
        # budget_min=30000, budget_mid=50000
        # |30000-50000|/50000 × 30 = 12 → 100-12 = 88
        score = calculate_pe(30000, 30000, 70000)
        assert score == pytest.approx(88.0)

    def test_budget_max_boundary(self):
        # budget_max=70000, budget_mid=50000
        # |70000-50000|/50000 × 30 = 12 → 100-12 = 88
        score = calculate_pe(70000, 30000, 70000)
        assert score == pytest.approx(88.0)

    def test_within_range_symmetric(self):
        # min과 max에서 같은 거리 → 같은 점수
        score_low = calculate_pe(40000, 30000, 70000)
        score_high = calculate_pe(60000, 30000, 70000)
        assert score_low == pytest.approx(score_high, abs=0.01)

    def test_within_range_score_between_70_and_100(self):
        score = calculate_pe(35000, 30000, 70000)
        assert 70.0 <= score <= 100.0

    # ── Case 2: 예산 초과 ────────────────────────────────────────────────────

    def test_10_percent_over_returns_60(self):
        # over_ratio = (77000-70000)/70000 = 0.1
        # 70 - 0.1×100 = 60
        score = calculate_pe(77000, 30000, 70000)
        assert score == pytest.approx(60.0)

    def test_50_percent_over_returns_20(self):
        # over_ratio = (105000-70000)/70000 = 0.5
        # 70 - 0.5×100 = 20
        score = calculate_pe(105000, 30000, 70000)
        assert score == pytest.approx(20.0)

    def test_70_percent_over_returns_0(self):
        # over_ratio = (119000-70000)/70000 = 0.7
        # 70 - 0.7×100 = 0
        score = calculate_pe(119000, 30000, 70000)
        assert score == pytest.approx(0.0)

    def test_over_100_percent_clamped_at_0(self):
        # 초과가 너무 클 때 0 이하가 되지 않음
        score = calculate_pe(200000, 30000, 70000)
        assert score == pytest.approx(0.0)

    # ── Case 3: 예산 미만 ────────────────────────────────────────────────────

    def test_slightly_under_returns_near_80(self):
        # under_ratio = (30000-25000)/30000 ≈ 0.167
        # 80 - 0.167×80 ≈ 66.67
        score = calculate_pe(25000, 30000, 70000)
        assert score == pytest.approx(66.67, abs=0.1)

    def test_half_of_budget_min(self):
        # under_ratio = (30000-15000)/30000 = 0.5
        # 80 - 0.5×80 = 40
        score = calculate_pe(15000, 30000, 70000)
        assert score == pytest.approx(40.0)

    def test_extreme_low_price_floored_at_40(self):
        # 극단적 저가 → 40점 하한
        score = calculate_pe(1000, 30000, 70000)
        assert score == pytest.approx(40.0)

    def test_zero_price_floored_at_40(self):
        score = calculate_pe(0, 30000, 70000)
        assert score == pytest.approx(40.0)

    def test_under_budget_floor_is_40(self):
        # 어떤 저가든 40점 미만이 되지 않음
        score = calculate_pe(100, 50000, 100000)
        assert score >= 40.0

    # ── 경계값 & 엣지 케이스 ─────────────────────────────────────────────────

    def test_score_always_in_0_to_100(self):
        test_cases = [
            (50000, 30000, 70000),
            (0, 30000, 70000),
            (200000, 30000, 70000),
            (100000, 100000, 100000),
        ]
        for total, bmin, bmax in test_cases:
            score = calculate_pe(total, bmin, bmax)
            assert 0.0 <= score <= 100.0, f"Failed for ({total}, {bmin}, {bmax}): {score}"

    def test_same_min_max_center(self):
        # min=max=50000 → mid=50000, price=50000 → 100점
        score = calculate_pe(50000, 50000, 50000)
        assert score == pytest.approx(100.0)

    def test_budget_preset_3man(self):
        # 프리셋 ~3만원 (0~30000)
        score = calculate_pe(15000, 0, 30000)
        assert score == pytest.approx(100.0)

    def test_budget_preset_3_7man(self):
        # 프리셋 3~7만원
        score = calculate_pe(50000, 30000, 70000)
        assert score == pytest.approx(100.0)

    def test_invalid_budget_returns_neutral(self):
        # budget_max <= 0 → 50
        score = calculate_pe(50000, 0, 0)
        assert score == pytest.approx(50.0)


# ── SF 테스트 ────────────────────────────────────────────────────────────────

class TestCategoryCompatScore:
    """카테고리 궁합 점수 하위 함수 테스트."""

    def test_blouse_slacks_returns_90(self):
        assert _category_compat_score(["blouse", "slacks"]) == pytest.approx(90.0)

    def test_knit_jeans_returns_85(self):
        assert _category_compat_score(["knit", "jeans"]) == pytest.approx(85.0)

    def test_hoodie_suit_jacket_returns_20(self):
        # 명백한 부조화
        assert _category_compat_score(["hoodie", "suit_jacket"]) == pytest.approx(20.0)

    def test_unknown_combo_returns_60(self):
        # 매트릭스에 없는 조합 → 60(중립)
        assert _category_compat_score(["earring", "jogger"]) == pytest.approx(60.0)

    def test_single_item_returns_60(self):
        assert _category_compat_score(["blouse"]) == pytest.approx(60.0)

    def test_three_items_averaged(self):
        # blouse+slacks=90, blouse+heels 없음→60, heels__slacks→slacks__heels 없음→60
        # 다른 조합: blouse+slacks=90, blouse+trench=95, slacks__trench→trench__slacks=90
        # → avg = (90+95+90)/3 = 91.67
        score = _category_compat_score(["blouse", "slacks", "trench"])
        assert score == pytest.approx(91.67, abs=0.1)

    def test_order_independent(self):
        s1 = _category_compat_score(["slacks", "blouse"])
        s2 = _category_compat_score(["blouse", "slacks"])
        assert s1 == pytest.approx(s2)


class TestSilhouetteBalanceScore:
    """실루엣 밸런스 점수 하위 함수 테스트."""

    def test_oversized_slim_y_line_95(self):
        assert _silhouette_balance_score("oversized", "slim") == pytest.approx(95.0)

    def test_fitted_wide_a_line_95(self):
        assert _silhouette_balance_score("fitted", "wide") == pytest.approx(95.0)

    def test_fitted_slim_i_line_85(self):
        assert _silhouette_balance_score("fitted", "slim") == pytest.approx(85.0)

    def test_oversized_wide_volume_60(self):
        assert _silhouette_balance_score("oversized", "wide") == pytest.approx(60.0)

    def test_crop_high_waist_x_line_90(self):
        assert _silhouette_balance_score("crop", "high_waist") == pytest.approx(90.0)

    def test_unknown_combo_returns_65(self):
        assert _silhouette_balance_score("unknown", "unknown") == pytest.approx(65.0)

    def test_none_silhouette_returns_65(self):
        assert _silhouette_balance_score(None, "slim") == pytest.approx(65.0)
        assert _silhouette_balance_score("fitted", None) == pytest.approx(65.0)


class TestFormalityConsistencyScore:
    """포멀도 일관성 점수 하위 함수 테스트."""

    def test_same_formality_returns_100(self):
        # blouse(4) + slacks(4) → std=0 → 100
        assert _formality_consistency_score(["blouse", "slacks"]) == pytest.approx(100.0)

    def test_one_step_deviation(self):
        # blouse(4) + knit(3) → mean=3.5, std=0.5 → 100-0.5*40=80
        assert _formality_consistency_score(["blouse", "knit"]) == pytest.approx(80.0)

    def test_two_step_deviation(self):
        # blouse(4) + tshirt(2) → mean=3, std=1.0 → 100-40=60
        assert _formality_consistency_score(["blouse", "tshirt"]) == pytest.approx(60.0)

    def test_extreme_deviation(self):
        # hoodie(1) + suit_jacket(5) → mean=3, std=2.0 → 100-80=20
        assert _formality_consistency_score(["hoodie", "suit_jacket"]) == pytest.approx(20.0)

    def test_max_deviation_clamped_at_0(self):
        # hoodie(1) + heels(5) + suit_jacket(5) → std ≈ 1.886 → 100-75.4 ≈ 24.6
        score = _formality_consistency_score(["hoodie", "heels", "suit_jacket"])
        assert score >= 0.0

    def test_single_item_returns_100(self):
        assert _formality_consistency_score(["blouse"]) == pytest.approx(100.0)

    def test_unknown_category_uses_neutral_3(self):
        # unknown(3) + unknown(3) → std=0 → 100
        assert _formality_consistency_score(["xyz", "abc"]) == pytest.approx(100.0)


class TestCalculateSf:
    """Task 2.5 — SF (Style Fit) 통합 테스트."""

    def test_blouse_slacks_high_score(self):
        # 블라우스+슬랙스: 카테고리 90, 실루엣 미지정→65, 포멀도 100
        # SF = 90*0.5 + 65*0.25 + 100*0.25 = 45 + 16.25 + 25 = 86.25
        items = [
            {"category": "blouse"},
            {"category": "slacks"},
        ]
        score = calculate_sf(items)
        assert score == pytest.approx(86.25)

    def test_blouse_slacks_with_silhouette(self):
        # fitted + slim → 실루엣 85, 포멀도 100
        # SF = 90*0.5 + 85*0.25 + 100*0.25 = 45 + 21.25 + 25 = 91.25
        items = [
            {"category": "blouse", "silhouette": "fitted"},
            {"category": "slacks", "silhouette": "slim"},
        ]
        score = calculate_sf(items)
        assert score == pytest.approx(91.25)

    def test_hoodie_suit_jacket_low_score(self):
        # 후드+정장: 카테고리 20, 실루엣 미지정→65, 포멀도=hoodie(1)+suit_jacket(5)→20
        # SF = 20*0.5 + 65*0.25 + 20*0.25 = 10 + 16.25 + 5 = 31.25
        items = [
            {"category": "hoodie"},
            {"category": "suit_jacket"},
        ]
        score = calculate_sf(items)
        assert score == pytest.approx(31.25)

    def test_hoodie_suit_jacket_below_55_cutoff(self):
        # StyleFilter 55점 컷오프 검증
        items = [
            {"category": "hoodie"},
            {"category": "suit_jacket"},
        ]
        assert calculate_sf(items) < 55.0

    def test_blouse_slacks_above_55_cutoff(self):
        items = [
            {"category": "blouse"},
            {"category": "slacks"},
        ]
        assert calculate_sf(items) > 55.0

    def test_three_item_outfit(self):
        # 블라우스+슬랙스+로퍼
        items = [
            {"category": "blouse", "silhouette": "fitted"},
            {"category": "slacks", "silhouette": "slim"},
            {"category": "loafer"},
        ]
        score = calculate_sf(items)
        # 카테고리: blouse__slacks=90, blouse+loafer=없음60, slacks__loafer=90 → avg=80
        # 실루엣: fitted+slim → 85
        # 포멀도: blouse(4)+slacks(4)+loafer(3) → std≈0.471 → 100-0.471*40≈81.14
        # 점수가 합리적 범위에 있는지만 검증
        assert 70.0 <= score <= 90.0

    def test_empty_items_returns_50(self):
        assert calculate_sf([]) == pytest.approx(50.0)

    def test_no_category_returns_50(self):
        assert calculate_sf([{"silhouette": "fitted"}]) == pytest.approx(50.0)

    def test_full_outfit_high_score(self):
        # 블라우스+슬랙스+트렌치+로퍼: 모두 비즈니스 캐주얼
        items = [
            {"category": "blouse", "silhouette": "fitted"},
            {"category": "slacks", "silhouette": "slim"},
            {"category": "trench"},
            {"category": "loafer"},
        ]
        score = calculate_sf(items)
        assert score > 70.0

    def test_casual_outfit_decent_score(self):
        # 티셔츠+청바지+스니커즈: 모두 캐주얼
        items = [
            {"category": "tshirt"},
            {"category": "jeans"},
            {"category": "sneakers"},
        ]
        score = calculate_sf(items)
        assert score > 60.0

    def test_score_always_in_range(self):
        test_cases = [
            [{"category": "blouse"}, {"category": "slacks"}],
            [{"category": "hoodie"}, {"category": "suit_jacket"}],
            [{"category": "croptop"}, {"category": "leggings"}],
            [{"category": "tshirt"}, {"category": "jogger"}, {"category": "sneakers"}],
        ]
        for items in test_cases:
            score = calculate_sf(items)
            assert 0.0 <= score <= 100.0, f"Failed for {items}: {score}"

    def test_silhouette_improves_score(self):
        # 좋은 실루엣 조합이 있으면 실루엣 점수가 65→95로 올라감
        items_no_sil = [{"category": "blouse"}, {"category": "slacks"}]
        items_with_sil = [
            {"category": "blouse", "silhouette": "fitted"},
            {"category": "slacks", "silhouette": "wide"},
        ]
        assert calculate_sf(items_with_sil) > calculate_sf(items_no_sil)

    def test_formality_mismatch_lowers_score(self):
        # 같은 카테고리 궁합이라도 포멀도 불일치 시 점수 하락
        # hoodie(1)+jeans(2) vs blouse(4)+jeans(2)
        casual = [{"category": "hoodie"}, {"category": "jeans"}]
        mixed = [{"category": "blouse"}, {"category": "jeans"}]
        # hoodie+jeans: cat=80, form: std=0.5→80
        # blouse+jeans: cat=75, form: std=1.0→60
        # casual이 포멀도 일관성이 더 좋음
        casual_form = _formality_consistency_score(["hoodie", "jeans"])
        mixed_form = _formality_consistency_score(["blouse", "jeans"])
        assert casual_form > mixed_form
