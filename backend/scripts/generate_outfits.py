"""
Task 1.10 — 코디 조합 생성 알고리즘
기획서 섹션 5.3.1 의사코드 기반 구현

레시피 기반 의도적 설계 생성:
  for each gender in [female, male]:
    for each tone in 12_tones:
      for each recipe (tpo) in recipes[gender]:
        1. 필수 카테고리 선택 (OR 그룹에서 1개씩)
        2. 선택 카테고리 확률적 추가
        3. 금지 카테고리 검증
        4. 포멀도 편차 ≤ 2 검증
        5. 가격 비율 5배 이내 검증
        6. 중복 조합 방지
        7. designed_tpo / designed_moods 태그 부여

목표: 2(성별) × 12(톤) × 8(TPO) × 8~10(코디) = 1,500~1,900개

사용법:
  python generate_outfits.py          # 전체 실행
  python generate_outfits.py --stats  # 상품 풀 통계만 출력
"""

import json
import hashlib
import random
import sys
import argparse
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
NORMALIZED_FILE = DATA_DIR / "normalized" / "normalized_products.json"
RECIPES_FILE    = DATA_DIR / "outfit_recipes.json"
OUTPUT_FILE     = DATA_DIR / "outfits.json"

# 목표 코디 수 per (gender × tone × tpo)
TARGET_PER_SLOT = 9       # 8~10 중간값
MAX_ATTEMPTS    = 300     # 슬롯당 최대 시도 횟수

# 선택 카테고리 추가 확률
OPTIONAL_PROB = {
    # major category → 추가 확률
    "shoes":    0.70,
    "bag":      0.50,
    "outer":    0.30,
    "acc":      0.25,
    "top":      0.20,
    "bottom":   0.20,
    "onepiece": 0.20,
}

TONES = [
    "spring_warm_light", "spring_warm_bright", "spring_warm_mute",
    "summer_cool_light", "summer_cool_soft",   "summer_cool_mute",
    "autumn_warm_bright","autumn_warm_deep",    "autumn_warm_mute",
    "winter_cool_light", "winter_cool_bright",  "winter_cool_deep",
]

# 카테고리 → major 매핑
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


def outfit_id(item_ids: list[str]) -> str:
    """상품 ID 집합으로 고유 코디 ID 생성"""
    key = ",".join(sorted(item_ids))
    return "outfit_" + hashlib.md5(key.encode()).hexdigest()[:12]


def build_product_pool(products: list[dict]) -> dict:
    """
    product_pool[(gender, tone, category)] = [product, ...]
    - female 풀: gender=="female" OR gender=="unisex"
    - male 풀:   gender=="male"  OR gender=="unisex"
    """
    pool = defaultdict(list)
    for p in products:
        if not p.get("category") or not p.get("source_tone_id"):
            continue
        cat    = p["category"]
        tone   = p["source_tone_id"]
        gender = p.get("gender", "unisex")
        price  = p.get("price", 0)
        if not price:
            continue

        if gender in ("female", "unisex"):
            pool[("female", tone, cat)].append(p)
        if gender in ("male", "unisex"):
            pool[("male", tone, cat)].append(p)

    return pool


def pick_item(pool: dict, gender: str, tone: str, category: str,
              used_ids: set, formality_range: list[int]) -> dict | None:
    """
    풀에서 조건에 맞는 아이템 랜덤 선택
    - 이미 사용된 product_id 제외
    - 포멀도 범위 내
    """
    candidates = pool.get((gender, tone, category), [])
    if not candidates:
        return None

    random.shuffle(candidates)
    fmin, fmax = formality_range
    for p in candidates:
        if p["product_id"] in used_ids:
            continue
        formality = p.get("formality", 3)
        if fmin <= formality <= fmax:
            return p
    # 포멀도 조건 완화 (±1)
    for p in candidates:
        if p["product_id"] in used_ids:
            continue
        formality = p.get("formality", 3)
        if (fmin - 1) <= formality <= (fmax + 1):
            return p
    return None


def validate_outfit(items: list[dict], recipe: dict) -> bool:
    """
    코디 유효성 검증
    1. 금지 카테고리 없음
    2. 포멀도 편차 ≤ 2
    3. 가격 비율 ≤ 5
    """
    categories = [p["category"] for p in items]
    forbidden  = set(recipe["forbidden"])

    # 금지 카테고리 검증
    if any(c in forbidden for c in categories):
        return False

    # 포멀도 편차 검증
    formalities = [p.get("formality", 3) for p in items]
    if max(formalities) - min(formalities) > 2:
        return False

    # 가격 비율 검증
    prices = [p.get("price", 1) for p in items if p.get("price", 0) > 0]
    if len(prices) >= 2 and max(prices) / min(prices) > 5:
        return False

    return True


def generate_outfit(recipe: dict, gender: str, tone: str,
                    pool: dict, used_combos: set) -> dict | None:
    """
    단일 코디 조합 생성 시도
    성공 시 outfit dict 반환, 실패 시 None
    """
    items        = []
    used_ids     = set()
    form_range   = recipe["formality_range"]
    forbidden    = set(recipe["forbidden"])

    # 1단계: 필수 카테고리 선택 (OR 그룹에서 1개씩)
    for or_group in recipe["required"]:
        random.shuffle(or_group)
        selected = None
        for cat in or_group:
            if cat in forbidden:
                continue
            item = pick_item(pool, gender, tone, cat, used_ids, form_range)
            if item:
                selected = item
                break
        if not selected:
            return None
        items.append(selected)
        used_ids.add(selected["product_id"])

    # 2단계: 선택 카테고리 확률적 추가
    already_majors = {CATEGORY_MAJOR.get(p["category"], "") for p in items}
    optional = list(recipe["optional"])
    random.shuffle(optional)
    for cat in optional:
        if cat in forbidden:
            continue
        major = CATEGORY_MAJOR.get(cat, "")
        # 같은 major 이미 있으면 스킵 (아우터 제외 — 겹쳐입기 가능)
        if major != "outer" and major in already_majors:
            continue
        prob = OPTIONAL_PROB.get(major, 0.25)
        if random.random() < prob:
            item = pick_item(pool, gender, tone, cat, used_ids, form_range)
            if item:
                items.append(item)
                used_ids.add(item["product_id"])
                already_majors.add(major)

    # 3단계: 유효성 검증
    if not validate_outfit(items, recipe):
        return None

    # 중복 조합 검증
    combo_key = frozenset(p["product_id"] for p in items)
    if combo_key in used_combos:
        return None

    # 코디 객체 생성
    item_ids    = [p["product_id"] for p in items]
    total_price = sum(p.get("price", 0) for p in items)
    tags        = [tone, recipe["tpo"]] + recipe["moods"]

    return {
        "id":             outfit_id(item_ids),
        "item_ids":       item_ids,
        "gender":         gender,
        "source_tone_id": tone,
        "designed_tpo":   recipe["tpo"],
        "designed_moods": recipe["moods"],
        "total_price":    total_price,
        "is_complete_outfit": True,
        "tags":           list(set(tags)),
        "scores":         None,   # Task 1.10 이후 스코어링에서 채움
        "llm_quality_score": None,  # Task 1.11에서 채움
    }


def main():
    parser = argparse.ArgumentParser(description="Task 1.10 - 코디 조합 생성")
    parser.add_argument("--stats", action="store_true", help="상품 풀 통계만 출력")
    parser.add_argument("--seed",  type=int, default=42, help="랜덤 시드")
    args = parser.parse_args()

    random.seed(args.seed)

    print("=" * 60)
    print("Task 1.10 — 코디 조합 생성 알고리즘")
    print("=" * 60)

    # 데이터 로드
    print("\n[1/4] 데이터 로드 중...")
    with open(NORMALIZED_FILE, encoding="utf-8") as f:
        products = json.load(f)
    with open(RECIPES_FILE, encoding="utf-8") as f:
        recipes_data = json.load(f)

    print(f"  -> 상품: {len(products):,}개")
    print(f"  -> 레시피: {len(recipes_data['female'])+len(recipes_data['male'])}개")

    # 상품 풀 구성
    print("\n[2/4] 상품 풀 구성 중...")
    pool = build_product_pool(products)
    print(f"  -> 풀 슬롯 수: {len(pool):,}개 (gender×tone×category)")

    if args.stats:
        print("\n[상품 풀 통계]")
        key_cats = ["blouse", "shirt", "knit", "slacks", "skirt", "onepiece",
                    "jeans", "jacket", "loafer", "sneakers", "heels", "cross_bag"]
        for gender in ["female", "male"]:
            print(f"\n  [{gender}]")
            for tone in TONES:
                counts = {cat: len(pool.get((gender, tone, cat), [])) for cat in key_cats}
                total  = sum(len(pool.get((gender, tone, c), [])) for c in CATEGORY_MAJOR)
                print(f"    {tone}: 총 {total}개 | " +
                      " ".join(f"{c}:{counts[c]}" for c in key_cats if counts[c]))
        return

    # 코디 생성
    print(f"\n[3/4] 코디 생성 중... (목표: ~{2*12*8*TARGET_PER_SLOT}개)")
    print(f"  설정: 슬롯당 목표={TARGET_PER_SLOT}개, 최대시도={MAX_ATTEMPTS}회\n")

    all_outfits  = []
    used_combos  = set()
    slot_stats   = []

    for gender in ["female", "male"]:
        recipes = recipes_data[gender]
        for tone in TONES:
            for recipe in recipes:
                generated  = 0
                attempts   = 0
                while generated < TARGET_PER_SLOT and attempts < MAX_ATTEMPTS:
                    attempts += 1
                    outfit = generate_outfit(recipe, gender, tone, pool, used_combos)
                    if outfit:
                        combo_key = frozenset(outfit["item_ids"])
                        used_combos.add(combo_key)
                        all_outfits.append(outfit)
                        generated += 1

                slot_stats.append({
                    "gender": gender, "tone": tone, "tpo": recipe["tpo"],
                    "generated": generated, "attempts": attempts,
                })

        total_so_far = sum(1 for o in all_outfits if o["gender"] == gender)
        print(f"  {gender} 완료: {total_so_far}개")

    # 결과 저장
    print(f"\n[4/4] 결과 저장 중...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_outfits, f, ensure_ascii=False, indent=2)

    # 통계 출력
    total    = len(all_outfits)
    female_n = sum(1 for o in all_outfits if o["gender"] == "female")
    male_n   = sum(1 for o in all_outfits if o["gender"] == "male")

    tpo_dist = defaultdict(int)
    tone_dist = defaultdict(int)
    for o in all_outfits:
        tpo_dist[o["designed_tpo"]] += 1
        tone_dist[o["source_tone_id"]] += 1

    low_slots = [s for s in slot_stats if s["generated"] < TARGET_PER_SLOT - 2]

    print("\n" + "=" * 60)
    print("완료!")
    print("=" * 60)
    print(f"  총 코디: {total:,}개 (목표: ~{2*12*8*TARGET_PER_SLOT}개)")
    print(f"  여성: {female_n:,}개 | 남성: {male_n:,}개")

    print(f"\n  [TPO별 분포]")
    for tpo, cnt in sorted(tpo_dist.items(), key=lambda x: -x[1]):
        print(f"    {tpo:12}: {cnt}개")

    print(f"\n  [톤별 분포]")
    for tone, cnt in sorted(tone_dist.items(), key=lambda x: -x[1]):
        print(f"    {tone:25}: {cnt}개")

    if low_slots:
        print(f"\n  ⚠️ 목표 미달 슬롯 ({len(low_slots)}개):")
        for s in low_slots[:10]:
            print(f"    {s['gender']:6} | {s['tone']:25} | {s['tpo']:12} → {s['generated']}개/{TARGET_PER_SLOT}개 ({s['attempts']}회 시도)")

    print(f"\n  저장 위치: {OUTPUT_FILE}")


if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    main()
