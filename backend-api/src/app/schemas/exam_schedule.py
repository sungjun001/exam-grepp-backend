from datetime import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..core.schemas import PersistentDeletion, TimestampSchema, UUIDSchema
from ..models.exam_schedule import ExamScheduleStatus

class ExamScheduleBase(BaseModel):
    title: Annotated[str, Field(min_length=2, max_length=300, examples=["Programers Exam"])]
    text: Annotated[str, Field(min_length=1, max_length=63206, examples=["This is the content of the exam schedule."])]
    start_at: Annotated[datetime, Field(examples=["2023-06-28 15:30"])]
    end_at: Annotated[datetime, Field(examples=["2023-06-28 17:30"])]
    max_users: Annotated[int, Field(ge=1, le=50000, example=50000)]
    media_url: Annotated[str, Field(example="https://www.examimageurl.com")]

    @field_validator('start_at', 'end_at', mode='before')
    def parse_minutes(cls, value):
        if isinstance(value, str):
            return datetime.strptime(value, "%Y-%m-%d %H:%M")
        return value

    @field_validator('end_at')    
    def end_after_start(cls, v, values):
        if v <= values.data["start_at"]:
            raise ValueError('end_at must be after start_at')
        return v
    


class ExamSchedule(TimestampSchema, ExamScheduleBase, UUIDSchema, PersistentDeletion):
    media_url: Annotated[
        str | None,
        Field(pattern=r"^(https?|ftp)://[^\s/$.?#].[^\s]*$", examples=["https://www.examimageurl.com"], default=None),
    ]
    created_by_user_id: int


class ExamScheduleRead(BaseModel):
    id: int
    title: Annotated[str, Field(min_length=2, max_length=300, examples=["Programers Exam"])]
    text: Annotated[str, Field(min_length=1, max_length=63206, examples=["This is the content of the exam schedule."])]
    media_url: Annotated[
        str | None,
        Field(examples=["https://www.examimageurl.com"], default=None),
    ]
    created_by_user_id: int
    start_at: datetime 
    end_at: datetime
    status: ExamScheduleStatus
    created_at: datetime  


class ExamScheduleCreate(ExamScheduleBase):
    model_config = ConfigDict(extra="forbid")

    media_url: Annotated[
        str | None,
        Field(pattern=r"^(https?|ftp)://[^\s/$.?#].[^\s]*$", examples=["https://www.examimageurl.com"], default=None),
    ]


class ExamScheduleCreateInternal(ExamScheduleCreate):
    created_by_user_id: int


class ExamScheduleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Annotated[str | None, Field(min_length=2, max_length=300, examples=["This is my updated"], default=None)]
    text: Annotated[
        str | None,
        Field(min_length=1, max_length=63206, examples=["This is the updated content of the exam schedule."], default=None),
    ]
    start_at: Annotated[datetime | None, Field(examples=["2023-06-27 15:30"], default=None)]
    end_at: Annotated[datetime | None, Field(examples=["2023-06-27 17:30"], default=None)]
    status: Annotated[Optional[str], Field( default=ExamScheduleStatus.AVAILABLE, examples=[ExamScheduleStatus.FULLY_BOOKED, ExamScheduleStatus.CANCELLED, ExamScheduleStatus.DELETED])]

    media_url: Annotated[
        str | None,
        Field(pattern=r"^(https?|ftp)://[^\s/$.?#].[^\s]*$", examples=["https://www.examimageurl.com"], default=None),
    ]

    @field_validator('start_at', 'end_at', mode='before')
    def parse_minutes(cls, value):
        if isinstance(value, str):
            return datetime.strptime(value, "%Y-%m-%d %H:%M")
        return value

    @field_validator('end_at')    
    def end_after_start(cls, v, values):
        if v <= values.data["start_at"]:
            raise ValueError('end_at must be after start_at')
        return v

class ExamScheduleUpdateInternal(ExamScheduleUpdate):
    updated_at: datetime


class ExamScheduleDelete(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_deleted: bool
    deleted_at: datetime
