from sqlalchemy import String, Integer, Boolean, SmallInteger, Index
from sqlalchemy.dialects.postgresql import ARRAY, TEXT, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Outfit(Base):
    __tablename__ = "outfits"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    item_ids: Mapped[list[str] | None] = mapped_column(ARRAY(TEXT))     # product IDs
    gender: Mapped[str | None] = mapped_column(String(10))              # female, male
    designed_tpo: Mapped[str | None] = mapped_column(String(20))        # 레시피 기반 설계 TPO
    designed_moods: Mapped[list[str] | None] = mapped_column(ARRAY(TEXT))
    total_price: Mapped[int | None] = mapped_column(Integer)
    lowest_total_price: Mapped[int | None] = mapped_column(Integer)
    is_complete_outfit: Mapped[bool | None] = mapped_column(Boolean)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(TEXT))
    scores: Mapped[dict | None] = mapped_column(JSONB)                  # {pcf, of, ch, pe, sf, total}
    style_details: Mapped[dict | None] = mapped_column(JSONB)           # StyleFilter 결과
    reasons: Mapped[list[str] | None] = mapped_column(ARRAY(TEXT))
    llm_quality_score: Mapped[int | None] = mapped_column(SmallInteger)  # Gemini 평가 1~5

    __table_args__ = (
        Index("ix_outfits_designed_tpo", "designed_tpo"),
        Index("ix_outfits_gender", "gender"),
        Index("ix_outfits_total_price", "total_price"),
    )
