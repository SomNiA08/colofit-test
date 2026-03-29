"""
네이버 쇼핑 API 수집 스크립트
12톤별 병렬 수집 — 4개 톤 동시 수집 × 3라운드로 12톤 커버
"""

import json
import os
import time
import logging
from datetime import datetime
from pathlib import Path

import httpx
from dotenv import load_dotenv

# .env 파일에서 API 키 읽기
load_dotenv()

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

NAVER_API_URL = "https://openapi.naver.com/v1/search/shop.json"
RAW_DATA_DIR = Path(__file__).parent.parent / "data" / "raw"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ── API 호출 ─────────────────────────────────────────────────────────────────

def search_products(query: str, display: int = 100, start: int = 1) -> dict:
    """
    네이버 쇼핑 API 호출.

    Args:
        query:   검색 키워드 (예: "봄 코랄 블라우스")
        display: 한 번에 가져올 상품 수 (최대 100)
        start:   검색 시작 위치 (1~1000)

    Returns:
        API 응답 dict. 실패 시 빈 dict 반환.
    """
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        raise RuntimeError(
            ".env 파일에 NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET이 설정되지 않았습니다."
        )

    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params = {
        "query": query,
        "display": display,
        "start": start,
        "sort": "sim",   # 정확도순
    }

    max_retries = 4
    delay = 1.0  # 초기 대기 시간 (exponential backoff)

    for attempt in range(max_retries):
        try:
            response = httpx.get(NAVER_API_URL, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                return response.json()

            # Rate limit 초과 (429) 또는 서버 오류 (5xx) → 재시도
            if response.status_code in (429, 500, 502, 503):
                logger.warning(
                    f"API 오류 {response.status_code} — {attempt + 1}번째 시도. "
                    f"{delay:.0f}초 후 재시도..."
                )
                time.sleep(delay)
                delay *= 2  # exponential backoff: 1s → 2s → 4s → 8s
                continue

            logger.error(f"API 호출 실패: {response.status_code} — {response.text}")
            return {}

        except httpx.TimeoutException:
            logger.warning(f"타임아웃 — {attempt + 1}번째 시도. {delay:.0f}초 후 재시도...")
            time.sleep(delay)
            delay *= 2

    logger.error(f"'{query}' 쿼리 최대 재시도 횟수 초과. 건너뜁니다.")
    return {}


# ── 파싱 & 저장 ───────────────────────────────────────────────────────────────

def parse_items(api_response: dict) -> list[dict]:
    """
    API 응답에서 상품 리스트 추출 및 기본 파싱.

    Returns:
        상품 dict 리스트. 각 항목은 title, link, image, lprice, hprice,
        mallName, category1~4 포함.
    """
    items = api_response.get("items", [])
    parsed = []
    for item in items:
        parsed.append({
            "title": item.get("title", ""),
            "link": item.get("link", ""),
            "image": item.get("image", ""),
            "lprice": item.get("lprice", ""),
            "hprice": item.get("hprice", ""),
            "mall_name": item.get("mallName", ""),
            "product_id": item.get("productId", ""),
            "category1": item.get("category1", ""),
            "category2": item.get("category2", ""),
            "category3": item.get("category3", ""),
            "category4": item.get("category4", ""),
        })
    return parsed


def save_raw(tone_id: str, query: str, items: list[dict]) -> None:
    """
    수집된 raw 상품 데이터를 JSON 파일로 저장.
    저장 경로: backend/data/raw/{tone_id}/{timestamp}_{query}.json
    """
    tone_dir = RAW_DATA_DIR / tone_id
    tone_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_query = query.replace(" ", "_").replace("/", "-")[:40]
    filename = tone_dir / f"{timestamp}_{safe_query}.json"

    payload = {
        "tone_id": tone_id,
        "query": query,
        "collected_at": datetime.now().isoformat(),
        "count": len(items),
        "items": items,
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    logger.info(f"저장 완료: {filename.name} ({len(items)}개)")


# ── 톤별 수집 ─────────────────────────────────────────────────────────────────

def collect_for_tone(tone_id: str, queries: list[str], max_per_query: int = 200) -> int:
    """
    단일 톤에 대해 모든 쿼리를 순서대로 수집.

    Args:
        tone_id:       톤 ID (예: "spring_warm_light")
        queries:       검색 키워드 리스트
        max_per_query: 쿼리당 최대 수집 상품 수 (API 최대 1,000개)

    Returns:
        총 수집 상품 수
    """
    total = 0
    display = 100  # 1회 호출당 최대

    for query in queries:
        collected_for_query = 0
        start = 1

        while collected_for_query < max_per_query:
            remaining = max_per_query - collected_for_query
            fetch_count = min(display, remaining)

            response = search_products(query, display=fetch_count, start=start)
            items = parse_items(response)

            if not items:
                break  # 결과 없으면 다음 쿼리로

            save_raw(tone_id, query, items)
            collected_for_query += len(items)
            total += len(items)

            # API가 반환한 전체 결과 수 확인
            api_total = response.get("total", 0)
            if start + fetch_count > min(api_total, 1000):
                break  # 더 이상 가져올 결과 없음

            start += fetch_count
            time.sleep(0.1)  # API Rate limit 보호 (초당 10회 이내)

        logger.info(f"[{tone_id}] '{query}' 완료 — {collected_for_query}개")

    return total


# ── 메인 실행 ─────────────────────────────────────────────────────────────────

def main() -> None:
    """
    tone_queries.json을 읽어 전체 12톤 수집 실행.
    실제 병렬 수집은 tmux 4세션으로 분리하여 실행한다 (주석 참고).
    """
    queries_path = Path(__file__).parent.parent / "data" / "tone_queries.json"

    if not queries_path.exists():
        logger.error(f"tone_queries.json 없음: {queries_path}")
        logger.error("먼저 Task 1.4를 완료하여 tone_queries.json을 생성하세요.")
        return

    with open(queries_path, encoding="utf-8") as f:
        tone_queries: dict[str, list[str]] = json.load(f)

    logger.info(f"수집 시작 — {len(tone_queries)}개 톤")

    grand_total = 0
    for tone_id, queries in tone_queries.items():
        logger.info(f"\n{'='*50}")
        logger.info(f"톤 수집 시작: {tone_id} ({len(queries)}개 쿼리)")
        count = collect_for_tone(tone_id, queries)
        grand_total += count
        logger.info(f"톤 수집 완료: {tone_id} — {count}개")

    logger.info(f"\n전체 수집 완료 — 총 {grand_total}개 상품")


# ── API 연결 테스트 ───────────────────────────────────────────────────────────

def test_connection() -> None:
    """
    API 키 설정 및 연결 상태를 확인하는 테스트 함수.
    실행: python curate_by_tone.py test
    """
    print("\n[API 연결 테스트]")
    print(f"NAVER_CLIENT_ID: {'설정됨 ✅' if NAVER_CLIENT_ID else '없음 ❌'}")
    print(f"NAVER_CLIENT_SECRET: {'설정됨 ✅' if NAVER_CLIENT_SECRET else '없음 ❌'}")

    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        print("\n⚠️  .env 파일에 API 키를 먼저 입력하세요.")
        return

    print("\n테스트 쿼리: '봄 코랄 블라우스'")
    response = search_products("봄 코랄 블라우스", display=3, start=1)

    if response:
        total = response.get("total", 0)
        items = response.get("items", [])
        print(f"✅ 연결 성공! 전체 결과: {total}개, 가져온 상품: {len(items)}개")
        if items:
            print(f"첫 번째 상품: {items[0].get('title', '')} / {items[0].get('mallName', '')}")
    else:
        print("❌ 연결 실패. API 키를 확인하세요.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_connection()
    else:
        main()
