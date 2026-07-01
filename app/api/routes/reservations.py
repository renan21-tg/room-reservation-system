from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.reservation import ReservationCreate, ReservationRead
from app.services.reservation_service import ReservationService

router = APIRouter()


@router.post("", response_model=ReservationRead, status_code=status.HTTP_201_CREATED)
def create_reservation(
    payload: ReservationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ReservationService(db).create(payload, current_user=current_user)


@router.get("", response_model=list[ReservationRead])
def list_reservations(
    user_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ReservationService(db).list(current_user=current_user, user_id=user_id)


@router.get("/{reservation_id}", response_model=ReservationRead)
def get_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reservation = ReservationService(db).get(reservation_id)
    if current_user.role != "admin" and reservation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return reservation


@router.patch("/{reservation_id}/checkin", response_model=ReservationRead)
def check_in_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ReservationService(db).check_in(reservation_id, current_user=current_user)


@router.patch("/{reservation_id}/cancel", response_model=ReservationRead)
def cancel_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ReservationService(db).cancel(reservation_id, current_user=current_user)


@router.patch("/{reservation_id}/approve", response_model=ReservationRead)
def approve_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return ReservationService(db).approve(reservation_id)


@router.patch("/{reservation_id}/reject", response_model=ReservationRead)
def reject_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return ReservationService(db).reject(reservation_id)
