"""
Task 2.8 + 2.9 — Hard Filter 체인 + Soft Score + 리랭킹 테스트.

실행: cd backend && venv/Scripts/activate && pytest tests/test_feed_builder.py -v
"""

import pytest

from app.services.feed_builder import (
    h1_gender,
    h2_budget,
    h3_season,
    h4_tpo,
    h5_brand,
    h6_llm_quality,
    compute_soft_scores,
    rerank,
    _is_complete_outfit,
    _personalization_bonus,
    h7_tone,
    h8_style_filter,
    apply_hard_filters,
)


# ── 공통 픽스처 ──────────────────────────────────────────────────────────────

def _make_outfit(**kwargs) -> dict:
    """테스트용 코디 dict 생성 헬퍼."""
    defaults = {
        "items": [],
        "total_price": 50000,
        "tags": [],
        "designed_tpo": [],
        "llm_quality_score": 4.0,
    }
    defaults.update(kwargs)
    return defaults


def _make_item(**kwargs) -> dict:
    """테스트용 아이템 dict 생성 헬퍼."""
    defaults = {
        "title": "",
        "gender": "female",
        "brand": "무신사 스탠다드",
        "tone_id": "spring_warm_light",
        "category": "blouse",
    }
    defaults.update(kwargs)
    return defaults


# ═══════════════════════════════════════════════════════════════════════════════
# H1 성별 필터
# ═══════════════════════════════════════════════════════════════════════════════

class TestH1Gender:
    def test_female_items_pass_female_user(self):
        outfit = _make_outfit(items=[_make_item(gender="female")])
        assert h1_gender(outfit, "female") is True

    def test_male_items_fail_female_user(self):
        outfit = _make_outfit(items=[_make_item(gender="male")])
        assert h1_gender(outfit, "female") is False

    def test_unisex_items_pass_any(self):
        outfit = _make_outfit(items=[_make_item(gender="unisex")])
        assert h1_gender(outfit, "female") is True
        assert h1_gender(outfit, "male") is True

    def test_mixed_gender_fails(self):
        outfit = _make_outfit(items=[
            _make_item(gender="female"),
            _make_item(gender="male"),
        ])
        assert h1_gender(outfit, "female") is False

    def test_empty_items_passes(self):
        outfit = _make_outfit(items=[])
        assert h1_gender(outfit, "female") is True


# ═══════════════════════════════════════════════════════════════════════════════
# H2 예산 초과 필터
# ═══════════════════════════════════════════════════════════════════════════════

class TestH2Budget:
    def test_within_budget_passes(self):
        outfit = _make_outfit(total_price=50000)
        assert h2_budget(outfit, 70000) is True

    def test_slightly_over_passes(self):
        # 30% 초과: 91000 <= 70000*1.5=105000 → 통과
        outfit = _make_outfit(total_price=91000)
        assert h2_budget(outfit, 70000) is True

    def test_50_percent_over_fails(self):
        # 50% 초과: 105001 > 70000*1.5=105000 → 제거
        outfit = _make_outfit(total_price=105001)
        assert h2_budget(outfit, 70000) is False

    def test_exactly_1_5x_passes(self):
        # 정확히 1.5배: 105000 <= 105000 → 통과
        outfit = _make_outfit(total_price=105000)
        assert h2_budget(outfit, 70000) is True

    def test_budget_zero_passes(self):
        outfit = _make_outfit(total_price=100000)
        assert h2_budget(outfit, 0) is True

    def test_under_budget_passes(self):
        # 예산 미만은 Hard Filter 아님
        outfit = _make_outfit(total_price=10000)
        assert h2_budget(outfit, 70000) is True


# ═══════════════════════════════════════════════════════════════════════════════
# H3 계절 완전 불일치 필터
# ═══════════════════════════════════════════════════════════════════════════════

class TestH3Season:
    def test_same_season_passes(self):
        outfit = _make_outfit(tags=["spring"])
        assert h3_season(outfit, current_month=4) is True

    def test_adjacent_season_passes(self):
        # 봄(4월)에 여름 코디 → 인접 시즌 허용
        outfit = _make_outfit(tags=["summer"])
        assert h3_season(outfit, current_month=4) is True

    def test_opposite_season_fails(self):
        # 봄(4월)에 가을 코디 → 반대 시즌 제거
        outfit = _make_outfit(tags=["autumn"])
        assert h3_season(outfit, current_month=4) is False

    def test_summer_coat_in_july_fails(self):
        # 여름(7월)에 겨울 코디 → 제거
        outfit = _make_outfit(tags=["winter"])
        assert h3_season(outfit, current_month=7) is False

    def test_no_season_tag_passes(self):
        # 시즌 태그 없으면 통과
        outfit = _make_outfit(tags=["casual", "date"])
        assert h3_season(outfit, current_month=4) is True

    def test_travel_tpo_bypasses(self):
        # travel TPO면 시즌 필터 면제
        outfit = _make_outfit(tags=["winter", "travel"])
        assert h3_season(outfit, current_month=7) is True

    def test_winter_spring_overlap(self):
        # 겨울(12월)에 봄 코디 → 인접 허용
        outfit = _make_outfit(tags=["spring"])
        assert h3_season(outfit, current_month=12) is True


# ═══════════════════════════════════════════════════════════════════════════════
# H4 TPO 완전 불일치 필터
# ═══════════════════════════════════════════════════════════════════════════════

class TestH4Tpo:
    def test_matching_tpo_passes(self):
        outfit = _make_outfit(designed_tpo=["office"])
        assert h4_tpo(outfit, ["office"]) is True

    def test_synonym_tpo_passes(self):
        # commute → {"office", "commute"}, tag="office" → match
        outfit = _make_outfit(designed_tpo=["office"])
        assert h4_tpo(outfit, ["commute"]) is True

    def test_no_match_fails(self):
        outfit = _make_outfit(designed_tpo=["workout"])
        assert h4_tpo(outfit, ["office"]) is False

    def test_all_tab_bypasses(self):
        outfit = _make_outfit(designed_tpo=["workout"])
        assert h4_tpo(outfit, ["office"], is_all_tab=True) is True

    def test_empty_user_tpo_passes(self):
        outfit = _make_outfit(designed_tpo=["office"])
        assert h4_tpo(outfit, []) is True

    def test_empty_outfit_tpo_passes(self):
        outfit = _make_outfit(designed_tpo=[])
        assert h4_tpo(outfit, ["office"]) is True

    def test_interview_matches_office(self):
        # interview → {"interview", "office"}
        outfit = _make_outfit(designed_tpo=["office"])
        assert h4_tpo(outfit, ["interview"]) is True


# ═══════════════════════════════════════════════════════════════════════════════
# H5 브랜드 화이트리스트 필터
# ═══════════════════════════════════════════════════════════════════════════════

class TestH5Brand:
    def test_whitelist_brand_passes(self):
        outfit = _make_outfit(items=[_make_item(brand="무신사 스탠다드")])
        assert h5_brand(outfit) is True

    def test_one_whitelist_brand_enough(self):
        outfit = _make_outfit(items=[
            _make_item(brand="알수없는브랜드"),
            _make_item(brand="유니클로"),
        ])
        assert h5_brand(outfit) is True

    def test_no_whitelist_brand_fails(self):
        outfit = _make_outfit(items=[
            _make_item(brand="알수없는브랜드A"),
            _make_item(brand="알수없는브랜드B"),
        ])
        assert h5_brand(outfit) is False

    def test_empty_brand_fails(self):
        outfit = _make_outfit(items=[_make_item(brand="")])
        assert h5_brand(outfit) is False

    def test_case_insensitive(self):
        outfit = _make_outfit(items=[_make_item(brand="COS")])
        assert h5_brand(outfit) is True


# ═══════════════════════════════════════════════════════════════════════════════
# H6 LLM 품질 필터
# ═══════════════════════════════════════════════════════════════════════════════

class TestH6LlmQuality:
    def test_score_3_passes(self):
        outfit = _make_outfit(llm_quality_score=3.0)
        assert h6_llm_quality(outfit) is True

    def test_score_below_3_fails(self):
        outfit = _make_outfit(llm_quality_score=2.5)
        assert h6_llm_quality(outfit) is False

    def test_score_none_passes(self):
        # 평가 안 됨 → 통과
        outfit = _make_outfit(llm_quality_score=None)
        assert h6_llm_quality(outfit) is True

    def test_score_5_passes(self):
        outfit = _make_outfit(llm_quality_score=5.0)
        assert h6_llm_quality(outfit) is True


# ═══════════════════════════════════════════════════════════════════════════════
# H7 톤 호환성 필터
# ═══════════════════════════════════════════════════════════════════════════════

class TestH7Tone:
    def test_same_tone_passes(self):
        outfit = _make_outfit(items=[_make_item(tone_id="spring_warm_light")])
        assert h7_tone(outfit, "spring_warm_light") is True

    def test_compatible_tone_passes(self):
        # 같은 시즌(spring) 내 다른 톤 → 호환
        outfit = _make_outfit(items=[_make_item(tone_id="spring_warm_bright")])
        assert h7_tone(outfit, "spring_warm_light") is True

    def test_incompatible_tone_all_items_fails(self):
        # 모든 아이템이 반대 시즌 → 제거
        outfit = _make_outfit(items=[
            _make_item(tone_id="winter_cool_deep"),
            _make_item(tone_id="winter_cool_bright"),
        ])
        assert h7_tone(outfit, "spring_warm_light") is False

    def test_one_compatible_enough(self):
        # 1개라도 호환 톤이면 통과
        outfit = _make_outfit(items=[
            _make_item(tone_id="winter_cool_deep"),
            _make_item(tone_id="spring_warm_bright"),
        ])
        assert h7_tone(outfit, "spring_warm_light") is True

    def test_no_tone_info_passes(self):
        # 톤 정보 없으면 통과
        outfit = _make_outfit(items=[_make_item(tone_id=None)])
        assert h7_tone(outfit, "spring_warm_light") is True

    def test_unknown_user_tone_passes(self):
        outfit = _make_outfit(items=[_make_item(tone_id="winter_cool_deep")])
        assert h7_tone(outfit, "unknown_tone") is True


# ═══════════════════════════════════════════════════════════════════════════════
# H8 StyleFilter 컷오프 필터
# ═══════════════════════════════════════════════════════════════════════════════

class TestH8StyleFilter:
    def test_good_outfit_passes(self):
        outfit = _make_outfit(items=[
            {"category": "blouse", "title": "블라우스"},
            {"category": "slacks", "title": "슬랙스"},
        ])
        assert h8_style_filter(outfit) is True

    def test_bad_outfit_fails(self):
        outfit = _make_outfit(items=[
            {"category": "hoodie", "title": "후드티"},
            {"category": "suit_jacket", "title": "정장"},
        ])
        assert h8_style_filter(outfit) is False

    def test_empty_items_fails(self):
        outfit = _make_outfit(items=[])
        assert h8_style_filter(outfit) is False


# ═══════════════════════════════════════════════════════════════════════════════
# apply_hard_filters 통합 테스트
# ═══════════════════════════════════════════════════════════════════════════════

class TestApplyHardFilters:
    def _good_outfit(self) -> dict:
        """모든 필터를 통과하는 정상 코디."""
        return _make_outfit(
            items=[
                _make_item(
                    title="블라우스",
                    category="blouse",
                    gender="female",
                    brand="무신사 스탠다드",
                    tone_id="spring_warm_light",
                ),
                _make_item(
                    title="슬랙스",
                    category="slacks",
                    gender="female",
                    brand="유니클로",
                    tone_id="spring_warm_bright",
                ),
            ],
            total_price=50000,
            tags=["spring"],
            designed_tpo=["office"],
            llm_quality_score=4.0,
        )

    def test_good_outfit_passes_all(self):
        outfits = [self._good_outfit()]
        result = apply_hard_filters(
            outfits,
            user_gender="female",
            budget_max=70000,
            user_tpo_list=["office"],
            user_tone_id="spring_warm_light",
            current_month=4,
        )
        assert len(result) == 1

    def test_gender_mismatch_removed(self):
        outfit = self._good_outfit()
        outfit["items"][0]["gender"] = "male"
        result = apply_hard_filters(
            [outfit],
            user_gender="female",
            budget_max=70000,
            user_tpo_list=["office"],
            user_tone_id="spring_warm_light",
            current_month=4,
        )
        assert len(result) == 0

    def test_budget_exceeded_removed(self):
        outfit = self._good_outfit()
        outfit["total_price"] = 200000  # 70000*1.5=105000 초과
        result = apply_hard_filters(
            [outfit],
            user_gender="female",
            budget_max=70000,
            user_tpo_list=["office"],
            user_tone_id="spring_warm_light",
            current_month=4,
        )
        assert len(result) == 0

    def test_tpo_mismatch_removed(self):
        outfit = self._good_outfit()
        outfit["designed_tpo"] = ["workout"]
        result = apply_hard_filters(
            [outfit],
            user_gender="female",
            budget_max=70000,
            user_tpo_list=["office"],
            user_tone_id="spring_warm_light",
            current_month=4,
        )
        assert len(result) == 0

    def test_tone_mismatch_removed(self):
        outfit = self._good_outfit()
        for item in outfit["items"]:
            item["tone_id"] = "winter_cool_deep"
        result = apply_hard_filters(
            [outfit],
            user_gender="female",
            budget_max=70000,
            user_tpo_list=["office"],
            user_tone_id="spring_warm_light",
            current_month=4,
        )
        assert len(result) == 0

    def test_multiple_outfits_filtered(self):
        good = self._good_outfit()
        bad_gender = self._good_outfit()
        bad_gender["items"][0]["gender"] = "male"
        bad_budget = self._good_outfit()
        bad_budget["total_price"] = 200000

        result = apply_hard_filters(
            [good, bad_gender, bad_budget],
            user_gender="female",
            budget_max=70000,
            user_tpo_list=["office"],
            user_tone_id="spring_warm_light",
            current_month=4,
        )
        assert len(result) == 1

    def test_empty_outfits_returns_empty(self):
        result = apply_hard_filters(
            [],
            user_gender="female",
            budget_max=70000,
            user_tpo_list=["office"],
            user_tone_id="spring_warm_light",
        )
        assert result == []


# ═══════════════════════════════════════════════════════════════════════════════
# Soft Score 테스트 (Task 2.9)
# ═══════════════════════════════════════════════════════════════════════════════

class TestComputeSoftScores:
    def _scored_outfit(self) -> dict:
        return _make_outfit(
            items=[
                _make_item(
                    category="blouse",
                    tone_id="spring_warm_light",
                    color_hex="#FFCBA4",
                ),
                _make_item(
                    category="slacks",
                    tone_id="spring_warm_bright",
                    color_hex="#F5F0E8",
                ),
            ],
            total_price=50000,
            designed_tpo=["office"],
        )

    def test_returns_all_five_axes(self):
        scores = compute_soft_scores(
            self._scored_outfit(),
            user_tone_id="spring_warm_light",
            user_tpo_list=["office"],
            budget_min=30000,
            budget_max=70000,
        )
        for key in ("pcf", "of", "ch", "pe", "sf", "total"):
            assert key in scores
            assert 0.0 <= scores[key] <= 100.0

    def test_total_is_weighted_sum(self):
        scores = compute_soft_scores(
            self._scored_outfit(),
            user_tone_id="spring_warm_light",
            user_tpo_list=["office"],
            budget_min=30000,
            budget_max=70000,
        )
        expected = (
            scores["pcf"] * 0.25
            + scores["of"] * 0.20
            + scores["ch"] * 0.15
            + scores["pe"] * 0.15
            + scores["sf"] * 0.25
        )
        assert scores["total"] == pytest.approx(expected, abs=0.01)

    def test_weight_overrides(self):
        overrides = {"pcf": 0.50, "of": 0.10, "ch": 0.10, "pe": 0.10, "sf": 0.20}
        scores = compute_soft_scores(
            self._scored_outfit(),
            user_tone_id="spring_warm_light",
            user_tpo_list=["office"],
            budget_min=30000,
            budget_max=70000,
            weight_overrides=overrides,
        )
        # 가중치 합이 1.0이면 정규화 후에도 동일
        expected = (
            scores["pcf"] * 0.50
            + scores["of"] * 0.10
            + scores["ch"] * 0.10
            + scores["pe"] * 0.10
            + scores["sf"] * 0.20
        )
        assert scores["total"] == pytest.approx(expected, abs=0.01)

    def test_pcf_high_for_matching_tone(self):
        scores = compute_soft_scores(
            self._scored_outfit(),
            user_tone_id="spring_warm_light",
            user_tpo_list=["office"],
            budget_min=30000,
            budget_max=70000,
        )
        assert scores["pcf"] > 90.0  # 동일/호환 톤

    def test_of_high_for_matching_tpo(self):
        scores = compute_soft_scores(
            self._scored_outfit(),
            user_tone_id="spring_warm_light",
            user_tpo_list=["office"],
            budget_min=30000,
            budget_max=70000,
        )
        assert scores["of"] >= 60.0  # office 매칭


# ═══════════════════════════════════════════════════════════════════════════════
# 리랭킹 헬퍼 테스트
# ═══════════════════════════════════════════════════════════════════════════════

class TestIsCompleteOutfit:
    def test_top_bottom_outer_is_complete(self):
        outfit = _make_outfit(items=[
            _make_item(category="blouse"),
            _make_item(category="slacks"),
            _make_item(category="blazer"),
        ])
        assert _is_complete_outfit(outfit) is True

    def test_top_bottom_only_not_complete(self):
        outfit = _make_outfit(items=[
            _make_item(category="blouse"),
            _make_item(category="slacks"),
        ])
        assert _is_complete_outfit(outfit) is False

    def test_with_shoes_and_bag_complete(self):
        outfit = _make_outfit(items=[
            _make_item(category="knit"),
            _make_item(category="jeans"),
            _make_item(category="coat"),
            _make_item(category="sneakers"),
        ])
        assert _is_complete_outfit(outfit) is True


class TestPersonalizationBonus:
    def test_no_preferences_returns_0(self):
        outfit = _make_outfit(items=[_make_item()])
        assert _personalization_bonus(outfit) == 0.0

    def test_tone_preference_adds_bonus(self):
        outfit = _make_outfit(items=[
            _make_item(tone_id="spring_warm_light"),
            _make_item(tone_id="spring_warm_light"),
        ])
        bonus = _personalization_bonus(
            outfit, preferred_tones=["spring_warm_light"],
        )
        assert bonus == pytest.approx(4.0)  # 2 matches * 2.0, capped at 4.0

    def test_brand_preference_adds_bonus(self):
        outfit = _make_outfit(items=[
            _make_item(brand="무신사 스탠다드"),
        ])
        bonus = _personalization_bonus(
            outfit, preferred_brands=["무신사 스탠다드"],
        )
        assert bonus == pytest.approx(1.5)

    def test_capped_at_10(self):
        outfit = _make_outfit(items=[
            _make_item(tone_id="spring_warm_light", category="blouse", brand="무신사 스탠다드"),
            _make_item(tone_id="spring_warm_light", category="blouse", brand="무신사 스탠다드"),
            _make_item(tone_id="spring_warm_light", category="blouse", brand="무신사 스탠다드"),
        ])
        bonus = _personalization_bonus(
            outfit,
            preferred_tones=["spring_warm_light"],
            preferred_categories=["blouse"],
            preferred_brands=["무신사 스탠다드"],
        )
        assert bonus <= 10.0


# ═══════════════════════════════════════════════════════════════════════════════
# Rerank 통합 테스트
# ═══════════════════════════════════════════════════════════════════════════════

def _scored(outfit_id, total, items=None, tone_id="spring_warm_light", main_product_id=None):
    """점수가 이미 계산된 코디 생성 헬퍼."""
    if items is None:
        items = [
            {"category": "blouse", "tone_id": tone_id, "product_id": main_product_id or outfit_id},
            {"category": "slacks", "tone_id": tone_id, "product_id": f"{outfit_id}_bot"},
        ]
    return {
        "outfit_id": outfit_id,
        "items": items,
        "scores": {"total": total},
    }


class TestRerank:
    def test_sorted_by_score_desc(self):
        outfits = [_scored("a", 70), _scored("b", 90), _scored("c", 80)]
        result = rerank(outfits)
        ids = [o["outfit_id"] for o in result]
        assert ids == ["b", "c", "a"]

    def test_dislike_excluded(self):
        outfits = [_scored("a", 90), _scored("b", 80)]
        result = rerank(outfits, disliked_ids={"a"})
        assert len(result) == 1
        assert result[0]["outfit_id"] == "b"

    def test_complete_outfit_bonus(self):
        # 완성 코디(+3)가 비완성보다 높아짐
        complete = _scored("complete", 80, items=[
            {"category": "blouse", "tone_id": "spring_warm_light", "product_id": "c1"},
            {"category": "slacks", "tone_id": "spring_warm_light", "product_id": "c2"},
            {"category": "coat", "tone_id": "spring_warm_light", "product_id": "c3"},
        ])
        incomplete = _scored("incomplete", 82)
        result = rerank([incomplete, complete])
        # complete: 80+3=83, incomplete: 82 → complete이 위
        assert result[0]["outfit_id"] == "complete"

    def test_tone_diversity_limits_to_3(self):
        # 동일 톤 4개 중 3개만 통과
        outfits = [
            _scored("a", 90, tone_id="spring_warm_light"),
            _scored("b", 85, tone_id="spring_warm_light"),
            _scored("c", 80, tone_id="spring_warm_light"),
            _scored("d", 75, tone_id="spring_warm_light"),
        ]
        result = rerank(outfits)
        assert len(result) == 3
        assert result[-1]["outfit_id"] == "c"

    def test_main_item_dedup(self):
        # 같은 메인아이템 product_id → 1개만 통과
        outfits = [
            _scored("a", 90, main_product_id="MAIN_1"),
            _scored("b", 85, main_product_id="MAIN_1"),
            _scored("c", 80, main_product_id="MAIN_2"),
        ]
        result = rerank(outfits)
        assert len(result) == 2
        ids = [o["outfit_id"] for o in result]
        assert "a" in ids
        assert "c" in ids
        assert "b" not in ids

    def test_max_results_limit(self):
        outfits = [_scored(f"o{i}", 100 - i) for i in range(300)]
        result = rerank(outfits, max_results=200)
        assert len(result) <= 200

    def test_personalization_bonus_reorders(self):
        # 개인화 보정으로 순위 역전
        low_score = _scored("liked", 75, tone_id="spring_warm_light")
        low_score["items"][0]["brand"] = "무신사 스탠다드"
        high_score = _scored("neutral", 80, tone_id="winter_cool_deep")
        result = rerank(
            [high_score, low_score],
            preferred_tones=["spring_warm_light"],
            preferred_brands=["무신사 스탠다드"],
        )
        # liked: 75 + 4.0(tone) + 1.5(brand) = 80.5 > neutral: 80
        assert result[0]["outfit_id"] == "liked"

    def test_total_reranked_stored(self):
        outfits = [_scored("a", 80)]
        result = rerank(outfits)
        assert "total_reranked" in result[0]["scores"]

    def test_empty_input(self):
        assert rerank([]) == []

    def test_diverse_tones_all_pass(self):
        outfits = [
            _scored("a", 90, tone_id="spring_warm_light"),
            _scored("b", 85, tone_id="summer_cool_soft"),
            _scored("c", 80, tone_id="autumn_warm_deep"),
            _scored("d", 75, tone_id="winter_cool_bright"),
        ]
        result = rerank(outfits)
        assert len(result) == 4
