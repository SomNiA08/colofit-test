import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class StyleSeed(Base):
    __tablename__ = "style_seeds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    mood_seed: Mapped[str | None] = mapped_column(String(30))       # minimal, casual, classic 등
    silhouette_seed: Mapped[str | None] = mapped_column(String(30)) # slim, oversized, wide 등
    color_seed: Mapped[str | None] = mapped_column(String(30))      # monotone, pastel, contrast 등
    price_seed: Mapped[str | None] = mapped_column(String(30))      # low, mid, mid_high, high
    seed_confidence: Mapped[int | None] = mapped_column(Integer)    # 0~4 (라운드 참여 수)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
