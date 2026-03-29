"""
Task 1.11 — 규칙 기반 코디 품질 평가
기획서 H6: 5점 척도 평가, 3점 미만 제거

평가 기준 (규칙 기반):
  5점: 완벽한 스타일 조화, TPO 완전 적합, 실용적
  4점: 좋은 조화, 약간의 개선 여지
  3점: 무난함, 착용 가능한 수준
  2점: 어색한 조합 또는 TPO 부적합
  1점: 명백히 부조화

사용법:
  python evaluate_outfits.py          # 전체 실행
  python evaluate_outfits.py --dry    # 평가만, 저장 안 함
"""

import json
import sys
import argparse
from pathlib import Path
from collections import defaultdict

BASE_DIR   = Path(__file__).parent.parent
DATA_DIR   = BASE_DIR / "data"
OUTFITS_FILE    = DATA_DIR / "outfits.json"
NORMALIZED_FILE = DATA_DIR / "normalized" / "normalized_products.json"
OUTPUT_FILE     = DATA_DIR / "outfits.json"

MIN_SCORE = 3

# 카테고리 → major 그룹
CATEGORY_MAJOR = {
    "tshirt": "top", "knit": "top", "shirt": "top", "blouse": "top",
    "cardigan": "top", "hoodie": "top", "crop_top": "top", "turtleneck": "top",
    "slacks": "bottom", "jeans": "bottom", "skirt": "bottom",
    "mini_skirt": "bottom", "leggings": "bottom",
    "jacket": "outer", "coat": "outer", "trench_coat": "outer",
    "padding": "outer", "jumper": "outer",
    "onepiece": "onepiece",
    "loafer": "shoes", "sneakers": "shoes", "boots": "shoes",
    "heels": "shoes", "sandals": "shoes", "flats": "shoes",
    "tote_bag": "bag", "cross_bag": "bag", "shoulder_bag": "bag", "clutch": "bag",
    "earrings": "acc", "belt": "acc",
}

# TPO별 필수 아이템 기대 구성 (충족 시 보너스)
TPO_BONUS_CATS = {
    "interview": {"shoes": ["loafer", "heels"], "outer": ["jacket"]},
    "commute":   {"shoes": ["loafer"], "bag": ["tote_bag"]},
    "date":      {"shoes": ["heels", "loafer", "flats"]},
    "event":     {"shoes": ["heels", "loafer"], "bag": ["clutch"]},
    "weekend":   {"shoes": ["sneakers"]},
    "campus":    {"shoes": ["sneakers"]},
    "travel":    {"shoes": ["sneakers", "sandals"]},
    "workout":   {"shoes": ["sneakers"]},
}

# TPO별 패널티 아이템 (있으면 감점)
TPO_PENALTY_CATS = {
    "interview": ["sneakers", "hoodie", "crop_top", "leggings", "padding"],
    "commute":   ["crop_top", "leggings", "hoodie"],
    "event":     ["sneakers", "hoodie", "tshirt", "shoulder_bag"],
    "workout":   ["heels", "loafer", "clutch", "blouse", "coat", "jacket"],
    "date":      ["padding", "hoodie"],
    "campus":    ["heels", "clutch", "coat", "jacket"],
}


def rule_score(outfit: dict, product_map: dict) -> int:
    """
    규칙 기반 품질 점수 (1~5)

    채점 기준:
    - 기본 2점에서 시작
    - 아이템 완성도 (top+bottom 또는 onepiece) → +1
    - 신발 포함 → +0.5
    - 가방 포함 → +0.3
    - TPO 보너스 아이템 → +0.5
    - TPO 패널티 아이템 → -1
    - 포멀도 편차 0~1 → +0.5, 편차 >2 → -1
    - 아이템 수 2개 이하 → -0.5
    - 최종 반올림 후 1~5 클리핑
    """
    item_ids = outfit.get("item_ids", [])
    items = [product_map[pid] for pid in item_ids if pid in product_map]

    if not items:
        return 2

    categories = [p.get("category", "") for p in items]
    majors = {CATEGORY_MAJOR.get(c, "") for c in categories}
    tpo = outfit.get("designed_tpo", "")

    score = 2.0

    # 완성도: 상하의 또는 원피스
    has_body = ("top" in majors and "bottom" in majors) or "onepiece" in majors
    if has_body:
        score += 1.0

    # 신발/가방
    if "shoes" in majors:
        score += 0.5
    if "bag" in majors:
        score += 0.3

    # 아이템 수 페널티 (2개 이하면 미완성)
    if len(items) <= 2:
        score -= 0.5

    # TPO 보너스
    bonus_map = TPO_BONUS_CATS.get(tpo, {})
    for major, good_cats in bonus_map.items():
        if any(c in categories for c in good_cats):
            score += 0.5
            break  # 보너스는 한 번만

    # TPO 패널티
    penalty_cats = TPO_PENALTY_CATS.get(tpo, [])
    if any(c in penalty_cats for c in categories):
        score -= 1.0

    # 포멀도 편차
    formalities = [p.get("formality", 3) for p in items]
    deviation = max(formalities) - min(formalities)
    if deviation <= 1:
        score += 0.5
    elif deviation > 2:
        score -= 1.0

    return max(1, min(5, round(score)))


def main():
    parser = argparse.ArgumentParser(description="Task 1.11 - 규칙 기반 코디 품질 평가")
    parser.add_argument("--dry", action="store_true", help="평가만, 저장 안 함")
    args = parser.parse_args()

    print("=" * 60)
    print("Task 1.11 - 규칙 기반 코디 품질 평가")
    print("=" * 60)

    print("\n[1/3] 데이터 로드 중...")
    with open(OUTFITS_FILE, encoding="utf-8") as f:
        outfits = json.load(f)
    with open(NORMALIZED_FILE, encoding="utf-8") as f:
        products = json.load(f)

    product_map = {p["product_id"]: p for p in products}
    print(f"  -> 코디: {len(outfits):,}개")
    print(f"  -> 상품: {len(products):,}개")

    print("\n[2/3] 규칙 기반 품질 평가 중...")
    score_dist = defaultdict(int)

    for outfit in outfits:
        score = rule_score(outfit, product_map)
        outfit["llm_quality_score"] = score
        score_dist[score] += 1

    # 3점 미만 제거
    before = len(outfits)
    if not args.dry:
        passed = [o for o in outfits if o.get("llm_quality_score", 0) >= MIN_SCORE]
        removed = before - len(passed)
    else:
        passed = outfits
        removed = sum(1 for o in outfits if o.get("llm_quality_score", 0) < MIN_SCORE)

    if not args.dry:
        print(f"\n[3/3] 결과 저장 중...")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(passed, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print("완료!")
    print("=" * 60)
    print(f"  전체 평가: {before:,}개")
    print(f"  3점 미만 제거: {removed:,}개")
    print(f"  최종 통과: {before - removed:,}/{before:,}개")

    print(f"\n  [점수 분포]")
    for s in range(5, 0, -1):
        cnt = score_dist.get(s, 0)
        bar = "█" * (cnt // 5) if cnt > 0 else ""
        print(f"    {s}점: {cnt:4}개  {bar}")

    if not args.dry:
        print(f"\n  저장 위치: {OUTPUT_FILE}")
    else:
        print(f"\n  드라이런 완료 (파일 변경 없음)")


if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    main()
