from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.reservation import Reservation, ReservationStatus
from app.repositories.reservation_repository import ReservationRepository
from app.repositories.room_repository import RoomRepository
from app.repositories.user_repository import UserRepository
from app.schemas.reservation import ReservationCreate


class ReservationService:
    def __init__(self, db: Session) -> None:
        self.repository = ReservationRepository(db)
        self.users = UserRepository(db)
        self.rooms = RoomRepository(db)

    def create(self, payload: ReservationCreate) -> Reservation:
        if self.users.get(payload.user_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        room = self.rooms.get(payload.room_id)
        if room is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
        if not room.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Room is inactive")

        try:
            if self.repository.has_conflict(payload.room_id, payload.starts_at, payload.ends_at):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Room already reserved for this time range",
                )
            reservation = Reservation(**payload.model_dump())
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

    def list(self, user_id: int | None = None) -> list[Reservation]:
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

    def cancel(self, reservation_id: int) -> Reservation:
        reservation = self.get(reservation_id)
        reservation.status = ReservationStatus.CANCELED.value
        self.repository.db.commit()
        self.repository.db.refresh(reservation)
        return reservation
