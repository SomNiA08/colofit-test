"""
StyleFilter — 규칙 기반 사전 필터 (기획서 §6.6).

카테고리 감지 → 3축 SF 점수 계산 → 55점 미만 탈락.
"""

import json
from functools import lru_cache
from pathlib import Path

from app.services.scoring import calculate_sf

# ── 경로 ────────────────────────────────────────────────────────────────────
_DATA_DIR = Path(__file__).parent.parent.parent / "data"
_LLM_CACHE_FILE = _DATA_DIR / "llm_cache.json"

# ── SF 컷오프 (기획서 §5.5.5: 55점 미만 제거) ──────────────────────────────
SF_CUTOFF = 55.0

# ── 카테고리 메타 (31종) ────────────────────────────────────────────────────
CATEGORIES: dict[str, dict] = {
    "tshirt":      {"major": "top",      "silhouette": "regular",   "formality": 2},
    "knit":        {"major": "top",      "silhouette": "oversized", "formality": 3},
    "shirt":       {"major": "top",      "silhouette": "regular",   "formality": 3},
    "blouse":      {"major": "top",      "silhouette": "regular",   "formality": 4},
    "cardigan":    {"major": "top",      "silhouette": "regular",   "formality": 3},
    "hoodie":      {"major": "top",      "silhouette": "oversized", "formality": 1},
    "croptop":     {"major": "top",      "silhouette": "fitted",    "formality": 2},
    "sweatshirt":  {"major": "top",      "silhouette": "oversized", "formality": 2},
    "turtleneck":  {"major": "top",      "silhouette": "slim",      "formality": 3},
    "slacks":      {"major": "bottom",   "silhouette": "wide",      "formality": 4},
    "jeans":       {"major": "bottom",   "silhouette": "slim",      "formality": 2},
    "wide_pants":  {"major": "bottom",   "silhouette": "wide",      "formality": 3},
    "skirt":       {"major": "bottom",   "silhouette": "wide",      "formality": 4},
    "mini_skirt":  {"major": "bottom",   "silhouette": "fitted",    "formality": 2},
    "shorts":      {"major": "bottom",   "silhouette": "regular",   "formality": 2},
    "jogger":      {"major": "bottom",   "silhouette": "slim",      "formality": 1},
    "leggings":    {"major": "bottom",   "silhouette": "slim",      "formality": 1},
    "chino":       {"major": "bottom",   "silhouette": "regular",   "formality": 3},
    "blazer":      {"major": "outer",    "silhouette": "regular",   "formality": 4},
    "trench":      {"major": "outer",    "silhouette": "regular",   "formality": 4},
    "coat":        {"major": "outer",    "silhouette": "oversized", "formality": 4},
    "padding":     {"major": "outer",    "silhouette": "oversized", "formality": 2},
    "jacket":      {"major": "outer",    "silhouette": "regular",   "formality": 3},
    "jumper":      {"major": "outer",    "silhouette": "regular",   "formality": 2},
    "suit_jacket": {"major": "outer",    "silhouette": "regular",   "formality": 5},
    "dress":       {"major": "onepiece", "silhouette": "fitted",    "formality": 4},
    "jumpsuit":    {"major": "onepiece", "silhouette": "regular",   "formality": 3},
    "sneakers":    {"major": "shoes",    "silhouette": "regular",   "formality": 2},
    "loafer":      {"major": "shoes",    "silhouette": "regular",   "formality": 3},
    "heels":       {"major": "shoes",    "silhouette": "fitted",    "formality": 5},
    "boots":       {"major": "shoes",    "silhouette": "regular",   "formality": 3},
    "sandals":     {"major": "shoes",    "silhouette": "regular",   "formality": 2},
    "derby":       {"major": "shoes",    "silhouette": "regular",   "formality": 4},
    "slipper":     {"major": "shoes",    "silhouette": "regular",   "formality": 1},
    "tote":        {"major": "bag",      "silhouette": "regular",   "formality": 3},
    "crossbody":   {"major": "bag",      "silhouette": "regular",   "formality": 2},
    "clutch":      {"major": "bag",      "silhouette": "fitted",    "formality": 5},
    "backpack":    {"major": "bag",      "silhouette": "regular",   "formality": 1},
    "shoulder":    {"major": "bag",      "silhouette": "regular",   "formality": 3},
    "earring":     {"major": "acc",      "silhouette": "regular",   "formality": 3},
    "necklace":    {"major": "acc",      "silhouette": "regular",   "formality": 3},
    "scarf":       {"major": "acc",      "silhouette": "regular",   "formality": 3},
    "hat":         {"major": "acc",      "silhouette": "regular",   "formality": 2},
    "belt":        {"major": "acc",      "silhouette": "regular",   "formality": 3},
    "hairband":    {"major": "acc",      "silhouette": "regular",   "formality": 2},
}

# ── 1단계: 키워드 매핑 (상품명 → 카테고리) ──────────────────────────────────
# raw_category 직접 매핑
_RAW_CATEGORY_MAP: dict[str, str] = {
    "티셔츠": "tshirt", "반팔티": "tshirt", "반팔": "tshirt", "긴팔티": "tshirt",
    "나시": "tshirt", "민소매": "tshirt", "롱슬리브": "tshirt",
    "니트": "knit", "풀오버": "knit", "스웨터": "knit", "니트풀오버": "knit", "니트티": "knit",
    "셔츠/남방": "shirt", "남방": "shirt", "린넨셔츠": "shirt", "옥스포드셔츠": "shirt",
    "체크셔츠": "shirt",
    "블라우스/셔츠": "blouse", "블라우스": "blouse",
    "카디건": "cardigan",
    "후드티": "hoodie", "후디": "hoodie", "후드집업": "hoodie", "집업": "hoodie",
    "맨투맨": "sweatshirt",
    "크롭티": "croptop", "크롭탑": "croptop", "크롭": "croptop",
    "터틀넥": "turtleneck", "목폴라": "turtleneck", "폴라티": "turtleneck",
    "슬랙스": "slacks", "정장바지": "slacks",
    "바지": "slacks", "팬츠": "slacks", "린넨바지": "slacks", "면바지": "slacks",
    "와이드팬츠": "wide_pants",
    "청바지": "jeans", "데님팬츠": "jeans", "데님": "jeans",
    "스커트": "skirt", "롱스커트": "skirt", "미디스커트": "skirt",
    "플리츠스커트": "skirt", "A라인스커트": "skirt",
    "미니스커트": "mini_skirt", "쁘띠/미니": "mini_skirt",
    "숏팬츠": "shorts", "반바지": "shorts",
    "조거팬츠": "jogger", "조거": "jogger", "트레이닝팬츠": "jogger",
    "레깅스": "leggings", "타이츠": "leggings",
    "치노팬츠": "chino", "치노": "chino",
    "블레이저": "blazer",
    "트렌치코트": "trench", "트렌치": "trench",
    "코트": "coat", "울코트": "coat", "롱코트": "coat",
    "패딩": "padding", "다운": "padding", "롱패딩": "padding",
    "재킷": "jacket", "자켓": "jacket",
    "점퍼": "jumper", "봄버재킷": "jumper",
    "정장": "suit_jacket", "수트": "suit_jacket",
    "원피스": "dress", "드레스": "dress",
    "점프수트": "jumpsuit",
    "스니커즈": "sneakers", "운동화": "sneakers",
    "로퍼": "loafer",
    "힐": "heels", "펌프스": "heels", "스틸레토": "heels",
    "부츠": "boots", "앵클부츠": "boots", "첼시부츠": "boots",
    "샌들": "sandals", "슬링백": "sandals",
    "더비슈즈": "derby", "옥스퍼드": "derby",
    "슬리퍼": "slipper",
    "토트백": "tote",
    "크로스백": "crossbody", "크로스바디백": "crossbody",
    "클러치": "clutch", "미니백": "clutch",
    "백팩": "backpack",
    "숄더백": "shoulder",
    "귀걸이": "earring", "이어링": "earring",
    "목걸이": "necklace",
    "스카프": "scarf", "머플러": "scarf",
    "모자": "hat", "캡": "hat",
    "벨트": "belt",
    "헤어밴드": "hairband",
}

# 상품명 키워드 → category (우선순위 매칭용)
_NAME_KEYWORDS: dict[str, list[str]] = {
    "tshirt":     ["티셔츠", "반팔티", "긴팔티", "나시", "민소매"],
    "knit":       ["니트", "스웨터", "풀오버"],
    "shirt":      ["셔츠", "남방"],
    "blouse":     ["블라우스"],
    "cardigan":   ["카디건"],
    "hoodie":     ["후드티", "후디", "후드집업"],
    "sweatshirt": ["맨투맨", "스웨트셔츠"],
    "croptop":    ["크롭티", "크롭탑", "크롭"],
    "turtleneck": ["터틀넥", "목폴라", "폴라"],
    "slacks":     ["슬랙스", "정장바지"],
    "wide_pants": ["와이드팬츠", "와이드 팬츠"],
    "jeans":      ["청바지", "데님팬츠", "데님"],
    "skirt":      ["스커트", "플리츠스커트"],
    "mini_skirt": ["미니스커트"],
    "shorts":     ["숏팬츠", "반바지"],
    "jogger":     ["조거", "트레이닝"],
    "leggings":   ["레깅스", "타이츠"],
    "chino":      ["치노"],
    "blazer":     ["블레이저"],
    "trench":     ["트렌치"],
    "coat":       ["코트"],
    "padding":    ["패딩", "다운"],
    "jacket":     ["재킷", "자켓"],
    "jumper":     ["점퍼", "봄버"],
    "suit_jacket": ["정장", "수트"],
    "dress":      ["원피스", "드레스"],
    "jumpsuit":   ["점프수트"],
    "sneakers":   ["스니커즈", "운동화"],
    "loafer":     ["로퍼"],
    "heels":      ["힐", "펌프스"],
    "boots":      ["부츠"],
    "sandals":    ["샌들", "슬링백"],
    "derby":      ["더비", "옥스퍼드"],
    "slipper":    ["슬리퍼"],
    "tote":       ["토트백"],
    "crossbody":  ["크로스백"],
    "clutch":     ["클러치"],
    "backpack":   ["백팩"],
    "shoulder":   ["숄더백"],
    "earring":    ["귀걸이", "이어링"],
    "necklace":   ["목걸이"],
    "scarf":      ["스카프", "머플러"],
    "hat":        ["모자", "캡"],
    "belt":       ["벨트"],
    "hairband":   ["헤어밴드"],
}


def _load_llm_cache() -> dict:
    """LLM 분류 캐시 파일을 로드한다."""
    if _LLM_CACHE_FILE.exists():
        with _LLM_CACHE_FILE.open(encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    return {}


def detect_category(
    title: str,
    category3: str | None = None,
    product_id: str | None = None,
) -> dict | None:
    """
    하이브리드 카테고리 감지 (기획서 §5.4.1).

    3단계 폴백:
      1. raw_category / 상품명 키워드 매칭 (~70%)
      2. LLM 캐시 조회 (~27%)
      3. 미분류 → None

    Args:
        title: 상품명
        category3: 네이버 쇼핑 API category3 (raw_category)
        product_id: LLM 캐시 조회용 상품 ID

    Returns:
        {"category": str, "silhouette": str, "formality": int} 또는 None
    """
    # 1단계: raw_category 직접 매핑
    if category3:
        cat = _RAW_CATEGORY_MAP.get(category3.strip())
        if cat and cat in CATEGORIES:
            meta = CATEGORIES[cat]
            return {
                "category": cat,
                "silhouette": meta["silhouette"],
                "formality": meta["formality"],
            }

    # 1단계: 상품명 키워드 매칭
    title_clean = title.strip()
    for cat, keywords in _NAME_KEYWORDS.items():
        if any(kw in title_clean for kw in keywords):
            meta = CATEGORIES[cat]
            return {
                "category": cat,
                "silhouette": meta["silhouette"],
                "formality": meta["formality"],
            }

    # 2단계: LLM 캐시 조회
    if product_id:
        cache = _load_llm_cache()
        cached = cache.get(product_id)
        if cached and isinstance(cached, dict):
            cat = cached.get("category")
            if cat and cat in CATEGORIES:
                meta = CATEGORIES[cat]
                return {
                    "category": cat,
                    "silhouette": cached.get("silhouette", meta["silhouette"]),
                    "formality": cached.get("formality", meta["formality"]),
                }

    # 3단계: 미분류
    return None


def filter_outfit(items: list[dict]) -> dict:
    """
    코디 아이템 리스트에 StyleFilter를 적용한다 (기획서 §6.6).

    Args:
        items: 코디 아이템 리스트. 각 dict는 최소 'title' 키를 포함.
               선택적으로 'category3', 'product_id', 'category', 'silhouette' 키.

    Returns:
        {
            "pass": bool,           # 55점 이상이면 True
            "score": float,         # SF 점수 (0~100)
            "categories": list,     # 감지된 카테고리 목록
            "items_enriched": list,  # category/silhouette 보강된 아이템
        }
    """
    enriched: list[dict] = []
    categories: list[str] = []

    for item in items:
        # 이미 category가 있으면 detect 건너뜀
        if item.get("category") and item["category"] in CATEGORIES:
            enriched.append(item)
            categories.append(item["category"])
            continue

        detected = detect_category(
            title=item.get("title", ""),
            category3=item.get("category3"),
            product_id=item.get("product_id"),
        )

        if detected:
            enriched_item = {**item, **detected}
            enriched.append(enriched_item)
            categories.append(detected["category"])
        else:
            enriched.append(item)

    score = calculate_sf(enriched)

    return {
        "pass": score >= SF_CUTOFF,
        "score": score,
        "categories": categories,
        "items_enriched": enriched,
    }
