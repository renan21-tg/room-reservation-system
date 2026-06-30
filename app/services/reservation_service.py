from threading import Lock

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.reservation import Reservation, ReservationStatus
from app.repositories.reservation_repository import ReservationRepository
from app.repositories.room_repository import RoomRepository
from app.repositories.user_repository import UserRepository
from app.schemas.reservation import ReservationCreate

reservation_creation_lock = Lock()


class ReservationService:
    def __init__(self, db: Session) -> None:
        self.repository = ReservationRepository(db)
        self.users = UserRepository(db)
        self.rooms = RoomRepository(db)

    def create(self, payload: ReservationCreate, current_user) -> Reservation:
        user_id = current_user.id
        if current_user.role == "admin" and payload.user_id is not None:
            user_id = payload.user_id
        elif payload.user_id is not None and payload.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        if self.users.get(user_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        room = self.rooms.get(payload.room_id)
        if room is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
        if not room.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Room is inactive")

        try:
            with reservation_creation_lock:
                if self.repository.has_conflict(payload.room_id, payload.starts_at, payload.ends_at):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Room already reserved for this time range",
                    )
                data = payload.model_dump(exclude={"user_id"})
                data["user_id"] = user_id
                data["status"] = ReservationStatus.PENDING.value
                reservation = Reservation(**data)
                self.repository.db.add(reservation)
                self.repository.db.commit()
                self.repository.db.refresh(reservation)
                return reservation
        except HTTPException:
            self.repository.db.rollback()
            raise
        except Exception as exc:
            self.repository.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unexpected error",
            ) from exc

    def list(self, current_user, user_id: int | None = None) -> list[Reservation]:
        if current_user.role != "admin":
            return self.repository.list_by_user(current_user.id)
        if user_id is not None:
            return self.repository.list_by_user(user_id)
        return self.repository.list()

    def get(self, reservation_id: int) -> Reservation:
        reservation = self.repository.get(reservation_id)
        if reservation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reservation not found",
            )
        return reservation

    def cancel(self, reservation_id: int, current_user) -> Reservation:
        reservation = self.get(reservation_id)
        if current_user.role != "admin" and reservation.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        reservation.status = ReservationStatus.CANCELED.value
        self.repository.db.commit()
        self.repository.db.refresh(reservation)
        return reservation

    def approve(self, reservation_id: int) -> Reservation:
        reservation = self.get(reservation_id)
        if reservation.status != ReservationStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending reservations can be approved",
            )
        reservation.status = ReservationStatus.APPROVED.value
        self.repository.db.commit()
        self.repository.db.refresh(reservation)
        return reservation

    def reject(self, reservation_id: int) -> Reservation:
        reservation = self.get(reservation_id)
        if reservation.status != ReservationStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending reservations can be rejected",
            )
        reservation.status = ReservationStatus.REJECTED.value
        self.repository.db.commit()
        self.repository.db.refresh(reservation)
        return reservation
