from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.reservation import ReservationCreate, ReservationRead
from app.services.reservation_service import ReservationService

router = APIRouter()


@router.post("", response_model=ReservationRead, status_code=status.HTTP_201_CREATED)
def create_reservation(payload: ReservationCreate, db: Session = Depends(get_db)):
    return ReservationService(db).create(payload)


@router.get("", response_model=list[ReservationRead])
def list_reservations(
    user_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
):
    return ReservationService(db).list(user_id=user_id)


@router.get("/{reservation_id}", response_model=ReservationRead)
def get_reservation(reservation_id: int, db: Session = Depends(get_db)):
    return ReservationService(db).get(reservation_id)


@router.patch("/{reservation_id}/cancel", response_model=ReservationRead)
def cancel_reservation(reservation_id: int, db: Session = Depends(get_db)):
    return ReservationService(db).cancel(reservation_id)
