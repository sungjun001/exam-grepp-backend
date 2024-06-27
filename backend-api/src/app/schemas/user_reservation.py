from datetime import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict

from ..core.schemas import PersistentDeletion, TimestampSchema, UUIDSchema
from ..models.user_reservation import ReservationStatus

class UserReservationBase(BaseModel):
    user_id: Annotated[int, Field()]
    exam_schedule_id: Annotated[int, Field()]
    status: Annotated[ReservationStatus, Field(default=ReservationStatus.RESERVED, examples=["RESERVED", "CONFIRMED", "CANCELLED", "DELETED"])]

    @field_validator('status')
    def validate_status(cls, value):
        if value not in ReservationStatus:
            raise ValueError("Invalid reservation status")
        return value

class UserReservationCreate(UserReservationBase):
    model_config = ConfigDict(extra="forbid")

class UserReservationRead(BaseModel):
    id: int
    user_id: int
    exam_schedule_id: int
    status: ReservationStatus
    created_at: datetime
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]
    is_deleted: bool

    class Config:
        orm_mode = True

class UserReservationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Annotated[Optional[str], Field(default=None, examples=["CONFIRMED", "CANCELLED", "DELETED"])]

    @field_validator('status')
    def validate_status(cls, value, values, **kwargs):
        if value not in ReservationStatus:
            raise ValueError("Invalid reservation status")
        return value

class UserReservationUpdateInternal(UserReservationUpdate):
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UserReservationDelete(PersistentDeletion):
    pass
