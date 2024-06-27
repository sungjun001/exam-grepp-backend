
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastcrud.paginated import PaginatedListResponse, compute_offset, paginated_response
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta


from ...api.dependencies import get_current_superuser, get_current_user
from ...core.db.database import async_get_db
from ...core.exceptions.http_exceptions import ForbiddenException, NotFoundException
from ...core.utils.cache import cache
from ...crud.crud_exam_schedule import crud_exam_schedule
from ...crud.crud_users import crud_users
from ...crud.crud_user_reservation import crud_user_reservation
from ...schemas.exam_schedule import ExamScheduleCreate, ExamScheduleCreateInternal, ExamScheduleRead, ExamScheduleUpdate
from ...schemas.user import UserRead
from ...schemas.user_reservation import UserReservationCreate, UserReservationRead, ReservationStatus


router = APIRouter(tags=["user_reservation"])


@router.post("/user_reservation", response_model=UserReservationRead, status_code=201)
async def create_user_reservation(
    reservation_in: UserReservationCreate,
    current_user: UserRead = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db)
) -> UserReservationRead:
    exam_schedule = await crud_exam_schedule.get(db=db, id=reservation_in.exam_schedule_id)
    if not exam_schedule:
        raise HTTPException(status_code=404, detail="ExamSchedule not found")

    if datetime.utcnow() >= exam_schedule.start_at - timedelta(days=3):
        raise HTTPException(status_code=400, detail="Reservations can only be made up to 3 days before the exam starts.")

    if exam_schedule.confirm_count >= exam_schedule.max_users:
        raise HTTPException(status_code=400, detail="Maximum number of confirmed reservations reached")

    reservation_in.user_id = current_user.id
    reservation = await crud_user_reservation.create(db=db, obj_in=reservation_in)
    return reservation

@router.patch("/user_reservation/{reservation_id}/status", response_model=UserReservationRead)
async def update_user_reservation_status(
    reservation_id: int,
    status: ReservationStatus,
    current_user: UserRead = Depends(get_current_superuser),
    db: AsyncSession = Depends(async_get_db)
) -> UserReservationRead:
    db_reservation = await crud_user_reservation.get(db=db, id=reservation_id)
    if not db_reservation:
        raise HTTPException(status_code=404, detail="UserReservation not found")

    exam_schedule = await crud_exam_schedule.get(db=db, id=db_reservation.exam_schedule_id)
    if not exam_schedule:
        raise HTTPException(status_code=404, detail="ExamSchedule not found")

    # Only superusers can force confirm beyond the maximum limit
    if status == ReservationStatus.CONFIRMED and (current_user.is_superuser or exam_schedule.confirm_count < exam_schedule.max_users):
        if db_reservation.status != ReservationStatus.CONFIRMED:
            exam_schedule.confirm_count += 1
            db_reservation.status = status
    elif status in [ReservationStatus.CANCELLED, ReservationStatus.DELETED] and db_reservation.status == ReservationStatus.CONFIRMED:
        exam_schedule.confirm_count -= 1
        db_reservation.status = status
    else:
        db_reservation.status = status

    await db.commit()
    await db.refresh(db_reservation)

    return db_reservation

@router.get("/my_reservations", response_model=PaginatedListResponse[UserReservationRead])
async def read_my_reservations(
    request: Request,
    db: AsyncSession = Depends(async_get_db),
    current_user: UserRead = Depends(get_current_user),
    page: int = 1,
    items_per_page: int = 10
) -> dict:
    """
    Retrieves paginated list of reservations for the current logged in user.
    """
    db_reservation = await crud_user_reservation.get_multi(db=db, offset=page, limit=items_per_page, user_id=current_user.id)

    response = paginated_response(
        crud_data=db_reservation,
        page=page,
        items_per_page=items_per_page,
        request=request
    )
    
    return response

@router.get("/all_reservations", response_model=PaginatedListResponse[UserReservationRead])
async def read_all_reservations(
    request: Request,
    db: AsyncSession = Depends(async_get_db),
    superuser: UserRead = Depends(get_current_superuser),  # Ensure this endpoint is only accessible by superusers,
    status: ReservationStatus = None,
    page: int = 1,
    items_per_page: int = 10
) -> dict:
    """
    Retrieves a paginated list of all reservations, accessible only by superusers.
    """
    if status:
        db_reservation = await crud_user_reservation.get_multi(db=db, offset=page, limit=items_per_page, status=status)
    else:
        db_reservation = await crud_user_reservation.get_multi(db=db, offset=page, limit=items_per_page)

    response = paginated_response(
        crud_data=db_reservation,
        page=page,
        items_per_page=items_per_page,
        request=request
    )

    return response    
