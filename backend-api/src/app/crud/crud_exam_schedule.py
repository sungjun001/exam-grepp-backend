from fastcrud import FastCRUD

from ..models.exam_schedule import ExamSchedule
from ..schemas.exam_schedule import ExamScheduleCreateInternal, ExamScheduleDelete, ExamScheduleUpdate, ExamScheduleUpdateInternal

CRUDExamSchedule = FastCRUD[ExamSchedule, ExamScheduleCreateInternal, ExamScheduleUpdate, ExamScheduleUpdateInternal, ExamScheduleDelete]
crud_exam_schedule = CRUDExamSchedule(ExamSchedule)
