import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Reaction(Base):
    __tablename__ = "reactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    outfit_id: Mapped[str | None] = mapped_column(
        String(50), ForeignKey("outfits.id")
    )
    reaction_type: Mapped[str | None] = mapped_column(String(10))  # save, dislike, click, purchase
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
