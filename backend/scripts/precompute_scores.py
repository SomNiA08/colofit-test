"""
스코어 프리컴퓨팅 스크립트 — 기획서 Task 2.12.

CH(색상 조화)와 SF(스타일 적합도)는 사용자 정보와 무관하므로
전체 코디에 대해 사전 계산하여 outfits.scores JSONB에 저장한다.

런타임(GET /api/feed)에서는 PCF·OF·PE만 계산하고
저장된 CH·SF를 그대로 재사용하여 응답 속도를 높인다.

실행:
  cd backend
  python scripts/precompute_scores.py           # 실제 DB 업데이트
  python scripts/precompute_scores.py --dry-run  # 결과만 미리 보기
"""

import asyncio
import os
import sys
from pathlib import Path

# backend/ 를 import 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.models.outfit import Outfit
from app.models.product import Product
from app.services.scoring import calculate_ch, calculate_sf


# ── DB 연결 설정 ──────────────────────────────────────────────────────────────

def _build_db_url() -> str:
    url = os.getenv("DATABASE_URL", "")
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


# ── 메인 로직 ─────────────────────────────────────────────────────────────────

async def precompute(dry_run: bool = False) -> None:
    """전체 코디의 CH·SF를 계산해 outfits.scores JSONB에 저장한다."""

    db_url = _build_db_url()
    if not db_url:
        print("ERROR: DATABASE_URL 환경변수가 설정되지 않았습니다.")
        print("  .env 파일에 DATABASE_URL=postgresql://... 을 추가하세요.")
        sys.exit(1)

    engine = create_async_engine(db_url, echo=False)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_maker() as session:
        # 1. 전체 코디 로드
        outfit_rows = (await session.execute(select(Outfit))).scalars().all()
        print(f"코디 로드: {len(outfit_rows):,}개")

        # 2. 참조된 상품 ID 수집 → 일괄 로드 (N+1 방지)
        all_item_ids: set[str] = set()
        for o in outfit_rows:
            if o.item_ids:
                all_item_ids.update(o.item_ids)

        print(f"상품 ID 수집: {len(all_item_ids):,}개")

        product_rows = (
            await session.execute(
                select(Product).where(Product.id.in_(all_item_ids))
            )
        ).scalars().all()

        # 스코어 계산에 필요한 필드만 보관
        products: dict[str, dict] = {
            p.id: {
                "product_id": p.id,
                "category":   p.category,
                "color_hex":  p.color_hex,
                "tone_id":    p.tone_id,
                "silhouette": p.silhouette,
                "formality":  p.formality,
            }
            for p in product_rows
        }
        print(f"상품 로드: {len(products):,}개\n")

        # 3. CH + SF 계산 & 업데이트
        updated = 0
        skipped = 0

        for o in outfit_rows:
            items = [
                products[pid]
                for pid in (o.item_ids or [])
                if pid in products
            ]

            if not items:
                skipped += 1
                continue

            # CH — 아이템 색상만 사용 (사용자 무관)
            valid_hex = [item["color_hex"] for item in items if item.get("color_hex")]
            ch = calculate_ch(valid_hex) if valid_hex else 60.0

            # SF — 카테고리/실루엣/포멀도 사용 (사용자 무관)
            sf = calculate_sf(items)

            # 기존 scores에 ch·sf만 덮어쓰기 (다른 필드는 유지)
            new_scores = {**(o.scores or {}), "ch": round(ch, 2), "sf": round(sf, 2)}

            if not dry_run:
                await session.execute(
                    update(Outfit)
                    .where(Outfit.id == o.id)
                    .values(scores=new_scores)
                )
            updated += 1

        if not dry_run:
            await session.commit()

        label = "[DRY RUN] " if dry_run else ""
        print(f"{label}완료:")
        print(f"  업데이트: {updated:,}개")
        print(f"  스킵 (아이템 없음): {skipped:,}개")

        if dry_run:
            print("\n실제로 저장하려면 --dry-run 없이 다시 실행하세요.")

    await engine.dispose()


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("[DRY RUN 모드] DB에 실제로 쓰지 않습니다.\n")
    asyncio.run(precompute(dry_run=dry_run))
