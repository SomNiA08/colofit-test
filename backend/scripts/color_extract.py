"""
Task 1.7 — 이미지 색상 추출 + 톤 매핑
- PIL + K-means(k=3)로 상품 이미지에서 dominant color 3개 추출
- 추출된 HEX → 12톤 팔레트와 RGB 유클리드 거리 비교
- 가장 가까운 톤 ID 매핑 (tone_id, color_hex 부여)
- 결과를 normalized_products.json에 덮어씀

사용법:
  python color_extract.py           # 전체 실행
  python color_extract.py --limit 100  # 테스트용 100개만
  python color_extract.py --resume  # 이미 처리된 항목 건너뜀
"""

import json
import math
import os
import sys
import time
import argparse
import concurrent.futures
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans

# ───────────────────────────── 경로 설정 ─────────────────────────────
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
PALETTES_DIR = DATA_DIR / "palettes"
NORMALIZED_FILE = DATA_DIR / "normalized" / "normalized_products.json"
OUTPUT_FILE = DATA_DIR / "normalized" / "normalized_products.json"

# ───────────────────────────── 상수 ─────────────────────────────
TIMEOUT = 8          # 이미지 다운로드 타임아웃 (초)
MAX_WORKERS = 8      # 병렬 처리 스레드 수
K_CLUSTERS = 3       # K-means 클러스터 수
IMG_SIZE = (100, 100)  # 리사이즈 크기 (속도 최적화)
SAVE_INTERVAL = 1000  # N개 처리마다 중간 저장

# 배경으로 간주할 밝기 임계값 (너무 흰색/검정 제거)
WHITE_THRESHOLD = 240
BLACK_THRESHOLD = 15

# ───────────────────────────── 팔레트 로드 ─────────────────────────────
def load_palettes() -> dict[str, list[tuple[int, int, int]]]:
    """12개 톤 팔레트를 로드해서 {tone_id: [(R,G,B), ...]} 형태로 반환"""
    palettes = {}
    for palette_file in PALETTES_DIR.glob("*.json"):
        with open(palette_file, encoding="utf-8") as f:
            data = json.load(f)
        tone_id = data["tone_id"]
        colors = [tuple(c["rgb"]) for c in data["colors"]]
        palettes[tone_id] = colors
    return palettes


# ───────────────────────────── 유틸 함수 ─────────────────────────────
def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def euclidean_distance(c1: tuple, c2: tuple) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))


def map_to_tone(rgb: tuple[int, int, int], palettes: dict) -> str:
    """
    RGB → 12톤 매핑
    각 톤의 모든 대표 색상과 유클리드 거리 계산 → 최소 거리 톤 반환
    """
    best_tone = None
    best_dist = float("inf")
    for tone_id, colors in palettes.items():
        min_dist = min(euclidean_distance(rgb, c) for c in colors)
        if min_dist < best_dist:
            best_dist = min_dist
            best_tone = tone_id
    return best_tone


def is_background(rgb: np.ndarray) -> bool:
    """너무 흰색이거나 너무 어두운 픽셀은 배경으로 간주"""
    r, g, b = rgb
    if r > WHITE_THRESHOLD and g > WHITE_THRESHOLD and b > WHITE_THRESHOLD:
        return True
    if r < BLACK_THRESHOLD and g < BLACK_THRESHOLD and b < BLACK_THRESHOLD:
        return True
    return False


def extract_dominant_color(image_url: str) -> tuple[int, int, int] | None:
    """
    이미지 URL에서 dominant color 추출
    1. 이미지 다운로드 + 리사이즈
    2. 배경 픽셀 제거
    3. K-means(k=3)로 클러스터링
    4. 가장 큰 클러스터의 중심색 반환
    """
    try:
        resp = requests.get(image_url, timeout=TIMEOUT, headers={
            "User-Agent": "Mozilla/5.0 (compatible; ColorFit/1.0)"
        })
        resp.raise_for_status()

        img = Image.open(BytesIO(resp.content)).convert("RGB")
        img = img.resize(IMG_SIZE, Image.LANCZOS)
        pixels = np.array(img).reshape(-1, 3).astype(float)

        # 배경 픽셀 제거
        mask = ~np.array([is_background(p) for p in pixels])
        filtered = pixels[mask]

        # 유효 픽셀이 너무 적으면 전체 픽셀 사용
        if len(filtered) < 10:
            filtered = pixels

        k = min(K_CLUSTERS, len(filtered))
        if k < 1:
            return None

        kmeans = KMeans(n_clusters=k, n_init=3, random_state=42)
        kmeans.fit(filtered)

        # 가장 큰 클러스터의 중심색 선택
        labels = kmeans.labels_
        centers = kmeans.cluster_centers_
        counts = np.bincount(labels)
        dominant_idx = np.argmax(counts)
        dominant_rgb = tuple(int(c) for c in centers[dominant_idx])

        return dominant_rgb

    except Exception:
        return None


# ───────────────────────────── 단일 상품 처리 ─────────────────────────────
def process_product(args) -> dict:
    """단일 상품에 대해 색상 추출 + 톤 매핑 수행"""
    product, palettes = args
    product = dict(product)  # 원본 보호용 복사

    # 이미 처리된 경우 스킵 (--resume 모드)
    if product.get("color_hex") and product.get("tone_id"):
        return product

    image_url = product.get("image_url")
    if not image_url:
        return product

    dominant_rgb = extract_dominant_color(image_url)
    if dominant_rgb:
        product["color_hex"] = rgb_to_hex(dominant_rgb)
        product["tone_id"] = map_to_tone(dominant_rgb, palettes)

    return product


# ───────────────────────────── 메인 ─────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Task 1.7 — 이미지 색상 추출 + 톤 매핑")
    parser.add_argument("--limit", type=int, default=None, help="처리할 최대 상품 수 (테스트용)")
    parser.add_argument("--resume", action="store_true", help="이미 처리된 항목 건너뜀")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS, help=f"병렬 스레드 수 (기본: {MAX_WORKERS})")
    args = parser.parse_args()

    print("=" * 60)
    print("Task 1.7 — 이미지 색상 추출 + 톤 매핑")
    print("=" * 60)

    # 팔레트 로드
    print("\n[1/3] 12톤 팔레트 로드 중...")
    palettes = load_palettes()
    print(f"  → {len(palettes)}개 톤 팔레트 로드 완료")
    for tone_id, colors in sorted(palettes.items()):
        print(f"     {tone_id}: {len(colors)}개 대표 색상")

    # 정규화 상품 로드
    print(f"\n[2/3] 정규화 상품 로드 중: {NORMALIZED_FILE}")
    with open(NORMALIZED_FILE, encoding="utf-8") as f:
        products = json.load(f)
    print(f"  → 총 {len(products):,}개 상품")

    # 처리 대상 필터링
    if args.resume:
        targets = [p for p in products if not (p.get("color_hex") and p.get("tone_id"))]
        print(f"  → 미처리 상품: {len(targets):,}개 (resume 모드)")
    else:
        targets = products

    if args.limit:
        targets = targets[:args.limit]
        print(f"  → 처리 제한: {args.limit}개")

    # 병렬 처리
    print(f"\n[3/3] 색상 추출 + 톤 매핑 시작 (스레드: {args.workers})")
    print(f"  처리 대상: {len(targets):,}개\n")

    # 인덱스 맵 생성 (product_id → index in products)
    id_to_idx = {p["product_id"]: i for i, p in enumerate(products)}

    processed = 0
    failed = 0
    start_time = time.time()

    task_args = [(p, palettes) for p in targets]

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process_product, arg): arg[0]["product_id"] for arg in task_args}

        for future in concurrent.futures.as_completed(futures):
            product_id = futures[future]
            try:
                result = future.result()
                # 원본 products 리스트 업데이트
                idx = id_to_idx.get(product_id)
                if idx is not None:
                    products[idx] = result

                if result.get("color_hex"):
                    processed += 1
                else:
                    failed += 1

            except Exception as e:
                failed += 1

            total_done = processed + failed
            if total_done % 100 == 0 and total_done > 0:
                elapsed = time.time() - start_time
                rate = total_done / elapsed
                remaining = (len(targets) - total_done) / rate if rate > 0 else 0
                print(
                    f"  진행: {total_done:,}/{len(targets):,} "
                    f"| 성공: {processed:,} | 실패: {failed:,} "
                    f"| 속도: {rate:.1f}개/초 "
                    f"| 남은 시간: {remaining/60:.1f}분"
                )

            # 중간 저장
            if total_done % SAVE_INTERVAL == 0 and total_done > 0:
                with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                    json.dump(products, f, ensure_ascii=False, indent=2)
                print(f"  💾 중간 저장 완료 ({total_done:,}개 처리)")

    # 최종 저장
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    elapsed = time.time() - start_time
    total_with_color = sum(1 for p in products if p.get("color_hex"))
    total_with_tone = sum(1 for p in products if p.get("tone_id"))

    # 톤별 분포
    tone_dist = {}
    for p in products:
        t = p.get("tone_id")
        if t:
            tone_dist[t] = tone_dist.get(t, 0) + 1

    print("\n" + "=" * 60)
    print("완료!")
    print("=" * 60)
    print(f"  처리 시간: {elapsed/60:.1f}분")
    print(f"  성공: {processed:,}개 | 실패: {failed:,}개")
    print(f"  color_hex 부여: {total_with_color:,}/{len(products):,}개")
    print(f"  tone_id 부여: {total_with_tone:,}/{len(products):,}개")
    print(f"\n  [톤별 분포]")
    for tone_id, count in sorted(tone_dist.items(), key=lambda x: -x[1]):
        print(f"    {tone_id}: {count:,}개")
    print(f"\n  저장 위치: {OUTPUT_FILE}")


if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    main()
