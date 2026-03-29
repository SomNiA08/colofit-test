import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Integer, func
from sqlalchemy.dialects.postgresql import UUID, ARRAY, TEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str | None] = mapped_column(String(255))
    provider: Mapped[str | None] = mapped_column(String(20))  # kakao, google
    gender: Mapped[str | None] = mapped_column(String(10))    # female, male
    tone_id: Mapped[str | None] = mapped_column(String(30))   # summer_cool_soft
    tpo_primary: Mapped[str | None] = mapped_column(String(20))
    tpo_secondary: Mapped[str | None] = mapped_column(String(20))
    tpo_list: Mapped[list[str] | None] = mapped_column(ARRAY(TEXT))   # 최대 3개
    style_moods: Mapped[list[str] | None] = mapped_column(ARRAY(TEXT))
    budget_min: Mapped[int | None] = mapped_column(Integer)
    budget_max: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
