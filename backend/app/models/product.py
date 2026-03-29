from datetime import datetime

from sqlalchemy import DateTime, String, Integer, SmallInteger, Index
from sqlalchemy.dialects.postgresql import ARRAY, TEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(500))
    brand: Mapped[str | None] = mapped_column(String(100))
    category: Mapped[str | None] = mapped_column(String(20))   # top, bottom, outer, onepiece, shoes, bag
    color_hex: Mapped[str | None] = mapped_column(String(7))
    tone_id: Mapped[str | None] = mapped_column(String(30))
    price: Mapped[int | None] = mapped_column(Integer)
    mall_name: Mapped[str | None] = mapped_column(String(50))
    mall_url: Mapped[str | None] = mapped_column(TEXT)
    image_url: Mapped[str | None] = mapped_column(TEXT)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(TEXT))
    gender: Mapped[str | None] = mapped_column(String(10))     # female, male, unisex
    silhouette: Mapped[str | None] = mapped_column(String(20)) # oversized, slim, fitted, wide, regular
    formality: Mapped[int | None] = mapped_column(SmallInteger) # 1~5
    last_observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("ix_products_tone_id", "tone_id"),
        Index("ix_products_gender", "gender"),
    )
