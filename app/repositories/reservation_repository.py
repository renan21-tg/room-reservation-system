from datetime import datetime

from app.models.reservation import Reservation, ReservationStatus
from app.repositories.base import BaseRepository


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
        """
        Verifica conflito de horário.
        Protegido contra concorrência no SQLite via WAL mode e busy_timeout (em session.py).
        """
        return (
            self.db.query(Reservation)
            .filter(
                Reservation.room_id == room_id,
                Reservation.status == ReservationStatus.ACTIVE.value,
                Reservation.starts_at < ends_at,
                Reservation.ends_at > starts_at,
            )
            .first() is not None
        )
