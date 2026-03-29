import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    tone_preferences: Mapped[dict] = mapped_column(JSONB, server_default="{}")     # {톤ID: 누적 점수}
    category_preferences: Mapped[dict] = mapped_column(JSONB, server_default="{}") # {카테고리: 누적 점수}
    brand_preferences: Mapped[dict] = mapped_column(JSONB, server_default="{}")    # {브랜드: 누적 점수}
    avg_liked_price: Mapped[int | None] = mapped_column(Integer)
    feedback_count: Mapped[int] = mapped_column(Integer, server_default="0")
    weight_overrides: Mapped[dict | None] = mapped_column(JSONB)                   # 5축 가중치 오버라이드
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
