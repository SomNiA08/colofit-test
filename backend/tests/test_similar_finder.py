"""
Task 3.1 — 유사 상품 매칭 서비스 테스트.

실행: cd backend && venv/Scripts/activate && pytest tests/test_similar_finder.py -v
"""

import math
import pytest

from app.services.similar_finder import (
    ProductInfo,
    SimilarResult,
    find_similar,
    _hex_to_rgb,
    _color_similarity,
    _price_similarity,
    _normalize_name,
    _is_exact,
)


# ── 픽스처 ────────────────────────────────────────────────────────────────────

@pytest.fixture
def base_product() -> ProductInfo:
    return ProductInfo(
        id="P001",
        name="오버핏 화이트 셔츠",
        brand="무신사스탠다드",
        category="top",
        color_hex="#FFFFFF",
        price=39000,
        mall_name="무신사",
    )


@pytest.fixture
def candidates() -> list[ProductInfo]:
    return [
        # Exact: 동일 이름 + 동일 브랜드, 다른 판매처
        ProductInfo(
            id="P002",
            name="오버핏 화이트 셔츠",
            brand="무신사스탠다드",
            category="top",
            color_hex="#FAFAFA",
            price=37000,
            mall_name="29CM",
        ),
        # Similar: 동일 카테고리, 비슷한 색상, 비슷한 가격
        ProductInfo(
            id="P003",
            name="루즈핏 면 셔츠",
            brand="에잇세컨즈",
            category="top",
            color_hex="#F5F5F0",
            price=35000,
            mall_name="W컨셉",
        ),
        # Similar: 색상 완전히 다름 (검정)
        ProductInfo(
            id="P004",
            name="블랙 슬림 셔츠",
            brand="자라",
            category="top",
            color_hex="#000000",
            price=45000,
            mall_name="자라",
        ),
        # Similar: 가격 크게 다름
        ProductInfo(
            id="P005",
            name="프리미엄 화이트 셔츠",
            brand="아크네",
            category="top",
            color_hex="#FFFDF9",
            price=320000,
            mall_name="아크네",
        ),
        # base 자신과 동일 id → 제외 대상
        ProductInfo(
            id="P001",
            name="오버핏 화이트 셔츠",
            brand="무신사스탠다드",
            category="top",
            color_hex="#FFFFFF",
            price=39000,
            mall_name="무신사",
        ),
    ]


# ── _hex_to_rgb 테스트 ────────────────────────────────────────────────────────

class TestHexToRgb:
    def test_with_hash(self):
        assert _hex_to_rgb("#FFFFFF") == (255, 255, 255)

    def test_without_hash(self):
        assert _hex_to_rgb("000000") == (0, 0, 0)

    def test_mixed_case(self):
        assert _hex_to_rgb("#ff6600") == (255, 102, 0)

    def test_invalid_length(self):
        assert _hex_to_rgb("#FFF") is None

    def test_invalid_chars(self):
        assert _hex_to_rgb("#ZZZZZZ") is None

    def test_none_input(self):
        assert _hex_to_rgb(None) is None  # type: ignore[arg-type]


# ── _color_similarity 테스트 ──────────────────────────────────────────────────

class TestColorSimilarity:
    def test_identical_colors(self):
        assert _color_similarity("#FFFFFF", "#FFFFFF") == pytest.approx(1.0)

    def test_max_distance(self):
        # 흰색 vs 검정 → 거리 441.67 → 유사도 0.0
        sim = _color_similarity("#FFFFFF", "#000000")
        assert sim == pytest.approx(0.0, abs=1e-2)

    def test_near_white(self):
        # 거의 같은 흰색 계열
        sim = _color_similarity("#FFFFFF", "#FAFAFA")
        assert sim > 0.97

    def test_none_returns_neutral(self):
        assert _color_similarity(None, "#FFFFFF") == pytest.approx(0.5)
        assert _color_similarity("#FFFFFF", None) == pytest.approx(0.5)
        assert _color_similarity(None, None) == pytest.approx(0.5)

    def test_range_0_to_1(self):
        sim = _color_similarity("#FF0000", "#00FF00")
        assert 0.0 <= sim <= 1.0


# ── _price_similarity 테스트 ─────────────────────────────────────────────────

class TestPriceSimilarity:
    def test_identical_price(self):
        assert _price_similarity(39000, 39000) == pytest.approx(1.0)

    def test_half_price(self):
        # 한쪽이 다른 쪽의 절반
        assert _price_similarity(20000, 40000) == pytest.approx(0.5)

    def test_symmetry(self):
        assert _price_similarity(30000, 50000) == pytest.approx(
            _price_similarity(50000, 30000)
        )

    def test_zero_price_returns_neutral(self):
        assert _price_similarity(0, 39000) == pytest.approx(0.5)
        assert _price_similarity(39000, 0) == pytest.approx(0.5)

    def test_none_returns_neutral(self):
        assert _price_similarity(None, 39000) == pytest.approx(0.5)  # type: ignore[arg-type]
        assert _price_similarity(39000, None) == pytest.approx(0.5)  # type: ignore[arg-type]

    def test_range_0_to_1(self):
        sim = _price_similarity(10000, 1000000)
        assert 0.0 <= sim <= 1.0


# ── _normalize_name 테스트 ────────────────────────────────────────────────────

class TestNormalizeName:
    def test_same_name(self):
        assert _normalize_name("오버핏 화이트 셔츠") == _normalize_name("오버핏 화이트 셔츠")

    def test_strips_whitespace(self):
        assert _normalize_name("오버핏  화이트") == _normalize_name("오버핏 화이트")

    def test_case_insensitive(self):
        assert _normalize_name("White Shirt") == _normalize_name("white shirt")

    def test_removes_hyphens(self):
        assert _normalize_name("오버-핏셔츠") == _normalize_name("오버핏셔츠")

    def test_none_returns_empty(self):
        assert _normalize_name(None) == ""


# ── _is_exact 테스트 ──────────────────────────────────────────────────────────

class TestIsExact:
    def test_exact_match(self, base_product, candidates):
        # P002: 동일 이름 + 동일 브랜드
        assert _is_exact(base_product, candidates[0]) is True

    def test_different_brand(self, base_product, candidates):
        # P003: 다른 이름 + 다른 브랜드
        assert _is_exact(base_product, candidates[1]) is False

    def test_missing_name(self, base_product):
        candidate = ProductInfo(
            id="P099",
            name=None,
            brand="무신사스탠다드",
            category="top",
            color_hex="#FFFFFF",
            price=39000,
        )
        assert _is_exact(base_product, candidate) is False

    def test_missing_brand(self, base_product):
        candidate = ProductInfo(
            id="P099",
            name="오버핏 화이트 셔츠",
            brand=None,
            category="top",
            color_hex="#FFFFFF",
            price=39000,
        )
        assert _is_exact(base_product, candidate) is False


# ── find_similar 통합 테스트 ──────────────────────────────────────────────────

class TestFindSimilar:
    def test_excludes_self(self, base_product, candidates):
        results = find_similar(base_product, candidates)
        ids = [r.product.id for r in results]
        assert "P001" not in ids

    def test_returns_at_most_top_n(self, base_product, candidates):
        results = find_similar(base_product, candidates, top_n=3)
        assert len(results) <= 3

    def test_default_top_5(self, base_product, candidates):
        results = find_similar(base_product, candidates)
        # candidates에 base 자신 제외하면 4개 → 최대 4개
        assert len(results) <= 5

    def test_sorted_by_similarity_desc(self, base_product, candidates):
        results = find_similar(base_product, candidates)
        sims = [r.similarity for r in results]
        assert sims == sorted(sims, reverse=True)

    def test_exact_match_detected(self, base_product, candidates):
        results = find_similar(base_product, candidates)
        exact_results = [r for r in results if r.match_type == "exact"]
        assert len(exact_results) == 1
        assert exact_results[0].product.id == "P002"

    def test_similar_match_detected(self, base_product, candidates):
        results = find_similar(base_product, candidates)
        similar_results = [r for r in results if r.match_type == "similar"]
        assert len(similar_results) >= 1

    def test_similarity_range(self, base_product, candidates):
        results = find_similar(base_product, candidates)
        for r in results:
            assert 0.0 <= r.similarity <= 1.0
            assert 0.0 <= r.color_similarity <= 1.0
            assert 0.0 <= r.price_similarity <= 1.0

    def test_score_formula(self, base_product):
        """total = color×0.6 + price×0.4 공식 검증."""
        candidate = ProductInfo(
            id="P010",
            name="테스트 상품",
            brand="브랜드A",
            category="top",
            color_hex="#FAFAFA",   # 흰색에 가까움
            price=39000,           # 동일 가격
        )
        results = find_similar(base_product, [candidate])
        assert len(results) == 1
        r = results[0]

        expected = r.color_similarity * 0.6 + r.price_similarity * 0.4
        assert r.similarity == pytest.approx(expected, abs=1e-4)

    def test_empty_candidates(self, base_product):
        results = find_similar(base_product, [])
        assert results == []

    def test_only_self_in_candidates(self, base_product):
        results = find_similar(base_product, [base_product])
        assert results == []

    def test_near_white_higher_than_black(self, base_product, candidates):
        """흰색 기준 상품 → 유사 흰색이 검정보다 높은 유사도."""
        results = find_similar(base_product, candidates)
        id_order = [r.product.id for r in results]
        # P003(흰색 계열)이 P004(검정)보다 앞에 있어야 함
        assert id_order.index("P003") < id_order.index("P004")
