from fastcrud import FastCRUD
from ..models.user_reservation import UserReservation
from ..schemas.user_reservation import (
    UserReservationCreate, UserReservationUpdate,
    UserReservationUpdateInternal, UserReservationDelete
)

CRUDUserReservation = FastCRUD[
    UserReservation,
    UserReservationCreate,
    UserReservationUpdate,
    UserReservationUpdateInternal,
    UserReservationDelete
]

crud_user_reservation = CRUDUserReservation(UserReservation)