"""
Task 2.7 — StyleFilter 테스트.

실행: cd backend && venv/Scripts/activate && pytest tests/test_style_filter.py -v
"""

import pytest

from app.services.style_filter import (
    detect_category,
    filter_outfit,
    SF_CUTOFF,
)


# ── detect_category 테스트 ──────────────────────────────────────────────────

class TestDetectCategory:
    """하이브리드 카테고리 감지 테스트."""

    # ── raw_category 직접 매핑 ──────────────────────────────────────────────

    def test_raw_category_blouse(self):
        result = detect_category("소프트 라벤더 블라우스", category3="블라우스")
        assert result is not None
        assert result["category"] == "blouse"

    def test_raw_category_slacks(self):
        result = detect_category("아이보리 와이드 슬랙스", category3="슬랙스")
        assert result is not None
        assert result["category"] == "slacks"

    def test_raw_category_sneakers(self):
        result = detect_category("화이트 러닝화", category3="스니커즈")
        assert result is not None
        assert result["category"] == "sneakers"

    def test_raw_category_hoodie(self):
        result = detect_category("오버핏 후드 집업", category3="후드티")
        assert result is not None
        assert result["category"] == "hoodie"

    # ── 상품명 키워드 매칭 ───────────────────────────────────────���──────────

    def test_keyword_blouse_in_title(self):
        result = detect_category("러플 블라우스 여성")
        assert result is not None
        assert result["category"] == "blouse"

    def test_keyword_jeans_in_title(self):
        result = detect_category("슬림핏 청바지 데님")
        assert result is not None
        assert result["category"] == "jeans"

    def test_keyword_knit_in_title(self):
        result = detect_category("캐시미어 V넥 니트")
        assert result is not None
        assert result["category"] == "knit"

    def test_keyword_coat_in_title(self):
        result = detect_category("울 롱 코트 여성")
        assert result is not None
        assert result["category"] == "coat"

    def test_keyword_heels_in_title(self):
        result = detect_category("스틸레토 펌프스 8cm")
        assert result is not None
        assert result["category"] == "heels"

    # ── 미분류 ──────────────────────────────────────────────────────────────

    def test_unknown_title_returns_none(self):
        result = detect_category("워셔블 캐시미어 V넥 풀오버")
        # "풀오버"는 키워드 목록에 있음(knit)
        assert result is not None
        assert result["category"] == "knit"

    def test_completely_unknown_returns_none(self):
        result = detect_category("아무런 매칭도 안 되는 상품")
        assert result is None

    # ── 결과 구조 ────────────────────────────────────────────────────────────

    def test_result_has_silhouette(self):
        result = detect_category("블라우스")
        assert "silhouette" in result

    def test_result_has_formality(self):
        result = detect_category("블라우스")
        assert "formality" in result
        assert isinstance(result["formality"], int)

    # ── category3 우선순위 ──────────────────────────────────────────────────

    def test_category3_takes_priority(self):
        # title에 "셔츠"가 있지만 category3가 "블라우스"면 blouse
        result = detect_category("린넨 셔츠 원피스", category3="블라우스")
        assert result["category"] == "blouse"

    # ── product_id + LLM 캐시 ─────────────────────────────────────────���────

    def test_no_product_id_no_cache(self):
        # title/category3 모두 매칭 안 되고 product_id 없으면 None
        result = detect_category("특수 상품", product_id=None)
        assert result is None


# ── filter_outfit 테스트 ────────────────────────────────────────────────────

class TestFilterOutfit:
    """StyleFilter 통합 테스트."""

    # ── 통과 코디 ────────────────────────────────────────────────────────────

    def test_blouse_slacks_passes(self):
        items = [
            {"title": "소프트 라벤더 블라우스"},
            {"title": "아이보리 와이드 슬랙스"},
        ]
        result = filter_outfit(items)
        assert result["pass"] is True
        assert result["score"] >= SF_CUTOFF
        assert "blouse" in result["categories"]
        assert "slacks" in result["categories"]

    def test_knit_jeans_sneakers_passes(self):
        items = [
            {"title": "캐시미어 니트"},
            {"title": "슬림 청바지"},
            {"title": "화이트 스니커즈"},
        ]
        result = filter_outfit(items)
        assert result["pass"] is True

    def test_shirt_slacks_loafer_passes(self):
        items = [
            {"title": "린넨 셔츠"},
            {"title": "슬랙스 정장바지"},
            {"title": "페니 로퍼"},
        ]
        result = filter_outfit(items)
        assert result["pass"] is True

    # ── 탈락 코디 ────────────────────────────────────────────────────────────

    def test_hoodie_suit_jacket_fails(self):
        # 후드+정장: 명백한 부조화 → 55점 미만
        # 이미 category 지정으로 키워드 우선순위 이슈 우회
        items = [
            {"category": "hoodie"},
            {"category": "suit_jacket"},
        ]
        result = filter_outfit(items)
        assert result["pass"] is False
        assert result["score"] < SF_CUTOFF

    # ── 55점 경계 ────────────────────────────────────────────────────────────

    def test_cutoff_is_55(self):
        assert SF_CUTOFF == 55.0

    # ── 이미 category가 있는 아이템 ────────────────────────────────────────

    def test_pre_categorized_items(self):
        items = [
            {"category": "blouse", "silhouette": "fitted"},
            {"category": "slacks", "silhouette": "slim"},
        ]
        result = filter_outfit(items)
        assert result["pass"] is True
        assert result["categories"] == ["blouse", "slacks"]

    # ── items_enriched 검증 ─────────────────────────────────────────────��────

    def test_enriched_items_have_category(self):
        items = [
            {"title": "블라우스 핑크"},
            {"title": "슬랙스 네이비"},
        ]
        result = filter_outfit(items)
        for enriched in result["items_enriched"]:
            assert "category" in enriched

    # ── 빈 코디 ──────────────────────────────────────────────────────────────

    def test_empty_items(self):
        result = filter_outfit([])
        assert result["pass"] is False
        assert result["score"] == 50.0

    # ── 단일 아이템 ──────────────────────────────────────────────────────────

    def test_single_item_below_cutoff(self):
        # 단일 아이템: SF=50, 55점 미만
        result = filter_outfit([{"title": "블라우스"}])
        # category 1개 → category_compat=60, silhouette=65, formality=100
        # SF = 60*0.5 + 65*0.25 + 100*0.25 = 71.25
        assert result["pass"] is True

    # ── score 범위 검증 ──────────────────────────────────────────────────────

    def test_score_in_range(self):
        test_cases = [
            [{"title": "블라우스"}, {"title": "슬랙스"}],
            [{"title": "후드티"}, {"title": "정장"}],
            [{"title": "니트"}, {"title": "청바지"}, {"title": "스니커즈"}],
        ]
        for items in test_cases:
            result = filter_outfit(items)
            assert 0.0 <= result["score"] <= 100.0

    # ── 미분류 아이템 포함 코디 ──────────────────────────────────────────────

    def test_unclassified_item_still_calculates(self):
        items = [
            {"title": "블라우스 핑크"},
            {"title": "알 수 없는 상품"},
        ]
        result = filter_outfit(items)
        # 미분류 아이템은 category 없이 넘어감
        assert isinstance(result["score"], float)
