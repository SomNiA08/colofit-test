"""
Task 1.8 — 전처리: 하이브리드 카테고리 분류
- 1단계: raw_category + 상품명 키워드 매칭 (~90%)
- 2단계: Gemini Flash 배치 분류 (나머지 ~10%)
- 분류 속성: category, silhouette, formality, tpo, gender
- 결과를 normalized_products.json에 덮어씀
- LLM 결과는 llm_cache.json에 캐싱

사용법:
  python classify_categories.py           # 전체 실행
  python classify_categories.py --test    # 50개 테스트
  python classify_categories.py --resume  # 이미 처리된 항목 건너뜀
"""

import json
import os
import sys
import time
import argparse
import re
from pathlib import Path

# ───────────────────────── 경로 설정 ─────────────────────────
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
NORMALIZED_FILE = DATA_DIR / "normalized" / "normalized_products.json"
LLM_CACHE_FILE = DATA_DIR / "llm_cache.json"

# ───────────────────────── 31개 카테고리 정의 ─────────────────────────
# 대카테고리: top, bottom, outer, onepiece, shoes, bag, acc
CATEGORIES = {
    # 상의 (top)
    "tshirt":     {"major": "top",      "silhouette": "regular",   "formality": 2, "tpo": ["casual", "weekend"]},
    "knit":       {"major": "top",      "silhouette": "oversized", "formality": 3, "tpo": ["casual", "date", "office"]},
    "shirt":      {"major": "top",      "silhouette": "regular",   "formality": 3, "tpo": ["office", "casual", "date"]},
    "blouse":     {"major": "top",      "silhouette": "regular",   "formality": 4, "tpo": ["office", "date", "wedding"]},
    "cardigan":   {"major": "top",      "silhouette": "regular",   "formality": 3, "tpo": ["casual", "date", "office"]},
    "hoodie":     {"major": "top",      "silhouette": "oversized", "formality": 1, "tpo": ["casual", "weekend", "campus"]},
    "crop_top":   {"major": "top",      "silhouette": "fitted",    "formality": 2, "tpo": ["casual", "date", "weekend"]},
    "turtleneck": {"major": "top",      "silhouette": "slim",      "formality": 3, "tpo": ["casual", "date", "office"]},
    # 하의 (bottom)
    "slacks":     {"major": "bottom",   "silhouette": "wide",      "formality": 4, "tpo": ["office", "date", "casual"]},
    "jeans":      {"major": "bottom",   "silhouette": "slim",      "formality": 2, "tpo": ["casual", "weekend", "campus"]},
    "skirt":      {"major": "bottom",   "silhouette": "wide",      "formality": 3, "tpo": ["date", "casual", "office"]},
    "mini_skirt": {"major": "bottom",   "silhouette": "fitted",    "formality": 2, "tpo": ["date", "casual", "weekend"]},
    "leggings":   {"major": "bottom",   "silhouette": "slim",      "formality": 1, "tpo": ["casual", "weekend", "sports"]},
    # 아우터 (outer)
    "jacket":     {"major": "outer",    "silhouette": "regular",   "formality": 3, "tpo": ["casual", "office", "date"]},
    "coat":       {"major": "outer",    "silhouette": "oversized", "formality": 4, "tpo": ["office", "date", "casual"]},
    "trench_coat":{"major": "outer",    "silhouette": "regular",   "formality": 4, "tpo": ["office", "date", "casual"]},
    "padding":    {"major": "outer",    "silhouette": "oversized", "formality": 2, "tpo": ["casual", "weekend", "campus"]},
    "jumper":     {"major": "outer",    "silhouette": "regular",   "formality": 2, "tpo": ["casual", "weekend"]},
    # 원피스 (onepiece)
    "onepiece":   {"major": "onepiece", "silhouette": "fitted",    "formality": 4, "tpo": ["date", "wedding", "casual"]},
    # 신발 (shoes)
    "loafer":     {"major": "shoes",    "silhouette": "regular",   "formality": 4, "tpo": ["office", "date", "casual"]},
    "sneakers":   {"major": "shoes",    "silhouette": "regular",   "formality": 1, "tpo": ["casual", "weekend", "campus"]},
    "boots":      {"major": "shoes",    "silhouette": "regular",   "formality": 3, "tpo": ["casual", "date", "office"]},
    "heels":      {"major": "shoes",    "silhouette": "fitted",    "formality": 5, "tpo": ["office", "date", "wedding"]},
    "sandals":    {"major": "shoes",    "silhouette": "regular",   "formality": 3, "tpo": ["casual", "date", "weekend"]},
    "flats":      {"major": "shoes",    "silhouette": "regular",   "formality": 3, "tpo": ["casual", "date", "office"]},
    # 가방 (bag)
    "tote_bag":   {"major": "bag",      "silhouette": "regular",   "formality": 3, "tpo": ["office", "casual", "campus"]},
    "cross_bag":  {"major": "bag",      "silhouette": "regular",   "formality": 2, "tpo": ["casual", "weekend", "campus"]},
    "shoulder_bag":{"major": "bag",     "silhouette": "regular",   "formality": 3, "tpo": ["casual", "date", "office"]},
    "clutch":     {"major": "bag",      "silhouette": "fitted",    "formality": 5, "tpo": ["date", "wedding", "party"]},
    # 액세서리 (acc)
    "earrings":   {"major": "acc",      "silhouette": "regular",   "formality": 3, "tpo": ["casual", "date", "office"]},
    "belt":       {"major": "acc",      "silhouette": "regular",   "formality": 3, "tpo": ["casual", "office", "date"]},
}

# ───────────────────────── 키워드 매핑 ─────────────────────────
# raw_category → canonical category
RAW_CATEGORY_MAP = {
    # 티셔츠
    "티셔츠": "tshirt", "반팔티": "tshirt", "반팔": "tshirt", "롱슬리브": "tshirt",
    "긴팔티": "tshirt", "나시": "tshirt", "민소매": "tshirt",
    # 니트
    "풀오버": "knit", "니트": "knit", "스웨터": "knit", "터틀넥풀오버": "turtleneck",
    "니트풀오버": "knit", "니트티": "knit",
    # 셔츠
    "셔츠/남방": "shirt", "남방": "shirt", "린넨셔츠": "shirt", "옥스포드셔츠": "shirt",
    "체크셔츠": "shirt",
    # 블라우스
    "블라우스/셔츠": "blouse", "블라우스": "blouse",
    # 카디건
    "카디건": "cardigan",
    # 후드
    "후드티": "hoodie", "후디": "hoodie", "후드집업": "hoodie", "집업": "hoodie",
    # 크롭탑
    "크롭티": "crop_top", "크롭탑": "crop_top", "크롭": "crop_top",
    # 터틀넥
    "터틀넥": "turtleneck", "목폴라": "turtleneck", "폴라티": "turtleneck",
    # 슬랙스/바지
    "바지": "slacks", "슬랙스": "slacks", "와이드팬츠": "slacks", "팬츠": "slacks",
    "정장바지": "slacks", "린넨바지": "slacks", "면바지": "slacks",
    # 청바지
    "청바지": "jeans", "데님팬츠": "jeans", "데님": "jeans", "진": "jeans",
    # 스커트
    "스커트": "skirt", "롱스커트": "skirt", "미디스커트": "skirt", "플리츠스커트": "skirt",
    "A라인스커트": "skirt", "롱": "skirt",
    # 미니스커트
    "미니스커트": "mini_skirt", "쁘띠/미니": "mini_skirt", "초미니": "mini_skirt",
    # 레깅스
    "레깅스": "leggings", "타이츠": "leggings",
    # 재킷
    "재킷": "jacket", "자켓": "jacket", "블레이저": "jacket", "테일러드재킷": "jacket",
    "크롭자켓": "jacket", "수트재킷": "jacket",
    # 코트
    "기타코트": "coat", "롱코트": "coat", "울코트": "coat", "하프코트": "coat",
    "더블코트": "coat",
    # 트렌치코트
    "트렌치코트": "trench_coat",
    # 패딩
    "패딩": "padding", "다운": "padding", "롱패딩": "padding", "숏패딩": "padding",
    "구스다운": "padding",
    # 점퍼
    "점퍼": "jumper", "봄버재킷": "jumper", "MA-1": "jumper",
    # 원피스
    "원피스": "onepiece", "드레스": "onepiece", "미니원피스": "onepiece",
    "롱원피스": "onepiece", "미디원피스": "onepiece", "쁘띠": "onepiece",
    # 로퍼
    "로퍼": "loafer", "페니로퍼": "loafer", "태슬로퍼": "loafer",
    # 스니커즈
    "스니커즈": "sneakers", "운동화": "sneakers", "캔버스화": "sneakers",
    # 부츠
    "앵클/숏부츠": "boots", "앵클부츠": "boots", "숏부츠": "boots", "롱부츠": "boots",
    "첼시부츠": "boots", "부츠": "boots",
    # 힐
    "힐": "heels", "펌프스": "heels", "스틸레토": "heels", "웨지힐": "heels",
    "킬힐": "heels",
    # 샌들
    "스트랩샌들": "sandals", "샌들": "sandals", "슬링백": "sandals",
    # 플랫
    "플랫": "flats", "뮬/블로퍼": "flats", "뮬": "flats", "블로퍼": "flats",
    "발레리나": "flats", "플랫슈즈": "flats",
    # 토트백
    "토트백": "tote_bag",
    # 크로스백
    "크로스백": "cross_bag", "크로스바디백": "cross_bag",
    # 숄더백
    "숄더백": "shoulder_bag",
    # 클러치
    "클러치백": "clutch", "클러치": "clutch", "미니백": "clutch",
    # 귀걸이
    "실버귀걸이": "earrings", "패션귀걸이": "earrings", "14K귀걸이": "earrings",
    "귀걸이": "earrings", "귀찌": "earrings", "골드귀걸이": "earrings",
    "패션주얼리세트": "earrings", "유색보석세트": "earrings", "기타주얼리소품": "earrings",
    # 벨트
    "정장벨트": "belt", "벨트": "belt", "가죽벨트": "belt", "멜빵": "belt",
    # 추가 신발
    "러닝화": "sneakers", "등산화": "boots",
    # 추가 아우터
    "베스트": "jacket", "숏코트": "coat", "아우터": "coat",
    "정장세트": "jacket",
    # 추가 상의
    "트레이닝복": "hoodie",
    # 추가 원피스
    "한복": "onepiece",
    # 추가 가방
    "백팩": "shoulder_bag", "도시락가방": "tote_bag", "볼링가방": "shoulder_bag",
    # 액세서리 (스카프/헤어)
    "머플러": "earrings", "목도리": "earrings", "스카프": "earrings",
    "스퀘어/까레스카프": "earrings", "아이스머플러/스카프": "earrings",
    "헤어밴드": "earrings", "헤어핀": "earrings", "헤어끈": "earrings",
    "두건/반다나": "earrings", "넥워머": "earrings", "일반캡": "earrings",
    "패션팔찌": "earrings", "실버팔찌": "earrings", "순금팔찌": "earrings",
    "기타패션소품": "earrings",
}

# 상품명 키워드 → category
NAME_KEYWORDS = {
    "tshirt":     ["티셔츠", "반팔티", "긴팔티", "나시", "민소매", "롱슬리브"],
    "knit":       ["니트", "스웨터", "풀오버", "울니트", "가디건니트"],
    "shirt":      ["셔츠", "남방", "린넨셔츠", "체크셔츠", "옥스포드"],
    "blouse":     ["블라우스", "플리츠블라우스", "러플블라우스"],
    "cardigan":   ["카디건"],
    "hoodie":     ["후드티", "후디", "후드집업", "집업"],
    "crop_top":   ["크롭티", "크롭탑", "크롭"],
    "turtleneck": ["터틀넥", "목폴라", "폴라"],
    "slacks":     ["슬랙스", "와이드팬츠", "정장바지", "린넨팬츠", "면팬츠"],
    "jeans":      ["청바지", "데님팬츠", "데님", "진"],
    "skirt":      ["스커트", "롱스커트", "미디스커트", "플리츠스커트"],
    "mini_skirt": ["미니스커트", "초미니스커트"],
    "leggings":   ["레깅스", "타이츠"],
    "jacket":     ["재킷", "자켓", "블레이저", "수트", "테일러드"],
    "coat":       ["코트", "울코트", "롱코트", "하프코트"],
    "trench_coat":["트렌치", "트렌치코트"],
    "padding":    ["패딩", "다운점퍼", "구스다운", "롱패딩"],
    "jumper":     ["점퍼", "봄버", "MA-1"],
    "onepiece":   ["원피스", "드레스", "투피스"],
    "loafer":     ["로퍼", "페니로퍼", "태슬로퍼"],
    "sneakers":   ["스니커즈", "운동화", "캔버스화"],
    "boots":      ["부츠", "앵클부츠", "숏부츠", "첼시부츠"],
    "heels":      ["힐", "펌프스", "스틸레토", "웨지힐"],
    "sandals":    ["샌들", "슬링백", "스트랩샌들"],
    "flats":      ["플랫", "뮬", "블로퍼", "발레리나"],
    "tote_bag":   ["토트백"],
    "cross_bag":  ["크로스백", "크로스바디"],
    "shoulder_bag":["숄더백"],
    "clutch":     ["클러치", "미니백"],
    "earrings":   ["귀걸이", "귀찌", "이어링"],
    "belt":       ["벨트"],
}

# 성별 키워드
FEMALE_KEYWORDS = ["여성", "여자", "우먼", "우먼즈", "ladies", "woman", "여아", "걸"]
MALE_KEYWORDS   = ["남성", "남자", "맨즈", "mens", "men", "man", "남아"]


# ───────────────────────── 분류 함수 ─────────────────────────
def keyword_classify(product: dict) -> dict | None:
    """raw_category + 상품명 기반 키워드 분류. 성공시 분류 결과 반환, 실패시 None."""
    raw_cat = (product.get("raw_category") or "").strip()
    name    = (product.get("name") or "").strip()

    # 1) raw_category 직접 매핑
    category = RAW_CATEGORY_MAP.get(raw_cat)

    # 2) raw_category 부분 매핑 (예: "앵클/숏부츠" → "부츠")
    if not category:
        for key, cat in RAW_CATEGORY_MAP.items():
            if key in raw_cat or raw_cat in key:
                category = cat
                break

    # 3) 상품명 키워드 매핑
    if not category:
        for cat, keywords in NAME_KEYWORDS.items():
            if any(kw in name for kw in keywords):
                category = cat
                break

    if not category:
        return None

    # 성별 판단
    name_lower = name.lower()
    raw_lower  = raw_cat.lower()
    combined   = name_lower + " " + raw_lower
    if any(kw in combined for kw in FEMALE_KEYWORDS):
        gender = "female"
    elif any(kw in combined for kw in MALE_KEYWORDS):
        gender = "male"
    else:
        # 카테고리별 기본 성별
        major = CATEGORIES[category]["major"]
        if major in ("bag", "acc"):
            gender = "unisex"
        elif major == "shoes":
            gender = "unisex"
        else:
            gender = "female"  # 수집이 여성 위주

    defaults = CATEGORIES[category]
    return {
        "category":   category,
        "silhouette": defaults["silhouette"],
        "formality":  defaults["formality"],
        "tpo":        defaults["tpo"],
        "gender":     gender,
    }


# ───────────────────────── Gemini 배치 분류 ─────────────────────────
def load_llm_cache() -> dict:
    if LLM_CACHE_FILE.exists():
        with open(LLM_CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_llm_cache(cache: dict):
    with open(LLM_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def gemini_batch_classify(products: list[dict], api_key: str, cache: dict) -> dict:
    """
    Gemini Flash로 배치 분류.
    반환: {product_id: {category, silhouette, formality, tpo, gender}}
    """
    from google import genai

    client = genai.Client(api_key=api_key)

    BATCH_SIZE = 30
    results = {}
    uncached = [p for p in products if p["product_id"] not in cache]

    print(f"  Gemini 배치 분류: {len(uncached)}개 (캐시 히트: {len(products)-len(uncached)}개)")

    # 캐시 히트 먼저 적용
    for p in products:
        pid = p["product_id"]
        if pid in cache:
            results[pid] = cache[pid]

    CATEGORY_LIST = ", ".join(CATEGORIES.keys())
    TPO_LIST = "office, date, casual, weekend, campus, wedding, party, sports"

    for i in range(0, len(uncached), BATCH_SIZE):
        batch = uncached[i:i+BATCH_SIZE]
        items_text = "\n".join(
            f'{j+1}. [ID:{p["product_id"]}] 상품명: {p["name"]}, 카테고리힌트: {p.get("raw_category","")}'
            for j, p in enumerate(batch)
        )

        prompt = f"""다음 패션 상품들을 분류해주세요. 각 상품에 대해 JSON 배열로 응답하세요.

분류 기준:
- category: 다음 중 하나 선택 → {CATEGORY_LIST}
- silhouette: oversized / slim / fitted / wide / regular 중 하나
- formality: 1(스포츠) ~ 5(포멀) 정수
- tpo: 다음 중 해당하는 것 최대 3개 → {TPO_LIST}
- gender: female / male / unisex 중 하나

상품 목록:
{items_text}

응답 형식 (JSON 배열만, 설명 없이):
[
  {{"id": "상품ID", "category": "...", "silhouette": "...", "formality": 3, "tpo": ["..."], "gender": "..."}},
  ...
]"""

        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            text = response.text.strip()
            # JSON 파싱
            if "```" in text:
                text = re.sub(r"```[a-z]*\n?", "", text).strip()
            parsed = json.loads(text)
            for item in parsed:
                pid = str(item.get("id", ""))
                if pid:
                    result = {
                        "category":   item.get("category"),
                        "silhouette": item.get("silhouette", "regular"),
                        "formality":  item.get("formality", 3),
                        "tpo":        item.get("tpo", ["casual"]),
                        "gender":     item.get("gender", "unisex"),
                    }
                    results[pid] = result
                    cache[pid] = result
            print(f"    배치 {i//BATCH_SIZE+1}/{(len(uncached)-1)//BATCH_SIZE+1} 완료 ({len(batch)}개)")
        except Exception as e:
            print(f"    배치 {i//BATCH_SIZE+1} 실패: {e}")

        # Rate limit 대응 (무료 플랜: 15 RPM)
        time.sleep(4)

    return results


# ───────────────────────── 메인 ─────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Task 1.8 - 하이브리드 카테고리 분류")
    parser.add_argument("--test",   action="store_true", help="50개 테스트 모드")
    parser.add_argument("--resume", action="store_true", help="이미 처리된 항목 건너뜀")
    args = parser.parse_args()

    print("=" * 60)
    print("Task 1.8 - 하이브리드 카테고리 분류")
    print("=" * 60)

    # API 키
    api_key = os.getenv("GEMINI_API_KEY") or ""
    # .env 직접 읽기
    env_file = BASE_DIR.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("GEMINI_API_KEY="):
                api_key = line.split("=", 1)[1].strip()
    use_gemini = bool(api_key and not api_key.startswith("여기에"))
    print(f"\nGemini API: {'사용 가능' if use_gemini else '미설정 (키워드만 사용)'}")

    # 데이터 로드
    print(f"\n[1/4] 상품 데이터 로드 중...")
    with open(NORMALIZED_FILE, encoding="utf-8") as f:
        products = json.load(f)
    print(f"  -> 총 {len(products):,}개")

    # LLM 캐시 로드
    llm_cache = load_llm_cache()
    print(f"  -> LLM 캐시: {len(llm_cache):,}개")

    if args.test:
        print(f"  -> 테스트 모드: 50개만 처리 (저장 안 함)")

    # 처리 대상
    if args.test:
        targets = products[:50]
    elif args.resume:
        targets = [p for p in products if not p.get("category")]
    else:
        targets = products

    # 인덱스 맵
    id_to_idx = {p["product_id"]: i for i, p in enumerate(products)}

    # 1단계: 키워드 분류
    print(f"\n[2/4] 1단계: 키워드 분류 ({len(targets):,}개)")
    keyword_success = 0
    keyword_fail_ids = []

    for p in targets:
        result = keyword_classify(p)
        if result:
            idx = id_to_idx[p["product_id"]]
            products[idx].update(result)
            keyword_success += 1
        else:
            keyword_fail_ids.append(p["product_id"])

    keyword_rate = keyword_success / len(targets) * 100 if targets else 0
    print(f"  -> 성공: {keyword_success:,}개 ({keyword_rate:.1f}%)")
    print(f"  -> 미분류: {len(keyword_fail_ids):,}개 ({100-keyword_rate:.1f}%)")

    # 2단계: Gemini 배치 분류
    if keyword_fail_ids and use_gemini:
        print(f"\n[3/4] 2단계: Gemini Flash 배치 분류 ({len(keyword_fail_ids):,}개)")
        fail_products = [p for p in products if p["product_id"] in set(keyword_fail_ids)]
        gemini_results = gemini_batch_classify(fail_products, api_key, llm_cache)

        gemini_success = 0
        for pid, result in gemini_results.items():
            idx = id_to_idx.get(pid)
            if idx is not None:
                products[idx].update(result)
                gemini_success += 1

        print(f"  -> Gemini 성공: {gemini_success:,}개")
        save_llm_cache(llm_cache)
        print(f"  -> LLM 캐시 저장: {len(llm_cache):,}개")
    elif keyword_fail_ids:
        print(f"\n[3/4] Gemini 미설정 → {len(keyword_fail_ids):,}개 미분류 상태로 저장")
    else:
        print(f"\n[3/4] 미분류 없음 → Gemini 호출 불필요")

    # 저장 (테스트 모드는 저장 안 함)
    if args.test:
        print(f"\n[4/4] 테스트 모드 - 저장 생략")
        print("\n" + "=" * 60)
        print("테스트 완료! (파일 변경 없음)")
        print("=" * 60)
        print(f"  키워드 분류율: {keyword_success/len(targets)*100:.1f}%")
        for p in targets[:5]:
            print(f"  {p.get('name','')[:25]} -> {p.get('category')} / {p.get('gender')}")
        return

    print(f"\n[4/4] 결과 저장 중...")
    with open(NORMALIZED_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    # 결과 통계
    total = len(products)
    classified = sum(1 for p in products if p.get("category"))
    category_dist = {}
    gender_dist = {}
    for p in products:
        cat = p.get("category")
        if cat:
            category_dist[cat] = category_dist.get(cat, 0) + 1
        g = p.get("gender")
        if g:
            gender_dist[g] = gender_dist.get(g, 0) + 1

    print("\n" + "=" * 60)
    print("완료!")
    print("=" * 60)
    print(f"  분류 완료: {classified:,}/{total:,}개 ({classified/total*100:.1f}%)")
    print(f"  미분류:   {total-classified:,}개")

    print(f"\n  [성별 분포]")
    for g, cnt in sorted(gender_dist.items(), key=lambda x: -x[1]):
        print(f"    {g}: {cnt:,}개")

    print(f"\n  [카테고리 분포 (상위 15개)]")
    for cat, cnt in sorted(category_dist.items(), key=lambda x: -x[1])[:15]:
        major = CATEGORIES.get(cat, {}).get("major", "?")
        print(f"    {cat} ({major}): {cnt:,}개")

    print(f"\n  저장 위치: {NORMALIZED_FILE}")


if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    main()
