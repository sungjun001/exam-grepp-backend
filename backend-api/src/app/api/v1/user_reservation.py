
from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Body, Query
from fastcrud.paginated import PaginatedListResponse, compute_offset, paginated_response
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, UTC
from sqlalchemy import and_, asc, desc, event
from sqlalchemy.engine import Engine

from ...api.dependencies import get_current_superuser, get_current_user
from ...core.db.database import async_get_db
from ...core.exceptions.http_exceptions import ForbiddenException, NotFoundException, BadRequestException
from ...core.utils.cache import cache
from ...crud.crud_exam_schedule import crud_exam_schedule
from ...crud.crud_users import crud_users
from ...crud.crud_user_reservation import crud_user_reservation
from ...schemas.exam_schedule import ExamScheduleCreate, ExamScheduleCreateInternal, ExamScheduleRead, ExamScheduleUpdate
from ...schemas.user import UserRead
from ...schemas.user_reservation import UserReservationCreate, UserReservationRead, ReservationStatus
from ...models.exam_schedule import ExamScheduleStatus, ExamSchedule
from ...models.user_reservation import UserReservation

import logging

router = APIRouter(tags=["user_reservation"])

@router.post("/user/reservation", response_model=UserReservationRead, status_code=201)
async def create_user_reservation(
    reservation_in: UserReservationCreate,
    current_user: UserRead = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db)
) -> UserReservationRead:
    
    try :
        exam_schedule = await crud_exam_schedule.get(db=db, id=reservation_in.exam_schedule_id)
        if not exam_schedule:
            raise HTTPException(status_code=404, detail="ExamSchedule not found")

        reservation_check = await crud_user_reservation.get(db=db, user_id=current_user["id"], exam_schedule_id=exam_schedule["id"])
        if reservation_check:
            raise HTTPException(status_code=400, detail="User already has a reservation for this exam schedule")

        # 예약할 때의 시간 제한을 검사하는 코드
        if datetime.now(UTC) >= exam_schedule["start_at"] - timedelta(days=3):
            raise HTTPException(status_code=400, detail="Reservations can only be made up to 3 days before the exam starts.")    

        if exam_schedule["confirm_count"] >= exam_schedule["max_users"]:
            raise HTTPException(status_code=400, detail="Maximum number of confirmed reservations reached")

        reservation_in.user_id = current_user["id"]
        reservation_in.exam_schedule_id = exam_schedule["id"]
        exam_schedule["reserve_count"] += 1
        reservation = await crud_user_reservation.create(db=db, object=reservation_in)
        return reservation
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/user/reservation/{reservation_id}/status/{status}", response_model=UserReservationRead)
async def update_user_reservation_status(
    request: Request,
    reservation_id: int,
    status: ReservationStatus ,
    current_user: UserRead = Depends(get_current_superuser),
    db: AsyncSession = Depends(async_get_db)
) -> UserReservationRead:
    db_reservation = await crud_user_reservation.get(db=db, id=reservation_id)
    if not db_reservation:
        raise HTTPException(status_code=404, detail="UserReservation not found")

    exam_schedule = await crud_exam_schedule.get(db=db, id=db_reservation["exam_schedule_id"], status=ExamScheduleStatus.AVAILABLE)
    if not exam_schedule:
        raise HTTPException(status_code=404, detail="ExamSchedule AVAILABLE not found")

    # Only superusers can force confirm beyond the maximum limit
    if db_reservation["status"] == ReservationStatus.RESERVED:
        if status == ReservationStatus.CONFIRMED:
            if exam_schedule["confirm_count"] >= exam_schedule["max_users"]: 
                raise HTTPException(status_code=400, detail="Maximum number of confirmed reservations reached")
            exam_schedule["confirm_count"] += 1
            exam_schedule["reserve_count"] -= 1
        elif status in [ReservationStatus.CANCELLED, ReservationStatus.DELETED]:
            exam_schedule["reserve_count"] -= 1
    elif db_reservation["status"] in [ReservationStatus.CANCELLED, ReservationStatus.DELETED]:
        if status == ReservationStatus.CONFIRMED:
            if exam_schedule["confirm_count"] >= exam_schedule["max_users"]: 
                raise HTTPException(status_code=400, detail="Maximum number of confirmed reservations reached")            
            exam_schedule["confirm_count"] += 1
        elif status == ReservationStatus.RESERVED:
            exam_schedule["reserve_count"] += 1
    elif db_reservation["status"] == ReservationStatus.CONFIRMED:
        if status in [ReservationStatus.CANCELLED, ReservationStatus.DELETED]:
            exam_schedule["confirm_count"] -= 1
        elif status == ReservationStatus.RESERVED:
            exam_schedule["reserve_count"] += 1
    elif db_reservation["status"] == status:
        return db_reservation
    
    if exam_schedule["reserve_count"] < 0:
        exam_schedule["reserve_count"] = 0
        
    if exam_schedule["confirm_count"] < 0:
        exam_schedule["confirm_count"] = 0 

    db_reservation["status"] = status

    if exam_schedule["confirm_count"] >= exam_schedule["max_users"]:
        exam_schedule["status"] = ExamScheduleStatus.FULLY_BOOKED

    if exam_schedule["status"] == ExamScheduleStatus.FULLY_BOOKED and exam_schedule["confirm_count"] < exam_schedule["max_users"]:
        exam_schedule["status"] = ExamScheduleStatus.AVAILABLE  
        

    await crud_exam_schedule.update(db=db, object=exam_schedule, id=exam_schedule["id"])
    await crud_user_reservation.update(db=db, object=db_reservation, id=db_reservation["id"])
    
    return db_reservation

@event.listens_for(Engine, "before_cursor_execute")
@router.get("/user/{username}/reservations", response_model=PaginatedListResponse[UserReservationRead])
async def read_my_reservations(
    request: Request, username: str,
    db: AsyncSession = Depends(async_get_db),
    current_user: UserRead = Depends(get_current_user),
    exam_schedule_id: Optional[int] = None,
    page: int = 1,
    items_per_page: int = 10
) -> dict:
    """
    Retrieves paginated list of reservations for the current logged in user.
    """


    filter_conditions = {"user_id": current_user["id"]}
    if exam_schedule_id is not None:
        filter_conditions["exam_schedule_id"] = exam_schedule_id


    db_reservation = await crud_user_reservation.get_multi(
        db=db, 
        offset=compute_offset(page, items_per_page),
        limit=items_per_page, 
        schema_to_select=UserReservationRead,
        **filter_conditions
        )

    response: dict[str, Any] = paginated_response(crud_data=db_reservation, page=page, items_per_page=items_per_page)    

    
    return response

@router.get("/admin/reservations/list", response_model=PaginatedListResponse[UserReservationRead])
async def read_all_reservations(
    request: Request,
    db: AsyncSession = Depends(async_get_db),
    superuser: UserRead = Depends(get_current_superuser),  # Ensure this endpoint is only accessible by superusers,
    status: Optional[ReservationStatus] = None,
    page: int = 1,
    items_per_page: int = 10,
    order_by: Optional[str] = Query(default="created_at desc", regex="^(created_at|updated_at|status|exam_schedule_id|user_id) (asc|desc)$"),
) -> dict:
    """
    Retrieves a paginated list of all reservations, accessible only by superusers.
    """

    filter_conditions = {}

    if status is not None:
        filter_conditions["status"] = status

    try:
        order_field, order_direction = order_by.split()
    except ValueError:
        raise BadRequestException("Invalid order_by parameter format")        

    order_clause = desc(order_field) if order_direction == "desc" else asc(order_field)            

    db_reservation = await crud_user_reservation.get_multi(
        db=db, 
        offset=compute_offset(page, items_per_page),
        limit=items_per_page, 
        schema_to_select=UserReservationRead,            
        order_by=order_clause,
        **filter_conditions
        
        )        

    response = paginated_response(
        crud_data=db_reservation,
        page=page,
        items_per_page=items_per_page,
    )

    return response    
