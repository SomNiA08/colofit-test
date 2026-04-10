"""
Task 3.1 — 유사 상품 매칭 서비스.

기준 상품과 색상·가격이 유사한 대안 상품을 찾아 반환한다.
- Exact: 동일 상품명(정규화) + 동일 브랜드 → 다른 판매처
- Similar: 동일 카테고리·유사 색상·유사 가격대 대체재

참조: 기획서 §6.2
"""

import math
import re
import unicodedata
from dataclasses import dataclass


# ── 상수 ──────────────────────────────────────────────────────────────────────

# RGB 유클리드 거리 최대값: sqrt(255²+255²+255²) ≈ 441.67
_RGB_MAX = 441.67

_COLOR_WEIGHT = 0.6
_PRICE_WEIGHT = 0.4

_TOP_N = 5


# ── 데이터 구조 ───────────────────────────────────────────────────────────────

@dataclass
class ProductInfo:
    """유사도 계산에 필요한 상품 정보."""
    id: str
    name: str | None
    brand: str | None
    category: str | None
    color_hex: str | None    # '#RRGGBB' 또는 'RRGGBB'
    price: int | None
    mall_name: str | None = None
    mall_url: str | None = None
    image_url: str | None = None


@dataclass
class SimilarResult:
    """유사 상품 매칭 결과 1건."""
    product: ProductInfo
    similarity: float          # 0.0 ~ 1.0
    match_type: str            # "exact" | "similar"
    color_similarity: float
    price_similarity: float


# ── 내부 헬퍼 ─────────────────────────────────────────────────────────────────

def _hex_to_rgb(hex_color: str | None) -> tuple[int, int, int] | None:
    """'#RRGGBB' 또는 'RRGGBB' → (R, G, B). 파싱 실패 시 None."""
    if hex_color is None:
        return None
    h = hex_color.strip().lstrip("#")
    if len(h) != 6:
        return None
    try:
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except ValueError:
        return None


def _color_similarity(hex1: str | None, hex2: str | None) -> float:
    """
    두 HEX 색상 간 색상 유사도 (0.0~1.0).

    color_similarity = 1.0 - euclidean_distance(rgb1, rgb2) / 441.67

    어느 한쪽이 None이면 0.5(중립) 반환.
    """
    if not hex1 or not hex2:
        return 0.5

    rgb1 = _hex_to_rgb(hex1)
    rgb2 = _hex_to_rgb(hex2)

    if rgb1 is None or rgb2 is None:
        return 0.5

    r1, g1, b1 = rgb1
    r2, g2, b2 = rgb2
    distance = math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)
    return 1.0 - distance / _RGB_MAX


def _price_similarity(price1: int | None, price2: int | None) -> float:
    """
    두 가격 간 가격 유사도 (0.0~1.0).

    price_similarity = min(p1, p2) / max(p1, p2)

    어느 한쪽이 0 이하이거나 None이면 0.5(중립) 반환.
    """
    if not price1 or not price2 or price1 <= 0 or price2 <= 0:
        return 0.5
    return min(price1, price2) / max(price1, price2)


def _normalize_name(name: str | None) -> str:
    """
    상품명 정규화: 소문자 + NFC 정규화 + 공백/특수문자 제거.
    Exact 판별에 사용한다.
    """
    if not name:
        return ""
    normalized = unicodedata.normalize("NFC", name).lower()
    return re.sub(r"[\s\-_/·()\[\]]+", "", normalized)


def _is_exact(base: ProductInfo, candidate: ProductInfo) -> bool:
    """
    동일 상품명(정규화) + 동일 브랜드이면 Exact (다른 판매처).
    이름 또는 브랜드 중 하나라도 없으면 False.
    """
    if not base.name or not candidate.name:
        return False
    if not base.brand or not candidate.brand:
        return False
    name_match = _normalize_name(base.name) == _normalize_name(candidate.name)
    brand_match = base.brand.strip().lower() == candidate.brand.strip().lower()
    return name_match and brand_match


# ── 퍼블릭 API ────────────────────────────────────────────────────────────────

def find_similar(
    base: ProductInfo,
    candidates: list[ProductInfo],
    top_n: int = _TOP_N,
) -> list[SimilarResult]:
    """
    기준 상품(base)과 유사한 상품을 candidates에서 찾아 반환한다.

    Args:
        base: 기준 상품
        candidates: 후보 상품 풀 (동일 카테고리 필터링은 호출부에서 해도 되고
                    여기서 해도 됨 — 이 함수는 candidates를 그대로 사용)
        top_n: 반환할 최대 건수 (기본 5)

    Returns:
        유사도 내림차순 정렬된 SimilarResult 리스트 (최대 top_n개).
        base 자신(id 동일)은 제외된다.

    Scoring:
        total_similarity = color_similarity × 0.6 + price_similarity × 0.4
    """
    results: list[SimilarResult] = []

    for candidate in candidates:
        # 자기 자신 제외
        if candidate.id == base.id:
            continue

        col_sim = _color_similarity(base.color_hex, candidate.color_hex)
        pri_sim = _price_similarity(base.price, candidate.price)
        total = col_sim * _COLOR_WEIGHT + pri_sim * _PRICE_WEIGHT

        match_type = "exact" if _is_exact(base, candidate) else "similar"

        results.append(
            SimilarResult(
                product=candidate,
                similarity=round(total, 4),
                match_type=match_type,
                color_similarity=round(col_sim, 4),
                price_similarity=round(pri_sim, 4),
            )
        )

    # 유사도 내림차순, 동점이면 Exact 우선
    results.sort(key=lambda r: (r.similarity, r.match_type == "exact"), reverse=True)
    return results[:top_n]
