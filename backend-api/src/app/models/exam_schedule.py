import uuid as uuid_pkg
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db.database import Base

from sqlalchemy.orm import relationship


class ExamSchedule(Base):
    __tablename__ = "exam_schedule"

    id: Mapped[int] = mapped_column("id", autoincrement=True, nullable=False, unique=True, primary_key=True, init=False)

    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    text: Mapped[str] = mapped_column(String(63206))
    uuid: Mapped[uuid_pkg.UUID] = mapped_column(default_factory=uuid_pkg.uuid4, primary_key=True, unique=True)
    media_url: Mapped[Optional[str]] = mapped_column(String, default=None)
    start_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=None)
    end_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=None)
    max_users: Mapped[int] = mapped_column(Integer, default=50000)
    reserve_count: Mapped[int] = mapped_column(Integer, default=0)
    confirm_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default_factory=lambda: datetime.now(UTC))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=None)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=None)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    reservations = relationship("UserReservation", back_populates="exam_schedule")
