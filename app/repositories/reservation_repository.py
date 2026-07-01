from datetime import datetime, date

from sqlalchemy import func

from app.models.reservation import Reservation, ReservationStatus
from app.repositories.base import BaseRepository

BLOCKING_STATUSES = [
    ReservationStatus.PENDING.value,
    ReservationStatus.APPROVED.value,
]


class ReservationRepository(BaseRepository[Reservation]):
    def __init__(self, db) -> None:
        super().__init__(db, Reservation)

    def list_by_user(self, user_id: int) -> list[Reservation]:
        return list(
            self.db.query(Reservation)
            .filter(Reservation.user_id == user_id)
            .order_by(Reservation.starts_at.desc())
            .all()
        )

    def has_conflict(
        self,
        room_id: int,
        starts_at: datetime,
        ends_at: datetime,
    ) -> bool:
        return (
            self.db.query(Reservation)
            .filter(
                Reservation.room_id == room_id,
                Reservation.status.in_(BLOCKING_STATUSES),
                Reservation.starts_at < ends_at,
                Reservation.ends_at > starts_at,
            )
            .first()
            is not None
        )

    def count_active_reservations(self, user_id: int) -> int:
        return (
            self.db.query(Reservation)
            .filter(
                Reservation.user_id == user_id,
                Reservation.status.in_(BLOCKING_STATUSES),
            )
            .count()
        )

    def sum_active_hours_on_day(self, user_id: int, day: date) -> float:
        reservations = (
            self.db.query(Reservation)
            .filter(
                Reservation.user_id == user_id,
                Reservation.status.in_(BLOCKING_STATUSES),
                func.date(Reservation.starts_at) == day.isoformat(),
            )
            .all()
        )
        total_seconds = sum(
            (r.ends_at - r.starts_at).total_seconds() for r in reservations
        )
        return total_seconds / 3600
