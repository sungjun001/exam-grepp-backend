from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastcrud.paginated import PaginatedListResponse, compute_offset, paginated_response
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import UTC, datetime

from ...api.dependencies import get_current_superuser, get_current_user
from ...core.db.database import async_get_db
from ...core.exceptions.http_exceptions import ForbiddenException, NotFoundException
from ...core.utils.cache import cache
from ...crud.crud_exam_schedule import crud_exam_schedule
from ...crud.crud_users import crud_users
from ...schemas.exam_schedule import ExamScheduleCreate, ExamScheduleCreateInternal, ExamScheduleRead, ExamScheduleUpdate
from ...schemas.user import UserRead

router = APIRouter(tags=["exam_schedule"])


@router.post("/exam_schedule", response_model=ExamScheduleRead, status_code=201)
async def write_exam_schedule(
    request: Request,
    examSchedule: ExamScheduleCreate,
    current_user: Annotated[UserRead, Depends(get_current_superuser)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> ExamScheduleRead:
    db_user = await crud_users.get(db=db, schema_to_select=UserRead, UserRead=current_user, is_deleted=False)
    if db_user is None:
        raise NotFoundException("User not found")

    if current_user["id"] != db_user["id"]:
        raise ForbiddenException()

    examSchedule_internal_dict = examSchedule.model_dump()
    examSchedule_internal_dict["created_by_user_id"] = db_user["id"]

    ## examSchedule_internal_dict 로그 출력
    print ( examSchedule_internal_dict)

    examSchedule_internal = ExamScheduleCreateInternal(**examSchedule_internal_dict)
    created_examSchedule: ExamScheduleRead = await crud_exam_schedule.create(db=db, object=examSchedule_internal)
    return created_examSchedule


@router.get("/exam_schedule", response_model=PaginatedListResponse[ExamScheduleRead])
# @cache(
#     key_prefix="exam_schedule:page_{page}:items_per_page:{items_per_page}",
#     expiration=60,
# )
async def read_exam_schedule(
    request: Request,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    page: int = 1,
    items_per_page: int = 10,
) -> dict:
    db_user = await crud_users.get(db=db, schema_to_select=UserRead, is_deleted=False)
    if not db_user:
        raise NotFoundException("User not found")

    posts_data = await crud_exam_schedule.get_multi(
        db=db,
        offset=compute_offset(page, items_per_page),
        limit=items_per_page,
        schema_to_select=ExamScheduleRead,
        created_by_user_id=db_user["id"],
        is_deleted=False,
    )

    response: dict[str, Any] = paginated_response(crud_data=posts_data, page=page, items_per_page=items_per_page)
    return response


@router.get("/exam_schedule/{id}", response_model=ExamScheduleRead)
# @cache(key_prefix="exam_schedule_cache", resource_id_name="id")
async def read_exam_schedule(
    request: Request, id: int, db: Annotated[AsyncSession, Depends(async_get_db)]
) -> dict:
    db_user = await crud_users.get(db=db, schema_to_select=UserRead, is_deleted=False)
    if db_user is None:
        raise NotFoundException("User not found")

    db_exam_schedule: ExamScheduleRead | None = await crud_exam_schedule.get(
        db=db, schema_to_select=ExamScheduleRead, id=id, is_deleted=False
    )
    if db_exam_schedule is None:
        raise NotFoundException("Exam Schedule not found")
    

    return db_exam_schedule


@router.patch("/exam_schedule/{id}")
# @cache("exam_schedule_cache", resource_id_name="id", pattern_to_invalidate_extra=["exam_schedule:*"])
async def patch_exam_schedule(
    request: Request,
    id: int,
    values: ExamScheduleUpdate,
    current_user: Annotated[UserRead, Depends(get_current_superuser)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> dict[str, str]:
    db_user = await crud_users.get(db=db, schema_to_select=UserRead, UserRead=current_user, is_deleted=False)
    if db_user is None:
        raise NotFoundException("User not found")

    if current_user["id"] != db_user["id"]:
        raise ForbiddenException()

    db_exam_schedule = await crud_exam_schedule.get(db=db, schema_to_select=ExamScheduleRead, id=id, is_deleted=False)
    if db_exam_schedule is None:
        raise NotFoundException("exam_schedule not found")

    await crud_exam_schedule.update(db=db, object=values, id=id)
    return {"message": "exam_schedule updated"}


@router.delete("/exam_schedule/{id}")
# @cache("exam_schedule_cache", resource_id_name="id", to_invalidate_extra={"exam_schedule": "{id}"})
async def erase_exam_schedule(
    request: Request,
    username: str,
    id: int,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> dict[str, str]:
    db_user = await crud_users.get(db=db, schema_to_select=UserRead, is_deleted=False)
    if db_user is None:
        raise NotFoundException("User not found")

    if current_user["id"] != db_user["id"]:
        raise ForbiddenException()

    db_post = await crud_exam_schedule.get(db=db, schema_to_select=ExamScheduleRead, id=id, is_deleted=False)
    if db_post is None:
        raise NotFoundException("exam_schedule not found")

    await crud_exam_schedule.delete(db=db, id=id)

    return {"message": "exam_schedule deleted"}


@router.delete("/db_exam_schedule/{id}", dependencies=[Depends(get_current_superuser)])
# @cache("exam_schedule_cache", resource_id_name="id", to_invalidate_extra={"exam_schedule": "{id}"})
async def erase_db_exam_schedule(
    request: Request, id: int, db: Annotated[AsyncSession, Depends(async_get_db)]
) -> dict[str, str]:
    db_user = await crud_users.get(db=db, schema_to_select=UserRead, is_deleted=False)
    if db_user is None:
        raise NotFoundException("User not found")

    db_post = await crud_exam_schedule.get(db=db, schema_to_select=ExamScheduleRead, id=id, is_deleted=False)
    if db_post is None:
        raise NotFoundException("exam_schedule not found")

    await crud_exam_schedule.db_delete(db=db, id=id)
    return {"message": "exam_schedule deleted from the database"}

