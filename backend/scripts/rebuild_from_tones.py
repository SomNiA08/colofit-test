"""
Task 1.6 — 전처리: 상품 정규화

raw/ 하위 JSON 파일들을 읽어 NormalizedProduct 형식으로 변환한다.
  - HTML 태그 제거 (<b> 등 title에 포함된 태그)
  - 브랜드명 추출 (mall_name 기반, 화이트리스트 확인 후 title 파싱 폴백)
  - NormalizedProduct 형식으로 data/normalized/normalized_products.json 출력

다음 단계:
  - color_hex, tone_id(색상 기반): Task 1.7 (이미지 색상 추출 + 톤 매핑)
  - category(정밀 분류): Task 1.8 (하이브리드 카테고리 분류)
"""

import json
import logging
import re
from pathlib import Path

# ── 경로 설정 ─────────────────────────────────────────────────────────────────

SCRIPTS_DIR = Path(__file__).parent
DATA_DIR = SCRIPTS_DIR.parent / "data"
RAW_DIR = DATA_DIR / "raw"
NORMALIZED_DIR = DATA_DIR / "normalized"
BRAND_WHITELIST_PATH = DATA_DIR / "brand_whitelist.json"
OUTPUT_PATH = NORMALIZED_DIR / "normalized_products.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ── HTML 태그 제거 ────────────────────────────────────────────────────────────

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def strip_html(text: str) -> str:
    """title 등에 포함된 HTML 태그 제거. 예: '울 <b>자켓</b>' → '울 자켓'"""
    return _HTML_TAG_RE.sub("", text).strip()


# ── 브랜드명 추출 ─────────────────────────────────────────────────────────────

def load_brand_whitelist() -> list[str]:
    """brand_whitelist.json 로드. 없으면 빈 리스트 반환."""
    if not BRAND_WHITELIST_PATH.exists():
        logger.warning(f"brand_whitelist.json 없음: {BRAND_WHITELIST_PATH}")
        return []
    with open(BRAND_WHITELIST_PATH, encoding="utf-8") as f:
        return json.load(f)


def extract_brand(mall_name: str, title: str, whitelist: list[str]) -> str:
    """
    브랜드명 추출 전략 (3단계):
      1. mall_name이 화이트리스트에 있으면 → 그대로 사용
      2. title 앞부분에서 화이트리스트 브랜드가 발견되면 → 그 브랜드명 사용
      3. 위 두 단계 모두 실패하면 → mall_name을 그대로 사용 (무명 쇼핑몰도 브랜드로 간주)

    Args:
        mall_name: 네이버 쇼핑 API의 mall_name 필드
        title:     HTML 태그 제거된 상품명
        whitelist: 인지도 있는 브랜드 리스트

    Returns:
        추출된 브랜드명 (빈 문자열이면 "알 수 없음")
    """
    # 1단계: mall_name이 화이트리스트에 있는지 확인 (대소문자 무시)
    mall_lower = mall_name.lower().strip()
    for brand in whitelist:
        if brand.lower() == mall_lower:
            return brand  # 정규화된 표기로 반환

    # 2단계: title 앞 40자에서 화이트리스트 브랜드 탐색
    title_prefix = title[:40]
    for brand in whitelist:
        if brand.lower() in title_prefix.lower():
            return brand

    # 3단계: mall_name 그대로 사용
    return mall_name if mall_name else "알 수 없음"


# ── NormalizedProduct 생성 ────────────────────────────────────────────────────

def normalize_item(
    item: dict,
    source_tone_id: str,
    whitelist: list[str],
) -> dict | None:
    """
    raw 상품 dict → NormalizedProduct dict 변환.

    NormalizedProduct 스키마 (기획서 섹션 5.4):
      product_id, name, brand, category,
      color_hex, tone_id, price,
      mall_name, mall_url, image_url, tags

    color_hex, tone_id(색상 기반): Task 1.7에서 채운다.
    category(정밀):               Task 1.8에서 채운다.
    raw_category:                 API 응답 category4 (가장 세부 분류) 보존.
    source_tone_id:               이 상품이 어떤 톤 쿼리로 수집됐는지 기록.
    """
    product_id = str(item.get("product_id", "")).strip()
    if not product_id:
        return None  # product_id 없는 항목은 건너뜀

    raw_title = item.get("title", "")
    clean_name = strip_html(raw_title)
    if not clean_name:
        return None  # 상품명 없는 항목은 건너뜀

    mall_name = item.get("mall_name", "")
    brand = extract_brand(mall_name, clean_name, whitelist)

    # API의 category4(가장 세부) → 없으면 category3 사용
    raw_category = item.get("category4") or item.get("category3") or ""

    # 가격: lprice 우선, 없으면 hprice
    lprice = item.get("lprice", "")
    hprice = item.get("hprice", "")
    price_str = lprice if lprice else hprice
    try:
        price = int(price_str)
    except (ValueError, TypeError):
        price = 0

    return {
        "product_id":      product_id,
        "name":            clean_name,
        "brand":           brand,
        # Task 1.8이 채울 필드 (하이브리드 카테고리 분류)
        "category":        None,
        "raw_category":    raw_category,
        # Task 1.7이 채울 필드 (이미지 색상 추출 + 톤 매핑)
        "color_hex":       None,
        "tone_id":         None,
        # 수집 메타데이터
        "source_tone_id":  source_tone_id,
        # 기본 상품 정보
        "price":           price,
        "mall_name":       mall_name,
        "mall_url":        item.get("link", ""),
        "image_url":       item.get("image", ""),
        # Task 1.7 / 1.8이 채울 태그
        "tags":            [],
    }


# ── 전체 raw 데이터 순회 ──────────────────────────────────────────────────────

def load_all_raw(raw_dir: Path, whitelist: list[str]) -> dict[str, dict]:
    """
    raw/ 하위 모든 JSON 파일을 읽어 NormalizedProduct dict를 반환.
    같은 product_id가 여러 톤에서 수집된 경우 첫 번째 것을 유지한다.

    Returns:
        {product_id: NormalizedProduct} dict
    """
    products: dict[str, dict] = {}
    duplicate_count = 0
    skip_count = 0

    tone_dirs = sorted(d for d in raw_dir.iterdir() if d.is_dir())
    logger.info(f"톤 폴더 {len(tone_dirs)}개 처리 시작")

    for tone_dir in tone_dirs:
        tone_id = tone_dir.name
        json_files = sorted(tone_dir.glob("*.json"))
        tone_new = 0

        for json_file in json_files:
            try:
                with open(json_file, encoding="utf-8") as f:
                    payload = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"파일 읽기 실패: {json_file.name} — {e}")
                continue

            items = payload.get("items", [])
            source_tone = payload.get("tone_id", tone_id)

            for item in items:
                normalized = normalize_item(item, source_tone, whitelist)
                if normalized is None:
                    skip_count += 1
                    continue

                pid = normalized["product_id"]
                if pid in products:
                    duplicate_count += 1
                else:
                    products[pid] = normalized
                    tone_new += 1

        logger.info(f"[{tone_id}] 신규 {tone_new}개")

    logger.info(
        f"\n처리 완료 — 고유 상품: {len(products)}개 | "
        f"중복 제거: {duplicate_count}개 | 건너뜀: {skip_count}개"
    )
    return products


# ── 저장 ─────────────────────────────────────────────────────────────────────

def save_normalized(products: dict[str, dict], output_path: Path) -> None:
    """정규화 결과를 JSON 파일로 저장."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    product_list = list(products.values())

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(product_list, f, ensure_ascii=False, indent=2)

    logger.info(f"저장 완료: {output_path} ({len(product_list)}개)")


# ── 메인 ──────────────────────────────────────────────────────────────────────

def main() -> None:
    logger.info("=== Task 1.6: 상품 정규화 시작 ===")

    whitelist = load_brand_whitelist()
    logger.info(f"브랜드 화이트리스트 로드: {len(whitelist)}개")

    products = load_all_raw(RAW_DIR, whitelist)

    if not products:
        logger.error("정규화된 상품이 없습니다. raw/ 디렉토리를 확인하세요.")
        return

    save_normalized(products, OUTPUT_PATH)
    logger.info("=== Task 1.6 완료 ===")
    logger.info(f"다음 단계:")
    logger.info(f"  Task 1.7 — 이미지 색상 추출 + 톤 매핑 (color_hex, tone_id 채우기)")
    logger.info(f"  Task 1.8 — 하이브리드 카테고리 분류 (category, tags 채우기)")


if __name__ == "__main__":
    main()
