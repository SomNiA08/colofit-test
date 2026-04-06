"""
5축 코디 스코어링 서비스.
각 함수는 순수 함수 (DB 의존 없음).
점수 범위: 0–100 (float).
"""

import json
import math
from functools import lru_cache
from pathlib import Path

# ── 팔레트 경로 ─────────────────────────────────────────────────────────────
_PALETTE_DIR = Path(__file__).parent.parent.parent / "data" / "palettes"

# ── 톤 호환 그룹 (같은 시즌 = 호환) ──────────────────────────────────────────
_SEASON_GROUPS: dict[str, set[str]] = {
    "spring": {"spring_warm_light", "spring_warm_bright", "spring_warm_mute"},
    "summer": {"summer_cool_light", "summer_cool_soft", "summer_cool_mute"},
    "autumn": {"autumn_warm_bright", "autumn_warm_mute", "autumn_warm_deep"},
    "winter": {"winter_cool_bright", "winter_cool_deep", "winter_cool_light"},
}

# tone_id → season 역방향 맵 (모듈 로드 시 1회 생성)
_TONE_TO_SEASON: dict[str, str] = {
    tone: season
    for season, tones in _SEASON_GROUPS.items()
    for tone in tones
}

# RGB 유클리드 거리 최대값: sqrt(255²+255²+255²) ≈ 441.67
# 점수 공식: score = max(0, 100 - d / 4.42)  →  d=0 → 100, d=441.67 → 0
_RGB_SCALE = 441.67 / 100  # ≈ 4.4167


@lru_cache(maxsize=12)
def _load_palette_rgb(tone_id: str) -> list[tuple[int, int, int]]:
    """팔레트 JSON에서 RGB 튜플 목록을 로드한다 (파일 I/O 1회)."""
    path = _PALETTE_DIR / f"{tone_id}.json"
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    return [tuple(c["rgb"]) for c in data["colors"]]  # type: ignore[return-value]


def _rgb_distance(r1: int, g1: int, b1: int, r2: int, g2: int, b2: int) -> float:
    return math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """'#RRGGBB' → (R, G, B). 앞 '#' 있어도 없어도 동작."""
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _tone_level_score(item_tone_id: str, user_tone_id: str) -> float:
    """톤 레벨 점수: 동일 톤 100, 호환 톤(같은 시즌) 95, 그 외 None."""
    if item_tone_id == user_tone_id:
        return 100.0
    user_season = _TONE_TO_SEASON.get(user_tone_id)
    item_season = _TONE_TO_SEASON.get(item_tone_id)
    if user_season and item_season and user_season == item_season:
        return 95.0
    return 0.0  # 비호환 톤 → 색상 레벨로 폴백 필요 없음, 0점


def _color_level_score(item_hex: str, user_tone_id: str) -> float:
    """
    아이템 hex 색상과 유저 팔레트 간 최소 RGB 거리를 점수로 변환.
    score = max(0, 100 - d_min / 4.42)
    """
    palette = _load_palette_rgb(user_tone_id)
    ir, ig, ib = _hex_to_rgb(item_hex)
    d_min = min(_rgb_distance(ir, ig, ib, pr, pg, pb) for pr, pg, pb in palette)
    return max(0.0, 100.0 - d_min / _RGB_SCALE)


def _item_pcf_score(
    item_tone_id: str | None,
    item_hex: str | None,
    user_tone_id: str,
) -> float:
    """
    단일 아이템의 PCF 점수를 반환한다.

    우선순위:
    1. item_tone_id가 있으면 톤 레벨 먼저.
       - 동일/호환 톤 → 그 점수 반환 (색상 레벨 불필요)
       - 비호환 톤 → item_hex로 색상 레벨 계산
    2. item_tone_id 없고 item_hex 있으면 색상 레벨만.
    3. 둘 다 없으면 50.0 (중립).
    """
    if item_tone_id:
        score = _tone_level_score(item_tone_id, user_tone_id)
        if score > 0:
            return score
        # 비호환 톤이지만 hex가 있으면 색상 거리로 보정
        if item_hex:
            return _color_level_score(item_hex, user_tone_id)
        return 0.0

    if item_hex:
        return _color_level_score(item_hex, user_tone_id)

    return 50.0  # 정보 없음 → 중립


def calculate_pcf(
    item_tone_ids: list[str | None],
    item_hex_colors: list[str | None],
    user_tone_id: str,
) -> float:
    """
    PCF (Personal Color Fit) 점수를 계산한다.

    Args:
        item_tone_ids: 코디 아이템별 tone_id 목록 (없으면 None)
        item_hex_colors: 코디 아이템별 대표 hex 색상 목록 (없으면 None)
        user_tone_id: 유저의 퍼스널컬러 tone_id

    Returns:
        0–100 float. 아이템이 0개면 50.0 반환.

    Note:
        item_tone_ids와 item_hex_colors의 길이가 같아야 한다.
        Hard Filter/Soft Score 분리 원칙에 따라 이 함수는 점수만 반환한다.
        탈락(필터) 로직은 호출부에서 처리한다.
    """
    if not item_tone_ids and not item_hex_colors:
        return 50.0

    n = max(len(item_tone_ids), len(item_hex_colors))

    # 길이 맞추기 (짧은 쪽을 None으로 패딩)
    tone_ids = list(item_tone_ids) + [None] * (n - len(item_tone_ids))
    hex_colors = list(item_hex_colors) + [None] * (n - len(item_hex_colors))

    scores = [
        _item_pcf_score(tid, hex_c, user_tone_id)
        for tid, hex_c in zip(tone_ids, hex_colors)
    ]

    return sum(scores) / len(scores)


# ═══════════════════════════════════════════════════════════════════════════════
# OF — Occasion Fit (TPO 적합도)
# ═══════════════════════════════════════════════════════════════════════════════

# 기획서 §5.5.2: TPO 동의어 확장 매핑
_TPO_SYNONYM_MAP: dict[str, frozenset[str]] = {
    "commute":   frozenset({"office", "commute"}),
    "office":    frozenset({"office", "commute"}),
    "weekend":   frozenset({"casual", "weekend", "daily"}),
    "casual":    frozenset({"casual", "weekend", "daily"}),
    "daily":     frozenset({"casual", "daily", "weekend"}),
    "interview": frozenset({"interview", "office"}),
    "campus":    frozenset({"campus", "casual"}),
    "event":     frozenset({"party", "wedding", "event"}),
    "party":     frozenset({"party", "event"}),
    "wedding":   frozenset({"wedding", "event"}),
    "workout":   frozenset({"workout"}),
}


def _expand_tpos(tpo_list: list[str]) -> frozenset[str]:
    """사용자 TPO 리스트를 동의어 확장한 집합으로 반환한다."""
    expanded: set[str] = set()
    for tpo in tpo_list:
        expanded.update(_TPO_SYNONYM_MAP.get(tpo, frozenset({tpo})))
    return frozenset(expanded)


def calculate_of(
    outfit_tags: list[str],
    user_tpo_list: list[str],
) -> float:
    """
    OF (Occasion Fit) 점수를 계산한다.

    Args:
        outfit_tags: 코디에 부여된 TPO 태그 리스트
        user_tpo_list: 유저가 설정한 TPO 리스트

    Returns:
        30–100 float. 완전 미매칭이어도 30점 하한 (태깅 불완전 보정).

    Scoring:
        match_count >= 2  → 80 + (match_count / total_tags) × 20  (최대 100)
        match_count == 1  → 60 + (1 / total_tags) × 20
        match_count == 0  → 30
    """
    if not outfit_tags or not user_tpo_list:
        return 30.0

    expanded = _expand_tpos(user_tpo_list)
    match_count = sum(1 for tag in outfit_tags if tag in expanded)
    total_tags = len(outfit_tags)

    if match_count >= 2:
        return min(100.0, 80.0 + (match_count / total_tags) * 20.0)
    if match_count == 1:
        return 60.0 + (1 / total_tags) * 20.0
    return 30.0


# ═══════════════════════════════════════════════════════════════════════════════
# CH — Color Harmony (색상 조화도)
# ═══════════════════════════════════════════════════════════════════════════════

def _rgb_to_saturation(r: int, g: int, b: int) -> float:
    """RGB → HSL 채도(S) 반환. 범위: 0.0~1.0."""
    r_n, g_n, b_n = r / 255.0, g / 255.0, b / 255.0
    c_max = max(r_n, g_n, b_n)
    c_min = min(r_n, g_n, b_n)
    delta = c_max - c_min
    if delta == 0:
        return 0.0
    lightness = (c_max + c_min) / 2.0
    return delta / (1.0 - abs(2.0 * lightness - 1.0))


def _ch_base_score(d_avg: float) -> float:
    """평균 쌍 거리 → 구간별 CH 점수 (기획서 §5.5.3)."""
    if d_avg < 30:
        return 60.0
    if d_avg < 80:
        return 80.0 + (d_avg - 30.0) / 50.0 * 20.0
    if d_avg < 150:
        return 100.0 - (d_avg - 80.0) / 70.0 * 21.0
    return max(30.0, 79.0 - (d_avg - 150.0) / 290.0 * 49.0)


def calculate_ch(item_hex_colors: list[str]) -> float:
    """
    CH (Color Harmony) 점수를 계산한다.

    Args:
        item_hex_colors: 코디 아이템별 대표 HEX 색상 리스트

    Returns:
        0–100 float. 아이템이 0~1개이면 60.0 반환 (쌍 거리 계산 불가).

    Scoring:
        d_avg < 30         → 60  (너무 유사, 단조로움)
        30 ≤ d_avg < 80   → 80~100  (유사색 조화)
        80 ≤ d_avg < 150  → 79~100  (적절한 대비)
        d_avg ≥ 150       → 30~79  (과도한 대비)

        채도 보너스: 아이템 3개 이상이고 채도 표준편차 0.15~0.40이면 +5 (최대 100)
    """
    colors = [_hex_to_rgb(h) for h in item_hex_colors]

    if len(colors) < 2:
        return 60.0

    # 모든 쌍의 RGB 거리
    distances: list[float] = []
    for i in range(len(colors)):
        for j in range(i + 1, len(colors)):
            r1, g1, b1 = colors[i]
            r2, g2, b2 = colors[j]
            distances.append(_rgb_distance(r1, g1, b1, r2, g2, b2))

    d_avg = sum(distances) / len(distances)
    score = _ch_base_score(d_avg)

    # 채도 보너스 (아이템 3개 이상 + 채도 표준편차 0.15~0.40)
    if len(colors) >= 3:
        saturations = [_rgb_to_saturation(r, g, b) for r, g, b in colors]
        mean_s = sum(saturations) / len(saturations)
        variance = sum((s - mean_s) ** 2 for s in saturations) / len(saturations)
        std_s = math.sqrt(variance)
        if 0.15 <= std_s <= 0.40:
            score = min(100.0, score + 5.0)

    return score


# ═══════════════════════════════════════════════════════════════════════════════
# PE — Price Efficiency (가격 효율성)
# ═══════════════════════════════════════════════════════════════════════════════


def calculate_pe(
    total_price: float,
    budget_min: float,
    budget_max: float,
) -> float:
    """
    PE (Price Efficiency) 점수를 계산한다.

    Args:
        total_price: 코디 총 가격
        budget_min: 사용자 최소 예산
        budget_max: 사용자 최대 예산

    Returns:
        0–100 float.

    Scoring (기획서 §5.5.4):
        budget_mid = (budget_min + budget_max) / 2

        Case 1: 예산 범위 내
            100 - |total_price - budget_mid| / budget_mid × 30
        Case 2: 예산 초과
            max(0, 70 - over_ratio × 100)
        Case 3: 예산 미만
            max(40, 80 - under_ratio × 80)
    """
    if budget_max <= 0 or budget_min < 0:
        return 50.0

    budget_mid = (budget_min + budget_max) / 2.0

    if budget_min <= total_price <= budget_max:
        # Case 1: 예산 범위 내 — 중앙에 가까울수록 높은 점수
        if budget_mid == 0:
            return 100.0
        return max(0.0, 100.0 - abs(total_price - budget_mid) / budget_mid * 30.0)

    if total_price > budget_max:
        # Case 2: 예산 초과 — 급격한 감점
        over_ratio = (total_price - budget_max) / budget_max
        return max(0.0, 70.0 - over_ratio * 100.0)

    # Case 3: 예산 미만 — 완만한 감점, 최저 40점
    under_ratio = (budget_min - total_price) / budget_min if budget_min > 0 else 0.0
    return max(40.0, 80.0 - under_ratio * 80.0)


# ═══════════════════════════════════════════════════════════════════════════════
# SF — Style Fit (스타일 적합도)
# ═══════════════════════════════════════════════════════════════════════════════

_DATA_DIR = Path(__file__).parent.parent.parent / "data"


@lru_cache(maxsize=1)
def _load_style_compat() -> dict[str, int]:
    """카테고리 궁합 매트릭스를 로드한다."""
    with (_DATA_DIR / "style_compat.json").open(encoding="utf-8") as f:
        return json.load(f)["scores"]


@lru_cache(maxsize=1)
def _load_silhouette_rules() -> dict[str, dict]:
    """실루엣 밸런스 규칙을 로드한다."""
    with (_DATA_DIR / "silhouette_rules.json").open(encoding="utf-8") as f:
        return json.load(f)["rules"]


@lru_cache(maxsize=1)
def _load_formality_map() -> dict[str, int]:
    """아이템별 포멀도 맵을 로드한다."""
    with (_DATA_DIR / "formality_map.json").open(encoding="utf-8") as f:
        return json.load(f)["formality"]


def _category_compat_score(categories: list[str]) -> float:
    """
    카테고리 궁합 점수를 계산한다 (0–100).
    모든 2-아이템 쌍의 평균 궁합 점수를 반환한다.
    매트릭스에 없는 조합은 60점(중립).
    """
    if len(categories) < 2:
        return 60.0

    compat = _load_style_compat()
    scores: list[float] = []

    for i in range(len(categories)):
        for j in range(i + 1, len(categories)):
            a, b = categories[i], categories[j]
            key = f"{a}__{b}"
            key_rev = f"{b}__{a}"
            val = compat.get(key) or compat.get(key_rev)
            scores.append(float(val) if val is not None else 60.0)

    return sum(scores) / len(scores)


def _silhouette_balance_score(
    top_silhouette: str | None,
    bottom_silhouette: str | None,
) -> float:
    """
    실루엣 밸런스 점수를 계산한다 (0–100).
    규칙에 없는 조합은 65점(중립).
    상의/하의 실루엣 정보가 없으면 65점.
    """
    if not top_silhouette or not bottom_silhouette:
        return 65.0

    rules = _load_silhouette_rules()
    key = f"{top_silhouette}__{bottom_silhouette}"
    rule = rules.get(key)
    if rule:
        return float(rule["score"])

    # 역순도 시도
    key_rev = f"{bottom_silhouette}__{top_silhouette}"
    rule_rev = rules.get(key_rev)
    if rule_rev:
        return float(rule_rev["score"])

    return 65.0


def _formality_consistency_score(categories: list[str]) -> float:
    """
    포멀도 일관성 점수를 계산한다 (0–100).
    score = max(0, 100 - std_dev × 40)

    아이템이 0~1개이면 100점 (편차 없음).
    매핑 없는 카테고리는 3(중립).
    """
    if len(categories) < 2:
        return 100.0

    fmap = _load_formality_map()
    values = [float(fmap.get(cat, 3)) for cat in categories]

    mean_v = sum(values) / len(values)
    variance = sum((v - mean_v) ** 2 for v in values) / len(values)
    std_dev = math.sqrt(variance)

    return max(0.0, 100.0 - std_dev * 40.0)


def calculate_sf(items: list[dict]) -> float:
    """
    SF (Style Fit) 점수를 계산한다.

    Args:
        items: 코디 아이템 리스트. 각 dict는 최소 'category' 키를 포함.
               선택적으로 'silhouette' 키를 포함할 수 있음.

    Returns:
        0–100 float.

    Scoring (기획서 §5.5.5):
        SF = category_score × 0.50
           + silhouette_score × 0.25
           + formality_score × 0.25
    """
    if not items:
        return 50.0

    categories = [item.get("category", "") for item in items if item.get("category")]

    if not categories:
        return 50.0

    # 1. 카테고리 궁합 (50%)
    cat_score = _category_compat_score(categories)

    # 2. 실루엣 밸런스 (25%)
    top_sil = None
    bottom_sil = None
    top_cats = {"blouse", "shirt", "knit", "tshirt", "hoodie", "sweatshirt", "croptop", "cardigan"}
    bottom_cats = {"slacks", "jeans", "wide_pants", "skirt", "mini_skirt", "shorts", "jogger", "leggings", "chino"}
    for item in items:
        cat = item.get("category", "")
        sil = item.get("silhouette")
        if cat in top_cats and sil and not top_sil:
            top_sil = sil
        elif cat in bottom_cats and sil and not bottom_sil:
            bottom_sil = sil
    sil_score = _silhouette_balance_score(top_sil, bottom_sil)

    # 3. 포멀도 일관성 (25%)
    form_score = _formality_consistency_score(categories)

    return cat_score * 0.50 + sil_score * 0.25 + form_score * 0.25
