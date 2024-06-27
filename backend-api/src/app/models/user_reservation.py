import uuid as uuid_pkg
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, Enum as SQLAEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import relationship

from ..core.db.database import Base

import enum


class ReservationStatus(enum.Enum):
    RESERVED = "RESERVED"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    DELETED = "DELETED"

class UserReservation(Base):
    __tablename__ = "user_reservation"

    id: Mapped[int] = mapped_column("id", autoincrement=True, nullable=False, unique=True, primary_key=True, init=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    exam_schedule_id: Mapped[int] = mapped_column(ForeignKey("exam_schedule.id"), index=True)
    status: Mapped[ReservationStatus] = mapped_column(SQLAEnum(ReservationStatus), nullable=False, default=ReservationStatus.RESERVED)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default_factory=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    
    __table_args__ = (
        UniqueConstraint("user_id", "exam_schedule_id", name="unique_user_exam_schedule"),
    )

    user = relationship("User", back_populates="reservations")
    exam_schedule = relationship("ExamSchedule", back_populates="reservations")
